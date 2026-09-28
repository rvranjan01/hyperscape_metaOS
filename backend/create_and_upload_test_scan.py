"""
create_and_upload_test_scan.py

Quick test helper: creates a scan via the API, then uploads every image in
a folder as chunks, so you don't have to click through Swagger 20 times.

Usage:
    python create_and_upload_test_scan.py test_data\\horse

Make sure uvicorn main:app --reload is running first (default: localhost:8000).
"""

import os
import sys
import requests

API_BASE = "http://127.0.0.1:8000"


def main():
    if len(sys.argv) != 2:
        print("Usage: python create_and_upload_test_scan.py <images_folder>")
        sys.exit(1)

    images_dir = sys.argv[1]
    image_files = sorted(
        f for f in os.listdir(images_dir)
        if f.lower().endswith((".jpg", ".jpeg", ".png"))
    )

    if not image_files:
        print(f"No images found in {images_dir}")
        sys.exit(1)

    print(f"Found {len(image_files)} images in {images_dir}")

    # Step 1: create the scan
    resp = requests.post(
        f"{API_BASE}/scans/create",
        json={"device_name": "test-script", "total_frames": len(image_files)},
    )
    resp.raise_for_status()
    scan_id = resp.json()["scan_id"]
    print(f"Created scan: {scan_id}")

    # Step 2: upload each image as a chunk
    for i, fname in enumerate(image_files, 1):
        fpath = os.path.join(images_dir, fname)
        with open(fpath, "rb") as f:
            resp = requests.post(
                f"{API_BASE}/scans/{scan_id}/upload-chunk",
                files={"chunk": (fname, f, "image/jpeg")},
            )
        resp.raise_for_status()
        data = resp.json()
        print(f"  [{i}/{len(image_files)}] uploaded {fname} -> "
              f"{data['uploaded_frames']}/{data['total_frames']} "
              f"(status: {data['scan_status']})")

    print(f"\nDone. scan_id = {scan_id}")
    print(f"Check status:  GET {API_BASE}/scans/{scan_id}/status")


if __name__ == "__main__":
    main()