# Git Workflow

*Branch management and collaboration standards for the Molecular Analysis Dashboard project.*

## Overview

We use a **GitFlow-inspired workflow** with `main` and `dev` branches, feature branches, and release branches. This ensures stable releases while allowing parallel development.

## Branch Structure

### Main Branches

#### `main` - Production Branch
- **Purpose**: Production-ready code only
- **Protection**: Direct commits disabled, requires PR with reviews
- **Deployment**: Auto-deploys to production environment
- **Tagging**: All releases tagged here (`v1.0.0`, `v1.1.0`, etc.)

#### `dev` - Development Integration
- **Purpose**: Integration branch for all feature development
- **Protection**: Direct commits discouraged, prefer PR workflow
- **Deployment**: Auto-deploys to staging environment
- **Testing**: All features tested together before release

### Supporting Branches

#### Feature Branches: `feature/MOL-{ticket}-{description}`
```bash
# Examples
feature/MOL-123-docking-engine-integration
feature/MOL-456-user-authentication
feature/MOL-789-molecule-visualization
```

**Lifecycle:**
1. Branch from `dev`
2. Develop feature with regular commits
3. Create PR to merge back into `dev`
4. Delete after successful merge

#### Release Branches: `release/v{version}`
```bash
# Examples
release/v1.0.0
release/v1.1.0
release/v2.0.0-beta.1
```

**Lifecycle:**
1. Branch from `dev` when feature-complete
2. Bug fixes and documentation updates only
3. Merge into both `main` and `dev`
4. Tag release on `main`

#### Hotfix Branches: `hotfix/v{version}-{description}`
```bash
# Examples
hotfix/v1.0.1-security-patch
hotfix/v1.1.1-database-connection-fix
```

**Lifecycle:**
1. Branch from `main` for urgent production fixes
2. Fix issue with minimal changes
3. Merge into both `main` and `dev`
4. Tag patch release on `main`

## Commit Message Standards

### Format
```
type(scope): subject

[optional body]

[optional footer(s)]
```

### Types
- **feat**: New feature for users
- **fix**: Bug fix for users
- **docs**: Documentation changes
- **style**: Code style changes (formatting, missing semi-colons, etc.)
- **refactor**: Code changes that neither fix bugs nor add features
- **perf**: Performance improvements
- **test**: Adding or updating tests
- **chore**: Maintenance tasks, dependency updates
- **ci**: CI/CD pipeline changes
- **build**: Build system or external dependency changes

### Scope Examples
- **api**: Backend API changes
- **frontend**: React frontend changes
- **db**: Database schema or migration changes
- **docker**: Docker configuration changes
- **docs**: Documentation updates
- **auth**: Authentication/authorization changes
- **docking**: Molecular docking engine changes

### Examples
```bash
# Good commit messages
feat(api): add REST endpoint for molecule upload
fix(frontend): resolve molecule viewer rendering issue
docs(setup): update Docker installation instructions
chore(deps): update FastAPI to v0.104.1
test(docking): add integration tests for Vina engine

# Bad commit messages
Fixed bug
Update code
WIP
Merge branch
```

### Breaking Changes
```bash
feat(api)!: change molecule upload endpoint format

BREAKING CHANGE: The molecule upload endpoint now expects
molecule data in SDF format instead of SMILES strings.
This affects all API clients.

Migration guide: https://docs.example.com/migration/v2
```

## Workflow Procedures

### Starting New Feature
```bash
# 1. Sync with latest dev
git checkout dev
git pull origin dev

# 2. Create feature branch
git checkout -b feature/MOL-123-new-docking-engine

# 3. Make your changes
git add .
git commit -m "feat(docking): add Gnina engine adapter"

# 4. Push and create PR
git push origin feature/MOL-123-new-docking-engine
# Create PR in GitHub UI targeting dev branch
```

### Release Preparation
```bash
# 1. Create release branch from dev
git checkout dev
git pull origin dev
git checkout -b release/v1.2.0

# 2. Update version numbers
# Edit pyproject.toml, package.json, etc.
git commit -m "chore(release): bump version to v1.2.0"

# 3. Final testing and bug fixes only
# No new features!

# 4. Create PR to main
git push origin release/v1.2.0
# Create PR in GitHub UI targeting main branch
```

