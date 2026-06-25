"""
RQ Worker Process
Background process that executes queued jobs
Run this in a separate terminal window
"""

from redis import Redis
from rq import Worker, Queue
from app.tasks import run_model_job
from app.logging_config import logger

if __name__ == "__main__":
    redis_conn = Redis(host="localhost", port=6379, db=0)
    q = Queue("default", connection=redis_conn)
    
    logger.info("Ocean Box Model Worker started")
    
    print("Worker started, listening for jobs...")
    print("Press Ctrl+C to stop")
    
    worker = Worker([q], connection=redis_conn)
    worker.work()
