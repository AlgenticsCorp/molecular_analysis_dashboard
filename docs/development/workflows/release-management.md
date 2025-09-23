# Release Management

*Version control, release planning, and deployment procedures for the Molecular Analysis Dashboard.*

## Overview

We follow **Semantic Versioning (SemVer)** with automated release processes, comprehensive testing, and coordinated deployments. Each release goes through staging validation before production deployment.

## Versioning Strategy

### Semantic Versioning Format
```
MAJOR.MINOR.PATCH[-PRERELEASE][+BUILD]

Examples:
1.0.0       # Initial release
1.1.0       # New features
1.1.1       # Bug fixes
2.0.0       # Breaking changes
1.2.0-beta.1  # Pre-release
1.2.0-rc.1    # Release candidate
```

### Version Components

#### MAJOR (X.0.0)
**Breaking changes that require user action**
- API contract changes (endpoint removal, parameter changes)
- Database schema changes requiring migration
- Authentication/authorization changes
- Configuration format changes
- Minimum system requirement changes

*Examples:*
- Changing REST API from v1 to v2 format
- Updating authentication from JWT to OAuth2
- Requiring new environment variables

#### MINOR (0.X.0)
**New features that are backward compatible**
- New API endpoints or functionality
- New docking engines or algorithms
- New frontend features or pages
- Performance improvements
- New configuration options (with defaults)

*Examples:*
- Adding new molecular visualization options
- Supporting additional file formats
- Adding new docking engine (Gnina, Smina)
- New dashboard features

#### PATCH (0.0.X)
**Bug fixes and security patches**
- Security vulnerability fixes
- Bug fixes without behavioral changes
- Documentation corrections
- Dependency updates (security patches)
- Performance optimizations

*Examples:*
- Fixing molecule upload validation
- Correcting docking job status updates
- Security patches for dependencies
- Memory leak fixes

### Pre-release Versions

#### Alpha (1.2.0-alpha.1)
- **Purpose**: Early development builds
- **Stability**: Unstable, expect breaking changes
- **Audience**: Internal development team
- **Testing**: Basic functionality testing

#### Beta (1.2.0-beta.1)
- **Purpose**: Feature-complete but needs testing
- **Stability**: Feature-complete, possible bugs
- **Audience**: Internal QA team, selected users
- **Testing**: Comprehensive testing, performance validation

#### Release Candidate (1.2.0-rc.1)
- **Purpose**: Production-ready candidate
- **Stability**: Production quality, final validation
- **Audience**: All stakeholders, production-like testing
- **Testing**: Full regression testing, security audit

## Release Planning

### Release Cycle

#### Regular Release Schedule
- **Minor Releases**: Every 4-6 weeks
- **Patch Releases**: As needed (1-2 weeks)
- **Major Releases**: Every 6-12 months
- **Security Releases**: Emergency (24-48 hours)

#### Release Milestones
```
Weeks 1-3: Development
├── Feature development in dev branch
├── Code reviews and testing
└── Documentation updates

Week 4: Release Preparation
├── Code freeze on release branch
├── QA testing and bug fixes
├── Documentation finalization
└── Staging deployment validation

Week 5: Release
├── Production deployment
├── Post-deployment monitoring
├── Hotfix releases if needed
└── Retrospective and planning
```

### Release Planning Process

#### 1. Release Planning Meeting (Week -2)
**Attendees**: Product, Engineering, QA, DevOps

**Agenda:**
- Review completed features in dev branch
- Assess feature readiness and quality
- Identify release blockers and dependencies
- Plan testing strategy and timeline
- Coordinate deployment schedule
- Communicate to stakeholders

**Outputs:**
- Release scope and timeline
- Testing plan and assignments
- Risk assessment and mitigation
- Communication plan

#### 2. Feature Freeze (Release Branch Creation)
```bash
# Create release branch from dev
git checkout dev
git pull origin dev
git checkout -b release/v1.2.0

# Update version numbers
# pyproject.toml, package.json, etc.
git commit -m "chore(release): bump version to v1.2.0"
git push origin release/v1.2.0
```

**Release Branch Rules:**
- **Allowed**: Bug fixes, documentation, small improvements
- **Prohibited**: New features, major refactoring, breaking changes
- **Review**: All changes require approval from release manager

#### 3. QA Testing Phase
**Testing Strategy:**
- **Regression Testing**: All existing functionality
- **New Feature Testing**: Comprehensive feature validation
- **Integration Testing**: Cross-service functionality
- **Performance Testing**: Load and stress testing
- **Security Testing**: Vulnerability scanning
- **User Acceptance Testing**: Stakeholder validation

