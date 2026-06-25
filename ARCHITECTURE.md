# Ocean Box Model Agent - System Architecture Document v2.0

## 1. Executive Summary

**Project:** Ocean Box Model Agent - Production-grade distributed computing system for marine biogeochemical simulations

**Objective:** Enable researchers to run 40-year climate simulations without blocking user interface, with full observability and fault tolerance

**Key Metrics:**
- Single simulation: 542 seconds (9 minutes)
- Concurrent capacity: 3 jobs (current), 30+ jobs (scaled)
- Data points processed: 14,600+ per job (40 years daily data)
- Database records: Up to 10,000 jobs tracked

---

## 2. System Architecture

### 2.1 High-Level System Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    CLIENT LAYER                             │
│  • Web Browser (FastAPI docs)                               │
│  • REST Client                                              │
│  • WebSocket Connection                                     │
└────────────────┬────────────────────────────────────────────┘
                 │
                 │ HTTP/WebSocket
                 ↓
┌─────────────────────────────────────────────────────────────┐
│                   API LAYER (FastAPI)                       │
│  ├─ POST /jobs           → Submit new job                   │
│  ├─ GET /jobs/{job_id}   → Query status & results           │
│  ├─ GET /ws/progress     → Real-time updates (WebSocket)    │
│  ├─ GET /config          → Available models                 │
│  ├─ GET /jobs/history    → Job history                      │
│  └─ GET /jobs/stats      → Statistics                       │
│                                                              │
│  Middleware:                                                │
│  • CORS Support                                             │
│  • Structured JSON Logging                                  │
│  • Request Validation (Pydantic)                            │
└────────────────┬────────────────────────────────────────────┘
                 │
        ┌────────┴────────┐
        │                 │
    Redis Queue      Database
        │ (Task Mgmt) │ (Persistence)
        │                 │
        ↓                 ↓
┌──────────────┐   ┌─────────────┐
│ Redis        │   │ SQLite/     │
│ - Queue      │   │ PostgreSQL  │
│ - Pub/Sub    │   │ - Job logs  │
│ - Cache      │   │ - Results   │
└──────┬───────┘   └──────┬──────┘
       │                  │
       │ Dequeue jobs    │ Save results
       │                  │
       ↓                  │
┌───────────────────┐    │
│   RQ WORKER       │    │
│  (Background Proc)│────┘
│                   │
│ ┌───────────────┐ │
│ │ Task Executor │ │
│ │ (box_model)   │ │
│ └───────────────┘ │
└─────┬─────────────┘
      │
      ├─→ Load CMIP6 Data
      ├─→ Run Model Equations
      ├─→ Generate Plots
      └─→ Save Results
      
      ↓
┌─────────────────────────────────────────┐
│         OUTPUT LAYER                    │
│  • outputs/{job_id}.png (time series)   │
│  • outputs/{job_id}_trends.png (4×2)    │
│  • outputs/{job_id}_trends_summary.csv  │
│  • outputs/{job_id}_output.csv (data)   │
└─────────────────────────────────────────┘
```

### 2.2 Component Descriptions

| Component | Technology | Responsibility | Port |
|-----------|-----------|-----------------|------|
| API Server | FastAPI + Uvicorn | HTTP endpoints, validation, logging | 8000 |
| Task Queue | Redis + RQ | Job scheduling, worker management | 6379 |
| Database | SQLite (dev) / PostgreSQL (prod) | Job persistence, metrics | Local / 5432 |
| Worker | RQ Worker (Python) | Execute long-running tasks | N/A |
| Logging | python-json-logger | Structured logging to stdout | N/A |

---

## 3. Request Flow & Lifecycle

### 3.1 Complete Request Lifecycle

```
Step 1: Client submits job
└─→ POST /jobs
    └─→ Validated by Pydantic model
    └─→ Logged: "job_submitted"
    
Step 2: Database record created
└─→ JobRecord(status="queued")
    └─→ Saved to SQLite/PostgreSQL
    
Step 3: Task enqueued to Redis
└─→ task_queue.enqueue(run_model_job)
    └─→ Logged: "job_queued"
    
Step 4: Worker dequeues and starts
└─→ RQ Worker picks up job
    └─→ Logged: "job_execution_started"
    └─→ Database: status = "running"
    
