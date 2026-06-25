"""
Enhanced version of box_model.py that tracks timing for each step
This is a wrapper around the original box_model.run_box_model
"""

import time
from datetime import datetime
from app.box_model import run_box_model as original_run_box_model


class TimingTracker:
    """Track timing for each step"""
    def __init__(self):
        self.timings = {}
        self.step_start_time = None
        self.total_start_time = time.time()
    
    def start_step(self, step_name):
        """Mark the start of a step"""
        self.step_start_time = time.time()
        print(f"\n  ⏱️  Starting: {step_name}")
    
    def end_step(self, step_name):
        """Mark the end of a step and record timing"""
        elapsed = time.time() - self.step_start_time
        self.timings[step_name] = elapsed
        print(f"  ✓ {step_name}: {elapsed:.1f}s")
    
    def get_summary(self):
        """Get timing summary"""
        total_time = time.time() - self.total_start_time
        return {
            "total_time": total_time,
            "step_timings": self.timings
        }


def run_box_model_with_timing(
    station: str,
    model: str,
    scenario: str,
    start_year: int,
    end_year: int,
    output_type: str,
    run_id: str
) -> dict:
    """
    Run model with detailed timing information
    
    Returns the same result as original, plus timing breakdown
    """
    
    timer = TimingTracker()
    
    print(f"\n{'='*60}")
    print(f"Running model with performance tracking")
    print(f"{'='*60}")
    
    try:
        timer.start_step("Model Execution")
        result = original_run_box_model(
            station=station,
            model=model,
            scenario=scenario,
            start_year=start_year,
            end_year=end_year,
            output_type=output_type,
            run_id=run_id
        )
        timer.end_step("Model Execution")
        
        # Add timing information to result
        timing_summary = timer.get_summary()
        result["performance_metrics"] = {
            "total_time_seconds": round(timing_summary["total_time"], 2),
            "step_breakdown": {
                step: round(duration, 2)
                for step, duration in timing_summary["step_timings"].items()
            }
        }
        
        return result
        
    except Exception as e:
        print(f"Error: {e}")
        raise
