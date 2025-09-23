# Development Workflows

*Standardized processes for contribution, testing, and deployment workflows.*

## Overview

This section contains all the standardized workflows and processes used in the Molecular Analysis Dashboard project. These workflows ensure consistency, quality, and reliability across all development activities.

## Available Workflows

### 📋 [Git Workflow](git-workflow.md)
**Branch management and collaboration standards**
- Feature branch workflow with dev/main branches
- Commit message conventions and standards
- Merge vs rebase strategies
- Hotfix and release branch procedures

### 🔍 [Pull Request Process](pull-request-process.md)
**Code review and integration procedures**
- PR creation guidelines and templates
- Review requirements and checklist
- Automated testing and quality gates
- Merge requirements and procedures

### 🚀 [Release Management](release-management.md)
**Version control and deployment procedures**
- Semantic versioning strategy
- Release planning and coordination
- Deployment procedures and rollback
- Hotfix release procedures

### ⚙️ [CI/CD Pipeline](cicd-pipeline.md)
**Automated testing and deployment workflows**
- GitHub Actions workflow configuration
- Quality gates and automated checks
- Docker image building and deployment
- Environment-specific deployment procedures

### 🧪 [Testing Workflows](testing-workflows.md)
**Testing strategies and execution procedures**
- Unit, integration, and E2E testing procedures
- Test data management and cleanup
- Performance testing and benchmarking
- Security testing and vulnerability scanning

## Quick Reference

### Common Git Commands
```bash
# Start new feature
git checkout dev
git pull origin dev
git checkout -b feature/MOL-123-new-feature

# Create PR
git push origin feature/MOL-123-new-feature
# Open PR in GitHub UI

# Release preparation
git checkout dev
git pull origin dev
git checkout -b release/v1.2.0
```

### Quality Checklist
- [ ] All tests pass (`docker compose -f docker-compose.test.yml up --abort-on-container-exit`)
- [ ] Code coverage meets requirements (≥80%)
- [ ] Pre-commit hooks pass (`pre-commit run --all-files`)
- [ ] Documentation updated (API docs, README, etc.)
- [ ] Security scan clean (no high/critical vulnerabilities)
- [ ] Performance impact assessed

## Workflow Integration

All workflows integrate with our development tools:

- **GitHub Projects**: Issue tracking and milestone management
- **Docker Compose**: Local development and testing environments (see [Setup Guide](../getting-started/setup.md))
- **Pre-commit Hooks**: Automated code quality checks
- **GitHub Actions**: CI/CD automation and deployment
- **Code Quality Gates**: Automated quality and security analysis

## Getting Help

- **New to Git?** Start with [Git Workflow](git-workflow.md) basics
- **First PR?** Follow the [Pull Request Process](pull-request-process.md) guide
- **Release Manager?** Reference [Release Management](release-management.md)
- **DevOps Setup?** Check [CI/CD Pipeline](cicd-pipeline.md) configuration

For questions or workflow improvements, create an issue with the `workflow` label or reach out in the team chat.
