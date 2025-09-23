# CI/CD Pipeline

*Automated testing and deployment workflows for continuous integration and delivery.*

## Overview

Our CI/CD pipeline uses **GitHub Actions** for automated testing, building, and deployment. The pipeline ensures code quality, runs comprehensive tests, and deploys to appropriate environments based on branch and tags.

## Pipeline Architecture

### Branch-based Workflows

#### Pull Request Pipeline
```yaml
# Triggered on: PR to dev/main branches
# Purpose: Quality gates and testing
# Duration: ~8-12 minutes

Jobs:
├── Code Quality (parallel)
│   ├── Backend linting (Black, isort, flake8)
│   ├── Frontend linting (ESLint, Prettier)
│   └── Security scanning (Bandit, npm audit)
├── Testing (parallel)
│   ├── Backend unit tests (pytest)
│   ├── Frontend unit tests (Jest/Vitest)
│   ├── Integration tests (Docker Compose)
│   └── E2E tests (Playwright)
└── Build Validation
    ├── Docker image builds
    ├── Bundle size analysis
    └── Performance benchmarks
```

#### Deployment Pipeline
```yaml
# Triggered on: Push to dev/main, version tags
# Purpose: Automated deployment
# Duration: ~15-20 minutes

Environments:
├── Staging (dev branch)
│   ├── Build and push images
│   ├── Deploy to staging cluster
│   ├── Run smoke tests
│   └── Performance validation
└── Production (version tags)
    ├── Build production images
    ├── Deploy with blue-green strategy
    ├── Database migrations
    ├── Health checks
    └── Rollback on failure
```

## Workflow Configurations

### Quality Gates Workflow
```yaml
# .github/workflows/quality-gates.yml
name: Quality Gates

on:
  pull_request:
    branches: [dev, main]
  push:
    branches: [dev]

jobs:
  backend-quality:
    runs-on: ubuntu-latest
    timeout-minutes: 10

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Install dependencies
        run: |
          pip install -r requirements-dev.txt
          pip install -e .

      - name: Code formatting (Black)
        run: black --check src/ tests/

      - name: Import sorting (isort)
        run: isort --check-only src/ tests/

      - name: Linting (flake8)
        run: flake8 src/ tests/

      - name: Type checking (mypy)
        run: mypy src/

      - name: Security scan (Bandit)
        run: bandit -r src/

  frontend-quality:
    runs-on: ubuntu-latest
    timeout-minutes: 8

    steps:
      - uses: actions/checkout@v4

      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '18'
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json

      - name: Install dependencies
        run: cd frontend && npm ci

      - name: Type checking
        run: cd frontend && npm run type-check

      - name: Linting
        run: cd frontend && npm run lint

      - name: Format checking
        run: cd frontend && npm run format:check

      - name: Security audit
        run: cd frontend && npm audit --audit-level=moderate
```

## Testing Strategies

### Test Execution Matrix
```yaml
# Parallel test execution for speed
test-matrix:
  strategy:
    matrix:
      test-type: [unit, integration, e2e]
      service: [api, frontend, worker]
    fail-fast: false

  include:
    # Backend Tests
    - test-type: unit
      service: api
      command: pytest tests/unit/ --cov=src --cov-fail-under=80
      timeout: 5min

    - test-type: integration
      service: api
      command: pytest tests/integration/
      timeout: 10min

    # Frontend Tests
    - test-type: unit
      service: frontend
      command: cd frontend && npm test
      timeout: 5min

    - test-type: e2e
      service: frontend
      command: cd frontend && npm run test:e2e
      timeout: 15min
```

### Database Testing
```yaml
# Integration tests with real database
services:
  postgres:
    image: postgres:15
    env:
      POSTGRES_PASSWORD: test
      POSTGRES_DB: molecular_test
    options: >-
      --health-cmd pg_isready
      --health-interval 10s
      --health-timeout 5s
      --health-retries 5

steps:
  - name: Run database migrations
    run: |
      export DATABASE_URL=postgresql://postgres:test@localhost/molecular_test
      alembic upgrade head

  - name: Run integration tests
    run: |
      pytest tests/integration/ -v
    env:
      DATABASE_URL: postgresql://postgres:test@localhost/molecular_test
      REDIS_URL: redis://localhost:6379
```