**Testing Environments:**
```yaml
# staging environment (production-like)
docker compose -f docker-compose.staging.yml up -d

# Run comprehensive test suite
docker compose -f docker-compose.test.yml up --abort-on-container-exit

# Performance testing
docker compose run --rm loadtest

# Security scanning
docker compose run --rm security-scan
```

#### 4. Release Candidate
```bash
# Tag release candidate
git tag v1.2.0-rc.1
git push origin v1.2.0-rc.1

# Deploy to staging for final validation
# Automated via CI/CD pipeline
```

**RC Validation:**
- **Stakeholder Sign-off**: Product owner approval
- **QA Sign-off**: All tests pass, no blocking issues
- **Security Sign-off**: Security review completed
- **Performance Sign-off**: Performance requirements met

## Release Procedures

### Standard Release Process

#### 1. Pre-release Preparation
```bash
# Ensure release branch is ready
git checkout release/v1.2.0
git pull origin release/v1.2.0

# Run final tests
docker compose -f docker-compose.test.yml up --abort-on-container-exit

# Validate staging deployment
curl https://staging-api.molecular-dashboard.com/health
```

#### 2. Release Execution
```bash
# Create and push release tag
git tag -a v1.2.0 -m "Release v1.2.0

Features:
- New Gnina docking engine support
- Improved molecule visualization
- Enhanced user authentication

Bug Fixes:
- Fixed job status updates
- Resolved memory leaks in worker processes
- Corrected API response formats

Breaking Changes:
- None

Migration Notes:
- Database migration required (automatic)
- No configuration changes needed"

git push origin v1.2.0
```

#### 3. Automated Deployment Pipeline
```yaml
# .github/workflows/release.yml
name: Release Deployment

on:
  push:
    tags:
      - 'v*'

jobs:
  deploy-production:
    runs-on: ubuntu-latest
    environment: production
    steps:
      - name: Deploy to Production
        run: |
          # Build and push Docker images
          docker build -t molecular-dashboard:${{ github.ref_name }} .
          docker push molecular-dashboard:${{ github.ref_name }}

          # Deploy to production cluster
          kubectl set image deployment/api api=molecular-dashboard:${{ github.ref_name }}
          kubectl rollout status deployment/api

          # Run database migrations
          kubectl run migrate --image=molecular-dashboard:${{ github.ref_name }} \
            --command -- alembic upgrade head

          # Health check
          kubectl run healthcheck --image=curlimages/curl \
            --command -- curl -f https://api.molecular-dashboard.com/health
```

#### 4. Post-deployment Validation
```bash
# Automated health checks
./scripts/health-check-production.sh

# Manual smoke tests
curl https://api.molecular-dashboard.com/health
curl https://api.molecular-dashboard.com/api/v1/molecules

# Monitor application metrics
# Check Grafana dashboards for errors/performance
# Monitor error rates and response times
# Validate user workflows
```

#### 5. Merge Release Branch
```bash
# Merge release branch to main
git checkout main
git merge release/v1.2.0 --no-ff
git push origin main

# Merge release branch to dev (for any fixes)
git checkout dev
git merge release/v1.2.0 --no-ff
git push origin dev

# Clean up release branch
git branch -d release/v1.2.0
git push origin --delete release/v1.2.0
```

### Hotfix Release Process

#### 1. Emergency Response
```bash
# Create hotfix branch from main
git checkout main
git pull origin main
git checkout -b hotfix/v1.1.1-security-fix

# Implement fix with minimal changes
# Focus only on the critical issue
git commit -m "fix(auth): patch JWT validation vulnerability (CVE-2023-1234)"

# Update version number
git commit -m "chore(release): bump version to v1.1.1"
```

#### 2. Accelerated Testing
```bash
# Run critical path tests
pytest tests/unit/auth/ tests/integration/auth/

# Security validation
bandit -r src/molecular_analysis_dashboard/

# Smoke tests in staging
docker compose -f docker-compose.staging.yml up -d
./scripts/smoke-test.sh
```

#### 3. Emergency Deployment
```bash
# Tag and deploy immediately
git tag v1.1.1
git push origin v1.1.1

# Monitor deployment closely
kubectl rollout status deployment/api --timeout=300s
./scripts/health-check-production.sh

# Notify stakeholders
./scripts/notify-release.sh v1.1.1 hotfix
```

