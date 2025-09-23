# Deployment Documentation

*Comprehensive deployment guides and infrastructure setup for the molecular analysis platform.*

## Overview

This section provides complete deployment strategies, infrastructure configuration, and operational procedures for deploying the molecular analysis dashboard in various environments from development to production.

## Deployment Components

### **[Cloud Deployment](cloud/README.md)**
Cloud infrastructure deployment strategies and configurations
- AWS deployment with ECS/EKS and RDS
- Azure deployment with Container Instances and PostgreSQL
- Google Cloud deployment with GKE and Cloud SQL
- Multi-cloud deployment strategies and considerations
- Auto-scaling and load balancing configurations

### **[Docker Deployment](docker/README.md)**
Containerized deployment strategies and Docker configurations
- Multi-stage Docker build optimization
- Container orchestration with Docker Compose
- Production-ready container configurations
- Container security and resource management
- Development vs production container differences

### **[Environment Configuration](environments/README.md)**
Environment-specific deployment configurations and management
- Development environment setup and configuration
- Staging environment deployment procedures
- Production environment hardening and optimization
- Environment-specific secrets and configuration management
- CI/CD pipeline integration for different environments

### **[Operations](operations/README.md)**
Operational procedures and deployment automation
- Continuous integration and deployment pipelines
- Blue-green and rolling deployment strategies
- Database migration and rollback procedures
- Health monitoring and alerting setup
- Disaster recovery and backup procedures

## Deployment Architecture

### Multi-Environment Strategy
```
┌─────────────────────────────────────────────────────────────┐
│                    Deployment Pipeline                      │
├─────────────────────────────────────────────────────────────┤
│  Development  │    Staging     │     Production             │
│               │                │                            │
│  • Local      │  • Integration │  • Blue-Green Deployment  │
│  • Hot Reload │  • E2E Testing │  • Zero-Downtime Updates  │
│  • Debug Mode │  • Performance │  • High Availability      │
│  • Test Data  │  • Load Tests  │  • Monitoring & Alerts    │
└─────────────────────────────────────────────────────────────┘
```

### Container Orchestration
```yaml
# Production deployment architecture
version: '3.8'

services:
  # API Gateway - Entry point for all requests
  gateway:
    image: molecular-analysis/gateway:${VERSION}
    ports:
      - "80:80"
      - "443:443"
    environment:
      - RATE_LIMIT_REQUESTS_PER_MINUTE=1000
      - JWT_SECRET=${JWT_SECRET}
    depends_on:
      - api
    deploy:
      replicas: 2
      update_config:
        parallelism: 1
        delay: 10s
        failure_action: rollback
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
    networks:
      - frontend
      - backend

  # FastAPI Application Servers
  api:
    image: molecular-analysis/api:${VERSION}
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - STORAGE_TYPE=s3
      - AWS_S3_BUCKET=${S3_BUCKET}
      - LOG_LEVEL=INFO
      - WORKER_PROCESSES=4
    depends_on:
      - postgres
      - redis
    deploy:
      replicas: 3
      update_config:
        parallelism: 1
        delay: 30s
        failure_action: rollback
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - backend
      - database

  # Celery Workers for Molecular Docking
  worker:
    image: molecular-analysis/worker:${VERSION}
    environment:
      - CELERY_BROKER_URL=${REDIS_URL}
      - CELERY_RESULT_BACKEND=${REDIS_URL}
      - DATABASE_URL=${DATABASE_URL}
      - VINA_EXECUTABLE_PATH=/usr/local/bin/vina
      - SMINA_EXECUTABLE_PATH=/usr/local/bin/smina
      - GNINA_EXECUTABLE_PATH=/usr/local/bin/gnina
    depends_on:
      - redis
      - postgres
    deploy:
      replicas: 5
      update_config:
        parallelism: 2
        delay: 10s
      resources:
        limits:
          cpus: '4'
          memory: 4G
        reservations:
          cpus: '2'
          memory: 2G
    networks:
      - backend
      - database

  # PostgreSQL Database
  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=${POSTGRES_DB}
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - POSTGRES_INITDB_ARGS=--auth-host=scram-sha-256
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./database/init:/docker-entrypoint-initdb.d:ro
    deploy:
      replicas: 1
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
      placement:
        constraints:
          - node.role == manager
    networks:
      - database

  # Redis Cache and Message Broker
  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    deploy:
      replicas: 1
      resources:
        limits:
          cpus: '1'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
    networks:
      - backend

  # React Frontend (served by Nginx)
  frontend:
    image: molecular-analysis/frontend:${VERSION}
    environment:
      - VITE_API_BASE_URL=https://${DOMAIN_NAME}/api
      - VITE_WS_URL=wss://${DOMAIN_NAME}/ws
    deploy:
      replicas: 2
      update_config:
        parallelism: 1
        delay: 10s
    networks:
      - frontend

volumes:
  postgres_data:
    driver: local
  redis_data:
    driver: local

networks:
  frontend:
    driver: overlay
    attachable: true
  backend:
    driver: overlay
    internal: true
  database:
    driver: overlay
    internal: true
```

