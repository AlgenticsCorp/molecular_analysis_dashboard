# Pull Request Process

*Code review and integration procedures for maintaining high code quality and team collaboration.*

## Overview

Pull Requests (PRs) are the primary mechanism for code integration, review, and knowledge sharing. Every change to `main` and `dev` branches must go through the PR process to ensure quality, maintainability, and team alignment.

## PR Creation Guidelines

### Before Creating a PR

#### 1. Pre-flight Checklist
- [ ] Feature branch is up-to-date with target branch
- [ ] All tests pass locally
- [ ] Pre-commit hooks pass (`pre-commit run --all-files`)
- [ ] Code follows project style guidelines
- [ ] Documentation updated (if applicable)
- [ ] Self-review completed

#### 2. Local Testing
```bash
# Run full test suite
docker compose -f docker-compose.test.yml up --abort-on-container-exit

# Check code coverage
pytest --cov=src/molecular_analysis_dashboard --cov-fail-under=80

# Frontend tests
cd frontend && npm test && npm run type-check

# Integration test with services
docker compose up -d postgres redis
docker compose run --rm api pytest tests/integration/
```

### PR Title and Description

#### Title Format
```
type(scope): Brief description (MOL-123)

# Examples
feat(api): Add molecule upload endpoint (MOL-123)
fix(frontend): Resolve docking job status updates (MOL-456)
docs(setup): Update Docker installation guide (MOL-789)
```

#### Description Template
```markdown
## Summary
Brief description of what this PR accomplishes and why.

## Changes
- [ ] Added new molecule upload API endpoint
- [ ] Updated frontend to handle file uploads
- [ ] Added validation for SDF format
- [ ] Updated API documentation

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests pass
- [ ] Manual testing completed
- [ ] Performance impact assessed

## Documentation
- [ ] API documentation updated
- [ ] README changes (if applicable)
- [ ] Architecture docs updated (if applicable)

## Breaking Changes
- None / [Description of breaking changes]

## Screenshots/Demo
[Include screenshots, GIFs, or links to demo deployments if applicable]

## Related Issues
Closes #123
Related to #456

## Deployment Notes
[Any special deployment considerations, migration steps, etc.]

## Reviewer Focus Areas
[Specific areas where you'd like reviewer attention]
```

## Review Requirements

### Automated Checks (Required)
All PRs must pass automated checks before merge:

#### Backend Checks
- **Tests**: All unit and integration tests pass
- **Coverage**: Code coverage ≥80% overall
- **Style**: Black, isort, flake8 pass
- **Types**: MyPy type checking passes
- **Security**: Bandit security analysis passes
- **Dependencies**: No known security vulnerabilities

#### Frontend Checks
- **Tests**: Jest unit tests and Vitest component tests pass
- **Types**: TypeScript compilation successful
- **Lint**: ESLint passes with project configuration
- **Format**: Prettier formatting applied
- **Bundle**: Build process completes successfully

#### Integration Checks
- **E2E Tests**: Playwright end-to-end tests pass
- **API Contract**: OpenAPI schema validation passes
- **Database**: Migration tests pass (if schema changes)
- **Performance**: No significant regression detected

### Human Review Requirements

#### For `dev` Branch
- **Minimum**: 1 approving review from team member
- **Recommended**: 2 reviews for complex changes
- **Required**: Architecture review for significant design changes

#### For `main` Branch (Releases)
- **Minimum**: 2 approving reviews
- **Required**: Lead developer or architect approval
- **Required**: QA sign-off for major releases
- **Required**: Security review for auth/permissions changes

### Review Criteria

#### Code Quality
- [ ] **Readability**: Code is self-documenting with clear variable/function names
- [ ] **Maintainability**: Follows SOLID principles and Clean Architecture
- [ ] **Performance**: No obvious performance issues or resource leaks
- [ ] **Security**: No security vulnerabilities or sensitive data exposure
- [ ] **Error Handling**: Proper error handling and logging
- [ ] **Testing**: Adequate test coverage and quality

#### Architecture Alignment
- [ ] **Clean Architecture**: Respects dependency inversion and layer boundaries
- [ ] **Ports & Adapters**: Uses interfaces for external dependencies
- [ ] **Multi-tenancy**: Proper organization-based data isolation
- [ ] **API Design**: RESTful conventions and proper status codes
- [ ] **Database**: Proper migrations and query optimization

