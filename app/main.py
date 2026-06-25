"""
Ocean Box Model Agent - Production FastAPI Application v2.0
Features: WebSocket progress, Database persistence, Structured logging, Performance monitoring
"""

from fastapi import FastAPI, HTTPException, WebSocket, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from redis import Redis
from rq import Queue
from rq.job import Job
from sqlalchemy.orm import Session
import uuid
import json
import time

from app.tasks import run_model_job
from app.database import init_db, get_db, JobRecord
from app.progress import get_job_progress
from app.logging_config import logger

# Initialize database
init_db()

app = FastAPI(
    title="Ocean Box Model Agent API v2.0",
    version="2.0",
    description="Production-grade ocean biogeochemical model with observability"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Redis connection
redis_conn = Redis(host="localhost", port=6379, db=0)
task_queue = Queue("default", connection=redis_conn)


class RunModelRequest(BaseModel):
    """Model run request schema"""
    station: str
    model: str
    scenario: str
    start_year: int
    end_year: int
    output_type: str = "integration"


@app.on_event("startup")
def startup_event():
    """Initialize on startup"""
    logger.info("Ocean Box Model Agent API v2.0 started")


@app.get("/")
def health_check():
    """Health check"""
    logger.info("API health check")
    return {
        "status": "ok",
        "version": "2.0",
        "features": ["WebSocket", "Database", "Structured Logging", "Performance Monitoring"]
    }


@app.get("/config")
def get_config():
    """Get available configurations"""
    from app.box_model import STATION_CONFIG
    
    logger.info("Config request")
    
    config = {}
    for station, info in STATION_CONFIG.items():
        config[station] = {
            "latitude": info["latitude"],
            "models": info["models"],
            "scenarios": info["scenarios"]
        }
    return config


@app.post("/jobs")
def submit_job(req: RunModelRequest, db: Session = Depends(get_db)):
    """Submit a new job"""
    from app.box_model import STATION_CONFIG
    
    job_id = str(uuid.uuid4())[:8]
    
    # Validate
    if req.station not in STATION_CONFIG:
        logger.error(f"Invalid station: {req.station}")
        raise HTTPException(status_code=400, detail=f"Unknown station: {req.station}")
    
    config = STATION_CONFIG[req.station]
    if req.model not in config["models"]:
        logger.error(f"Invalid model {req.model} for station {req.station}")
        raise HTTPException(status_code=400, detail=f"Unknown model: {req.model}")
    
    # Log job submission
    logger.info(f"Job {job_id} submitted: {req.station}/{req.model}/{req.scenario}")
    
    # Save to database
    job_record = JobRecord(
        job_id=job_id,
        station=req.station,
        model=req.model,
        scenario=req.scenario,
        output_type=req.output_type,
        start_year=req.start_year,
        end_year=req.end_year,
        status="queued"
    )
    db.add(job_record)
    db.commit()
    
    # Enqueue
    job = task_queue.enqueue(
        run_model_job,
        station=req.station,
        model=req.model,
        scenario=req.scenario,
        start_year=req.start_year,
        end_year=req.end_year,
        output_type=req.output_type,
        run_id=job_id,
        job_id=job_id,
        job_timeout=3600,
    )
    
    logger.info(f"Job {job_id} queued")
    
    return {
        "job_id": job.id,
        "status": "queued",
        "ws_url": f"ws://127.0.0.1:8000/ws/progress/{job_id}"
    }


@app.get("/jobs/{job_id}")
def get_job_status(job_id: str, db: Session = Depends(get_db)):
    """Query job status and results"""
    logger.info(f"Status query for job {job_id}")
    
    try:
        job = Job.fetch(job_id, connection=redis_conn)
    except Exception:
        logger.error(f"Job {job_id} not found")
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    db_record = db.query(JobRecord).filter(JobRecord.job_id == job_id).first()
    status = job.get_status()
    
    response = {"job_id": job_id, "status": status}
    
    if db_record:
        response["created_at"] = db_record.created_at.isoformat() if db_record.created_at else None
        response["started_at"] = db_record.started_at.isoformat() if db_record.started_at else None
        response["finished_at"] = db_record.finished_at.isoformat() if db_record.finished_at else None
    
    if status == "finished":
        response["result"] = job.result
        if db_record and db_record.total_time:
            response["performance"] = {
                "total_time_seconds": db_record.total_time,
                "data_load_time": db_record.data_load_time,
                "model_run_time": db_record.model_run_time,
                "plotting_time": db_record.plotting_time
            }
    elif status == "failed":
        response["error"] = str(job.exc_info) if job.exc_info else "Unknown error"
    
    return response


@app.websocket("/ws/progress/{job_id}")
async def websocket_progress(websocket: WebSocket, job_id: str):
    """WebSocket endpoint for real-time progress"""
    await websocket.accept()
    
    logger.info(f"WebSocket connected for job {job_id}")
    
    try:
        while True:
            progress = get_job_progress(job_id)
            if progress:
                await websocket.send_json(progress)
            
            try:
                job = Job.fetch(job_id, connection=redis_conn)
                if job.get_status() in ["finished", "failed"]:
                    await websocket.send_json({
                        "job_id": job_id,
                        "stage": "finished" if job.get_status() == "finished" else "failed",
                        "progress_percent": 100 if job.get_status() == "finished" else 0
                    })
                    break
            except Exception:
                pass
            
            import asyncio
            await asyncio.sleep(1)
    
    except Exception as e:
        logger.error(f"WebSocket error for job {job_id}: {str(e)}")
    finally:
        await websocket.close()
        logger.info(f"WebSocket disconnected for job {job_id}")


@app.get("/jobs/stats/summary")
def get_summary(db: Session = Depends(get_db)):
    """Get job statistics"""
    from sqlalchemy import func
    
    logger.info("Stats summary request")
    
    total = db.query(JobRecord).count()
    completed = db.query(JobRecord).filter(JobRecord.status == "finished").count()
    failed = db.query(JobRecord).filter(JobRecord.status == "failed").count()
    
    avg_time = db.query(func.avg(JobRecord.total_time)).filter(
        JobRecord.status == "finished"
    ).scalar()
    
    return {
        "total_jobs": total,
        "completed": completed,
        "failed": failed,
        "in_progress": total - completed - failed,
        "average_execution_time_seconds": round(avg_time, 2) if avg_time else None
    }


@app.get("/jobs/history")
def get_history(limit: int = 20, station: str = None, db: Session = Depends(get_db)):
    """Get job history"""
    logger.info(f"History request: limit={limit}, station={station}")
    
    query = db.query(JobRecord).order_by(JobRecord.created_at.desc()).limit(limit)
    
    if station:
        query = query.filter(JobRecord.station == station)
    
    jobs = query.all()
    
    return [
        {
            "job_id": job.job_id,
            "station": job.station,
            "model": job.model,
            "scenario": job.scenario,
            "status": job.status,
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "total_time": job.total_time,
        }
        for job in jobs
    ]