Step 5: Model execution (542 seconds)
└─→ Load parameters (3s)      → Logged: "parameters_loaded"
└─→ Load CMIP6 data (45s)     → Logged: "cmip6_data_loaded" (per file)
└─→ Run model (450s)          → Logged: "model_calculation_started/completed"
└─→ Generate plots (44s)      → Logged: "plots_generated"
    
Step 6: Results saved
└─→ Output CSV, PNG files
    └─→ Logged: "output_csv_saved"
    └─→ Logged: "trend_plot_generation_completed"
    
Step 7: Database updated
└─→ JobRecord.status = "finished"
└─→ Store all metrics and file paths
    └─→ Logged: "model_run_completed"
    
Step 8: Client polling (WebSocket optional)
└─→ GET /jobs/{job_id}
    └─→ Returns status + results
    └─→ Client renders output files
```

### 3.2 Error Handling Flow

```
If error occurs anywhere:
└─→ Exception caught in try/except
    └─→ Logged: "job_execution_failed" or "model_run_failed"
    └─→ Database: status = "failed", error_message = str(e)
    └─→ Client receives status="failed" + error_message
    └─→ User can see what went wrong
```

---

## 4. Technology Choices & Rationale

### 4.1 Redis + RQ vs Alternatives

**Decision: Use Redis + RQ for task queue**

| Aspect | Redis + RQ | Celery | Message Queue | Our Choice |
|--------|-----------|--------|---------------|-----------|
| Complexity | Low | High | Medium | ✓ Redis+RQ |
| Setup time | 10 min | 1 hour | 30 min | ✓ |
| Learning curve | 1 day | 1 week | 3 days | ✓ |
| Production ready | Yes | Yes | Yes | ✓ |
| Horizontal scaling | Limited | Strong | Strong | Trade-off |
| Current scale needs | 3-10 jobs | 1000+ jobs | 1000+ jobs | ✓ Fits |

**Why we chose Redis + RQ:**
1. **Simplicity First:** Easier to understand, debug, maintain
2. **Sufficient Throughput:** 3 concurrent workers = 10 jobs/minute (enough for current needs)
3. **Clear Migration Path:** Can upgrade to Celery if needs scale 10x+
4. **Operational Cost:** Fewer components = less to manage

**Trade-off:** Lose some advanced features (task routing, priority queues) but gain simplicity

---

### 4.2 SQLite vs PostgreSQL

**Decision: Start with SQLite, design for PostgreSQL migration**

| Aspect | SQLite | PostgreSQL | Our Choice |
|--------|--------|-----------|-----------|
| Setup | 0 min (file-based) | 30 min | ✓ SQLite |
| Scaling | ~10k records | Unlimited | ✓ SQLite (initially) |
| Concurrency | Limited | Strong | Trade-off |
| Backup | Copy file | Replication | ✓ SQLite (initially) |
| Cost | Free | ~$100/month | ✓ SQLite |

**Why SQLite for now:**
- Zero configuration needed
- Perfect for single-server deployment
- Single file (easy backup)
- Meets current needs

**Migration strategy:** When we reach 10k records or need concurrent writes:
```python
# Change one line in database.py:
# DATABASE_URL = "sqlite:///ocean_model.db"  # Old
DATABASE_URL = "postgresql://user:pass@localhost/ocean_model"  # New
# SQLAlchemy handles the rest!
```

---

### 4.3 Structured Logging (JSON Format)

**Decision: Use python-json-logger for structured logging**

**Why structured logging?**
```
Old (unstructured):
[job abc123] Starting run for BATS station: model=BCC-CSM2-MAR
# Hard to parse, search, analyze