#### Documentation
- [ ] **Code Comments**: Complex logic explained with comments
- [ ] **API Docs**: OpenAPI specifications updated
- [ ] **README**: Updated if user-facing changes
- [ ] **Architecture**: Updated if design changes
- [ ] **Changelog**: Entry added for user-facing changes

## Review Process

### For Reviewers

#### 1. Initial Review Setup
```bash
# Check out the PR branch locally
git fetch origin
git checkout feature/MOL-123-new-feature

# Run tests locally
docker compose -f docker-compose.test.yml up --abort-on-container-exit

# Test the feature manually
docker compose up -d
# Navigate to http://localhost and test (gateway route)
# Alternative: http://localhost:3000 for direct frontend access
```

#### 2. Review Checklist
- [ ] Read PR description and understand the goal
- [ ] Review changed files for code quality
- [ ] Check test coverage and test quality
- [ ] Verify documentation updates
- [ ] Test functionality manually (if user-facing)
- [ ] Consider security implications
- [ ] Assess performance impact
- [ ] Check for breaking changes

#### 3. Feedback Guidelines

**Types of Comments:**
- **Nitpick**: Minor style/preference issues (non-blocking)
- **Question**: Clarification needed (non-blocking)
- **Suggestion**: Improvement recommendation (non-blocking)
- **Issue**: Must be addressed before merge (blocking)
- **Blocker**: Critical issue that prevents merge (blocking)

**Comment Examples:**
```markdown
# Good feedback
**Issue**: This function could cause a memory leak because it doesn't close the database connection.

**Suggestion**: Consider extracting this logic into a separate service class for better testability.

**Nitpick**: Variable name could be more descriptive (e.g., `user_molecules` instead of `data`).

**Question**: Is this endpoint backward compatible with existing clients?
```

#### 4. Approval Guidelines
- **Approve**: All requirements met, ready to merge
- **Request Changes**: Blocking issues that must be addressed
- **Comment**: Feedback provided but not blocking merge

### For Authors

#### Responding to Feedback
1. **Address all feedback**: Respond to every comment
2. **Make requested changes**: Fix all blocking issues
3. **Ask for clarification**: If feedback is unclear
4. **Update PR description**: If scope changes significantly
5. **Re-request review**: After making substantial changes

#### Comment Resolution
```markdown
# Addressing feedback
✅ **Fixed**: Updated the function to properly close database connections.

❓ **Question**: Could you clarify what you mean by "more descriptive"?

💭 **Acknowledged**: I'll create a follow-up issue to refactor this into a service class.

🔄 **Updated**: Changed variable name to `user_molecules` as suggested.
```

## Merge Procedures

### Pre-merge Requirements
- [ ] All automated checks pass
- [ ] Required approvals obtained
- [ ] All feedback addressed or acknowledged
- [ ] Branch is up-to-date with target branch
- [ ] No merge conflicts
- [ ] Final manual testing completed (if required)

### Merge Strategies

#### Feature → Dev: Squash and Merge
```bash
# GitHub will automatically:
# 1. Squash all commits into one
# 2. Use PR title as commit message
# 3. Include PR description in commit body
# 4. Delete feature branch
```

**Benefits:**
- Clean linear history in dev branch
- Easy to revert entire features
- Simplifies changelog generation

#### Release/Hotfix → Main: Merge Commit
```bash
# GitHub will:
# 1. Create merge commit preserving branch history
# 2. Tag with version number
# 3. Trigger production deployment
```

**Benefits:**
- Preserves development history
- Clear release boundaries
- Supports semantic versioning

### Post-merge Actions

#### Automatic
- **CI/CD Pipeline**: Triggers deployment to appropriate environment
- **Branch Cleanup**: Feature branches automatically deleted
- **Issue Updates**: Related issues marked as resolved
- **Notifications**: Team notified via Slack/email

#### Manual
- **Update Local Branches**: Pull latest changes
- **Monitor Deployment**: Check deployment status and health
- **Update Documentation**: External docs if needed
- **Create Follow-up Issues**: For any identified improvements

## PR Templates

