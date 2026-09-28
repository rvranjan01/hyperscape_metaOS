"""
worker.py

Background worker that polls the database for scans marked "processing" and
runs them through: COLMAP -> Splatfacto -> mark complete.

MVP design (per plan): simple DB polling, one job at a time. No SQS, no
concurrency. Run this as a second terminal/process alongside `uvicorn main:app`.

Usage:
    cd backend
    venv\\Scripts\\activate
    python -m workers.worker
"""

import os
import sys
import time

# allow `python -m workers.worker` to import sibling modules (database.py etc.)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import Scan, Job, Asset, SessionLocal
from workers.colmap_runner import run_colmap, ColmapError
from workers.splatfacto_runner import run_splatfacto, SplatfactoError

UPLOAD_DIR = "./uploads"       # matches routes/upload.py
PROCESSING_DIR = "./processing"  # colmap + splat working directory
POLL_INTERVAL_SECONDS = 10


def find_next_scan_to_process(db):
    """Grab the oldest scan whose uploads are done but not yet processed."""
    return (
        db.query(Scan)
        .filter(Scan.status == "processing")
        .order_by(Scan.created_at.asc())
        .first()
    )


def process_scan(scan_id: str):
    db = SessionLocal()
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        db.close()
        return

    images_dir = os.path.join(UPLOAD_DIR, scan_id)
    work_dir = os.path.join(PROCESSING_DIR, scan_id)
    colmap_out = os.path.join(work_dir, "colmap")
    splat_out = os.path.join(work_dir, "splat")

    # Track the pipeline stage as a Job row so /status can report it later
    job = Job(scan_id=scan_id, stage="colmap", status="running")
    db.add(job)
    db.commit()

    try:
        print(f"[worker] scan {scan_id}: running COLMAP on {images_dir}")
        model_dir = run_colmap(scan_id, images_dir, colmap_out)

        job.stage = "splat_training"
        db.commit()

        print(f"[worker] scan {scan_id}: running Splatfacto")
        splat_file = run_splatfacto(scan_id, images_dir, model_dir, splat_out)

        # Record the output asset so GET /scans/{id}/asset can find it
        asset = Asset(scan_id=scan_id, file_type="splat", s3_key=splat_file)
        db.add(asset)

        job.stage = "complete"
        job.status = "done"
        scan.status = "complete"
        db.commit()
        print(f"[worker] scan {scan_id}: COMPLETE -> {splat_file}")

    except Exception as e:
        job.status = "failed"
        scan.status = "failed"
        db.commit()
        print(f"[worker] scan {scan_id}: FAILED - {e}")

    finally:
        db.close()


def main_loop():
    print("[worker] started. Polling for scans to process every "
          f"{POLL_INTERVAL_SECONDS}s. Ctrl+C to stop.")
    os.makedirs(PROCESSING_DIR, exist_ok=True)

    while True:
        db = SessionLocal()
        scan = find_next_scan_to_process(db)
        scan_id = scan.id if scan else None
        db.close()

        if scan_id:
            process_scan(scan_id)
        else:
            time.sleep(POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    main_loop()