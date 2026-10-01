"""
config.py

Central place for settings. Reads from the project-root .env file.
"""

import os
from pathlib import Path
from dotenv import load_dotenv


# Project root:
# metaOS_APK/
BASE_DIR = Path(__file__).resolve().parent.parent

# Project root .env:
# metaOS_APK/.env
ENV_PATH = BASE_DIR / ".env"

# Load environment variables
load_dotenv(ENV_PATH)


DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError(
        f"DATABASE_URL is missing. Expected it in: {ENV_PATH}"
    )


AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")
S3_BUCKET_RAW_CAPTURES = os.getenv("S3_BUCKET_RAW_CAPTURES", "")
S3_BUCKET_SPLAT_OUTPUTS = os.getenv("S3_BUCKET_SPLAT_OUTPUTS", "")
S3_BUCKET_APP_ASSETS = os.getenv("S3_BUCKET_APP_ASSETS", "")