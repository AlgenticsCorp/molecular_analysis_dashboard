---
name: Performance Issue
description: Report performance problems or optimization needs
labels: ["type:performance", "priority:high", "status:triage"]
title: "[Performance]: "
assignees: []
---

## ⚡ Performance Issue Summary
Provide a clear description of the performance problem.

## 🔍 Performance Context

### Issue Type
- [ ] **Latency** - Response time too slow
- [ ] **Throughput** - System can't handle load
- [ ] **Memory** - High memory usage/leaks
- [ ] **CPU** - High CPU utilization
- [ ] **Database** - Slow queries/operations
- [ ] **Network** - Bandwidth/connectivity issues
- [ ] **Storage** - Disk I/O bottlenecks
- [ ] **Concurrency** - Thread/process contention
- [ ] **Cache** - Poor cache performance
- [ ] **Scaling** - Horizontal scaling issues

### Affected Component
- [ ] **API Endpoints** - Specific routes
- [ ] **Database Operations** - Queries/transactions
- [ ] **Docking Engine Processing** - Vina/Smina/Gnina
- [ ] **File Processing** - Upload/download/conversion
- [ ] **Job Queue** - Celery task processing
- [ ] **Frontend Rendering** - React component performance
- [ ] **3D Visualization** - 3Dmol.js rendering
- [ ] **Authentication** - JWT/OIDC processing
- [ ] **Multi-tenant Operations** - Organization isolation
- [ ] **Cache Operations** - Redis performance
- [ ] **Storage Operations** - File system/S3

## 📊 Performance Metrics

### Current Performance
**Response Times:**
- Endpoint: `[/api/v1/endpoint]`
- Current: `[X]ms` (p50), `[Y]ms` (p95), `[Z]ms` (p99)
- Expected: `[A]ms` (p50), `[B]ms` (p95), `[C]ms` (p99)

**Throughput:**
- Current: `[X]` requests/second or jobs/hour
- Expected: `[Y]` requests/second or jobs/hour

**Resource Usage:**
- CPU: `[X]%` average, `[Y]%` peak
- Memory: `[X]GB` average, `[Y]GB` peak
- Storage: `[X]GB` used, `[Y]` IOPS

**Database Performance:**
- Query time: `[X]ms` average, `[Y]ms` slowest
- Connection pool: `[X]/[Y]` connections used
- Lock contention: `[X]` blocked queries

### Measurement Details
**How measured:**
- [ ] Application logs
- [ ] APM tool (New Relic, DataDog, etc.)
- [ ] Database monitoring
- [ ] Custom metrics
- [ ] Load testing tools
- [ ] Browser dev tools
- [ ] System monitoring (htop, iostat, etc.)

**Measurement period:** [e.g., "Peak hours 9-11 AM EST over 1 week"]
**Sample size:** [e.g., "1000 requests", "24 hours continuous"]

## 🧪 Reproduction Steps

### Environment Setup
```bash
# Commands to set up test environment
docker compose up -d postgres redis
docker compose up -d api worker
```

### Load Generation
```bash
# Example load test command
curl -X POST /api/v1/molecules \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@large_molecule.sdf"
```

**Test Data:**
- Molecule file size: `[X]MB`
- Number of concurrent users: `[X]`
- Test duration: `[X]` minutes
- Molecular complexity: `[atoms/bonds count]`

### Monitoring Commands
```bash
# Commands used to monitor during testing
docker stats
docker compose logs api -f
top -p $(pgrep -f "celery worker")
```

## 🎯 Performance Targets

### Target Metrics
**API Response Times:**
- Molecule upload: < 2s for 10MB files
- Docking job submission: < 500ms
- Results retrieval: < 1s for 100 results
- Authentication: < 100ms

**Throughput Requirements:**
- Concurrent users: 100+
- Molecules processed: 50/hour per worker
- API requests: 1000/second sustained

**Resource Limits:**
- Memory per container: < 1GB
- CPU per container: < 2 cores under normal load
- Database connections: < 50 per API instance

### Business Impact
**User Experience:**
- [ ] Critical - Users cannot complete workflows
- [ ] High - Significant delays in research work
- [ ] Medium - Some inconvenience but functional
- [ ] Low - Minor optimization opportunity

**System Capacity:**
- [ ] Blocking new customer onboarding
- [ ] Limiting current user growth
- [ ] Approaching capacity limits
- [ ] Proactive optimization

## 🔧 Architecture Context

