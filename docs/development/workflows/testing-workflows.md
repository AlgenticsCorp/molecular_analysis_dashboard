# Testing Workflows

*Comprehensive testing strategies and execution procedures for quality assurance.*

## Testing Strategy Overview

Our testing approach follows the **Test Pyramid** with extensive automation, focusing on fast feedback and high confidence in deployments.

```
    /\    E2E Tests (UI/API Integration)
   /  \   ├── User workflows
  /____\  ├── Cross-service integration
 /      \ └── Performance validation
/________\
Integration Tests (Service Level)
├── Database operations
├── External service mocks
├── Multi-container testing
└── API contract validation

Unit Tests (Component Level)
├── Business logic validation
├── Error handling
├── Edge case coverage
└── Mock-heavy isolation
```

## Test Categories

### Unit Tests (80% of tests)
**Purpose**: Fast, isolated testing of individual components
**Target**: >80% code coverage
**Duration**: <30 seconds total

```bash
# Backend unit tests
pytest tests/unit/ --cov=src/molecular_analysis_dashboard --cov-fail-under=80

# Frontend unit tests
cd frontend && npm test -- --coverage --watchAll=false
```

### Integration Tests (15% of tests)
**Purpose**: Service integration and database operations
**Target**: All critical paths covered
**Duration**: <2 minutes total

```bash
# Backend integration with real database
docker compose up -d postgres redis
pytest tests/integration/ -v

# Frontend component integration
cd frontend && npm run test:integration
```

### E2E Tests (5% of tests)
**Purpose**: Full user workflow validation
**Target**: All user journeys covered
**Duration**: <10 minutes total

```bash
# Full application E2E tests
docker compose up -d
cd frontend && npm run test:e2e
```

## Test Execution Workflows

### Local Development Testing
```bash
# Quick test cycle (before commit)
./scripts/test-quick.sh

# Full test suite (before PR)
./scripts/test-full.sh

# Specific test debugging
pytest tests/unit/test_docking.py::test_vina_execution -v -s
```

### CI/CD Testing Pipeline
```yaml
# Parallel test execution for speed
test-matrix:
  runs-on: ubuntu-latest
  strategy:
    matrix:
      test-suite: [unit-backend, unit-frontend, integration, e2e]
    fail-fast: false

  steps:
    - name: Run test suite
      run: |
        case "${{ matrix.test-suite }}" in
          unit-backend)
            pytest tests/unit/ --cov=src --junit-xml=junit-backend.xml
            ;;
          unit-frontend)
            cd frontend && npm test -- --coverage --ci --reporters=jest-junit
            ;;
          integration)
            docker compose up -d postgres redis
            pytest tests/integration/ --junit-xml=junit-integration.xml
            ;;
          e2e)
            docker compose up -d
            cd frontend && npm run test:e2e -- --reporter junit
            ;;
        esac
```

## Backend Testing

### Unit Test Structure
```python
# tests/unit/test_docking_service.py
import pytest
from unittest.mock import Mock, patch
from src.molecular_analysis_dashboard.use_cases.docking import CreateDockingJobUseCase
from src.molecular_analysis_dashboard.domain.entities import Molecule, DockingJob

class TestCreateDockingJobUseCase:
    @pytest.fixture
    def mock_repository(self):
        return Mock()

    @pytest.fixture
    def mock_docking_engine(self):
        engine = Mock()
        engine.validate_input.return_value = True
        engine.estimate_runtime.return_value = 300  # 5 minutes
        return engine

    @pytest.fixture
    def use_case(self, mock_repository, mock_docking_engine):
        return CreateDockingJobUseCase(
            repository=mock_repository,
            docking_engine=mock_docking_engine
        )

    def test_create_job_success(self, use_case, mock_repository):
        # Arrange
        molecule = Molecule(id="mol-1", smiles="CCO", organization_id="org-1")
        job_request = DockingJobRequest(
            molecule_id="mol-1",
            target_protein="1ABC",
            engine="vina"
        )

        # Act
        result = use_case.execute(job_request)

        # Assert
        assert result.success is True
        assert result.job.molecule_id == "mol-1"
        mock_repository.save_job.assert_called_once()

    def test_create_job_invalid_molecule(self, use_case):
        # Test error handling for invalid input
        pass

    def test_create_job_engine_failure(self, use_case, mock_docking_engine):
        # Test engine validation failure
        mock_docking_engine.validate_input.return_value = False
        # ... test implementation
```