## Deployment Workflows

### Staging Deployment
```yaml
# .github/workflows/deploy-staging.yml
name: Deploy to Staging

on:
  push:
    branches: [dev]

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: staging

    steps:
      - uses: actions/checkout@v4

      - name: Build Docker images
        run: |
          docker build -f docker/Dockerfile.api -t staging-api:${{ github.sha }} .
          docker build -f docker/Dockerfile.frontend -t staging-frontend:${{ github.sha }} .
          docker build -f docker/Dockerfile.worker -t staging-worker:${{ github.sha }} .

      - name: Push to registry
        run: |
          echo ${{ secrets.REGISTRY_PASSWORD }} | docker login -u ${{ secrets.REGISTRY_USERNAME }} --password-stdin
          docker push staging-api:${{ github.sha }}
          docker push staging-frontend:${{ github.sha }}
          docker push staging-worker:${{ github.sha }}

      - name: Deploy to staging
        run: |
          # Update Kubernetes deployments
          kubectl set image deployment/api api=staging-api:${{ github.sha }}
          kubectl set image deployment/frontend frontend=staging-frontend:${{ github.sha }}
          kubectl set image deployment/worker worker=staging-worker:${{ github.sha }}

          # Wait for rollout
          kubectl rollout status deployment/api --timeout=300s
          kubectl rollout status deployment/frontend --timeout=300s
          kubectl rollout status deployment/worker --timeout=300s

      - name: Run smoke tests
        run: |
          # Wait for services to be ready
          sleep 30

          # Basic health checks
          curl -f https://staging-api.molecular-dashboard.com/health
          curl -f https://staging.molecular-dashboard.com/

          # API functionality test
          curl -f -H "Authorization: Bearer ${{ secrets.TEST_TOKEN }}" \
            https://staging-api.molecular-dashboard.com/api/v1/molecules
```

### Production Deployment
```yaml
# .github/workflows/deploy-production.yml
name: Deploy to Production

on:
  push:
    tags:
      - 'v*'

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: production

    steps:
      - uses: actions/checkout@v4

      - name: Extract version
        id: version
        run: echo "VERSION=${GITHUB_REF#refs/tags/}" >> $GITHUB_OUTPUT

      - name: Build production images
        run: |
          docker build -f docker/Dockerfile.api \
            --build-arg VERSION=${{ steps.version.outputs.VERSION }} \
            -t molecular-api:${{ steps.version.outputs.VERSION }} .

          docker build -f docker/Dockerfile.frontend \
            --build-arg VERSION=${{ steps.version.outputs.VERSION }} \
            -t molecular-frontend:${{ steps.version.outputs.VERSION }} .

      - name: Security scan images
        run: |
          # Scan for vulnerabilities
          trivy image molecular-api:${{ steps.version.outputs.VERSION }}
          trivy image molecular-frontend:${{ steps.version.outputs.VERSION }}

      - name: Blue-Green Deployment
        run: |
          # Deploy to green environment
          kubectl patch deployment api -p '{"spec":{"template":{"metadata":{"labels":{"version":"green"}}}}}'
          kubectl set image deployment/api api=molecular-api:${{ steps.version.outputs.VERSION }}

          # Wait for green to be ready
          kubectl rollout status deployment/api --timeout=600s

          # Health check green environment
          kubectl run healthcheck-${{ github.sha }} --image=curlimages/curl \
            --command -- curl -f http://api-green.molecular-dashboard.com/health

          # Switch traffic to green
          kubectl patch service api -p '{"spec":{"selector":{"version":"green"}}}'

          # Cleanup blue environment after 5 minutes
          sleep 300
          kubectl delete deployment api-blue || true
```

## Performance and Security

### Performance Monitoring
```yaml
# Performance regression detection
- name: Performance Benchmarks
  run: |
    # API performance test
    k6 run --out json=api-results.json scripts/performance/api-load-test.js

    # Frontend bundle analysis
    cd frontend && npm run analyze

    # Compare with baseline
    python scripts/compare-performance.py api-results.json baseline-results.json
```

