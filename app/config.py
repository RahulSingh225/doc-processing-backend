from dotenv import load_dotenv
import os

load_dotenv()

class Config:
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
    S3_BUCKET = os.getenv("S3_BUCKET")
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    MAX_WORKERS = int(os.getenv("MAX_WORKERS", 4))
    TEMP_FILE_TTL = int(os.getenv("TEMP_FILE_TTL", 86400))  # Seconds

config = Config()