### Integration Test Setup
```python
# tests/integration/test_docking_pipeline.py
import pytest
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from src.molecular_analysis_dashboard.infrastructure.database import get_database_session

@pytest.fixture(scope="session")
async def test_database():
    """Create test database for integration tests."""
    engine = create_async_engine("postgresql+asyncpg://test:test@localhost/molecular_test")

    # Run migrations
    import alembic.config
    alembic_cfg = alembic.config.Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", "postgresql://test:test@localhost/molecular_test")
    alembic.command.upgrade(alembic_cfg, "head")

    yield engine

    # Cleanup
    await engine.dispose()

@pytest.fixture
async def db_session(test_database):
    """Provide clean database session for each test."""
    async with get_database_session() as session:
        yield session
        await session.rollback()

class TestDockingPipelineIntegration:
    async def test_full_docking_workflow(self, db_session):
        # Test complete workflow from molecule upload to results
        pass

    async def test_concurrent_job_execution(self, db_session):
        # Test multiple jobs running simultaneously
        pass
```

## Frontend Testing

### Component Unit Tests
```typescript
// frontend/src/components/MoleculeUpload/MoleculeUpload.test.tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import MoleculeUpload from './MoleculeUpload';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

const mockUploadMolecule = vi.fn();
vi.mock('../../services/api', () => ({
  uploadMolecule: mockUploadMolecule,
}));

describe('MoleculeUpload', () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });

  const renderWithProviders = (component: React.ReactElement) => {
    return render(
      <QueryClientProvider client={queryClient}>
        {component}
      </QueryClientProvider>
    );
  };

  it('uploads valid SDF file successfully', async () => {
    // Arrange
    const file = new File(['valid sdf content'], 'molecule.sdf', { type: 'chemical/x-sdf' });
    mockUploadMolecule.mockResolvedValueOnce({ id: 'mol-1', name: 'Test Molecule' });

    renderWithProviders(<MoleculeUpload onUploadSuccess={vi.fn()} />);

    // Act
    const fileInput = screen.getByLabelText(/upload molecule/i);
    fireEvent.change(fileInput, { target: { files: [file] } });

    const submitButton = screen.getByRole('button', { name: /upload/i });
    fireEvent.click(submitButton);

    // Assert
    await waitFor(() => {
      expect(mockUploadMolecule).toHaveBeenCalledWith(file);
    });

    expect(screen.getByText(/upload successful/i)).toBeInTheDocument();
  });

  it('displays error for invalid file format', async () => {
    // Test error handling
    const file = new File(['invalid content'], 'molecule.txt', { type: 'text/plain' });

    renderWithProviders(<MoleculeUpload onUploadSuccess={vi.fn()} />);

    const fileInput = screen.getByLabelText(/upload molecule/i);
    fireEvent.change(fileInput, { target: { files: [file] } });

    expect(screen.getByText(/invalid file format/i)).toBeInTheDocument();
  });
});
```

