# GitHub Projects & Issues — Project Management Guide

> **Scope:** Org Project (v2) **AlgenticsCorp / Project 1** and repo **AlgenticsCorp/molecular_analysis_dashboard**

## 🎯 Quick Reference

### Essential Commands for AI Agents
```bash
# Create issue with full project integration (RECOMMENDED)
create_issue_complete "task: Title" "Description" "Milestone" "Status"

# Update issue status in project
update_issue_status <ISSUE_NUMBER> "Status"

# Check milestone exists
milestone_exists "Milestone Name"
```

### Status Values
- **Backlog** - Default for new tasks
- **Ready** - Ready to start
- **In Progress** - Currently being worked on
- **In Review** - In code review
- **Done** - Completed

---

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

---

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
```

---

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

# Available status values:
# "Backlog", "Ready", "In Progress", "In Review", "Done"

# Update priority field
gh project item-edit 1 \
  --owner AlgenticsCorp \
  --id <ITEM_ID> \
  --field "Priority" \
  --single-select "High"
```

---

## 🔧 Helper Functions for AI Agents

### Complete Issue Creation (RECOMMENDED)
```bash
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
```

### Update Issue Status
```bash
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
```

### Milestone Validation
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
```

---

## 🎯 Common Workflows

### 1) Create Issue with Full Integration (RECOMMENDED)
```bash
# Complete workflow - creates issue + assigns milestone + adds to project + sets status
create_issue_complete \
  "task: Implement health endpoint" \
  "Detailed implementation requirements..." \
  "Stage 0: Bootstrap API Health" \
  "Backlog"
```

### 2) Update Issue Status in Kanban
```bash
# Update status using helper function
update_issue_status 20 "In Progress"
update_issue_status 16 "Done"
```

### 3) Create PR Linked to Issue
```bash
# After commits & local tests pass, create a PR that closes the issue
gh pr create --fill \
  --repo AlgenticsCorp/molecular_analysis_dashboard \
  --title "[feat] <concise title>" \
  --body "Closes #<ISSUE_NUMBER>. Summary:\n- <what>\nTests:\n- <how verified>" \
  --add-project "AlgenticsCorp / Project 1"
```

---

## 🚨 Safety & Validation

### Pre-flight Check
```bash
# Ensure token has the 'project' scope and you can see Org Project 1
gh project view 1 --owner AlgenticsCorp
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

---

## 📊 Reporting

### Milestone Progress Report
```bash
MILESTONE_NUM=11
echo "=== Milestone Progress Report ==="
gh api repos/AlgenticsCorp/molecular_analysis_dashboard/milestones/$MILESTONE_NUM | \
  jq -r '"Title: " + .title, "Open Issues: " + (.open_issues | tostring), "Closed Issues: " + (.closed_issues | tostring), "Progress: " + ((.closed_issues / (.open_issues + .closed_issues) * 100) | floor | tostring) + "%"'
```

### Project Status Summary
```bash
echo "=== Project Status Summary ==="
gh project item-list 1 --owner AlgenticsCorp --limit 100 --format json | \
  jq -r '.items | group_by(.status.name) | .[] | "\(.[0].status.name): \(length) items"'
```

---

## 🏷️ Label Conventions

Use consistent labels across issues:
- **Type:** `type:feature`, `type:bug`, `type:task`, `type:documentation`, `type:performance`
- **Priority:** `priority:critical`, `priority:high`, `priority:medium`, `priority:low`
- **Status:** `status:triage`, `status:blocked`, `status:needs-review`, `status:ready`
- **Stage:** `stage:0`, `stage:1`, etc. (corresponding to implementation milestones)