### Clean Architecture Layer
**Primary Performance Issue:**
- [ ] Domain Layer - Business logic complexity
- [ ] Use Cases - Application service inefficiency
- [ ] Adapters - External service integration
- [ ] Infrastructure - Database/messaging configuration
- [ ] Presentation - API serialization/validation
- [ ] Frontend - React rendering/state management

### Technical Stack Analysis
**Database Performance:**
```sql
-- Slow query example
EXPLAIN ANALYZE SELECT * FROM docking_jobs
WHERE organization_id = 'xxx' AND status = 'running';
```

**API Endpoint Analysis:**
```python
# Bottleneck in code
async def expensive_operation():
    # Point where performance degrades
    pass
```

**Frontend Performance:**
```typescript
// Slow component or operation
const SlowComponent = () => {
  // Performance issue location
};
```

## 🔍 Investigation Data

### Profiling Results
**Backend Profiling:**
```
[Include cProfile, py-spy, or other profiling output]
Top 10 functions by cumulative time:
1. function_name: 2.5s (45%)
2. other_function: 1.2s (20%)
...
```

**Database Query Analysis:**
```sql
-- Query execution plan
[Include EXPLAIN output for slow queries]
```

**Frontend Performance:**
```
[Include browser profiling data, Lighthouse scores]
Performance Score: 65/100
Largest Contentful Paint: 3.2s
First Input Delay: 250ms
```

### System Resources
**Container Resources:**
```
CONTAINER         CPU %    MEM USAGE / LIMIT     MEM %
api               45.3%    512MB / 1GB          51.2%
worker            89.1%    768MB / 2GB          38.4%
postgres          23.7%    256MB / 1GB          25.6%
```

**Database Stats:**
```
Connections: 45/100
Buffer hit ratio: 92%
Slow queries: 15 (last hour)
Index usage: 78%
```

## 💡 Optimization Ideas

### Potential Solutions
**Database Optimizations:**
- [ ] Add missing indexes
- [ ] Optimize query patterns
- [ ] Implement connection pooling
- [ ] Add read replicas
- [ ] Partition large tables

**Application Optimizations:**
- [ ] Add caching layer
- [ ] Optimize serialization
- [ ] Implement async processing
- [ ] Reduce N+1 queries
- [ ] Add pagination

**Infrastructure Optimizations:**
- [ ] Scale containers horizontally
- [ ] Optimize container resources
- [ ] Implement CDN
- [ ] Add load balancing
- [ ] Optimize network configuration

**Frontend Optimizations:**
- [ ] Code splitting
- [ ] Lazy loading
- [ ] Optimize bundle size
- [ ] Implement virtual scrolling
- [ ] Add service worker caching

### Architecture Changes
**Caching Strategy:**
```python
# Example caching implementation
@cache_result(ttl=300)
async def get_docking_results(job_id: str):
    return await repository.get_results(job_id)
```

**Database Schema:**
```sql
-- Proposed index additions
CREATE INDEX idx_docking_jobs_org_status
ON docking_jobs(organization_id, status);
```

## 🧪 Testing Plan

### Performance Testing
**Load Testing:**
- [ ] Baseline performance measurement
- [ ] Stress testing to find limits
- [ ] Endurance testing for stability
- [ ] Spike testing for burst handling

**Monitoring:**
- [ ] Set up performance monitoring
- [ ] Create performance dashboards
- [ ] Implement alerting
- [ ] Track key metrics over time

### Validation Criteria
**Success Metrics:**
- [ ] Response time improved by X%
- [ ] Throughput increased by Y%
- [ ] Resource usage reduced by Z%
- [ ] User satisfaction improved

## 🎯 Implementation Stage
**Related Milestone:** [Stage 0-9 from implementation plan]
**Priority:** [P0/P1/P2/P3]
**Estimated Effort:** [S/M/L/XL]

## 🔗 Related Issues
- Related performance issues: #[numbers]
- Blocking features: #[numbers]
- Architecture decisions: #[numbers]

## 📚 References
- Performance requirements: `project_design/[doc].md`
- Architecture docs: `project_design/ARCHITECTURE.md`
- Monitoring runbook: `project_design/RUNBOOK.md`
- Similar optimizations: [links to past work]

## 📈 Additional Context
**Historical Performance:**
- [ ] Performance was acceptable until [event/change]
- [ ] Gradual degradation over [time period]
- [ ] Sudden regression after [deployment/change]

**User Feedback:**
[Include relevant user complaints or feedback about performance]

**Business Context:**
[Include information about why this performance issue matters to the business]