### E2E Test Setup
```typescript
// frontend/tests/e2e/docking-workflow.spec.ts
import { test, expect, Page } from '@playwright/test';

test.describe('Docking Workflow', () => {
  let page: Page;

  test.beforeAll(async ({ browser }) => {
    page = await browser.newPage();

    // Login with test user
    await page.goto('/login');
    await page.fill('[data-testid=email]', 'test@example.com');
    await page.fill('[data-testid=password]', 'testpassword');
    await page.click('[data-testid=login-button]');
    await page.waitForURL('/dashboard');
  });

  test('complete molecule docking workflow', async () => {
    // Navigate to molecule upload
    await page.click('[data-testid=upload-molecule-button]');

    // Upload test molecule file
    const fileChooserPromise = page.waitForEvent('filechooser');
    await page.click('[data-testid=file-upload-button]');
    const fileChooser = await fileChooserPromise;
    await fileChooser.setFiles('tests/fixtures/test-molecule.sdf');

    // Wait for upload completion
    await expect(page.getByText('Upload successful')).toBeVisible();

    // Configure docking job
    await page.click('[data-testid=create-docking-job]');
    await page.selectOption('[data-testid=target-protein]', '1ABC');
    await page.selectOption('[data-testid=docking-engine]', 'vina');
    await page.click('[data-testid=submit-job]');

    // Verify job creation
    await expect(page.getByText('Docking job created')).toBeVisible();

    // Check job appears in jobs list
    await page.goto('/jobs');
    await expect(page.getByText('1ABC')).toBeVisible();

    // Wait for job completion (or mock completion)
    await page.click('[data-testid=job-row-0]');
    await expect(page.getByText('Completed')).toBeVisible({ timeout: 30000 });

    // Verify results visualization
    await expect(page.locator('[data-testid=molecule-viewer]')).toBeVisible();
    await expect(page.getByText('Binding Affinity')).toBeVisible();
  });

  test('handles docking job failures gracefully', async () => {
    // Test error scenarios
  });
});
```

## Performance Testing

### Load Testing Setup
```javascript
// scripts/performance/api-load-test.js
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

export const errorRate = new Rate('errors');

export const options = {
  stages: [
    { duration: '2m', target: 10 },  // Ramp up to 10 users
    { duration: '5m', target: 10 },  // Stay at 10 users
    { duration: '2m', target: 20 },  // Ramp up to 20 users
    { duration: '5m', target: 20 },  // Stay at 20 users
    { duration: '2m', target: 0 },   // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'], // 95% of requests under 500ms
    http_req_failed: ['rate<0.01'],   // Error rate under 1%
    errors: ['rate<0.01'],
  },
};

const BASE_URL = 'https://api.molecular-dashboard.com';
const AUTH_TOKEN = 'test-jwt-token';

export default function () {
  // Test API endpoints
  const headers = { Authorization: `Bearer ${AUTH_TOKEN}` };

  // List molecules
  let response = http.get(`${BASE_URL}/api/v1/molecules`, { headers });
  check(response, {
    'molecules list status 200': (r) => r.status === 200,
    'molecules response time OK': (r) => r.timings.duration < 200,
  }) || errorRate.add(1);

  // Get specific molecule
  if (response.json() && response.json().length > 0) {
    const moleculeId = response.json()[0].id;
    response = http.get(`${BASE_URL}/api/v1/molecules/${moleculeId}`, { headers });
    check(response, {
      'molecule detail status 200': (r) => r.status === 200,
    }) || errorRate.add(1);
  }

  // List docking jobs
  response = http.get(`${BASE_URL}/api/v1/jobs`, { headers });
  check(response, {
    'jobs list status 200': (r) => r.status === 200,
  }) || errorRate.add(1);

  sleep(1);
}
```

### Performance Benchmarking
```bash
#!/bin/bash
# scripts/performance/benchmark.sh

set -e

echo "Running performance benchmarks..."

# API load testing
echo "Testing API performance..."
k6 run --out json=api-results.json scripts/performance/api-load-test.js

# Frontend performance testing
echo "Testing frontend performance..."
cd frontend
npm run build
npx lighthouse http://localhost --output json --output-path lighthouse-results.json --chrome-flags="--headless"

# Database performance testing
echo "Testing database performance..."
docker compose exec postgres pgbench -i molecular_dashboard
docker compose exec postgres pgbench -c 10 -j 2 -t 1000 molecular_dashboard

# Generate performance report
python scripts/performance/generate-report.py api-results.json lighthouse-results.json
```

## Test Data Management