### Infrastructure as Code
```terraform
# main.tf - Terraform infrastructure definition
terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# VPC and Networking
module "vpc" {
  source = "terraform-aws-modules/vpc/aws"

  name = "${var.project_name}-vpc"
  cidr = var.vpc_cidr

  azs             = var.availability_zones
  private_subnets = var.private_subnet_cidrs
  public_subnets  = var.public_subnet_cidrs

  enable_nat_gateway = true
  enable_vpn_gateway = false

  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = var.common_tags
}

# ECS Cluster for Container Orchestration
resource "aws_ecs_cluster" "main" {
  name = "${var.project_name}-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = var.common_tags
}

# Application Load Balancer
resource "aws_lb" "main" {
  name               = "${var.project_name}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = module.vpc.public_subnets

  enable_deletion_protection = var.enable_deletion_protection

  tags = var.common_tags
}

# RDS PostgreSQL Database
resource "aws_db_instance" "postgres" {
  identifier = "${var.project_name}-postgres"

  engine         = "postgres"
  engine_version = "15.4"
  instance_class = var.db_instance_class

  allocated_storage     = var.db_allocated_storage
  max_allocated_storage = var.db_max_allocated_storage
  storage_type          = "gp3"
  storage_encrypted     = true

  db_name  = var.db_name
  username = var.db_username
  password = var.db_password

  vpc_security_group_ids = [aws_security_group.rds.id]
  db_subnet_group_name   = aws_db_subnet_group.main.name

  backup_retention_period = var.db_backup_retention_period
  backup_window          = "03:00-04:00"
  maintenance_window     = "Sun:04:00-Sun:05:00"

  skip_final_snapshot = var.skip_final_snapshot
  deletion_protection = var.enable_deletion_protection

  performance_insights_enabled = true
  monitoring_interval         = 60
  monitoring_role_arn        = aws_iam_role.rds_enhanced_monitoring.arn

  tags = var.common_tags
}

# ElastiCache Redis Cluster
resource "aws_elasticache_subnet_group" "redis" {
  name       = "${var.project_name}-redis-subnet-group"
  subnet_ids = module.vpc.private_subnets
}

resource "aws_elasticache_replication_group" "redis" {
  replication_group_id         = "${var.project_name}-redis"
  description                  = "Redis cluster for ${var.project_name}"

  node_type                    = var.redis_node_type
  num_cache_clusters           = var.redis_num_cache_clusters
  port                         = 6379
  parameter_group_name         = "default.redis7"

  subnet_group_name            = aws_elasticache_subnet_group.redis.name
  security_group_ids           = [aws_security_group.redis.id]

  at_rest_encryption_enabled   = true
  transit_encryption_enabled   = true
  auth_token                   = var.redis_auth_token

  snapshot_retention_limit     = var.redis_snapshot_retention_limit
  snapshot_window             = "03:00-05:00"

  tags = var.common_tags
}

# ECS Task Definition for API Service
resource "aws_ecs_task_definition" "api" {
  family                   = "${var.project_name}-api"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]

  cpu    = var.api_cpu
  memory = var.api_memory

  execution_role_arn = aws_iam_role.ecs_execution_role.arn
  task_role_arn      = aws_iam_role.ecs_task_role.arn

  container_definitions = jsonencode([
    {
      name  = "api"
      image = "${var.ecr_repository_url}:${var.image_tag}"

      portMappings = [
        {
          containerPort = 8000
          protocol      = "tcp"
        }
      ]

      environment = [
        {
          name  = "DATABASE_URL"
          value = "postgresql://${var.db_username}:${var.db_password}@${aws_db_instance.postgres.endpoint}/${var.db_name}"
        },
        {
          name  = "REDIS_URL"
          value = "redis://:${var.redis_auth_token}@${aws_elasticache_replication_group.redis.primary_endpoint_address}:6379"
        },
        {
          name  = "LOG_LEVEL"
          value = "INFO"
        }
      ]

      secrets = [
        {
          name      = "JWT_SECRET"
          valueFrom = aws_ssm_parameter.jwt_secret.arn
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.api.name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "ecs"
        }
      }

      healthCheck = {
        command     = ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"]
        interval    = 30
        timeout     = 5
        retries     = 3
        startPeriod = 60
      }
    }
  ])

  tags = var.common_tags
}

# ECS Service for API
resource "aws_ecs_service" "api" {
  name            = "${var.project_name}-api"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.api.arn
  launch_type     = "FARGATE"

  desired_count                      = var.api_desired_count
  deployment_minimum_healthy_percent = 50
  deployment_maximum_percent         = 200

  network_configuration {
    subnets          = module.vpc.private_subnets
    security_groups  = [aws_security_group.api.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.api.arn
    container_name   = "api"
    container_port   = 8000
  }

  deployment_configuration {
    deployment_circuit_breaker {
      enable   = true
      rollback = true
    }
  }

  depends_on = [aws_lb_listener.main]

  tags = var.common_tags
}
```