### Security Scanning
```yaml
# Multi-layer security scanning
security-scan:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4

    # Code security scan
    - name: Run Bandit (Python)
      run: bandit -r src/ -f json -o bandit-report.json

    # Dependency vulnerability scan
    - name: Run Safety (Python deps)
      run: safety check --json --output safety-report.json

    # Frontend security scan
    - name: Run npm audit
      run: cd frontend && npm audit --json > npm-audit.json

    # Container image scan
    - name: Run Trivy (Container scan)
      run: trivy image --format json --output trivy-report.json molecular-api:latest

    # Upload security reports
    - name: Upload security artifacts
      uses: actions/upload-artifact@v3
      with:
        name: security-reports
        path: |
          bandit-report.json
          safety-report.json
          npm-audit.json
          trivy-report.json
```

## Environment Management

### Environment Configuration
```yaml
# Environment-specific secrets and variables
environments:
  staging:
    secrets:
      - DATABASE_URL
      - REDIS_URL
      - JWT_SECRET_KEY
      - DOCKER_REGISTRY_PASSWORD
    variables:
      - LOG_LEVEL: INFO
      - DEBUG: false
      - CORS_ORIGINS: https://staging.molecular-dashboard.com

  production:
    secrets:
      - DATABASE_URL
      - REDIS_URL
      - JWT_SECRET_KEY
      - DOCKER_REGISTRY_PASSWORD
      - MONITORING_API_KEY
    variables:
      - LOG_LEVEL: WARNING
      - DEBUG: false
      - CORS_ORIGINS: https://molecular-dashboard.com
```

### Deployment Strategies
```yaml
# Blue-Green Deployment Configuration
blue-green:
  enabled: true
  health-check-url: /health
  health-check-timeout: 300s
  rollback-on-failure: true

# Canary Deployment (future)
canary:
  enabled: false
  traffic-split: 10%  # 10% to new version initially
  success-criteria:
    error-rate: <1%
    response-time: <500ms
    duration: 10min
```

## Monitoring and Observability

### Pipeline Metrics
```yaml
# Key metrics to track
metrics:
  - pipeline-duration
  - test-success-rate
  - deployment-frequency
  - mean-time-to-recovery
  - change-failure-rate

# Alerting thresholds
alerts:
  - name: Pipeline Failure
    condition: failure-rate > 10%
    channels: [slack, email]

  - name: Slow Pipeline
    condition: duration > 20min
    channels: [slack]

  - name: Security Vulnerability
    condition: high-severity-vuln > 0
    channels: [slack, email, pagerduty]
```

## Troubleshooting

### Common Pipeline Issues

#### Test Failures
```bash
# Debug test failures locally
docker compose -f docker-compose.test.yml up --abort-on-container-exit

# Run specific test with verbose output
pytest tests/integration/test_api.py::test_molecule_upload -v -s

# Check logs for flaky tests
docker compose logs api worker
```

#### Build Failures
```bash
# Test Docker builds locally
docker build -f docker/Dockerfile.api -t test-api .

# Check for dependency conflicts
pip-compile requirements.in --verbose

# Validate frontend build
cd frontend && npm run build
```

#### Deployment Issues
```bash
# Check deployment status
kubectl rollout status deployment/api

# View recent events
kubectl get events --sort-by='.lastTimestamp'

# Check pod logs
kubectl logs -l app=api --tail=100
```

### Recovery Procedures

#### Pipeline Recovery
```bash
# Re-run failed jobs
gh workflow run quality-gates.yml --ref feature/branch-name

# Skip CI for documentation-only changes
git commit -m "docs: update README [skip ci]"

# Emergency deployment bypass
git tag -a v1.2.1-hotfix -m "Emergency security fix"
git push origin v1.2.1-hotfix
```

## Resources

- **GitHub Actions Documentation**: https://docs.github.com/en/actions
- **Docker Best Practices**: https://docs.docker.com/develop/best-practices/
- **Kubernetes Deployment Strategies**: https://kubernetes.io/docs/concepts/workloads/controllers/deployment/
- **Security Scanning Tools**: https://github.com/aquasecurity/trivy
