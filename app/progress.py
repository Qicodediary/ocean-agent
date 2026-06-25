"""
Progress tracking and performance monitoring
Stores progress updates for WebSocket broadcasting
"""

import time
from typing import Dict, List
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum


class ProgressStage(Enum):
    """Job execution stages"""
    QUEUED = "queued"
    LOADING_PARAMS = "loading_parameters"
    LOADING_DATA = "loading_cmip6_data"
    RUNNING_MODEL = "running_model_calculation"
    GENERATING_PLOTS = "generating_plots"
    FINISHED = "finished"
    FAILED = "failed"


@dataclass
class ProgressUpdate:
    """Single progress update"""
    job_id: str
    stage: str
    progress_percent: int  # 0-100
    message: str
    elapsed_time: float  # seconds
    eta_seconds: float  # estimated remaining time
    timestamp: str  # ISO format


class ProgressTracker:
    """Track job progress and performance"""
    
    def __init__(self, job_id: str):
        self.job_id = job_id
        self.start_time = time.time()
        self.stage_times: Dict[str, float] = {}
        self.updates: List[ProgressUpdate] = []
        self.current_stage = ProgressStage.QUEUED.value
        self.progress_map = {
            ProgressStage.QUEUED.value: 0,
            ProgressStage.LOADING_PARAMS.value: 5,
            ProgressStage.LOADING_DATA.value: 20,
            ProgressStage.RUNNING_MODEL.value: 50,
            ProgressStage.GENERATING_PLOTS.value: 85,
            ProgressStage.FINISHED.value: 100,
            ProgressStage.FAILED.value: 0,
        }
        self.stage_start_time = time.time()
    
    def update(self, stage: str, message: str, eta_seconds: float = 0):
        """Record a progress update"""
        elapsed = time.time() - self.start_time
        progress = self.progress_map.get(stage, 0)
        
        # Record stage timing
        if self.current_stage != stage:
            stage_duration = time.time() - self.stage_start_time
            self.stage_times[self.current_stage] = stage_duration
            self.current_stage = stage
            self.stage_start_time = time.time()
        
        update = ProgressUpdate(
            job_id=self.job_id,
            stage=stage,
            progress_percent=progress,
            message=message,
            elapsed_time=round(elapsed, 1),
            eta_seconds=round(eta_seconds, 1),
            timestamp=datetime.utcnow().isoformat()
        )
        self.updates.append(update)
        return update
    
    def finish(self):
        """Mark job as finished and record final timing"""
        self.stage_times[self.current_stage] = time.time() - self.stage_start_time
        return {
            "total_time": time.time() - self.start_time,
            "stage_times": self.stage_times,
            "updates": [asdict(u) for u in self.updates]
        }
    
    def get_latest_update(self) -> ProgressUpdate:
        """Get the most recent update"""
        return self.updates[-1] if self.updates else None


# Global progress storage (in production, use Redis)
_progress_store: Dict[str, ProgressTracker] = {}


def get_progress_tracker(job_id: str) -> ProgressTracker:
    """Get or create progress tracker for job"""
    if job_id not in _progress_store:
        _progress_store[job_id] = ProgressTracker(job_id)
    return _progress_store[job_id]


def get_job_progress(job_id: str) -> dict:
    """Get current progress for job"""
    tracker = _progress_store.get(job_id)
    if not tracker:
        return None
    
    latest = tracker.get_latest_update()
    if not latest:
        return None
    
    return {
        "job_id": job_id,
        "stage": latest.stage,
        "progress_percent": latest.progress_percent,
        "message": latest.message,
        "elapsed_time": latest.elapsed_time,
        "eta_seconds": latest.eta_seconds,
        "timestamp": latest.timestamp
    }


def clear_progress(job_id: str):
    """Clean up progress tracker"""
    if job_id in _progress_store:
        del _progress_store[job_id]
