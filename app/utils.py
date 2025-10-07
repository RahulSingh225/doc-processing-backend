import boto3
import uuid
import os
from fastapi import HTTPException
from app.config import config

s3_client = boto3.client(
    's3',
    aws_access_key_id=config.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY,
    region_name='ap-south-1'
)

def generate_presigned_url(key: str, method: str = 'put_object', expires_in: int = 3600):
    try:
        return s3_client.generate_presigned_url(
            method,
            Params={'Bucket': config.S3_BUCKET, 'Key': key},
            ExpiresIn=expires_in
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate URL: {str(e)}")

def download_from_s3(key: str, local_path: str):
    s3_client.download_file(config.S3_BUCKET, key, local_path)

def upload_to_s3(local_path: str, key: str):
    s3_client.upload_file(local_path, config.S3_BUCKET, key)
    os.remove(local_path)  # Cleanup temp file

def validate_file(key: str):
    # Basic validation: Check extension, size via head_object
    try:
        head = s3_client.head_object(Bucket=config.S3_BUCKET, Key=key)
        if head['ContentLength'] > 500 * 1024 * 1024:  # 500MB limit
            raise ValueError("File too large")
        # Add MIME check or ClamAV scan here if integrated
        return True
    except Exception as e:
        raise HTTPException(400, detail=f"Invalid file: {str(e)}")

def generate_job_id():
    return str(uuid.uuid4())