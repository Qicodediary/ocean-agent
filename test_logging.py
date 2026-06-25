"""
Simple example showing how to use structured logging
"""

import time
from app.logging_config import logger


def simulate_job():
    """Simulate a job with structured logging"""
    
    job_id = "test_job_001"
    
    # Log job start
    logger.info(
        "job_started",
        extra={
            "job_id": job_id,
            "station": "BATS",
            "model": "BCC-CSM2-MAR",
            "scenario": "ssp585"
        }
    )
    
    # Simulate loading data
    print("\n[Simulating data loading...]")
    time.sleep(2)
    
    logger.info(
        "data_loaded",
        extra={
            "job_id": job_id,
            "duration_seconds": 2.1,
            "file_count": 3,
            "file_size_mb": 450
        }
    )
    
    # Simulate running model
    print("[Simulating model calculation...]")
    time.sleep(3)
    
    logger.info(
        "model_calculation_complete",
        extra={
            "job_id": job_id,
            "duration_seconds": 3.5,
            "status": "success"
        }
    )
    
    # Log job finish
    logger.info(
        "job_finished",
        extra={
            "job_id": job_id,
            "total_time_seconds": 5.6,
            "status": "success",
            "mean_phytoplankton": 12.45
        }
    )


if __name__ == "__main__":
    print("="*60)
    print("Structured Logging Example")
    print("="*60)
    print("\nOutput (JSON format):\n")
    
    simulate_job()
    
    print("\n" + "="*60)
    print("✓ Each line above is a valid JSON object!")
    print("You can parse, filter, and analyze these logs easily.")
    print("="*60)