### Hotfix Process
```bash
# 1. Create hotfix branch from main
git checkout main
git pull origin main
git checkout -b hotfix/v1.1.1-security-fix

# 2. Fix the critical issue
git commit -m "fix(auth): patch JWT validation vulnerability"

# 3. Update version number
git commit -m "chore(release): bump version to v1.1.1"

# 4. Create PRs to both main and dev
git push origin hotfix/v1.1.1-security-fix
# Create PRs in GitHub UI
```

## Branch Protection Rules

### `main` Branch
- Require PR with at least 2 approving reviews
- Require status checks to pass:
  - All CI tests (unit, integration, E2E)
  - Code coverage ≥80%
  - Security scan (no high/critical issues)
  - Pre-commit hooks pass
- Require branches to be up to date before merging
- Require linear history (squash and merge only)
- Restrict pushes to administrators only

### `dev` Branch
- Require PR with at least 1 approving review
- Require status checks to pass:
  - All CI tests pass
  - Code coverage ≥80%
  - Pre-commit hooks pass
- Allow merge commits for feature integration
- Dismiss stale reviews when new commits pushed

## Merge Strategies

### Feature → Dev: Squash and Merge
- Creates clean linear history
- Combines all feature commits into single commit
- Preserves PR description in commit message
- Easier to revert entire features if needed

### Release/Hotfix → Main: Merge Commit
- Preserves branch history for release tracking
- Maintains clear release boundaries
- Easier to identify what went into each release
- Supports semantic versioning and changelog generation

### Dev → Main (via Release): Merge Commit
- Preserves development history
- Clear release boundaries in git log
- Supports automated changelog generation

## Git Aliases and Tools

### Recommended Git Aliases
```bash
# Add to ~/.gitconfig
[alias]
    co = checkout
    br = branch
    ci = commit
    st = status
    unstage = reset HEAD --
    last = log -1 HEAD
    visual = !gitk

    # Workflow helpers
    new-feature = "!f() { git checkout dev && git pull origin dev && git checkout -b feature/MOL-$1; }; f"
    sync-dev = "!git checkout dev && git pull origin dev"
    cleanup-branches = "!git branch --merged dev | grep -E '^\\s+feature/' | xargs -n 1 git branch -d"

    # Pretty logging
    lg = log --color --graph --pretty=format:'%Cred%h%Creset -%C(yellow)%d%Creset %s %Cgreen(%cr) %C(bold blue)<%an>%Creset' --abbrev-commit
    lga = log --color --graph --pretty=format:'%Cred%h%Creset -%C(yellow)%d%Creset %s %Cgreen(%cr) %C(bold blue)<%an>%Creset' --abbrev-commit --all
```

### Pre-commit Hooks
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
        args: ['--maxkb=500']

  - repo: https://github.com/psf/black
    rev: 23.7.0
    hooks:
      - id: black
        language_version: python3

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
        args: ["--profile", "black"]

  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
        args: ["--max-line-length=88", "--extend-ignore=E203,W503"]
```

## Troubleshooting

### Common Issues

#### "Branch protection rule violations"
- Ensure all required status checks pass
- Get required number of approving reviews
- Update branch with latest changes from target

#### "Merge conflicts"
```bash
# Update your branch with latest target branch
git checkout your-feature-branch
git fetch origin
git merge origin/dev  # or origin/main

# Resolve conflicts in your editor
# Then commit the resolution
git add .
git commit -m "resolve merge conflicts with dev"
```

#### "Pre-commit hooks failing"
```bash
# Run hooks manually to see detailed errors
pre-commit run --all-files

# Fix issues and commit again
git add .
git commit -m "fix code style issues"
```

### Recovery Procedures

#### Accidentally committed to wrong branch
```bash
# Move commits to correct branch
git log --oneline  # Note commit hashes
git checkout correct-branch
git cherry-pick commit-hash

# Remove from wrong branch
git checkout wrong-branch
git reset --hard HEAD~1  # Remove last commit
```

#### Need to update commit message
```bash
# Last commit only (not yet pushed)
git commit --amend -m "new message"

# Multiple commits or already pushed
# Create new commit with fix
git commit -m "fix: correct previous commit message"
```

## Resources

- **Git Documentation**: https://git-scm.com/doc
- **GitHub Flow**: https://guides.github.com/introduction/flow/
- **Conventional Commits**: https://www.conventionalcommits.org/
- **Semantic Versioning**: https://semver.org/
- **Pre-commit Framework**: https://pre-commit.com/