### CI/CD Pipeline Configuration
```yaml
# .github/workflows/deploy.yml - GitHub Actions deployment pipeline
name: Deploy to Production

on:
  push:
    branches: [main]
    tags: ['v*']
  workflow_dispatch:

env:
  AWS_REGION: us-west-2
  ECR_REPOSITORY: molecular-analysis-dashboard

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: test
          POSTGRES_USER: test
          POSTGRES_DB: test_molecular_db
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 6379:6379

    steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r requirements-dev.txt

    - name: Run linting
      run: |
        black --check src/ tests/
        isort --check-only src/ tests/
        flake8 src/ tests/
        mypy src/

    - name: Run backend tests
      run: |
        pytest tests/ --cov=src/molecular_analysis_dashboard --cov-fail-under=80
      env:
        DATABASE_URL: postgresql://test:test@localhost/test_molecular_db
        REDIS_URL: redis://localhost:6379/0

    - name: Set up Node.js
      uses: actions/setup-node@v4
      with:
        node-version: '18'
        cache: 'npm'
        cache-dependency-path: frontend/package-lock.json

    - name: Install frontend dependencies
      run: |
        cd frontend
        npm ci

    - name: Run frontend tests
      run: |
        cd frontend
        npm run test -- --coverage
        npm run type-check
        npm run lint

  build-and-push:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main' || startsWith(github.ref, 'refs/tags/v')

    outputs:
      image-tag: ${{ steps.meta.outputs.tags }}
      image-digest: ${{ steps.build.outputs.digest }}

    steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v4
      with:
        aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
        aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        aws-region: ${{ env.AWS_REGION }}

    - name: Login to Amazon ECR
      id: login-ecr
      uses: aws-actions/amazon-ecr-login@v2

    - name: Extract metadata
      id: meta
      uses: docker/metadata-action@v5
      with:
        images: ${{ steps.login-ecr.outputs.registry }}/${{ env.ECR_REPOSITORY }}
        tags: |
          type=ref,event=branch
          type=ref,event=tag
          type=sha,prefix={{branch}}-
          type=raw,value=latest,enable={{is_default_branch}}

    - name: Build and push Docker images
      id: build
      uses: docker/build-push-action@v5
      with:
        context: .
        file: ./docker/Dockerfile.api
        push: true
        tags: ${{ steps.meta.outputs.tags }}
        labels: ${{ steps.meta.outputs.labels }}
        cache-from: type=gha
        cache-to: type=gha,mode=max

  deploy:
    needs: [test, build-and-push]
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main' || startsWith(github.ref, 'refs/tags/v')
    environment: production

    steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v4
      with:
        aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
        aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        aws-region: ${{ env.AWS_REGION }}

    - name: Setup Terraform
      uses: hashicorp/setup-terraform@v3
      with:
        terraform_version: 1.6.0

    - name: Terraform Init
      run: |
        cd infrastructure/terraform
        terraform init

    - name: Terraform Plan
      run: |
        cd infrastructure/terraform
        terraform plan -var="image_tag=${{ needs.build-and-push.outputs.image-tag }}"

    - name: Terraform Apply
      run: |
        cd infrastructure/terraform
        terraform apply -auto-approve -var="image_tag=${{ needs.build-and-push.outputs.image-tag }}"

    - name: Update ECS Service
      run: |
        aws ecs update-service \
          --cluster molecular-analysis-cluster \
          --service molecular-analysis-api \
          --task-definition molecular-analysis-api:LATEST \
          --force-new-deployment

    - name: Wait for deployment
      run: |
        aws ecs wait services-stable \
          --cluster molecular-analysis-cluster \
          --services molecular-analysis-api

    - name: Run smoke tests
      run: |
        # Wait for service to be healthy
        sleep 60

        # Run smoke tests against production
        curl -f https://api.molecular-analysis.com/health

        # Run additional API tests
        python scripts/smoke-tests.py --env production
```

