import os
from database import Scan, SessionLocal
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
  
  
# venv\Scripts\activate 
# uvicorn main:app --reload  