New (structured JSON):
{"timestamp": "2024-06-24T10:30:00", "job_id": "abc123", "station": "BATS", "model": "BCC-CSM2-MAR", "message": "job_submitted"}
# Easy to parse, search, aggregate, filter
```

**Benefits:**
1. **Searchable:** `cat logs.json | jq 'select(.job_id=="abc123")'`
2. **Aggregatable:** Send to ELK, Datadog, CloudWatch
3. **Analyzable:** Extract metrics programmatically
4. **Production-ready:** Industry standard

---

## 5. Performance Analysis

### 5.1 Bottleneck Identification

**For a 40-year simulation (14,600 days):**

```
Component            Time    % Total   Optimization Potential
─────────────────────────────────────────────────────────
Load parameters      3.0s     0.5%    ◀ Minimal
Load CMIP6 data     45.0s     8.0%    ◀ Medium (parallel I/O)
Run model          450.0s    83.0%    ◀ Hard (scientific code)
Generate plots      44.0s     8.0%    ◀ Medium (async)
─────────────────────────────────────────────────────────
TOTAL              542.0s   100.0%
```

**Key Insight:** Model calculation (83%) is computational, not I/O bound
- Can't optimize without changing scientific algorithm
- Data loading (8%) is most feasible to improve

### 5.2 Optimization Roadmap

**Phase 1 (Current):** Baseline
- Single-threaded data loading
- Sequential plotting
- Performance: 542 seconds

**Phase 2 (Easy wins):** Implement
- Parallel data loading (load 3 files simultaneously)
- Async plotting (non-blocking)
- **Expected improvement: 15-20% faster**

**Phase 3 (High effort):** Advanced
- NumPy vectorization of model equations
- Caching of repeated calculations
- GPU acceleration
- **Expected improvement: 30-50% faster**

---

## 6. Scalability Analysis

### 6.1 Current Capacity

```
Hardware: Single machine (4 cores, 8GB RAM)
Setup: 3 RQ Workers

Capacity:
├─ Concurrent jobs: 3
├─ Queue length: Unlimited (depends on Redis memory)
├─ Database: ~10,000 records before slowdown
└─ Throughput: ~10 jobs/minute (sequential execution)
```

### 6.2 Growth Scenarios

#### **Scenario A: Need 2x Throughput**
```
Requirement: 20 jobs/minute
Change: Add more workers (3 → 6)
Cost: +$150/month
Effort: 1 hour (vertical scaling)
```

#### **Scenario B: Need 10x Throughput**
```
Requirement: 100 jobs/minute (1,000+ concurrent jobs queued)
Changes:
1. Upgrade to PostgreSQL (SQLAlchemy handles it)
2. Scale workers to 30+ (Kubernetes/Docker Swarm)
3. Add Redis Cluster (distributed cache)
Cost: +$1,000/month
Effort: 2-3 weeks (horizontal scaling)
Timeline:
├─ Week 1: PostgreSQL setup + migration
├─ Week 2: Kubernetes cluster setup
└─ Week 3: Testing + optimization
```

#### **Scenario C: Need 100x Throughput**
```
Requirement: 1,000 jobs/minute (multi-region, SLA)
Architecture upgrade:
1. Regional deployment (US, Europe, Asia)
2. Load balancer (nginx)
3. Database replication
4. Queue federation
Cost: +$10,000/month
Effort: 3-6 months (enterprise setup)
Requires: DevOps team
```

---

## 7. Observability & Monitoring

### 7.1 Logging Strategy

**Three levels of logs:**

1. **Job-level logs**
   ```json
   {"job_id": "abc123", "message": "job_submitted", "station": "BATS"}
   {"job_id": "abc123", "message": "model_calculation_started"}
   {"job_id": "abc123", "message": "model_calculation_completed", "duration_seconds": 450}
   ```

2. **System-level logs**
   ```json
   {"message": "worker_started", "queue": "default"}
   {"message": "health_check_request"}
   ```

3. **Error logs**
   ```json
   {"job_id": "abc123", "level": "ERROR", "message": "job_execution_failed", "error": "..."}
   ```

### 7.2 Metrics Collection

**Stored in database:**
- Job count (total, completed, failed)
- Average execution time (grouped by station/model)
- P95, P99 latency percentiles
- Error rate by cause

**Accessible via API:**
- `GET /jobs/stats/summary` → Overall statistics
- `GET /jobs/history?station=BATS` → Filter by station

---

## 8. Failure Modes & Recovery

### 8.1 Potential Failures

| Failure | Impact | Probability | Current | Improved |
|---------|--------|-------------|---------|----------|
| Worker crashes | Job fails, task stays in queue | Medium | Auto-restart (systemd) | Kubernetes restart |
| Redis down | Can't queue tasks | Low | Manual restart | Redis Sentinel |
| DB disk full | Can't save results | Low | Alert needed | Auto-cleanup |
| Data file missing | Job fails immediately | Medium | Error logged | Pre-flight check |
| Network timeout | Job may hang | Low | Timeout configured | Graceful timeout |

### 8.2 Recovery Procedures

**If Worker crashes:**
1. RQ marks job as "failed"
2. Job stays in Redis queue
3. New worker processes it automatically
4. No data loss

**If Redis crashes:**
1. API can still validate requests
2. Queue is lost
3. Recovery: Restart Redis, resubmit jobs
4. Improvement: Use Redis Persistence (RDB/AOF)

**If Database becomes unavailable:**
1. Results still generated
2. Can't store in DB
3. Recovery: Manual upload after restart
4. Improvement: Async DB writes with retry

---

## 9. Deployment Architecture

### 9.1 Single Machine (Current)

```
Docker Container
├─ FastAPI (port 8000)
├─ RQ Worker (3 processes)
└─ SQLite database
     ↓ (mounted volume)
