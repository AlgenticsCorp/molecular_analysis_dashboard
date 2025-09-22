# Molecular Analysis Dashboard - AI Coding Agent Instructions

This is a **molecular analysis platform** built with **Clean Architecture** (Ports & Adapters), supporting pluggable docking engines (Vina/Smina/Gnina) with React TypeScript frontend and FastAPI backend.

## 🔄 Terminal & Process Management
- **Reuse the last active integrated terminal** for commands
- **Only open a new terminal** if the last active terminal is running a long-lived process (e.g., dev server, tail, watch). Detect by checking recent process output or known start commands (npm run dev, vite, uvicorn, flask, next dev, etc.)
- When opening a new terminal, **name it** with the task (e.g., `build`, `tests`, `lint`) and reuse it thereafter
- **Environment activation**: Before running any commands, ensure the correct environment is active:
  - Backend: Check for virtual environment (`venv`, `conda`, `poetry`) activation
  - Frontend: Ensure correct Node.js version if using version managers
  - Docker: Verify services are running before executing dependent commands

## 🛡️ Change Safety & Approvals
- **Do not modify or write code** unless the user has explicitly asked for an update, modification, or implementation
- Before any change:
  1) **Read** all `.md` guidance in the repo (project_design/*.md, README.md, CONTRIBUTING.md, etc.) and **map** the repo structure to decide correct locations
  2) **Propose a short plan** (files to touch, functions to add/change, tests to run). **Ask for approval** before editing
- When a task is done:
  - **Run** the solution end-to-end, **read console output**, and summarize results and any errors
  - **Ask for approval** to mark the task complete

## 🐛 Debugging Discipline
- During debugging, you may insert **temporary diagnostics** (logs, asserts, feature flags) but **remove all debug code** once fixed
- Apply the **final fix in place** in the canonical file(s) (no duplicate/new versions unless explicitly requested)

## 🗑️ Dependency & Deletion Safety
- Before removing any file or symbol, **analyze references** (imports, exports, runtime use) to ensure it isn't depended on. Propose the removal plan and get approval

## ✅ Testing & Validation
- After completing a task or fix, **run the relevant tests/linters** and **execute** the app/command needed to prove it works. Summarize console output and status

## 📝 Git & CI
- In GitHub repos: after successful local validation, **ask for approval** before `git commit` / `git push` / PR creation
- Use descriptive commit messages; if creating a PR, include a summary of changes, tests run, and risk notes

## 🔁 Interaction Loop (applies after *every* user request)
1) Clarify intent if ambiguous
2) If the user did **not** ask for changes → provide analysis/plan only; **do not edit**
3) If changes are requested → read guidelines, propose plan → **wait for approval**
4) Implement approved plan; reuse terminals; respect env activation
5) Test, run, read console; **ask for approval** to finish
6) Sync Project: update/create issue as needed, ensure item exists in Org Project 1, and set an appropriate **Status** (Backlog/In Progress/In Review/Done) using the commands below.
7) If GitHub: ask approval to commit/push/PR after tests pass

## 🧬 Domain Knowledge

**Core Entities**: `Molecule`, `DockingJob`, `Pipeline`, `Organization` - molecular structures undergo docking analysis via computational engines
**Key Workflows**: Upload molecules → Configure pipeline parameters → Submit docking jobs → Monitor execution → Visualize 3D results
**Multi-tenant**: Organization-based data isolation with per-org results databases
**Async Processing**: Long-running molecular docking via Celery workers (separate from API)

## 🏗️ Clean Architecture Pattern

**STRICT layering** - dependencies point inward only:

```
src/molecular_analysis_dashboard/
├── domain/          # Pure business logic (Molecule, DockingJob entities)
├── use_cases/       # Application services (CreateDockingJobUseCase)
├── ports/           # Abstract interfaces (DockingEnginePort, RepositoryPort)
├── adapters/        # Implementations (PostgreSQLRepository, VinaAdapter)
├── infrastructure/  # Framework setup (Celery, FastAPI, DB sessions)
├── presentation/    # API routes and Pydantic schemas
└── shared/          # Cross-cutting utilities
```

**Adding features**: Start with `domain/` entities → `use_cases/` orchestration → `ports/` interfaces → `adapters/` implementations → wire in `infrastructure/`

## 🛠️ Development Patterns

### Docker-First Development
```bash
# Backend services (always start with this)
docker compose up -d postgres redis
docker compose run --rm migrate  # Run migrations first
docker compose up -d api worker

# Frontend (separate terminal)
cd frontend && npm run dev

# Scale workers independently
docker compose up -d --scale worker=3
```

### Testing Strategy
- **Unit tests**: `pytest tests/unit/` - fast, isolated business logic
- **Integration**: `pytest tests/integration/` - database and service integration
- **E2E**: `docker compose -f docker-compose.test.yml up --abort-on-container-exit`
- **Frontend**: `cd frontend && npm test`

### Code Quality (MANDATORY)
```bash
# Backend - all must pass
pre-commit run --all-files  # Black, isort, flake8, mypy, bandit
pytest --cov=src/molecular_analysis_dashboard --cov-fail-under=80

# Frontend
npm run type-check && npm run lint && npm test
```

## 🔌 Key Integration Patterns

### Docking Engine Adapters
- **Pluggable engines**: Implement `DockingEnginePort` for new engines (Vina/Smina/Gnina/custom)
- **Subprocess execution**: Engines run as external processes, results parsed from output files
- **Error handling**: Map engine-specific errors to domain exceptions

### Database Patterns
- **Multi-tenant**: Shared metadata DB + per-org results DBs (dynamic connection routing)
- **Async SQLAlchemy**: All DB operations use `async`/`await` with connection pooling
- **Alembic migrations**: Always run `docker compose run --rm migrate` after schema changes

### File Storage
- **Development**: Local filesystem (`STORAGE_TYPE=local`)
- **Production**: S3/MinIO (`STORAGE_TYPE=s3`) - same adapter interface
- **Artifacts**: Store URIs or paths in DB, not file contents

## 📁 File Placement Rules

**Domain Logic** → `domain/entities/`, `domain/services/`
**Business Workflows** → `use_cases/commands/`, `use_cases/queries/`
**External Contracts** → `ports/repository/`, `ports/external/`
**Database/Engine/API** → `adapters/database/`, `adapters/messaging/`
**Config/DI/Security** → `infrastructure/`
**HTTP API** → `presentation/api/`
**React Components** → `frontend/src/components/`, `frontend/src/pages/`

## 🎯 API & Frontend Patterns

### FastAPI Conventions
- **JWT auth**: All endpoints require org-scoped JWT tokens
- **Pydantic schemas**: Strict input/output validation
- **Health checks**: `/health` (liveness), `/ready` (dependencies)
- **API versioning**: `/api/v1/` prefix

### React TypeScript Patterns
- **Material-UI**: Consistent design system with theme
- **React Query**: Server state management for API calls
- **3Dmol.js**: Molecular visualization in browser
- **Form handling**: React Hook Form + Zod validation
- **Type safety**: Shared TypeScript interfaces between frontend/backend

## ⚡ Performance & Scaling

**API**: Stateless FastAPI - scale horizontally (`--scale api=N`)
**Workers**: CPU-bound Celery workers - tune concurrency per queue
**Database**: Connection pooling, read replicas for large datasets
**Storage**: Object storage (S3/MinIO) for large molecular files
**Caching**: Redis for job queues and result caching via `input_signature`

## 🔄 Common Workflows

### Adding New Docking Engine
1. Implement `DockingEnginePort` in `adapters/external/`
2. Add engine config to `infrastructure/settings.py`
3. Register in dependency injection
4. Add engine option to pipeline creation UI

### Database Schema Changes
1. Create Alembic migration: `alembic revision --autogenerate -m "description"`
2. Test migration: `docker compose run --rm migrate`
3. Update repository adapters and domain entities
4. Run tests to verify data flow

### New API Endpoints
1. Define Pydantic schemas in `presentation/api/schemas/`
2. Create use case in `use_cases/` (business logic)
3. Add FastAPI router in `presentation/api/routes/`
4. Update frontend API client in `frontend/src/services/`

## 🚨 Critical Conventions

- **Never bypass the adapter pattern** - don't import SQLAlchemy models in use cases
- **Async everywhere** - all database and HTTP operations use async/await
- **Multi-tenant aware** - all queries must filter by `org_id`
- **Type safety** - use mypy strict mode, comprehensive docstrings
- **Docker-first** - local development uses containers, not local Python installs
- **Test coverage** - maintain 80%+ coverage, test at correct architectural layers

## 📚 Key Reference Files

- Architecture: `project_design/ARCHITECTURE.md`, `project_design/FRAMEWORK_DESIGN.md`
- API contracts: `project_design/API_CONTRACT.md`
- Database schema: `project_design/ERD.md`
- Deployment: `project_design/DEPLOYMENT_DOCKER.md`
- Implementation stages: `project_design/IMPLEMENTATION_PLAN.md`

---

## 🚨 CRITICAL: Follow the Interaction Loop

**Every request must follow this sequence:**
1. **Clarify** if intent is ambiguous
2. **Analyze** before acting - read relevant docs and understand the change
3. **Propose** a plan and wait for approval if making changes
4. **Implement** using proper terminals and environments
5. **Test** and validate the solution works
6. Sync Project: update/create issue as needed, ensure item exists in Org Project 1, and set an appropriate **Status** (Backlog/In Progress/In Review/Done) using the commands below.
7. **Report** results and ask for approval to complete

## 🗂️ GitHub Projects & Issues — Copilot Playbook (AlgenticsCorp)

> **Scope:** Org Project (v2) **AlgenticsCorp / Project 1** and repo **AlgenticsCorp/molecular_analysis_dashboard**. These commands are templates the Agent should use and run **only after approval of the plan**.

### ✅ Pre‑flight (one time per machine or when scopes change)
```bash
# Ensure token has the 'project' scope and you can see Org Project 1
gh project view 1 --owner AlgenticsCorp
```

## 📋 Milestone Management

### Create Milestones
```bash
# Create a milestone with title and description
gh api \
  repos/AlgenticsCorp/molecular_analysis_dashboard/milestones \
  --method POST \
  --field title="Stage X: Milestone Title" \
  --field description="## Goal\n<description>\n\n## Acceptance Criteria\n- [ ] <criteria>"

# Create milestone with due date (ISO 8601 format)
gh api \
  repos/AlgenticsCorp/molecular_analysis_dashboard/milestones \
  --method POST \
  --field title="Release v1.0" \
  --field description="Production release milestone" \
  --field due_on="2025-12-31T23:59:59Z"
```

### List Milestones
```bash
# List all milestones (open and closed) with details
gh api repos/AlgenticsCorp/molecular_analysis_dashboard/milestones \
  --jq '.[] | {number, title, state, open_issues, closed_issues, due_on}'

# List only open milestones sorted by number
gh api repos/AlgenticsCorp/molecular_analysis_dashboard/milestones \
  --jq '.[] | select(.state == "open") | "\(.number): \(.title)"' | sort -n

# Get milestone details by number
gh api repos/AlgenticsCorp/molecular_analysis_dashboard/milestones/<MILESTONE_NUMBER>
```

### Update Milestones
```bash
# Update milestone title and description
gh api \
  repos/AlgenticsCorp/molecular_analysis_dashboard/milestones/<MILESTONE_NUMBER> \
  --method PATCH \
  --field title="Updated Title" \
  --field description="Updated description"

# Close a milestone
gh api \
  repos/AlgenticsCorp/molecular_analysis_dashboard/milestones/<MILESTONE_NUMBER> \
  --method PATCH \
  --field state="closed"

# Reopen a milestone
gh api \
  repos/AlgenticsCorp/molecular_analysis_dashboard/milestones/<MILESTONE_NUMBER> \
  --method PATCH \
  --field state="open"
```

### Delete Milestones
```bash
# Delete a milestone (WARNING: Cannot be undone)
gh api \
  repos/AlgenticsCorp/molecular_analysis_dashboard/milestones/<MILESTONE_NUMBER> \
  --method DELETE

# Bulk delete all milestones (use with extreme caution)
gh api repos/AlgenticsCorp/molecular_analysis_dashboard/milestones \
  --jq '.[].number' | while read milestone; do
    gh api repos/AlgenticsCorp/molecular_analysis_dashboard/milestones/$milestone --method DELETE
    echo "Deleted milestone #$milestone"
  done
```

## 🎫 Issue Management
```bash
## 🎫 Issue Management

### Create Issues
```bash
# Create an issue with labels and milestone
ISSUE_URL=$(gh issue create \
  --repo AlgenticsCorp/molecular_analysis_dashboard \
  --title "<type>: <clear actionable title>" \
  --body "Goal:\n- <what>\nAcceptance:\n- <checks>\nContext:\n- See project_design/<doc>.md" \
  --label "type:feature,priority:high" \
  --milestone "<MILESTONE_NUMBER>" \
  --assignee "@me" \
  --json url -q .url)

# Create issue and add to project in one step
gh issue create \
  --repo AlgenticsCorp/molecular_analysis_dashboard \
  --title "feat: implement user authentication" \
  --body "Implementation details..." \
  --label "type:feature" | \
  xargs -I {} gh project item-add 1 --owner AlgenticsCorp --url {}
```

### List Issues
```bash
# List all open issues with details
gh issue list \
  --repo AlgenticsCorp/molecular_analysis_dashboard \
  --state open \
  --json number,title,labels,milestone,assignees

# List issues by milestone
gh issue list \
  --repo AlgenticsCorp/molecular_analysis_dashboard \
  --milestone "<MILESTONE_TITLE>" \
  --json number,title,state

# List issues by label
gh issue list \
  --repo AlgenticsCorp/molecular_analysis_dashboard \
  --label "type:bug" \
  --json number,title,state

# Search issues by text
gh issue list \
  --repo AlgenticsCorp/molecular_analysis_dashboard \
  --search "docking engine" \
  --json number,title
```

### Update Issues
```bash
# Update issue title and body
gh issue edit <ISSUE_NUMBER> \
  --repo AlgenticsCorp/molecular_analysis_dashboard \
  --title "Updated title" \
  --body "Updated description"

# Add labels to existing issue
gh issue edit <ISSUE_NUMBER> \
  --repo AlgenticsCorp/molecular_analysis_dashboard \
  --add-label "priority:high,status:blocked"

# Remove labels from issue
gh issue edit <ISSUE_NUMBER> \
  --repo AlgenticsCorp/molecular_analysis_dashboard \
  --remove-label "status:blocked"

# Assign user to issue
gh issue edit <ISSUE_NUMBER> \
  --repo AlgenticsCorp/molecular_analysis_dashboard \
  --add-assignee "@username"

# Remove assignee from issue
gh issue edit <ISSUE_NUMBER> \
  --repo AlgenticsCorp/molecular_analysis_dashboard \
  --remove-assignee "@username"
```

### Milestone Management for Issues
```bash
# Assign milestone to issue (by milestone title)
gh issue edit <ISSUE_NUMBER> \
  --repo AlgenticsCorp/molecular_analysis_dashboard \
  --milestone "Stage 0: Bootstrap API Health"

# Assign milestone to issue (by milestone number)
gh issue edit <ISSUE_NUMBER> \
  --repo AlgenticsCorp/molecular_analysis_dashboard \
  --milestone "11"

# Remove milestone from issue
gh issue edit <ISSUE_NUMBER> \
  --repo AlgenticsCorp/molecular_analysis_dashboard \
  --milestone ""

# Bulk assign milestone to multiple issues
for issue in 16 17 22 23 24 25; do
  gh issue edit $issue \
    --repo AlgenticsCorp/molecular_analysis_dashboard \
    --milestone "Stage 0: Bootstrap API Health"
done

# Assign milestone during issue creation (preferred approach)
ISSUE_URL=$(gh issue create \
  --repo AlgenticsCorp/molecular_analysis_dashboard \
  --title "task: Example task" \
  --body "Task description" \
  | grep -o 'https://github.com/[^[:space:]]*')

ISSUE_NUMBER=$(echo $ISSUE_URL | grep -o '[0-9]*$')
gh issue edit $ISSUE_NUMBER \
  --repo AlgenticsCorp/molecular_analysis_dashboard \
  --milestone "Stage 0: Bootstrap API Health"

# Verify milestone assignment
gh issue view <ISSUE_NUMBER> \
  --repo AlgenticsCorp/molecular_analysis_dashboard \
  --json milestone,title

# Move issues between milestones
gh issue edit <ISSUE_NUMBER> \
  --repo AlgenticsCorp/molecular_analysis_dashboard \
  --milestone "Stage 1: Metadata DB + Alembic Baseline"
```

### AI Agent Milestone Workflow
```bash
# COMPLETE workflow for creating issues with milestone, project, and status
create_issue_complete() {
  local title="$1"
  local body="$2"
  local milestone="$3"
  local status="${4:-Backlog}"  # Default to Backlog if not specified

  # Project constants
  local PROJECT_ID="PVT_kwDODBEF7M4BDcvv"
  local STATUS_FIELD_ID="PVTSSF_lADODBEF7M4BDcvvzg1XXs0"

  # Status option IDs
  local BACKLOG_ID="f75ad846"
  local READY_ID="61e4505c"
  local IN_PROGRESS_ID="47fc9ee4"
  local IN_REVIEW_ID="df73e18b"
  local DONE_ID="98236657"

  # Step 1: Create issue and capture URL
  local issue_url=$(gh issue create \
    --repo AlgenticsCorp/molecular_analysis_dashboard \
    --title "$title" \
    --body "$body" \
    | grep -o 'https://github.com/[^[:space:]]*')

  # Step 2: Extract issue number
  local issue_number=$(echo $issue_url | grep -o '[0-9]*$')

  # Step 3: Assign milestone
  gh issue edit $issue_number \
    --repo AlgenticsCorp/molecular_analysis_dashboard \
    --milestone "$milestone"

  # Step 4: Add to project
  gh project item-add 1 --owner AlgenticsCorp --url "$issue_url"

  # Step 5: Set status (get project item ID first)
  sleep 2  # Allow time for project item to be created
  local item_id=$(gh project item-list 1 --owner AlgenticsCorp --limit 50 --format json | \
    jq -r ".items[] | select(.content.number == $issue_number) | .id")

  # Determine status option ID
  local status_option_id
  case "$status" in
    "Backlog") status_option_id="$BACKLOG_ID";;
    "Ready") status_option_id="$READY_ID";;
    "In Progress") status_option_id="$IN_PROGRESS_ID";;
    "In Review") status_option_id="$IN_REVIEW_ID";;
    "Done") status_option_id="$DONE_ID";;
    *) status_option_id="$BACKLOG_ID";;  # Default to Backlog
  esac

  # Set status
  if [ -n "$item_id" ]; then
    gh project item-edit \
      --project-id "$PROJECT_ID" \
      --id "$item_id" \
      --field-id "$STATUS_FIELD_ID" \
      --single-select-option-id "$status_option_id"
    echo "✅ Issue #$issue_number created with status: $status"
  else
    echo "⚠️  Issue #$issue_number created but status not set (item ID not found)"
  fi

  echo "Created issue #$issue_number: $issue_url"
  return $issue_number
}

# Usage examples
create_issue_complete \
  "task: Implement health endpoint" \
  "Detailed implementation requirements..." \
  "Stage 0: Bootstrap API Health" \
  "Backlog"

# For completed work
create_issue_complete \
  "task: Already completed task" \
  "Task that was already done..." \
  "Stage 0: Bootstrap API Health" \
  "Done"
```

### Project Status Management
```bash
# Get project and field IDs (run once to get current values)
PROJECT_ID=$(gh project view 1 --owner AlgenticsCorp --format json | jq -r '.id')
STATUS_FIELD_ID="PVTSSF_lADODBEF7M4BDcvvzg1XXs0"

# Status option IDs for quick reference
BACKLOG_ID="f75ad846"       # Default for new tasks
READY_ID="61e4505c"         # Ready to start
IN_PROGRESS_ID="47fc9ee4"   # Currently being worked on
IN_REVIEW_ID="df73e18b"     # In code review
DONE_ID="98236657"          # Completed

# Update issue status in project
update_issue_status() {
  local issue_number="$1"
  local status="$2"

  # Get project item ID
  local item_id=$(gh project item-list 1 --owner AlgenticsCorp --limit 50 --format json | \
    jq -r ".items[] | select(.content.number == $issue_number) | .id")

  # Determine status option ID
  local status_option_id
  case "$status" in
    "Backlog") status_option_id="f75ad846";;
    "Ready") status_option_id="61e4505c";;
    "In Progress") status_option_id="47fc9ee4";;
    "In Review") status_option_id="df73e18b";;
    "Done") status_option_id="98236657";;
    *) echo "❌ Invalid status: $status"; return 1;;
  esac

  if [ -n "$item_id" ]; then
    gh project item-edit \
      --project-id "PVT_kwDODBEF7M4BDcvv" \
      --id "$item_id" \
      --field-id "PVTSSF_lADODBEF7M4BDcvvzg1XXs0" \
      --single-select-option-id "$status_option_id"
    echo "✅ Issue #$issue_number status updated to: $status"
  else
    echo "❌ Could not find project item for issue #$issue_number"
    return 1
  fi
}

# Usage examples
update_issue_status 20 "In Progress"
update_issue_status 16 "Done"
```

### Milestone Validation Commands
```bash
# Check if milestone exists before assignment
milestone_exists() {
  local milestone_name="$1"
  gh api repos/AlgenticsCorp/molecular_analysis_dashboard/milestones \
    --jq ".[] | select(.title == \"$milestone_name\") | .number" | head -1
}

# Validate milestone assignment worked
validate_milestone_assignment() {
  local issue_number="$1"
  local expected_milestone="$2"

  local actual_milestone=$(gh issue view $issue_number \
    --repo AlgenticsCorp/molecular_analysis_dashboard \
    --json milestone --jq '.milestone.title')

  if [ "$actual_milestone" = "$expected_milestone" ]; then
    echo "✅ Issue #$issue_number assigned to milestone: $expected_milestone"
  else
    echo "❌ Issue #$issue_number milestone assignment failed"
    echo "   Expected: $expected_milestone"
    echo "   Actual: $actual_milestone"
  fi
}

# List issues in a specific milestone
gh issue list \
  --repo AlgenticsCorp/molecular_analysis_dashboard \
  --milestone "Stage 0: Bootstrap API Health" \
  --json number,title,state,assignees
```

### Close/Reopen Issues
```bash
# Close issue with comment
gh issue close <ISSUE_NUMBER> \
  --repo AlgenticsCorp/molecular_analysis_dashboard \
  --comment "Completed in PR #123"

# Reopen issue
gh issue reopen <ISSUE_NUMBER> \
  --repo AlgenticsCorp/molecular_analysis_dashboard

# Close multiple issues
echo "1 2 3" | xargs -n1 gh issue close \
  --repo AlgenticsCorp/molecular_analysis_dashboard
```

### Delete Issues
```bash
# Delete issue (requires admin permissions)
gh api \
  repos/AlgenticsCorp/molecular_analysis_dashboard/issues/<ISSUE_NUMBER> \
  --method DELETE
```

## 📊 Project Management

### List Project Items
```bash
# List all items in project with details
gh project item-list 1 --owner AlgenticsCorp --limit 100 \
  --format json | jq '.items[] | {id, title, status}'

# List items by status
gh project item-list 1 --owner AlgenticsCorp --limit 100 \
  --format json | jq '.items[] | select(.status.name == "In Progress")'

# Get project field information
gh project field-list 1 --owner AlgenticsCorp
```

### Add Items to Project
```bash
# Add issue to project by URL
gh project item-add 1 --owner AlgenticsCorp --url "$ISSUE_URL"

# Add issue to project by number
ISSUE_URL="https://github.com/AlgenticsCorp/molecular_analysis_dashboard/issues/<ISSUE_NUMBER>"
gh project item-add 1 --owner AlgenticsCorp --url "$ISSUE_URL"

# Add multiple issues to project
for issue in 1 2 3; do
  ISSUE_URL="https://github.com/AlgenticsCorp/molecular_analysis_dashboard/issues/$issue"
  gh project item-add 1 --owner AlgenticsCorp --url "$ISSUE_URL"
done
```

### Update Project Item Status
```bash
# Set Status using single-select helper
gh project item-edit 1 \
  --owner AlgenticsCorp \
  --id <ITEM_ID> \
  --field "Status" \
  --single-select "In Progress"

# Available status values (adjust based on your project):
# "Backlog", "In Progress", "In Review", "Done"

# Update priority field
gh project item-edit 1 \
  --owner AlgenticsCorp \
  --id <ITEM_ID> \
  --field "Priority" \
  --single-select "High"
```

### Remove Items from Project
```bash
# Remove item from project
gh project item-delete 1 --owner AlgenticsCorp --id <ITEM_ID>

# Remove multiple items (get IDs first)
gh project item-list 1 --owner AlgenticsCorp --limit 100 \
  --format json | jq -r '.items[] | select(.title | contains("old")) | .id' | \
  xargs -I {} gh project item-delete 1 --owner AlgenticsCorp --id {}
```

## 🔧 Advanced Commands for AI Agents

### Bulk Operations
```bash
# Create multiple related issues for a milestone
MILESTONE_NUM=11
for task in "Setup Docker" "Configure Database" "Add Health Checks"; do
  gh issue create \
    --repo AlgenticsCorp/molecular_analysis_dashboard \
    --title "task: $task" \
    --body "Part of Stage 0 implementation" \
    --label "type:task" \
    --milestone "$MILESTONE_NUM"
done

# Close all issues in a milestone
gh issue list \
  --repo AlgenticsCorp/molecular_analysis_dashboard \
  --milestone "Stage 0: Bootstrap API Health" \
  --state open \
  --json number | jq -r '.[].number' | \
  xargs -I {} gh issue close {} \
    --repo AlgenticsCorp/molecular_analysis_dashboard \
    --comment "Milestone completed"
```

### Status Reporting
```bash
# Get milestone progress report
MILESTONE_NUM=11
echo "=== Milestone Progress Report ==="
gh api repos/AlgenticsCorp/molecular_analysis_dashboard/milestones/$MILESTONE_NUM | \
  jq -r '"Title: " + .title, "Open Issues: " + (.open_issues | tostring), "Closed Issues: " + (.closed_issues | tostring), "Progress: " + ((.closed_issues / (.open_issues + .closed_issues) * 100) | floor | tostring) + "%"'

# Get project status summary
echo "=== Project Status Summary ==="
gh project item-list 1 --owner AlgenticsCorp --limit 100 --format json | \
  jq -r '.items | group_by(.status.name) | .[] | "\(.[0].status.name): \(length) items"'
```

### Cleanup Operations
```bash
# Archive completed milestones (close them)
gh api repos/AlgenticsCorp/molecular_analysis_dashboard/milestones | \
  jq -r '.[] | select(.open_issues == 0 and .closed_issues > 0) | .number' | \
  xargs -I {} gh api \
    repos/AlgenticsCorp/molecular_analysis_dashboard/milestones/{} \
    --method PATCH --field state="closed"

# Remove items from project that are closed
gh project item-list 1 --owner AlgenticsCorp --limit 100 --format json | \
  jq -r '.items[] | select(.content.state == "CLOSED") | .id' | \
  xargs -I {} gh project item-delete 1 --owner AlgenticsCorp --id {}
```

## 🚨 Safety Commands

### Backup Before Bulk Operations
```bash
# Export all milestones to JSON backup
gh api repos/AlgenticsCorp/molecular_analysis_dashboard/milestones > milestones_backup.json

# Export all issues to JSON backup
gh issue list \
  --repo AlgenticsCorp/molecular_analysis_dashboard \
  --state all \
  --limit 1000 \
  --json number,title,body,state,labels,milestone > issues_backup.json

# Export project items to backup
gh project item-list 1 --owner AlgenticsCorp --limit 1000 --format json > project_backup.json
```

### Validation Commands
```bash
# Verify milestone exists before operations
if gh api repos/AlgenticsCorp/molecular_analysis_dashboard/milestones/<MILESTONE_NUMBER> &>/dev/null; then
  echo "Milestone exists"
else
  echo "Milestone not found"
fi

# Check if issue exists
if gh issue view <ISSUE_NUMBER> --repo AlgenticsCorp/molecular_analysis_dashboard &>/dev/null; then
  echo "Issue exists"
else
  echo "Issue not found"
fi
```

## 🎯 Common Workflows

### 1) Create a Story (Issue) with Milestone, Project, and Status
```bash
# Method 1: Complete workflow (RECOMMENDED for AI agents)
# Creates issue + assigns milestone + adds to project + sets status
create_issue_complete \
  "task: Implement health endpoint" \
  "Detailed implementation requirements..." \
  "Stage 0: Bootstrap API Health" \
  "Backlog"

# Method 2: Manual step-by-step process
# Step 1: Create issue and capture URL
ISSUE_URL=$(gh issue create \
  --repo AlgenticsCorp/molecular_analysis_dashboard \
  --title "<type>: <clear actionable title>" \
  --body "Goal:\n- <what>\nAcceptance:\n- <checks>\nContext:\n- See project_design/<doc>.md" \
  | grep -o 'https://github.com/[^[:space:]]*')

# Step 2: Extract issue number and assign milestone
ISSUE_NUMBER=$(echo $ISSUE_URL | grep -o '[0-9]*$')
gh issue edit $ISSUE_NUMBER \
  --repo AlgenticsCorp/molecular_analysis_dashboard \
  --milestone "Stage 0: Bootstrap API Health"

# Step 3: Add to project
gh project item-add 1 --owner AlgenticsCorp --url "$ISSUE_URL"

# Step 4: Set status to Backlog (or appropriate status)
update_issue_status $ISSUE_NUMBER "Backlog"
```

> **🚨 CRITICAL for AI Agents:** Always use Method 1 (`create_issue_complete`) to ensure milestone, project, and status are properly assigned. This prevents orphaned issues and maintains project organization.

### 2) Update the Kanban **Status** of a Project Item
```bash
# Discover fields and items (run once or when schema changes)
gh project field-list 1 --owner AlgenticsCorp
gh project item-list  1 --owner AlgenticsCorp --limit 100

# Set Status using the single-select helper (preferred when supported)
gh project item-edit 1 \
  --owner AlgenticsCorp \
  --id <ITEM_ID> \
  --field "Status" \
  --single-select "In Progress"
```

> If the helper can't find the option (custom names), fall back to GraphQL:
```bash
# Replace PROJECT_ID, ITEM_ID, FIELD_ID, OPTION_ID with real node IDs
gh api graphql -f query='
mutation UpdateStatus($project:ID!, $item:ID!, $field:ID!, $opt:String!) {
  updateProjectV2ItemFieldValue(input:{
    projectId:$project, itemId:$item, fieldId:$field,
    value:{ singleSelectOptionId:$opt }
  }) { projectV2Item { id } }
}' -F project=<PROJECT_ID> -F item=<ITEM_ID> -F field=<FIELD_ID> -F opt=<OPTION_ID>
```

### 3) Create a Branch from an Issue (professional flow)
```bash
# Link a dev branch to the issue and base it on main
gh issue develop <ISSUE_NUMBER_OR_URL> \
  --repo AlgenticsCorp/molecular_analysis_dashboard \
  --name "feat/<short-issue-slug>" \
  --base main \
  --checkout
```
> If not available in your gh version, use native git: `git switch -c feat/<slug> origin/main`

### 4) Open a PR that closes the Issue and adds it to the Project
```bash
# After commits & local tests pass, create a PR that closes the issue
gh pr create --fill \
  --repo AlgenticsCorp/molecular_analysis_dashboard \
  --title "[feat] <concise title>" \
  --body "Closes #<ISSUE_NUMBER>. Summary:\n- <what>\nTests:\n- <how verified>" \
  --add-project "AlgenticsCorp / Project 1"
```

### 5) Done Checklist (Agent must perform before asking to finish)
- Run unit/integration tests and start any relevant service; **read console output** and summarize pass/fail.
- Move the linked project item **Status → In Review** (then **Done** after merge).
- Ask approval before `git commit` / `git push` / PR create/merge.

### 🔒 Agent Guardrails (augment global rules)
- Never modify code unless the user requested a change **and** approved the plan.
- For epics: create a parent **Epic** issue, link child issues in the body, and add all to Project 1.
- When deleting/migrating items, ensure **no dependencies** are left (links/refs/parents). Propose first, then execute.
```

> _Tip:_ Use labels `type:feature|bug|task|doc` consistently.

### 2) Update the Kanban **Status** of a Project Item
```bash
# Discover fields and items (run once or when schema changes)
gh project field-list 1 --owner AlgenticsCorp
gh project item-list  1 --owner AlgenticsCorp --limit 100

# Set Status using the single-select helper (preferred when supported)
gh project item-edit 1 \
  --owner AlgenticsCorp \
  --id <ITEM_ID> \
  --field "Status" \
  --single-select "In Progress"
```

> If the helper can’t find the option (custom names), fall back to GraphQL:
```bash
# Replace PROJECT_ID, ITEM_ID, FIELD_ID, OPTION_ID with real node IDs
gh api graphql -f query='
mutation UpdateStatus($project:ID!, $item:ID!, $field:ID!, $opt:String!) {
  updateProjectV2ItemFieldValue(input:{
    projectId:$project, itemId:$item, fieldId:$field,
    value:{ singleSelectOptionId:$opt }
  }) { projectV2Item { id } }
}' -F project=<PROJECT_ID> -F item=<ITEM_ID> -F field=<FIELD_ID> -F opt=<OPTION_ID>
```
