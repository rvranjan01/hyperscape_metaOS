import os
import shutil
from database import Scan, SessionLocal
from fastapi import APIRouter, File, HTTPException, UploadFile

router = APIRouter()

UPLOAD_DIR = "./uploads"


@router.post("/scans/{scan_id}/upload-chunk")
async def upload_chunk(scan_id: str, chunk: UploadFile = File(...)):
  db = SessionLocal()
  scan = db.query(Scan).filter(Scan.id == scan_id).first()

  if not scan:
    db.close()
    raise HTTPException(status_code=404, detail="Scan ID not found")

  # Create folder for specific scan if it does not exist
  scan_dir = os.path.join(UPLOAD_DIR, scan_id)
  os.makedirs(scan_dir, exist_ok=True)

  # Save uploaded chunk file to local disk
  file_path = os.path.join(scan_dir, chunk.filename)
  with open(file_path, "wb") as buffer:
    shutil.copyfileobj(chunk.file, buffer)

  # Increment uploaded frames count
  scan.uploaded_frames += 1

  # Update status once total frames are reached
  if scan.total_frames > 0 and scan.uploaded_frames >= scan.total_frames:
    scan.status = "processing"

  db.commit()
  db.refresh(scan)
  db.close()

  return {
      "status": "received",
      "filename": chunk.filename,
      "uploaded_frames": scan.uploaded_frames,
      "total_frames": scan.total_frames,
      "scan_status": scan.status,
  }