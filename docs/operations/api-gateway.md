# API Gateway Operations

*Operational procedures and troubleshooting for the API Gateway service.*

## Overview

The API Gateway (OpenResty/Nginx) provides intelligent routing, authentication, and observability for all service communications.

## Key Resources

- **[API Gateway Architecture](../architecture/integration/gateway.md)** - Complete design and patterns
- **[Phase 3A Completion Status](../implementation/phases/phase-3/completion-reports/phase-3a-completion.md)** - Implementation details
- **[Docker Setup Guide](../deployment/docker/setup.md)** - Container orchestration
- **[Security Configuration](../security/architecture.md)** - JWT and authentication setup

## Operational Procedures

### Health Monitoring
```bash
# Check gateway health
curl -f http://localhost:80/health

# Monitor service routing
docker compose logs gateway

# Check service discovery
docker compose exec gateway nginx -t
```

### Common Operations

**Reload Configuration:**
```bash
docker compose exec gateway nginx -s reload
```

**Scale Backend Services:**
```bash
docker compose up -d --scale api=3
```

**Monitor Request Routing:**
```bash
docker compose logs -f gateway | grep -E "(upstream|backend)"
```

## Configuration Files

- **Gateway Config**: `docker/nginx.conf`
- **Service Discovery**: `docker-compose.yml`
- **SSL/TLS Setup**: See [Production Deployment](../deployment/cloud/production.md)

## Troubleshooting

For detailed troubleshooting procedures, see the [Operations Runbook](runbook.md).
