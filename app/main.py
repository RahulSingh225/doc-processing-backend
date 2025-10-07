from fastapi import FastAPI, Depends, WebSocket, HTTPException
from fastapi.responses import JSONResponse
from concurrent.futures import ThreadPoolExecutor
import asyncio
import redis
import json
from typing import Dict
from app.config import config
from app.models import ProcessRequest, StatusResponse
from app.operations.factory import OperationFactory
from app.utils import generate_presigned_url, validate_file, generate_job_id

app = FastAPI()
executor = ThreadPoolExecutor(max_workers=config.MAX_WORKERS)
redis_client = redis.from_url(config.REDIS_URL)
pubsub = redis_client.pubsub()

async def execute_operation(job_id: str, operation_name: str, inputs: Dict):
    """Async wrapper for operation execution."""
    try:
        op = OperationFactory.get(operation_name)
        # Run the async execute directly (no sync wrapper needed)
        result = await op.execute({'job_id': job_id, **inputs})
        output_key = result['output_key']
        download_url = generate_presigned_url(output_key, 'get_object', 3600)
        redis_client.hset(f"job:{job_id}", mapping={
            "status": "completed",
            "download_url": download_url,
            "metadata": json.dumps(result.get('metadata', {}))
        })
        redis_client.expire(f"job:{job_id}", config.TEMP_FILE_TTL)
        redis_client.publish("job_updates", json.dumps({"job_id": job_id, "status": "completed"}))
    except Exception as e:
        redis_client.hset(f"job:{job_id}", "status", "failed")
        redis_client.hset(f"job:{job_id}", "error", str(e))
        redis_client.publish("job_updates", json.dumps({"job_id": job_id, "status": "failed"}))

        
@app.get("/upload-url")
async def get_upload_url(file_name: str):
    key = f"uploads/{file_name}"
    url = generate_presigned_url(key, 'put_object')
    return {"upload_url": url, "key": key}

@app.post("/process", response_model=Dict[str, str])
async def process_document(request: ProcessRequest):
    job_id = generate_job_id()
    for key in request.file_keys:
        validate_file(key)
    inputs = {"file_keys": request.file_keys, "options": request.options}
    redis_client.hset(f"job:{job_id}", mapping={
        "status": "pending",
        "operation": request.operation,
        "inputs": json.dumps(inputs)
    })
    asyncio.create_task(execute_operation(job_id, request.operation, inputs))
    return {"job_id": job_id}

@app.get("/status/{job_id}", response_model=StatusResponse)
async def get_status(job_id: str):
    data = redis_client.hgetall(f"job:{job_id}")
    if not data:
        raise HTTPException(404, "Job not found")
    return StatusResponse(
        status=data.get(b"status", b"unknown").decode(),
        download_url=data.get(b"download_url", None).decode() if b"download_url" in data else None,
        error=data.get(b"error", None).decode() if b"error" in data else None
    )

@app.get("/debug-config")
async def debug_config():
    return {"s3_bucket": config.S3_BUCKET, "aws_access_key": config.AWS_ACCESS_KEY_ID[:4] + "..." if config.AWS_ACCESS_KEY_ID else None}


# WebSocket for real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    pubsub.subscribe("job_updates")
    try:
        while True:
            message = pubsub.get_message(ignore_subscribe_messages=True)
            if message:
                data = json.loads(message['data'])
                await websocket.send_json(data)
            await asyncio.sleep(0.1)
    finally:
        pubsub.unsubscribe()