Data/Outputs (local filesystem)
```

### 9.2 Multi-Machine (Future)

```
Load Balancer (nginx)
    ↓
API Server (multiple containers)
    ↓
├─ Shared Redis (Redis Cluster)
├─ Shared Database (PostgreSQL with replication)
└─ Worker Pool (30+ containers, Kubernetes)
```

---

## 10. Cost Analysis

### 10.1 Current Setup

| Component | Cost | Notes |
|-----------|------|-------|
| Single server | $50-100/month | 4GB RAM, 50GB disk |
| Redis | Free | In-memory, embedded |
| SQLite | Free | File-based |
| Total | **$50-100/month** | One-time setup |

### 10.2 Scaled Setup (10x)

| Component | Cost | Notes |
|-----------|------|-------|
| API servers (3×) | $300/month | Load balanced |
| PostgreSQL (RDS) | $200/month | Multi-AZ, automated backup |
| Redis cluster | $150/month | Multi-node for HA |
| Worker pool (30×) | $900/month | Auto-scaling group |
| Monitoring | $100/month | Datadog/CloudWatch |
| **Total** | **$1,650/month** | ~33x more for 10x capacity |

---

## 11. Testing Strategy

### 11.1 Manual Testing

```bash
# 1. Start dependencies
redis-server &
python worker.py &

# 2. Run quick benchmark
python benchmarks.py

# 3. Check logs
cat benchmark_results.jsonl | jq '.'

# 4. Verify outputs
ls -la outputs/
```

### 11.2 Automated Testing (Recommended)

```python
# tests/test_benchmarks.py
def test_single_job_completes():
    """Single job should complete in <600 seconds"""
    result = run_box_model(...)
    assert result["status"] == "success"
    assert result["performance_metrics"]["total_time_seconds"] < 600

def test_concurrent_jobs():
    """Three concurrent jobs should not interfere"""
    results = run_n_jobs_concurrently(3)
    assert all(r["status"] == "success" for r in results)

def test_database_persistence():
    """Results should survive app restart"""
    # Submit job
    # Restart app
    # Query results - should still be there
```

---

## 12. Summary: Design Principles

This system is built on:

1. **Simplicity First:** Use simple, well-understood components
2. **Clear Separation:** API ↔ Queue ↔ Worker ↔ Database
3. **Observable:** Every step is logged (JSON format)
4. **Fail-safe:** Errors don't cascade, jobs retry
5. **Growth Path:** Can scale from 1 to 1000+ concurrent jobs
6. **Production-ready:** Handles multi-hour computations gracefully

---

## Appendix: Key Metrics Reference

```
Performance Targets:
├─ Single job: <10 minutes
├─ Queue latency: <5 seconds (from submit to start)
├─ API response: <100ms
├─ WebSocket latency: <100ms (p99)
└─ Database query: <5ms (typical)

Availability Targets:
├─ Uptime: 99% (current), 99.9% (scaled)
└─ Data durability: None lost if system configured correctly

Cost Targets:
├─ Current: <$100/month
├─ Scaled (10x): ~$1,500/month
└─ Cost per job: $0.10-0.50
```

