# Backend Architecture Documentation

*Server-side architecture, computational engines, and backend service patterns.*

## Overview

This section documents the backend architecture including molecular docking engines, storage adapters, message queues, and server-side service patterns that power the computational workflows.

## Backend Components

### **[Docking Engines](docking-engines.md)**
Molecular docking engine integration and computational workflows
- AutoDock Vina, Smina, and Gnina engine implementations
- Pluggable engine architecture using Ports & Adapters
- Job execution patterns and resource management
- Performance optimization and parallelization strategies

### **[Queue Design](queue-design.md)**
Asynchronous task processing and message queue architecture
- Celery-based distributed task processing
- Task routing and prioritization strategies
- Queue monitoring and failure handling
- Worker scaling and resource allocation

### **[Storage Adapters](storage-adapters.md)**
File storage patterns and molecular data management
- Local and cloud storage adapter implementations
- Molecular file format handling (PDB, SDF, MOL2, PDBQT)
- File validation and conversion pipelines
- Storage security and access control patterns

## Architecture Patterns

### Computational Engine Architecture
```
┌─────────────────────────────────────┐
│         Engine Interface            │ ← Abstract docking engine port
├─────────────────────────────────────┤
│    Vina    │   Smina   │   Gnina    │ ← Concrete engine adapters
├─────────────────────────────────────┤
│        Job Orchestration            │ ← Task scheduling and execution
├─────────────────────────────────────┤
│         Result Processing           │ ← Output parsing and storage
└─────────────────────────────────────┘
```

### Message Queue Architecture
```
┌─────────────────────────────────────┐
│            API Layer                │ ← FastAPI job submission
├─────────────────────────────────────┤
│          Celery Broker              │ ← Redis message broker
├─────────────────────────────────────┤
│     Worker Pool Management          │ ← Dynamic worker scaling
├─────────────────────────────────────┤
│    Compute Node Distribution        │ ← Multi-node job distribution
└─────────────────────────────────────┘
```

### Storage Layer Architecture
```
┌─────────────────────────────────────┐
│        Storage Interface            │ ← Abstract storage port
├─────────────────────────────────────┤
│   Local FS  │    S3     │  MinIO    │ ← Storage adapter implementations
├─────────────────────────────────────┤
│      File Validation Layer          │ ← Format validation & conversion
├─────────────────────────────────────┤
│    Organization Data Isolation      │ ← Multi-tenant file separation
└─────────────────────────────────────┘
```

## Key Features

### 🧮 **Computational Engine Support**
- **Multiple Engines**: Vina, Smina, Gnina with unified interface
- **Pluggable Architecture**: Easy addition of new docking engines
- **Parameter Optimization**: Engine-specific parameter tuning
- **Resource Management**: CPU and memory allocation per job
- **Result Standardization**: Consistent output format across engines

### 📋 **Task Queue Management**
- **Distributed Processing**: Horizontal scaling across multiple workers
- **Priority Queues**: Job prioritization based on user/org requirements
- **Failure Handling**: Automatic retry with exponential backoff
- **Progress Tracking**: Real-time job status and progress updates
- **Resource Monitoring**: Worker health and performance metrics

### 💾 **Storage Management**
- **Multi-format Support**: Native handling of molecular file formats
- **Validation Pipeline**: File format validation and error reporting
- **Access Control**: Organization-based file access restrictions
- **Backup & Recovery**: Automated backup and disaster recovery
- **Performance Optimization**: Caching and compression strategies

## Implementation Guidelines

### Adding New Docking Engines
1. **Implement Engine Interface**: Create adapter implementing `DockingEnginePort`
2. **Configuration**: Add engine configuration to settings
3. **Registration**: Register engine in dependency injection container
4. **Testing**: Add comprehensive unit and integration tests
5. **Documentation**: Update engine documentation and examples

### Scaling Considerations
- **Worker Scaling**: Use `docker compose up -d --scale worker=N`
- **Queue Partitioning**: Separate queues for different job types
- **Resource Allocation**: Configure worker memory and CPU limits
- **Monitoring**: Implement comprehensive metrics and alerting
- **Load Testing**: Regular performance testing under load

### Performance Optimization
- **Job Batching**: Group small jobs for efficient processing
- **Caching**: Cache intermediate results and computations
- **Parallel Processing**: Utilize multi-core processing where possible
- **Resource Pooling**: Reuse expensive resources (databases, engines)
- **Async I/O**: Non-blocking I/O for better throughput

## Related Documentation

- **[System Design](../system-design/README.md)** - Overall architecture patterns
- **[Database Design](../../database/README.md)** - Data persistence patterns
- **[API Contracts](../../api/contracts/rest-api.md)** - Backend API specifications
- **[Deployment Setup](../../deployment/docker/setup.md)** - Backend service deployment
- **[Performance Tuning](../../database/management/performance.md)** - Optimization strategies

## Troubleshooting

### Common Issues
- **Engine Failures**: Check engine logs and configuration
- **Queue Backlog**: Monitor worker capacity and scaling
- **Storage Issues**: Verify permissions and disk space
- **Performance**: Profile bottlenecks and optimize accordingly

### Monitoring Commands
```bash
# Check worker status
docker compose exec worker celery -A app.worker inspect active

# Monitor queue length
docker compose exec redis redis-cli llen default

# Check storage usage
docker compose exec api df -h /app/storage
```
