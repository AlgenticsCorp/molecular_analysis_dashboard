"""Test project automation workflow configurations."""

import pathlib
import yaml
import pytest


def test_workflow_files_are_valid_yaml():
    """Test that all workflow files contain valid YAML."""
    workflow_dir = pathlib.Path(__file__).parent.parent.parent / ".github" / "workflows"
    workflow_files = list(workflow_dir.glob("*.yml"))
    
    # Ensure we have workflow files to test
    assert len(workflow_files) >= 3, "Expected at least 3 workflow files"
    
    for workflow_file in workflow_files:
        with open(workflow_file) as f:
            try:
                yaml.safe_load(f)
            except yaml.YAMLError as e:
                pytest.fail(f"Invalid YAML in {workflow_file.name}: {e}")


def test_project_automation_workflow_structure():
    """Test that project automation workflow has required structure."""
    workflow_file = pathlib.Path(__file__).parent.parent.parent / ".github" / "workflows" / "project-automation.yml"
    
    with open(workflow_file) as f:
        workflow = yaml.safe_load(f)
    
    # Check basic structure
    assert "name" in workflow
    assert True in workflow or "on" in workflow  # YAML parses 'on' as boolean True
    assert "jobs" in workflow
    
    # Get the events section (could be under True or "on")
    events = workflow.get(True) or workflow.get("on")
    assert events is not None
    
    # Check event triggers
    expected_events = ["issues", "pull_request"]
    for event in expected_events:
        assert event in events
    
    # Check job names
    expected_jobs = ["add-to-project", "update-project-status", "assign-based-on-labels"]
    for job in expected_jobs:
        assert job in workflow["jobs"]


def test_issue_templates_exist():
    """Test that issue templates are present."""
    template_dir = pathlib.Path(__file__).parent.parent.parent / ".github" / "ISSUE_TEMPLATE"
    
    expected_templates = ["bug_report.md", "feature_request.md", "epic.md", "user_story.md", "task.md"]
    
    for template in expected_templates:
        template_file = template_dir / template
        assert template_file.exists(), f"Missing issue template: {template}"
        
        # Verify template has frontmatter
        with open(template_file) as f:
            content = f.read()
            assert content.startswith("---"), f"Template {template} missing frontmatter"


def test_pull_request_template_exists():
    """Test that pull request template exists and has required sections."""
    template_file = pathlib.Path(__file__).parent.parent.parent / ".github" / "PULL_REQUEST_TEMPLATE.md"
    
    assert template_file.exists(), "Missing pull request template"
    
    with open(template_file) as f:
        content = f.read()
    
    # Check for required sections
    required_sections = [
        "## Description",
        "## Related Issues", 
        "## Type of Change",
        "## Area of Change",
        "## Testing",
        "## Checklist"
    ]
    
    for section in required_sections:
        assert section in content, f"Missing section in PR template: {section}"


def test_project_setup_documentation_exists():
    """Test that project setup documentation is present."""
    doc_file = pathlib.Path(__file__).parent.parent.parent / ".github" / "PROJECT_SETUP.md"
    
    assert doc_file.exists(), "Missing project setup documentation"
    
    with open(doc_file) as f:
        content = f.read()
    
    # Check for key sections
    required_sections = [
        "## Overview",
        "## Setup Instructions", 
        "## Workflow Files",
        "## Usage",
        "## Troubleshooting"
    ]
    
    for section in required_sections:
        assert section in content, f"Missing section in project setup docs: {section}"