## Release Communication

### Changelog Generation
```bash
# Automated changelog from conventional commits
npx conventional-changelog -p angular -i CHANGELOG.md -s

# Manual review and enhancement
# Add breaking change details
# Include migration instructions
# Add performance improvements
# Note security fixes
```

### Release Notes Template
```markdown
# Release v1.2.0 - "Quantum Leap"

*Released on 2024-03-15*

## 🎯 Highlights

This release introduces advanced molecular docking capabilities with the new Gnina engine, enhanced visualization features, and significant performance improvements.

## ✨ New Features

### Gnina Docking Engine Integration
- **What**: Added support for Gnina AI-powered docking engine
- **Impact**: 40% faster docking with improved accuracy
- **Usage**: Available in pipeline configuration under "Advanced Engines"

### Enhanced Molecular Visualization
- **What**: 3D molecule viewer with interactive controls
- **Impact**: Better result analysis and presentation
- **Usage**: Automatic for all docking results

### Multi-tenant Dashboard Improvements
- **What**: Organization-specific analytics and reporting
- **Impact**: Better insights for team collaboration
- **Usage**: Available in main dashboard for org admins

## 🐛 Bug Fixes

- **Fixed**: Job status updates not reflecting in real-time
- **Fixed**: Memory leaks in long-running worker processes
- **Fixed**: API response format inconsistencies
- **Fixed**: Molecule upload validation edge cases

## 🔧 Improvements

- **Performance**: 25% faster API response times
- **Security**: Enhanced JWT token validation
- **Documentation**: Updated API documentation with examples
- **Testing**: Increased test coverage to 87%

## 🚨 Breaking Changes

**None** - This release is fully backward compatible.

## 🔄 Migration Guide

### Database Migration
```bash
# Automatic migration during deployment
# No manual action required
docker compose run --rm migrate
```

### Configuration Updates
```bash
# Optional: Enable Gnina engine
export GNINA_ENABLED=true
export GNINA_MODEL_PATH=/models/gnina
```

## 📊 Performance Metrics

- **API Response Time**: Improved from 200ms to 150ms (25% faster)
- **Docking Job Throughput**: Increased from 100 to 140 jobs/hour (40% faster)
- **Memory Usage**: Reduced worker memory footprint by 15%
- **Test Coverage**: Increased from 82% to 87%

## 🔗 Resources

- **Documentation**: [docs.molecular-dashboard.com](https://docs.molecular-dashboard.com)
- **API Reference**: [api.molecular-dashboard.com/docs](https://api.molecular-dashboard.com/docs)
- **Migration Guide**: [docs.molecular-dashboard.com/migration/v1.2.0](https://docs.molecular-dashboard.com/migration/v1.2.0)
- **Support**: [support@molecular-dashboard.com](mailto:support@molecular-dashboard.com)

## 📈 What's Next

Looking ahead to v1.3.0 (planned for May 2024):
- **Advanced Analytics**: Machine learning insights for docking results
- **API v2**: Enhanced REST API with GraphQL support
- **Mobile Support**: Responsive design improvements
- **Integration**: Third-party molecular database connections

---

**Full Changelog**: [v1.1.0...v1.2.0](https://github.com/AlgenticsCorp/molecular_analysis_dashboard/compare/v1.1.0...v1.2.0)
```

### Communication Channels

#### Internal Communication
```bash
# Slack notification
curl -X POST -H 'Content-type: application/json' \
  --data '{
    "text": "🚀 Release v1.2.0 deployed to production!",
    "attachments": [{
      "color": "good",
      "fields": [
        {"title": "Version", "value": "v1.2.0", "short": true},
        {"title": "Environment", "value": "Production", "short": true},
        {"title": "Health", "value": "✅ All systems operational", "short": false}
      ]
    }]
  }' \
  $SLACK_WEBHOOK_URL
```

#### External Communication
- **Release Notes**: Published on website and documentation
- **Email Newsletter**: Sent to all users with highlights
- **Social Media**: Twitter/LinkedIn announcements
- **Blog Post**: Detailed feature explanations and use cases

## Release Monitoring

