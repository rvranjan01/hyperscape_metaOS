import os
from database import Asset, Scan, SessionLocal
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from routes.upload import router as upload_router

app = FastAPI(title="Immverse Room Scan API")

# Include the file upload endpoint route
app.include_router(upload_router)

class CreateScanRequest(BaseModel):
  device_name: str
  total_frames: int = 0


@app.get("/")
def root():
  return {"message": "Welcome to the Immverse Room Scan API!"}

@app.get("/health")
def health_check():
  return {"status": "online", "database": "connected"}


@app.post("/scans/create")
def create_scan(request: CreateScanRequest):
  db = SessionLocal()
  new_scan = Scan(
      device_name=request.device_name, total_frames=request.total_frames
  )
  db.add(new_scan)
  db.commit()
  db.refresh(new_scan)
  db.close()

  return {
      "scan_id": new_scan.id,
      "status": new_scan.status,
      "device_name": new_scan.device_name,
  }

@app.get("/scans")
def get_all_scans():
    db = SessionLocal()

    scans = db.query(Scan).all()

    db.close()

    return [
        {
            "scan_id": scan.id,
            "status": scan.status,
            "device_name": scan.device_name,
            "total_frames": scan.total_frames,
        }
        for scan in scans
    ]


@app.get("/scans/{scan_id}/status")
def get_scan_status(scan_id: str):
  db = SessionLocal()
  scan = db.query(Scan).filter(Scan.id == scan_id).first()
  db.close()

  if not scan:
    raise HTTPException(status_code=404, detail="Scan ID not found")

  progress = (
      (scan.uploaded_frames / scan.total_frames * 100)
      if scan.total_frames
      else 0.0
  )

  return {
      "scan_id": scan.id,
      "status": scan.status,
      "uploaded_frames": scan.uploaded_frames,
      "total_frames": scan.total_frames,
      "progress_percentage": round(progress, 2),
  }
  
  
# --- Add this to backend/main.py ---
# (import Asset alongside Scan at the top: `from database import Scan, Asset, SessionLocal`)

@app.get("/scans/{scan_id}/asset")
def get_scan_asset(scan_id: str):
    db = SessionLocal()
    scan = db.query(Scan).filter(Scan.id == scan_id).first()

    if not scan:
        db.close()
        raise HTTPException(status_code=404, detail="Scan ID not found")

    if scan.status != "complete":
        db.close()
        return {"scan_id": scan_id, "status": scan.status, "message": "Not ready yet"}

    asset = (
        db.query(Asset)
        .filter(Asset.scan_id == scan_id, Asset.file_type == "splat")
        .first()
    )
    db.close()

    if not asset:
        raise HTTPException(status_code=404, detail="No splat asset found for this scan")

    # Week 2/local: s3_key is actually a local file path.
    # Week 3, once you're on AWS: swap this for a presigned S3 URL instead.
    return {"scan_id": scan_id, "status": "complete", "splat_path": asset.s3_key}
# venv\Scripts\activate 
# uvicorn main:app --reload  