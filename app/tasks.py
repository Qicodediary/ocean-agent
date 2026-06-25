"""
Task definitions for RQ job queue
All tasks are executed by worker processes
"""

import time
from datetime import datetime
from sqlalchemy.orm import sessionmaker
from app.box_model import run_box_model
from app.database import engine, JobRecord
from app.logging_config import logger


def run_model_job(
    station: str,
    model: str,
    scenario: str,
    start_year: int,
    end_year: int,
    run_id: str,
    output_type: str = "integration"
) -> dict:
    """
    Main task function executed by worker
    Wraps the actual model with database updates and logging
    """
    
    Session = sessionmaker(bind=engine)
    db = Session()
    
    job_start_time = time.time()
    
    try:
        # Update database: mark as started
        job_record = db.query(JobRecord).filter(JobRecord.job_id == run_id).first()
        if job_record:
            job_record.status = "running"
            job_record.started_at = datetime.utcnow()
            db.commit()
        
        logger.info(f"Job {run_id} execution started: {station}/{model}/{scenario}")
        
        # Run the actual model
        result = run_box_model(
            station=station,
            model=model,
            scenario=scenario,
            start_year=start_year,
            end_year=end_year,
            output_type=output_type,
            run_id=run_id
        )
        
        # Update database with results
        total_time = time.time() - job_start_time
        
        if job_record:
            job_record.status = "finished"
            job_record.finished_at = datetime.utcnow()
            job_record.total_time = total_time
            
            # Extract timing from result if available
            if "performance_metrics" in result:
                metrics = result["performance_metrics"]
                job_record.data_load_time = metrics.get("data_load_time")
                job_record.model_run_time = metrics.get("model_run_time")
                job_record.plotting_time = metrics.get("plotting_time")
            
            # Store results
            job_record.mean_surface_phytoplankton = result.get("mean_surface_phytoplankton")
            job_record.mean_subsurface_phytoplankton = result.get("mean_subsurface_phytoplankton")
            job_record.mean_chlorophyll = result.get("mean_chlorophyll")
            job_record.mean_mld = result.get("mean_mld")
            
            # Store file paths
            job_record.plot_path = result.get("plot_path")
            job_record.trend_plot_path = result.get("trend_plot_path")
            job_record.trend_summary_csv = result.get("trend_summary_csv")
            job_record.data_path = result.get("data_path")
            
            db.commit()
        
        logger.info(f"Job {run_id} completed successfully in {round(total_time, 2)}s")
        
        return result
        
    except Exception as e:
        # Update database with error
        if job_record:
            job_record.status = "failed"
            job_record.finished_at = datetime.utcnow()
            job_record.total_time = time.time() - job_start_time
            job_record.error_message = str(e)
            db.commit()
        
        logger.error(f"Job {run_id} failed: {str(e)}")
        
        raise
    
    finally:
        db.close()
