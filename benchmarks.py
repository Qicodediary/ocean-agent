"""
Performance Benchmark Tool
Measures and records model execution performance
"""

import json
import time
import pandas as pd
from datetime import datetime
from app.box_model import run_box_model
from app.logging_config import logger


def run_benchmark(
    station: str = "BATS",
    model: str = "BCC-CSM2-MAR",
    scenario: str = "ssp585",
    start_year: int = 2020,
    end_year: int = 2025,
    output_type: str = "integration",
    num_runs: int = 1
):
    """
    Run benchmark tests and record performance
    
    Args:
        station: BATS or HOT
        model: GCM model name
        scenario: Climate scenario
        start_year, end_year: Simulation range
        output_type: integration or concentration
        num_runs: How many times to run
    """
    
    print("\n" + "="*70)
    print("OCEAN BOX MODEL - PERFORMANCE BENCHMARK")
    print("="*70)
    print(f"Configuration:")
    print(f"  Station: {station}")
    print(f"  Model: {model}")
    print(f"  Scenario: {scenario}")
    print(f"  Year range: {start_year}-{end_year}")
    print(f"  Output type: {output_type}")
    print(f"  Number of runs: {num_runs}")
    print("="*70 + "\n")
    
    results = []
    
    for run_num in range(num_runs):
        print(f"\n[Run {run_num + 1}/{num_runs}]")
        print("-" * 70)
        
        job_id = f"benchmark_{run_num:03d}"
        start_time = time.time()
        
        try:
            # Run model
            result = run_box_model(
                station=station,
                model=model,
                scenario=scenario,
                start_year=start_year,
                end_year=end_year,
                output_type=output_type,
                run_id=job_id
            )
            
            total_time = time.time() - start_time
            
            # Extract performance metrics
            perf = result.get("performance_metrics", {})
            
            record = {
                "run_number": run_num + 1,
                "timestamp": datetime.now().isoformat(),
                "job_id": job_id,
                "station": station,
                "model": model,
                "scenario": scenario,
                "years_simulated": end_year - start_year + 1,
                "output_type": output_type,
                "total_time_seconds": round(total_time, 2),
                "parameter_load_time": round(perf.get("parameter_load_time", 0), 2),
                "data_load_time": round(perf.get("data_load_time", 0), 2),
                "model_run_time": round(perf.get("model_run_time", 0), 2),
                "plotting_time": round(perf.get("plotting_time", 0), 2),
                "status": "success"
            }
            
            results.append(record)
            
            # Print timing breakdown
            print(f"\n✓ Run completed successfully")
            print(f"\nTiming Breakdown:")
            print(f"  Parameter load:    {record['parameter_load_time']:8.2f}s ({record['parameter_load_time']/total_time*100:5.1f}%)")
            print(f"  Data load:         {record['data_load_time']:8.2f}s ({record['data_load_time']/total_time*100:5.1f}%)")
            print(f"  Model calculation: {record['model_run_time']:8.2f}s ({record['model_run_time']/total_time*100:5.1f}%)")
            print(f"  Plotting:          {record['plotting_time']:8.2f}s ({record['plotting_time']/total_time*100:5.1f}%)")
            print(f"  ─────────────────────────────────")
            print(f"  TOTAL:             {total_time:8.2f}s (100.0%)")
            
            logger.info("benchmark_run_completed", extra={
                "job_id": job_id,
                "run_number": run_num + 1,
                "total_time": round(total_time, 2),
                "status": "success"
            })
            
        except Exception as e:
            print(f"\n✗ Run failed: {str(e)}")
            
            record = {
                "run_number": run_num + 1,
                "timestamp": datetime.now().isoformat(),
                "job_id": job_id,
                "station": station,
                "model": model,
                "scenario": scenario,
                "total_time_seconds": round(time.time() - start_time, 2),
                "status": "failed",
                "error": str(e)
            }
            
            results.append(record)
            
            logger.error("benchmark_run_failed", extra={
                "job_id": job_id,
                "run_number": run_num + 1,
                "error": str(e)
            })
    
    # Save results
    print("\n" + "="*70)
    print("BENCHMARK SUMMARY")
    print("="*70)
    
    if results:
        # Convert to DataFrame for analysis
        df = pd.DataFrame(results)
        
        successful_runs = df[df["status"] == "success"]
        
        if len(successful_runs) > 0:
            print(f"\nSuccessful runs: {len(successful_runs)}/{len(results)}")
            print(f"\nExecution Time Statistics:")
            print(f"  Mean:    {successful_runs['total_time_seconds'].mean():8.2f}s")
            print(f"  Min:     {successful_runs['total_time_seconds'].min():8.2f}s")
            print(f"  Max:     {successful_runs['total_time_seconds'].max():8.2f}s")
            print(f"  Std Dev: {successful_runs['total_time_seconds'].std():8.2f}s")
            
            if len(successful_runs) > 1:
                print(f"\nComponent Time Breakdown (averaged):")
                print(f"  Parameter load:    {successful_runs['parameter_load_time'].mean():8.2f}s")
                print(f"  Data load:         {successful_runs['data_load_time'].mean():8.2f}s")
                print(f"  Model calculation: {successful_runs['model_run_time'].mean():8.2f}s")
                print(f"  Plotting:          {successful_runs['plotting_time'].mean():8.2f}s")
        
        if len(successful_runs) < len(results):
            print(f"\nFailed runs: {len(results) - len(successful_runs)}/{len(results)}")
    
    # Save to file
    output_file = "benchmark_results.jsonl"
    with open(output_file, "a") as f:
        for record in results:
            f.write(json.dumps(record) + "\n")
    
    print(f"\n✓ Results saved to: {output_file}")
    print("="*70 + "\n")
    
    return results


if __name__ == "__main__":
    # Quick benchmark: 5-year simulation
    run_benchmark(
        station="BATS",
        model="BCC-CSM2-MAR",
        scenario="ssp585",
        start_year=2020,
        end_year=2025,
        output_type="integration",
        num_runs=1
    )
