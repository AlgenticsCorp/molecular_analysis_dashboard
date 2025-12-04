# Job Polling System - Required Improvements

## Critical Issues to Fix

### 1. **Add Maximum Retry Limit**
**Current:** Retries forever on API errors  
**Fix:** Add max_retries parameter to Celery task

```python
@celery_app.task(name="mad.poll_job_status", bind=True, max_retries=10)
def poll_job_status(self, execution_id: str, external_job_id: str, task_id: str):
    # Add retry with exponential backoff
    try:
        # ... polling logic ...
    except Exception as exc:
        raise self.retry(exc=exc, countdown=min(60 * (2 ** self.request.retries), 600))
```

### 2. **Add Job Timeout Mechanism**
**Current:** Jobs can poll indefinitely  
**Fix:** Check job age and fail if exceeds timeout

```python
# In task_framework_executions table, check created_at
job_age = datetime.now() - execution.created_at
MAX_JOB_DURATION = timedelta(hours=24)  # Configurable per task type

if job_age > MAX_JOB_DURATION and new_status == "running":
    update_fields["status"] = "failed"
    update_fields["error_message"] = f"Job timeout after {MAX_JOB_DURATION}"
    update_fields["completed_at"] = datetime.now()
```

### 3. **Implement Orphaned Job Recovery**
**Current:** If worker crashes, jobs stuck in "running" forever  
**Fix:** Periodic task to check for stale running jobs

```python
@celery_app.task(name="mad.recover_orphaned_jobs")
def recover_orphaned_jobs():
    """Find running jobs with no recent polling activity and restart polling."""
    # Query jobs with status='running' and updated_at > 5 minutes ago
    # Re-schedule poll_job_status for each
```

### 4. **Add Polling Deduplication**
**Current:** Multiple workers could poll same job  
**Fix:** Use Redis lock before polling

```python
from redis import Redis
redis_client = Redis.from_url(os.getenv("CELERY_BROKER_URL"))

lock_key = f"poll_lock:{execution_id}"
if not redis_client.set(lock_key, "1", nx=True, ex=45):  # 45s lock
    logger.info(f"Another worker is polling {execution_id}, skipping")
    return {"status": "skipped", "message": "Already being polled"}
```

### 5. **Download Result Files Locally**
**Current:** Only stores NeuroSnap Cloud URLs  
**Fix:** Download files and store in execution_files table

```python
import httpx

for filename, url in download_urls.items():
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers={"X-API-KEY": get_api_key()})
        if response.status_code == 200:
            await file_service.store_output_file(
                execution_id=execution_id,
                parameter_name="output",
                file_content=response.content,
                filename=filename,
                content_type=response.headers.get("content-type", "application/octet-stream")
            )
```

## Testing Checklist

### Unit Tests Needed:
- [ ] Poll job that's already completed (early exit)
- [ ] Poll job that transitions running → completed
- [ ] Poll job that fails
- [ ] Poll job that gets cancelled
- [ ] NeuroSnap API returns 404 (job not found)
- [ ] NeuroSnap API returns 500 (server error)
- [ ] NeuroSnap API timeout
- [ ] Malformed JSON response from NeuroSnap
- [ ] Database update failure
- [ ] Result fetch succeeds but file download fails
- [ ] Job exceeds timeout duration
- [ ] Concurrent polling attempts (deduplication)

### Integration Tests Needed:
- [ ] Submit real job → poll until completion → verify results
- [ ] Submit job → kill worker mid-poll → verify recovery
- [ ] Submit 10 concurrent jobs → verify all complete correctly
- [ ] Test with NeuroSnap API rate limiting
- [ ] Test with slow NeuroSnap responses (30+ seconds)

## Monitoring & Observability

### Add Metrics:
- Counter: `polling_attempts_total{status}`
- Gauge: `jobs_currently_polling`
- Histogram: `polling_duration_seconds`
- Counter: `polling_errors_total{error_type}`

### Add Logging:
```python
logger.info(f"Poll attempt {self.request.retries + 1}/{self.max_retries} for {execution_id}")
logger.warning(f"Job {execution_id} has been running for {job_age}, max is {MAX_JOB_DURATION}")
logger.error(f"Polling failed for {execution_id}: {error_type}", extra={"execution_id": execution_id})
```

## Configuration Needed

Add to environment variables:
```bash
# Polling configuration
POLLING_INTERVAL_SECONDS=30
POLLING_MAX_RETRIES=10
POLLING_RETRY_BACKOFF_BASE=60
POLLING_MAX_RETRY_DELAY=600

# Job timeouts (seconds)
JOB_TIMEOUT_GNINA=86400  # 24 hours
JOB_TIMEOUT_DEFAULT=43200  # 12 hours

# Recovery
ORPHANED_JOB_CHECK_INTERVAL=300  # 5 minutes
ORPHANED_JOB_THRESHOLD=300  # Consider orphaned if no update in 5 minutes
```