### Health Monitoring
```bash
# Automated monitoring script
#!/bin/bash
# scripts/monitor-release.sh

set -e

VERSION=$1
ENVIRONMENT=${2:-production}

echo "Monitoring release $VERSION in $ENVIRONMENT..."

# Health checks
curl -f https://api.molecular-dashboard.com/health || exit 1
curl -f https://molecular-dashboard.com/health || exit 1

# Performance metrics
RESPONSE_TIME=$(curl -w "%{time_total}" -s -o /dev/null https://api.molecular-dashboard.com/api/v1/molecules)
if (( $(echo "$RESPONSE_TIME > 1.0" | bc -l) )); then
  echo "Warning: API response time high: ${RESPONSE_TIME}s"
fi

# Error rate check
ERROR_RATE=$(curl -s https://monitoring.molecular-dashboard.com/api/error-rate)
if (( $(echo "$ERROR_RATE > 0.01" | bc -l) )); then
  echo "Warning: Error rate elevated: ${ERROR_RATE}%"
fi

echo "Release monitoring complete: All systems healthy"
```

### Rollback Procedures

#### Automatic Rollback Triggers
- Error rate > 5% for 5 minutes
- API response time > 2 seconds for 5 minutes
- Health check failures > 3 consecutive
- Critical service unavailable > 1 minute

#### Manual Rollback
```bash
# Emergency rollback to previous version
kubectl rollout undo deployment/api
kubectl rollout undo deployment/frontend
kubectl rollout undo deployment/worker

# Verify rollback
kubectl rollout status deployment/api
./scripts/health-check-production.sh

# Notify team
./scripts/notify-rollback.sh $PREVIOUS_VERSION
```

### Post-Release Activities

#### Release Retrospective (Week +1)
**Participants**: Release team, stakeholders

**Agenda:**
- Release timeline review
- Quality metrics assessment
- Issue identification and resolution
- Process improvement opportunities
- Documentation updates

**Outputs:**
- Lessons learned document
- Process improvement backlog
- Updated release procedures
- Team recognition and feedback

#### Metrics Collection
```bash
# Collect release metrics
./scripts/release-metrics.sh v1.2.0

# Generate release report
./scripts/generate-release-report.sh v1.2.0
```

**Key Metrics:**
- **Lead Time**: Feature commit to production
- **Deployment Frequency**: Releases per month
- **Mean Time to Recovery**: Issue detection to resolution
- **Change Failure Rate**: Rollbacks per release
- **Customer Impact**: User satisfaction and adoption

## Tools and Automation

### Release Automation Tools

#### Semantic Release
```json
// package.json
{
  "devDependencies": {
    "@semantic-release/changelog": "^6.0.0",
    "@semantic-release/git": "^10.0.0",
    "semantic-release": "^21.0.0"
  },
  "release": {
    "branches": ["main"],
    "plugins": [
      "@semantic-release/commit-analyzer",
      "@semantic-release/release-notes-generator",
      "@semantic-release/changelog",
      "@semantic-release/npm",
      "@semantic-release/git",
      "@semantic-release/github"
    ]
  }
}
```

#### Release Scripts
```bash
#!/bin/bash
# scripts/release.sh

set -e

VERSION_TYPE=${1:-minor}  # major, minor, patch
CURRENT_VERSION=$(git describe --tags --abbrev=0)

echo "Current version: $CURRENT_VERSION"
echo "Release type: $VERSION_TYPE"

# Validate release readiness
./scripts/validate-release.sh

# Create release branch
git checkout dev
git pull origin dev
git checkout -b "release/$NEW_VERSION"

# Update version numbers
./scripts/bump-version.sh $VERSION_TYPE

# Run tests
docker compose -f docker-compose.test.yml up --abort-on-container-exit

# Create PR for release
gh pr create --title "Release $NEW_VERSION" \
             --body-file .github/RELEASE_TEMPLATE.md \
             --base main \
             --head "release/$NEW_VERSION"

echo "Release $NEW_VERSION ready for review"
```

### Monitoring Integration
```yaml
# docker-compose.monitoring.yml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana:latest
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    ports:
      - "3001:3000"
    volumes:
      - ./monitoring/grafana:/etc/grafana/provisioning

  alertmanager:
    image: prom/alertmanager:latest
    volumes:
      - ./monitoring/alertmanager.yml:/etc/alertmanager/alertmanager.yml
    ports:
      - "9093:9093"
```

## Resources

- **Semantic Versioning**: https://semver.org/
- **Conventional Commits**: https://www.conventionalcommits.org/
- **GitFlow**: https://nvie.com/posts/a-successful-git-branching-model/
- **Release Engineering**: https://sre.google/sre-book/release-engineering/
- **Continuous Delivery**: https://continuousdelivery.com/
- **Monitoring**: https://sre.google/sre-book/monitoring-distributed-systems/
