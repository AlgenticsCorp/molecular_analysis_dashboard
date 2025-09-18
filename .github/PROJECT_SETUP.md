# GitHub Projects v2 Configuration

This directory contains configuration files and documentation for setting up and managing GitHub Projects v2 for the Molecular Analysis Dashboard.

## Overview

The GitHub Project automation in this repository provides:

1. **Automatic item addition**: Issues and PRs are automatically added to the project board
2. **Status management**: Item statuses are updated based on issue/PR state changes
3. **Label automation**: Smart labeling based on content and file changes
4. **Lifecycle management**: Automated handling of stale items and status transitions

## Setup Instructions

### 1. Create a GitHub Project

1. Go to your organization or repository
2. Click on "Projects" tab
3. Click "New project"
4. Choose "Board" template
5. Name it "Molecular Analysis Dashboard"

### 2. Configure Project Fields

Create these custom fields in your project:

#### Status Field (Single Select)
- **Backlog**: New items, not yet started
- **Ready**: Ready to be worked on
- **In Progress**: Currently being worked on
- **In Review**: Under code review
- **Testing**: In QA/testing phase
- **Done**: Completed
- **Cancelled**: Work cancelled/not needed

#### Priority Field (Single Select)
- **High**: Critical items
- **Medium**: Standard priority
- **Low**: Nice to have

#### Size Field (Single Select)
- **XS**: 1-2 hours
- **Small**: Half day
- **Medium**: 1-2 days
- **Large**: 3-5 days
- **XL**: 1+ weeks

#### Area Field (Single Select)
- **Backend**: Server-side code
- **Frontend**: Client-side code
- **Infrastructure**: DevOps, CI/CD
- **Documentation**: Docs and guides
- **Testing**: Test improvements

### 3. Update Workflow Configuration

Edit the workflow files in `.github/workflows/` to match your project:

1. Update `PROJECT_URL` in the workflows to point to your project
2. Adjust field names if you used different names
3. Configure team assignments in `project-automation.yml`

### 4. Create Project Secrets (if needed)

For enhanced automation, you may want to create these repository secrets:

- `PROJECT_TOKEN`: A personal access token with project permissions
- `PROJECT_ID`: Your project's GraphQL node ID

## Workflow Files

### project-automation.yml
- Automatically adds new issues and PRs to the project
- Updates status based on item state changes
- Handles team assignments based on labels

### project-board-management.yml
- Provides manual project management operations
- Syncs missing items to the project
- Cleans up closed items
- Initializes project labels

### issue-pr-lifecycle.yml
- Auto-labels issues and PRs based on content
- Manages status transitions during review process
- Handles stale item detection

## Usage

### Automatic Operations

Once configured, the following happens automatically:

1. **New Issues**: Added to "Backlog" with auto-detected labels
2. **New PRs**: Added to "In Progress" with size and area labels
3. **PR Reviews**: Status updated based on review state
4. **Closed Items**: Moved to "Done" status
5. **Stale Items**: Marked and eventually closed

### Manual Operations

You can trigger manual operations via GitHub Actions:

1. Go to Actions → Project Board Management
2. Run workflow with desired action:
   - **sync**: Add missing items to project
   - **cleanup**: Remove closed items
   - **initialize**: Create standard labels

## Label Strategy

### Automatic Labels

The system automatically applies these labels:

#### Type Labels
- `type:bug`: Bug fixes
- `type:feature`: New features
- `type:enhancement`: Improvements

#### Area Labels
- `area:backend`: Python/FastAPI code
- `area:frontend`: React/TypeScript code
- `area:infrastructure`: Docker/CI/CD
- `area:docs`: Documentation

#### Size Labels
- `size:xs`: < 10 line changes
- `size:small`: 10-50 line changes
- `size:medium`: 50-200 line changes
- `size:large`: 200-500 line changes
- `size:xl`: 500+ line changes

#### Priority Labels
- `priority:high`: Critical/urgent
- `priority:medium`: Standard (default)
- `priority:low`: Nice to have

#### Status Labels
- `status:needs-review`: Ready for code review
- `status:approved`: Approved by reviewers
- `status:changes-requested`: Changes needed
- `status:blocked`: Waiting on external dependency
- `status:stale`: No activity for 30+ days

## Best Practices

### For Issues
1. Use descriptive titles that trigger correct auto-labeling
2. Include relevant keywords in the description
3. Reference related issues/PRs using `#123` syntax
4. Use issue templates for consistent formatting

### For Pull Requests
1. Use conventional commit style titles (`feat:`, `fix:`, `docs:`)
2. Link to issues using `fixes #123` or `closes #123`
3. Use draft PRs for work in progress
4. Request specific reviewers when ready

### For Project Management
1. Review board weekly to ensure items are in correct status
2. Use priority labels to guide work focus
3. Check for stale items regularly
4. Update estimates using size labels

## Customization

### Adding New Areas
1. Add area labels to `project-board-management.yml`
2. Update detection logic in `issue-pr-lifecycle.yml`
3. Add team assignments in `project-automation.yml`

### Modifying Status Flow
1. Update status mappings in `project-automation.yml`
2. Adjust field values to match your project setup
3. Test changes with draft PRs first

### Integration with External Tools
The project data can be accessed via GitHub's GraphQL API for integration with:
- Slack notifications
- Email reports
- External dashboards
- Time tracking tools

## Troubleshooting

### Common Issues

**Items not added to project**
- Check project URL in workflow files
- Verify GitHub token permissions
- Ensure project is public or token has access

**Status not updating**
- Verify field names match your project
- Check if custom fields exist
- Look for GraphQL API errors in workflow logs

**Labels not applied**
- Check if labels exist in repository
- Run "initialize" workflow to create standard labels
- Verify auto-detection logic matches your content

### Getting Help

1. Check workflow run logs in GitHub Actions
2. Review GitHub's Project API documentation
3. Open an issue with `area:infrastructure` label