## Security and Compliance

### Production Security Configuration
```yaml
# Security hardening for production deployment
version: '3.8'

services:
  api:
    image: molecular-analysis/api:${VERSION}
    user: "1001:1001"  # Non-root user
    read_only: true
    tmpfs:
      - /tmp:size=100M,noexec,nosuid,nodev
    cap_drop:
      - ALL
    cap_add:
      - CHOWN
      - SETGID
      - SETUID
    security_opt:
      - no-new-privileges:true
    environment:
      - PYTHONDONTWRITEBYTECODE=1
      - PYTHONUNBUFFERED=1
      - SECURE_SSL_REDIRECT=true
      - SESSION_COOKIE_SECURE=true
      - CSRF_COOKIE_SECURE=true
    secrets:
      - jwt_secret
      - db_password
    networks:
      - backend
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
          pids: 100
        reservations:
          cpus: '1'
          memory: 1G

secrets:
  jwt_secret:
    external: true
  db_password:
    external: true

networks:
  backend:
    driver: overlay
    driver_opts:
      encrypted: "true"
```

### Environment-Specific Configurations
```bash
# Production environment variables
# .env.production

# Application Configuration
NODE_ENV=production
DEBUG=false
LOG_LEVEL=INFO
API_WORKERS=4

# Security Configuration
JWT_ALGORITHM=RS256
SESSION_TIMEOUT=1800
RATE_LIMIT_REQUESTS_PER_MINUTE=100
ENABLE_CORS=false
ALLOWED_ORIGINS=https://molecular-analysis.com

# Database Configuration
DATABASE_MAX_CONNECTIONS=20
DATABASE_POOL_TIMEOUT=30
DATABASE_SSL_MODE=require
ENABLE_QUERY_LOGGING=false

# Storage Configuration
STORAGE_TYPE=s3
AWS_S3_BUCKET=molecular-analysis-prod-storage
AWS_S3_REGION=us-west-2
ENABLE_STORAGE_ENCRYPTION=true

# Monitoring Configuration
ENABLE_PROMETHEUS_METRICS=true
SENTRY_DSN=${SENTRY_DSN}
LOG_AGGREGATION_ENDPOINT=${DATADOG_ENDPOINT}

# Feature Flags
ENABLE_NEW_DOCKING_ENGINE=false
ENABLE_BATCH_PROCESSING=true
MAX_CONCURRENT_JOBS_PER_ORG=10
```