### Test Fixtures
```python
# tests/fixtures/molecules.py
import pytest
from src.molecular_analysis_dashboard.domain.entities import Molecule

@pytest.fixture
def sample_molecules():
    return [
        Molecule(
            id="mol-1",
            name="Caffeine",
            smiles="CN1C=NC2=C1C(=O)N(C(=O)N2C)C",
            organization_id="org-test",
            molecular_weight=194.19,
            formula="C8H10N4O2"
        ),
        Molecule(
            id="mol-2",
            name="Aspirin",
            smiles="CC(=O)OC1=CC=CC=C1C(=O)O",
            organization_id="org-test",
            molecular_weight=180.16,
            formula="C9H8O4"
        ),
    ]

@pytest.fixture
def test_sdf_file():
    return """
  Mrv2014 01012021

  2  1  0  0  0  0            999 V2000
    0.0000    0.0000    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
    1.0000    0.0000    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
  1  2  1  0  0  0  0
M  END
$$$$
"""
```

### Database Seeding
```python
# tests/utils/database.py
async def seed_test_database(session):
    """Seed database with test data for integration tests."""

    # Create test organization
    org = Organization(id="org-test", name="Test Organization")
    session.add(org)

    # Create test molecules
    molecules = [
        Molecule(id="mol-1", name="Test Mol 1", organization_id="org-test"),
        Molecule(id="mol-2", name="Test Mol 2", organization_id="org-test"),
    ]
    session.add_all(molecules)

    # Create test docking jobs
    jobs = [
        DockingJob(
            id="job-1",
            molecule_id="mol-1",
            target_protein="1ABC",
            status=JobStatus.COMPLETED,
            organization_id="org-test"
        )
    ]
    session.add_all(jobs)

    await session.commit()
```

## Test Automation Scripts

### Test Execution Scripts
```bash
#!/bin/bash
# scripts/test-quick.sh - Fast pre-commit tests

set -e

echo "Running quick test suite..."

# Backend unit tests only
pytest tests/unit/ --cov=src --cov-fail-under=80 -x

# Frontend unit tests only
cd frontend && npm test -- --watchAll=false --coverage

# Basic linting
pre-commit run --all-files

echo "Quick tests completed successfully!"
```

```bash
#!/bin/bash
# scripts/test-full.sh - Complete test suite

set -e

echo "Running full test suite..."

# Start services
docker compose up -d postgres redis

# Backend tests
pytest tests/ --cov=src --cov-fail-under=80 --junit-xml=junit-backend.xml

# Frontend tests
cd frontend
npm test -- --watchAll=false --coverage
npm run test:integration
npm run type-check
npm run lint

# E2E tests
docker compose up -d
npm run test:e2e

# Performance tests
cd ../
k6 run scripts/performance/api-load-test.js

# Security tests
bandit -r src/
cd frontend && npm audit

echo "All tests completed successfully!"
```

## Quality Gates

### Coverage Requirements
```yaml
# Coverage thresholds
coverage:
  backend:
    line: 80%
    branch: 75%
    function: 85%

  frontend:
    line: 80%
    branch: 70%
    function: 80%
    statement: 80%
```

### Performance Thresholds
```yaml
# Performance requirements
performance:
  api:
    p95_response_time: 500ms
    error_rate: <1%
    throughput: >100 rps

  frontend:
    lighthouse_performance: >90
    first_contentful_paint: <1.5s
    largest_contentful_paint: <2.5s
    bundle_size: <2MB
```

## Troubleshooting

### Common Test Issues
```bash
# Flaky test debugging
pytest tests/integration/test_flaky.py --count=10

# Database connection issues
docker compose down && docker compose up -d postgres redis
sleep 10  # Wait for services to start

# Frontend test memory issues
cd frontend && npm test -- --no-cache --maxWorkers=2

# E2E test debugging
cd frontend && npm run test:e2e -- --debug --headed
```

### Test Environment Recovery
```bash
# Reset test database
docker compose exec postgres dropdb molecular_test || true
docker compose exec postgres createdb molecular_test
alembic upgrade head

# Clear test caches
pytest --cache-clear
cd frontend && npm test -- --clearCache

# Reset Docker test environment
docker compose down -v
docker compose up -d
```

## Resources

- **pytest Documentation**: https://docs.pytest.org/
- **Jest Testing Framework**: https://jestjs.io/docs/getting-started
- **Playwright E2E Testing**: https://playwright.dev/
- **K6 Load Testing**: https://k6.io/docs/
- **Testing Best Practices**: https://testing.googleblog.com/