### Feature PR Template
```markdown
## 🎯 Objective
[Brief description of the feature and its business value]

## 🔧 Implementation
### Changes Made
- [ ] Backend: [describe backend changes]
- [ ] Frontend: [describe frontend changes]
- [ ] Database: [describe schema changes]
- [ ] Tests: [describe test additions/updates]

### Architecture Decisions
[Explain any significant architectural choices]

## 🧪 Testing
- [ ] Unit tests added/updated (coverage: X%)
- [ ] Integration tests pass
- [ ] E2E tests updated (if applicable)
- [ ] Manual testing scenarios:
  - [ ] [Scenario 1]
  - [ ] [Scenario 2]

## 📖 Documentation
- [ ] API documentation updated
- [ ] Code comments added for complex logic
- [ ] README updated (if applicable)

## 🚨 Breaking Changes
[List any breaking changes and migration steps]

## 📸 Screenshots/Demo
[Visual evidence of the feature working]

## 🔗 Related
- Closes #[issue-number]
- Related to #[related-issue]

## 🎯 Reviewer Focus
[Specific areas where you want reviewer attention]
```

### Bug Fix PR Template
```markdown
## 🐛 Problem
[Description of the bug and its impact]

## 🔍 Root Cause
[Analysis of what caused the bug]

## 🛠️ Solution
[Description of the fix and why this approach was chosen]

## 🧪 Testing
- [ ] Reproduction test added
- [ ] Fix verified manually
- [ ] Regression tests updated
- [ ] Edge cases considered

## 🚨 Risk Assessment
- **Impact**: [Low/Medium/High]
- **Urgency**: [Low/Medium/High/Critical]
- **Affected Users**: [Description]

## 📖 Documentation
- [ ] Troubleshooting docs updated
- [ ] Known issues removed

## 🔗 Related
- Fixes #[issue-number]
- Related incidents: [links]
```

## Quality Gates

### Automated Quality Checks

#### Code Quality
```yaml
# .github/workflows/quality.yml
name: Quality Gates

on:
  pull_request:
    branches: [dev, main]

jobs:
  backend-quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run backend tests
        run: |
          docker compose -f docker-compose.test.yml up --abort-on-container-exit
      - name: Check coverage
        run: |
          docker compose run --rm api pytest --cov=src --cov-fail-under=80
      - name: Security scan
        run: |
          docker compose run --rm api bandit -r src/

  frontend-quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      - name: Install dependencies
        run: cd frontend && npm ci
      - name: Run tests
        run: cd frontend && npm test
      - name: Type check
        run: cd frontend && npm run type-check
      - name: Build
        run: cd frontend && npm run build
```

#### Security Scanning
- **SAST**: Static analysis with Bandit, ESLint security rules
- **Dependency Scan**: Known vulnerabilities in npm/pip packages
- **Secret Detection**: Prevent secrets in code
- **Container Scan**: Docker image vulnerability scanning

### Performance Gates
- **Bundle Size**: Frontend bundle size limits
- **API Response Time**: Backend endpoint performance
- **Database Query Performance**: N+1 queries and slow queries
- **Memory Usage**: Container resource consumption

## Troubleshooting

### Common PR Issues

#### "Checks are failing"
1. Check the specific failing check in PR status
2. Run the same check locally to debug
3. Fix the issue and push new commits
4. Checks will re-run automatically

#### "Merge conflicts"
```bash
# Update your branch with target branch
git checkout your-feature-branch
git fetch origin
git merge origin/dev  # or origin/main

# Resolve conflicts in your editor
# Commit the resolution
git add .
git commit -m "resolve merge conflicts"
git push origin your-feature-branch
```

#### "Missing required reviews"
- Request reviews from team members
- Address any blocking feedback
- Ping reviewers if urgent
- Check if you need specific reviewer types (architect, security, etc.)

#### "Branch protection violations"
- Ensure all required status checks pass
- Get the required number of approving reviews
- Update branch to be current with target
- Check for any custom protection rules

### Review Best Practices

#### For Large PRs
- Break into smaller, focused PRs when possible
- Provide detailed description and context
- Schedule sync review session for complex changes
- Consider draft PR for early feedback

#### For Urgent Fixes
- Label PR as "urgent" or "hotfix"
- Ping specific reviewers immediately
- Provide extra context about urgency
- Fast-track review process with senior approval

#### For Architecture Changes
- Create design document first
- Get architecture review before implementation
- Include performance and scalability considerations
- Document migration strategy

## Resources

- **GitHub PR Guide**: https://docs.github.com/en/pull-requests
- **Code Review Best Practices**: https://google.github.io/eng-practices/review/
- **Clean Code**: https://clean-code-developer.com/
- **Testing Best Practices**: https://testing.googleblog.com/
- **Security Review Guidelines**: https://owasp.org/www-project-code-review-guide/