## Monitoring and Observability

### Health Check Implementation
```python
# Health check endpoints for deployment validation
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from ..infrastructure.database import get_db_session
import redis
import asyncio
import time

router = APIRouter()

@router.get("/health")
async def health_check():
    """Basic health check - API is responding"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "service": "molecular-analysis-api"
    }

@router.get("/ready")
async def readiness_check(db: AsyncSession = Depends(get_db_session)):
    """Comprehensive readiness check - all dependencies available"""

    checks = {}
    overall_status = "healthy"

    # Database connectivity check
    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = "healthy"
    except Exception as e:
        checks["database"] = f"unhealthy: {str(e)}"
        overall_status = "unhealthy"

    # Redis connectivity check
    try:
        redis_client = redis.from_url(settings.REDIS_URL)
        redis_client.ping()
        checks["redis"] = "healthy"
    except Exception as e:
        checks["redis"] = f"unhealthy: {str(e)}"
        overall_status = "unhealthy"

    # External services check (docking engines)
    try:
        # Check if docking engines are available
        vina_available = await check_vina_availability()
        checks["docking_engines"] = "healthy" if vina_available else "degraded"
    except Exception as e:
        checks["docking_engines"] = f"unhealthy: {str(e)}"
        overall_status = "degraded"

    if overall_status != "healthy":
        raise HTTPException(status_code=503, detail={
            "status": overall_status,
            "checks": checks,
            "timestamp": time.time()
        })

    return {
        "status": overall_status,
        "checks": checks,
        "timestamp": time.time()
    }

@router.get("/metrics")
async def metrics_endpoint():
    """Prometheus-compatible metrics endpoint"""

    # Return Prometheus-formatted metrics
    metrics = [
        f"api_requests_total{{method=\"GET\",status=\"200\"}} {get_request_count()}",
        f"api_response_time_seconds {{get_avg_response_time()}}",
        f"database_connections_active {{get_db_connection_count()}}",
        f"celery_workers_active {{get_active_worker_count()}}",
        f"docking_jobs_queued {{get_queued_job_count()}}",
    ]

    return Response(content="\n".join(metrics), media_type="text/plain")
```

## Best Practices

### Deployment Strategy
- **Blue-Green Deployment**: Zero-downtime deployments with automatic rollback
- **Progressive Rollout**: Gradual traffic shifting to new deployments
- **Health Checks**: Comprehensive health and readiness checks
- **Rollback Strategy**: Automated rollback on deployment failures
- **Security Hardening**: Container and network security best practices

### Infrastructure Management
- **Infrastructure as Code**: Version-controlled infrastructure definitions
- **Environment Parity**: Consistent environments across development, staging, and production
- **Resource Optimization**: Right-sized resources based on actual usage
- **Cost Management**: Resource tagging and cost monitoring
- **Backup and Recovery**: Automated backup and disaster recovery procedures

### Operational Excellence
- **Monitoring and Alerting**: Comprehensive observability and incident response
- **Log Aggregation**: Centralized logging and analysis
- **Performance Monitoring**: Application and infrastructure performance tracking
- **Security Scanning**: Continuous security vulnerability assessment
- **Documentation**: Comprehensive operational runbooks and procedures

## Related Documentation

- **[Operations Guide](operations/README.md)** - Operational procedures and automation
- **[Security Configuration](../security/README.md)** - Security policies and implementation
- **[Database Management](../database/management/README.md)** - Database deployment procedures
- **[Development Guides](../development/guides/README.md)** - Development to deployment workflow
- **[Architecture Overview](../architecture/README.md)** - System architecture and components
