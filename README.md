# Ocean Box Model Agent - Complete User Guide

A web-based system for running a two-layer ocean biogeochemical model with AI agent support. Generates time-series predictions of phytoplankton, zooplankton, nutrients, and chlorophyll under different climate scenarios using CMIP6 data.

**Key Features:**
- RESTful API for submitting model jobs
- Asynchronous task queue (no waiting during long computations)
- Automatic MSTL trend analysis with linear regression
- Support for both Integration (stocks) and Concentration outputs
- Dual stations (BATS and HOT) with multiple GCM models
- 4×2 visualization layout for easy trend comparison

---

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Installation](#installation)
3. [Project Structure](#project-structure)
4. [Quick Start](#quick-start)
5. [Data Preparation](#data-preparation)
6. [Running the System](#running-the-system)
7. [API Documentation](#api-documentation)
8. [Output Files](#output-files)
9. [Troubleshooting](#troubleshooting)

---

## System Requirements

### Easiest Way: Docker Desktop

**Recommended for all users** - Simplest setup, no dependencies management

- **Docker Desktop** (includes Docker and Docker Compose)
  - Download: https://www.docker.com/products/docker-desktop
  - Installation guide: See [INSTALL_DOCKER.md](INSTALL_DOCKER.md)
  - Works on: macOS, Linux, Windows (WSL2)

### Alternative: Traditional Python Setup

If you prefer not to use Docker:

**Software:**
- **Python**: 3.9 or later
- **Redis**: For task queue management
- **Git** (optional, for cloning)

**Operating Systems (Tested):**
- macOS 10.15+
- Ubuntu 18.04 LTS+
- Windows 10/11 (with WSL2)

**Python Package Dependencies:**
All dependencies are in `requirements.txt`. Key packages:
- `fastapi`: Web API framework
- `uvicorn`: ASGI web server
- `redis`, `rq`: Task queue system
- `pandas`, `numpy`: Data processing
- `matplotlib`: Visualization
- `statsmodels`: Time series analysis
- `scikit-learn`: Machine learning utilities

### Hardware Requirements

- **Minimum**: 4GB RAM, 2GB free disk space
- **Recommended**: 8GB+ RAM, 10GB free disk space (for data storage)

---

## Installation

### Option 1️⃣: Docker Compose Setup (Recommended)

**Step 1: Install Docker Desktop**

See detailed instructions: [INSTALL_DOCKER.md](INSTALL_DOCKER.md)

**Step 2: Download and Extract Project**

```bash
cd ~/Desktop
unzip ocean-agent.zip
cd ocean-agent

# Verify files exist
ls -la
# You should see: app/, data/, docker-compose.yml, requirements.txt, etc.
```

**Step 3: Start the System**

```bash
docker-compose up
```

**That's it!** Open browser to `http://127.0.0.1:8000/docs`

---

### Option 2️⃣: Traditional Python Setup

If you prefer not to use Docker:

**Step 1: Ensure Python and Dependencies are Installed**

macOS (using Homebrew):
```bash
brew install python@3.10
brew install redis
python3 --version
redis-cli --version
```

Ubuntu/Debian:
```bash
sudo apt update
sudo apt install python3.10 python3.10-venv python3-pip redis-server
python3 --version
redis-cli --version
```

**Step 2: Download and Set Up the Project**

```bash
cd ~/Desktop
unzip ocean-agent.zip
cd ocean-agent

# Verify files exist
ls -la
```

**Step 3: Create Virtual Environment**

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # macOS/Linux
# or: venv\Scripts\activate  # Windows

# Verify activation (you should see (venv) in your prompt)
```

**Step 4: Install Python Dependencies**

```bash
pip install --upgrade pip
pip install -r requirements.txt

# Verify installation
pip list | grep fastapi
```

**Step 5: Start the System** (see [Quick Start](#quick-start) - Option 2)

---

## Project Structure

After extraction, your project directory should look like this:

```
ocean-agent/
│
├── README_EN.md                    # This file
├── requirements.txt                # Python dependencies
│
├── def_solar_BATS.py              # Core model equations (two functions)
├── worker.py                       # Background worker process
│
├── app/                            # Application code
│   ├── __init__.py
│   ├── main.py                     # FastAPI application and endpoints
│   ├── tasks.py                    # Task functions for worker
│   └── box_model.py                # Model wrapper and utility functions
│
├── data/                           # Data storage (you need to create this)
│   ├── BATS/
│   │   ├── parameters/
│   │   │   └── parameter_input_final.csv
│   │   ├── BCC-CSM2-MAR/
│   │   │   └── ssp585/
│   │   │       ├── rsdscs_Omon_BCC-CSM2-MAR_ssp585_r1i1p1f1_1990-2100_BATS_daily.csv
│   │   │       ├── rsds_Omon_BCC-CSM2-MAR_ssp585_r1i1p1f1_1990-2100_BATS_daily.csv
│   │   │       └── mlotst_Omon_BCC-CSM2-MAR_ssp585_r1i1p1f1_1990-2100_BATS_daily.csv
│   │   └── [4 more GCM models for BATS]
│   │
│   └── HOT/
│       ├── parameters/
│       │   └── parameter_input_final_HOT.csv
│       ├── CanESM5/
│       │   └── ssp585/
│       │       ├── rsdscs_Omon_CanESM5_ssp585_r1i1p1f1_1990-2100_HOT_daily.csv
│       │       ├── rsds_Omon_CanESM5_ssp585_r1i1p1f1_1990-2100_HOT_daily.csv
│       │       └── mlotst_Omon_CanESM5_ssp585_r1i1p1f1_1990-2100_HOT_daily.csv
│       └── [8 more GCM models for HOT]
│
└── outputs/                        # Generated output files (created automatically)
    ├── {job_id}.png
    ├── {job_id}_output.csv
    ├── {job_id}_trends.png
    └── {job_id}_trends_summary.csv
```

**Important Notes:**
- The `data/` directory is NOT included in the zip file. **You must create it and add your own data files.**
- The `outputs/` directory is created automatically when the system runs.
- All paths in the code are **relative paths**, so the system works from any location.

---

## Data Preparation

### Creating the Data Directory Structure

```bash
# From project root (ocean-agent/)

# Create BATS station directories
mkdir -p data/BATS/parameters
mkdir -p data/BATS/BCC-CSM2-MAR/ssp585
mkdir -p data/BATS/CESM2-WACCM/ssp585
mkdir -p data/BATS/CMCC-CM2-SR5/ssp585
mkdir -p data/BATS/CMCC-ESM2/ssp585
mkdir -p data/BATS/GFDL-ESM4/ssp585

# Create HOT station directories
mkdir -p data/HOT/parameters
mkdir -p data/HOT/CanESM5/ssp585
mkdir -p data/HOT/CESM2-WACCM/ssp585
mkdir -p data/HOT/CMCC-CM2-SR5/ssp585
mkdir -p data/HOT/CMCC-ESM2/ssp585
mkdir -p data/HOT/EC-Earth-Veg/ssp585
mkdir -p data/HOT/EC-Earth3/ssp585
mkdir -p data/HOT/GFDL-ESM4/ssp585
mkdir -p data/HOT/IPSL-CM6A-LR/ssp585
mkdir -p data/HOT/NorESM2-MM/ssp585
```

### File Naming Convention

Each model/scenario combination requires **exactly 3 CSV files** with these exact names:

#### BATS Station Files
```
rsdscs_Omon_[MODEL]_[SCENARIO]_r1i1p1f1_1990-2100_BATS_daily.csv
rsds_Omon_[MODEL]_[SCENARIO]_r1i1p1f1_1990-2100_BATS_daily.csv
mlotst_Omon_[MODEL]_[SCENARIO]_r1i1p1f1_1990-2100_BATS_daily.csv
```

Example for BCC-CSM2-MAR, ssp585:
```
rsdscs_Omon_BCC-CSM2-MAR_ssp585_r1i1p1f1_1990-2100_BATS_daily.csv
rsds_Omon_BCC-CSM2-MAR_ssp585_r1i1p1f1_1990-2100_BATS_daily.csv
mlotst_Omon_BCC-CSM2-MAR_ssp585_r1i1p1f1_1990-2100_BATS_daily.csv
```

#### HOT Station Files
```
rsdscs_Omon_[MODEL]_[SCENARIO]_r1i1p1f1_1990-2100_HOT_daily.csv
rsds_Omon_[MODEL]_[SCENARIO]_r1i1p1f1_1990-2100_HOT_daily.csv
mlotst_Omon_[MODEL]_[SCENARIO]_r1i1p1f1_1990-2100_HOT_daily.csv
```

### Parameter Files

Place parameter files in:
- `data/BATS/parameters/parameter_input_final.csv`
- `data/HOT/parameters/parameter_input_final_HOT.csv`

These CSV files **must have a column named 'default'** containing parameter values.

---

## Quick Start

### 🐳 Option 1: Docker Compose (Recommended - Easiest!)

**Prerequisites:** Docker Desktop installed

One command to start everything:

```bash
cd /path/to/ocean-agent
docker-compose up
```

Then open in your browser:
```
http://127.0.0.1:8000/docs
```

**That's it!** All components (Redis, API, 3 Workers) start automatically in one terminal.

What happens:
- ✅ Redis queue starts
- ✅ FastAPI server starts (port 8000)
- ✅ 3 Worker processes start
- ✅ Database initializes
- ✅ All logs visible in one terminal

To stop, press `Ctrl+C`

**Need to install Docker?** See [INSTALL_DOCKER.md](INSTALL_DOCKER.md)

---

### 💻 Option 2: Traditional Python (Alternative)

If you prefer not to use Docker, run these in 3 separate terminal windows:

**Terminal 1: Start Redis**
```bash
redis-server
# Should see: * Ready to accept connections
```

**Terminal 2: Start Worker**
```bash
cd /path/to/ocean-agent
source venv/bin/activate
python worker.py
# Should see: Worker started, listening for jobs...
```

**Terminal 3: Start API**
```bash
cd /path/to/ocean-agent
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
# Should see: Uvicorn running on http://0.0.0.0:8000
```

**Browser: Access the API**
```
http://127.0.0.1:8000/docs
```

---

## Using the API

You'll see the interactive API documentation at `http://127.0.0.1:8000/docs`. You can:
- **POST /jobs** - Submit a new model run
- **GET /jobs/{job_id}** - Check status and get results
- **GET /config** - See available stations, models, scenarios

---

## Running the System

### Full Example: Submit and Monitor a Job

#### Step 1: Submit a Job

In the `/docs` interface, expand **POST /jobs** and click "Try it out".

Enter this request body:
```json
{
  "station": "BATS",
  "model": "BCC-CSM2-MAR",
  "scenario": "ssp585",
  "start_year": 2020,
  "end_year": 2025,
  "output_type": "integration"
}
```

Click "Execute". Response will be:
```json
{
  "job_id": "a1b2c3d4",
  "status": "queued",
  "message": "Job submitted successfully"
}
```

**Note the job_id!**

#### Step 2: Monitor Progress

Watch the worker terminal - you should see:
```
[Job a1b2c3d4] Starting run for BATS station: model=BCC-CSM2-MAR, scenario=ssp585
[Job a1b2c3d4] Loading CMIP6 data...
[Job a1b2c3d4] Running model calculation...
[Job a1b2c3d4] Generating trend plots...
[Job a1b2c3d4] Model run completed!
```

#### Step 3: Retrieve Results

In the `/docs` interface, expand **GET /jobs/{job_id}**.

Enter the job_id (e.g., "a1b2c3d4") and click "Execute".

When status is "finished", the response includes:
```json
{
  "job_id": "a1b2c3d4",
  "status": "finished",
  "result": {
    "station": "BATS",
    "model": "BCC-CSM2-MAR",
    "scenario": "ssp585",
    "output_type": "integration",
    "mean_surface_phytoplankton": 12.345,
    "plot_path": "/path/to/outputs/a1b2c3d4.png",
    "trend_plot_path": "/path/to/outputs/a1b2c3d4_trends.png",
    "trend_summary_csv": "/path/to/outputs/a1b2c3d4_trends_summary.csv",
    "data_path": "/path/to/outputs/a1b2c3d4_output.csv"
  }
}
```

#### Step 4: Access Output Files

Output files are saved in the `outputs/` directory:
- `a1b2c3d4.png` - Time series plot
- `a1b2c3d4_trends.png` - 4×2 trend analysis
- `a1b2c3d4_trends_summary.csv` - Slope and p-value statistics
- `a1b2c3d4_output.csv` - Complete daily data

---

## API Documentation

### Endpoints

#### 1. Health Check
```
GET /
```
Check if API is running.

**Response:**
```json
{
  "status": "ok",
  "message": "Ocean Box Model Agent API is running"
}
```

---

#### 2. Get Available Configuration
```
GET /config
```
List all available stations, models, and scenarios.

**Response:**
```json
{
  "BATS": {
    "latitude": 31,
    "models": ["BCC-CSM2-MAR", "CESM2-WACCM", "CMCC-CM2-SR5", "CMCC-ESM2", "GFDL-ESM4"],
    "scenarios": ["ssp126", "ssp245", "ssp585"]
  },
  "HOT": {
    "latitude": 22,
    "models": ["CanESM5", "CESM2-WACCM", ...],
    "scenarios": ["ssp126", "ssp245", "ssp585"]
  }
}
```

---

#### 3. Submit Model Run Job
```
POST /jobs
```

**Request Body:**
```json
{
  "station": "BATS",           // Required: "BATS" or "HOT"
  "model": "BCC-CSM2-MAR",      // Required: model name from /config
  "scenario": "ssp585",          // Required: scenario from /config
  "start_year": 2020,            // Required: simulation start
  "end_year": 2050,              // Required: simulation end
  "output_type": "integration"   // Optional: "integration" (default) or "concentration"
}
```

**Response:**
```json
{
  "job_id": "a1b2c3d4",
  "status": "queued",
  "message": "Job submitted successfully"
}
```

**Notes:**
- Job runs asynchronously. Returns immediately with `job_id`.
- Use this `job_id` to query results with `/jobs/{job_id}`.

---

#### 4. Query Job Status and Results
```
GET /jobs/{job_id}
```

**URL Parameter:**
- `job_id`: Job ID returned from `/jobs` endpoint

**Response (while running):**
```json
{
  "job_id": "a1b2c3d4",
  "status": "started"
}
```

**Response (when complete):**
```json
{
  "job_id": "a1b2c3d4",
  "status": "finished",
  "result": {
    "station": "BATS",
    "model": "BCC-CSM2-MAR",
    "scenario": "ssp585",
    "output_type": "integration",
    "start_year": 2020,
    "end_year": 2050,
    "latitude": 31,
    "mean_surface_phytoplankton": 12.345,
    "mean_subsurface_phytoplankton": 8.912,
    "mean_chlorophyll": 5.678,
    "mean_mld": 45.23,
    "plot_path": "outputs/a1b2c3d4.png",
    "trend_plot_path": "outputs/a1b2c3d4_trends.png",
    "trend_summary_csv": "outputs/a1b2c3d4_trends_summary.csv",
    "data_path": "outputs/a1b2c3d4_output.csv",
    "status": "success"
  }
}
```

**Possible Status Values:**
- `queued` - Waiting to run
- `started` - Currently executing
- `finished` - Completed successfully
- `failed` - Error occurred

---

## Output Files

For each job, four files are generated in the `outputs/` directory:

### 1. Time Series Plot
**File:** `{job_id}.png`

Shows monthly median values of:
- Surface and subsurface phytoplankton (mmolN m⁻²)
- Surface and subsurface chlorophyll (mg m⁻²)
- Mixed layer depth (m)

### 2. Trend Analysis Plots
**File:** `{job_id}_trends.png`

4×2 layout showing:
- **Rows:** Chla, Pstr, Zstr, Nutstr
- **Columns:** Surface (left), Subsurface (right)

Each subplot shows:
- MSTL trend component (solid line)
- Linear fit (dashed red line)
- Slope and p-value in legend

### 3. Trend Statistics (CSV)
**File:** `{job_id}_trends_summary.csv`

4 rows, 4 columns:
```csv
Variable,Surface (Slope / P-value),Subsurface (Slope / P-value),Unit
Chla,0.001234 / 0.034567,-0.000456 / 0.234567,mg m^-2/yr
Pstr,0.012345 / 0.001234,0.005678 / 0.012345,mmolN m^-2/yr
Zstr,-0.000123 / 0.456789,0.000456 / 0.234567,mmolN m^-2/yr
Nutstr,-0.012345 / 0.001234,0.005678 / 0.012345,mmolN m^-2/yr
```

- **Slope**: Linear trend (units/year)
- **P-value**: Statistical significance (p < 0.05 = significant)

### 4. Complete Time Series Data (CSV)
**File:** `{job_id}_output.csv`

Daily resolution data with columns:
- Date
- Depth_EU, MLZ (mixed layer depth)
- I, I_sub (light levels)
- Pstr, Pstr_sub (phytoplankton)
- Chla, Chla_sub (chlorophyll)
- Zstr, Zstr_sub (zooplankton)
- Nutstr, Nd_str (nutrients)

---

## Troubleshooting

### Common Issues and Solutions

#### 1. "Connection refused" when starting API
```
ERROR: [errno 111] Connection refused
```

**Solution:** Redis server is not running.
```bash
# In Terminal 1, make sure Redis is running:
redis-server
# Should see: "Ready to accept connections"
```

---

#### 2. "ModuleNotFoundError: No module named 'pandas'"
```
ModuleNotFoundError: No module named 'pandas'
```

**Solution:** Dependencies not installed or wrong virtual environment.
```bash
# Make sure venv is activated
source venv/bin/activate
# Reinstall dependencies
pip install -r requirements.txt
```

---

#### 3. Data file not found error
```
FileNotFoundError: data file not found: data/BATS/parameters/parameter_input_final.csv
```

**Solutions:**
1. Check file exists in correct location:
```bash
ls -la data/BATS/parameters/
# Should show: parameter_input_final.csv
```

2. Check file naming is exact (case-sensitive on Linux/Mac):
```bash
# File names must match exactly:
rsdscs_Omon_BCC-CSM2-MAR_ssp585_r1i1p1f1_1990-2100_BATS_daily.csv
rsds_Omon_BCC-CSM2-MAR_ssp585_r1i1p1f1_1990-2100_BATS_daily.csv
mlotst_Omon_BCC-CSM2-MAR_ssp585_r1i1p1f1_1990-2100_BATS_daily.csv
```

---

#### 4. Job stuck in "queued" status forever
**Solution:** Worker process is not running or crashed.

Check worker terminal:
```bash
# If worker crashed, restart it:
python worker.py
```

---

#### 5. API returns 400 error for invalid station/model
```json
{
  "detail": "Unknown station: BATS123"
}
```

**Solution:** Check valid options:
```
1. Go to http://127.0.0.1:8000/config in browser
2. Or call GET /config in the API docs
3. Use exact names from the response
```

---

#### 6. Port 8000 already in use
```
ERROR: [Errno 48] Address already in use
```

**Solution:** Use a different port:
```bash
# Use port 8001 instead
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
# Then access at http://127.0.0.1:8001/docs
```

---

### Getting Help

For issues not covered above:

1. **Check worker terminal** for the actual error message
2. **Verify data files** exist with correct names and paths
3. **Verify Redis is running** (port 6379)
4. **Check file permissions** (data files should be readable)
5. **Check disk space** (10GB recommended for data)

---

## Advanced Usage

### Running Multiple Jobs

You can submit jobs from multiple terminals simultaneously:
```bash
# Terminal A:
curl -X POST "http://127.0.0.1:8000/jobs" \
  -H "Content-Type: application/json" \
  -d '{"station":"BATS","model":"BCC-CSM2-MAR","scenario":"ssp585","start_year":2020,"end_year":2030}'

# Terminal B:
curl -X POST "http://127.0.0.1:8000/jobs" \
  -H "Content-Type: application/json" \
  -d '{"station":"HOT","model":"CanESM5","scenario":"ssp585","start_year":2020,"end_year":2030}'
```

Worker will process them sequentially.

### Using with Python

```python
import requests
import json

# Submit job
response = requests.post(
    "http://127.0.0.1:8000/jobs",
    json={
        "station": "BATS",
        "model": "BCC-CSM2-MAR",
        "scenario": "ssp585",
        "start_year": 2020,
        "end_year": 2050,
        "output_type": "integration"
    }
)
job_id = response.json()["job_id"]
print(f"Job ID: {job_id}")

# Check status
import time
while True:
    status_response = requests.get(f"http://127.0.0.1:8000/jobs/{job_id}")
    status = status_response.json()["status"]
    print(f"Status: {status}")
    
    if status == "finished":
        result = status_response.json()["result"]
        print("Results:", json.dumps(result, indent=2))
        break
    
    time.sleep(10)  # Check every 10 seconds
```

---

## Citation

If you use this model system in your research, please cite:

```
Ocean Box Model Agent (2024)
https://github.com/your-repo
```

---

## License

[Your license here]

---

## Support

For questions or issues:
1. Check this README first
2. Check the Troubleshooting section
3. Review error messages in the worker terminal
4. Contact: [your-email@example.com]

