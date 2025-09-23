# Contributing Guide

We welcome contributions to the Molecular Analysis Dashboard! This guide helps you contribute effectively while maintaining our high standards for code quality, architecture, and user experience.

## 🚀 **Quick Start for Contributors**

### **1. Fork and Setup**
```bash
# Fork the repository on GitHub, then:
git clone https://github.com/your-username/molecular_analysis_dashboard.git
cd molecular_analysis_dashboard

# Set up development environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev,docs,tools]"

# Install pre-commit hooks
pre-commit install

# Start development services
cd database && make up && make migrate && make seed
```

### **2. Create Feature Branch**
```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/issue-description
```

### **3. Make Your Changes**
Follow our [Developer Guide](developer-guide.md) for architecture patterns and coding standards.

### **4. Submit Pull Request**
See [Pull Request Process](#pull-request-process) below for detailed steps.

---

## 📋 **Development Standards**

### **Architecture Requirements**

We follow **Clean Architecture** (Ports & Adapters) strictly:

- **Domain Layer**: Pure business logic with no external dependencies
- **Use Cases**: Application orchestration depending only on domain and ports
- **Ports**: Abstract interfaces enabling dependency inversion
- **Adapters**: Framework-specific implementations of ports
- **Infrastructure**: Dependency injection and configuration
- **Presentation**: HTTP/CLI interfaces depending on use cases

**Example of proper layering**:
```python
# ✅ Correct: Use case depends on port (abstraction)
class ProcessMoleculeUseCase:
    def __init__(self, repository: MoleculeRepositoryPort):
        self._repository = repository  # Depends on abstraction

# ❌ Wrong: Use case depends on adapter (implementation)
class ProcessMoleculeUseCase:
    def __init__(self, repository: PostgreSQLMoleculeRepository):
        self._repository = repository  # Depends on implementation
```

### **Code Quality Standards**

All contributions must meet these requirements:

#### **Documentation**
- **Google-style docstrings** for all public APIs
- **Type hints** for all function parameters and returns
- **Code comments** explaining non-obvious logic (see commenting guidelines)
- **README updates** for new features affecting setup or usage

#### **Testing**
- **Unit tests** for business logic (≥80% coverage)
- **Integration tests** for database and external service interactions
- **End-to-end tests** for complete workflows
- **Test isolation** - tests must not depend on each other

#### **Code Style**
- **Black** formatting (line length: 100)
- **isort** import sorting
- **mypy** type checking in strict mode
- **flake8** linting with docstring enforcement
- **Complexity limits**: ≤10 cyclomatic complexity per function

### **Security Requirements**

- **No secrets in code** - use environment variables
- **Input validation** for all user-facing APIs
- **SQL injection prevention** - use parameterized queries
- **Proper error handling** - don't expose internal details
- **Security scanning** - bandit checks must pass

---

## 🧪 **Testing Guidelines**

### **Test Structure and Naming**

```
tests/
├── unit/                 # Fast, isolated tests
│   ├── domain/           # Pure business logic
│   ├── use_cases/        # Application services (mocked dependencies)
│   └── shared/           # Utility functions
├── integration/          # Database and service integration
│   ├── adapters/         # Repository and external service tests
│   └── infrastructure/   # Configuration and DI tests
└── e2e/                  # Complete workflow tests
    ├── api/              # HTTP API workflows
    └── cli/              # Command-line interface tests
```

### **Test Categories and Markers**

```python
import pytest

@pytest.mark.unit
def test_molecule_validation():
    """Unit test - pure domain logic, no I/O."""
    molecule = Molecule(name="aspirin", smiles="CC(=O)OC1=CC=CC=C1C(=O)O")
    assert molecule.validate_structure()

@pytest.mark.integration
@pytest.mark.asyncio
async def test_job_repository_persistence():
    """Integration test - real database interaction."""
    async with test_session() as session:
        repository = PostgreSQLJobRepository(session)
        job = create_test_job()

        saved_job = await repository.save(job)
        retrieved = await repository.get_by_id(saved_job.id)

        assert retrieved == saved_job

@pytest.mark.e2e
@pytest.mark.slow
async def test_complete_docking_workflow(api_client):
    """End-to-end test - full workflow including API calls."""
    # Upload molecule
    molecule = await api_client.upload_molecule("test_ligand.sdf")

    # Submit docking job
    job = await api_client.submit_docking_job(
        ligand=molecule.uri,
        protein="test_protein.pdb"
    )

    # Wait for completion and verify results
    result = await job.wait_for_completion(timeout=300)
    assert result.status == "COMPLETED"
    assert len(result.poses) > 0
```

### **Running Tests**

```bash
# Run all tests
pytest

# Run specific categories
pytest -m unit                     # Fast unit tests only
pytest -m integration              # Database integration tests
pytest -m "not slow"              # Skip time-consuming tests

# Run with coverage
pytest --cov=src --cov-report=html

# Run in parallel (faster)
pytest -n auto

# Run specific test
pytest tests/unit/domain/test_molecule.py::test_validation -v
```

### **Test Writing Best Practices**

**Good Test Structure (Arrange-Act-Assert)**:
```python
def test_docking_job_creation():
    """Test that docking jobs are created with proper defaults."""
    # Arrange
    molecule = create_test_molecule()
    target = create_test_target()

    # Act
    job = DockingJob.create(
        molecule=molecule,
        target=target,
        parameters=DockingParameters(exhaustiveness=8)
    )

    # Assert
    assert job.status == JobStatus.PENDING
    assert job.molecule == molecule
    assert job.target == target
    assert job.parameters.exhaustiveness == 8
    assert job.created_at is not None
```

**Mocking External Dependencies**:
```python
@pytest.mark.unit
async def test_job_use_case_with_mocked_repository():
    """Test use case logic without database dependency."""
    # Arrange
    mock_repository = Mock(spec=JobRepositoryPort)
    mock_repository.save = AsyncMock(return_value=create_test_job())

    use_case = CreateJobUseCase(mock_repository)
    command = CreateJobCommand(
        molecule_id="mol123",
        target_id="target456"
    )

    # Act
    result = await use_case.execute(command)

    # Assert
    assert result.status == JobStatus.PENDING
    mock_repository.save.assert_called_once()
```

---

## 📝 **Commit Guidelines**

### **Conventional Commits**

We follow [Conventional Commits](https://www.conventionalcommits.org/) for consistent history:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

**Types**:
- `feat`: New feature for users
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style/formatting changes
- `refactor`: Code restructuring without behavior changes
- `test`: Test additions or modifications
- `chore`: Maintenance tasks, dependency updates
- `perf`: Performance improvements
- `ci`: CI/CD configuration changes

**Examples**:
```
feat(domain): add molecular weight calculation for compounds

fix(api): handle timeout errors in docking service calls

docs: update installation guide with Docker setup steps

test(use_cases): add edge cases for job validation logic

refactor(adapters): extract common database connection logic

perf(queries): optimize job listing query with proper indexing
```

### **Commit Best Practices**

- **Atomic commits**: Each commit should represent one logical change
- **Clear messages**: Describe what and why, not how
- **Present tense**: "Add feature" not "Added feature"
- **Reference issues**: Include issue numbers when applicable
- **Sign commits**: Use GPG signing for security

```bash
# Good commit sequence
git add src/domain/entities/molecule.py
git commit -m "feat(domain): add molecular weight calculation"

git add tests/unit/domain/test_molecule.py
git commit -m "test(domain): add tests for molecular weight calculation"

git add docs/api/molecules.md
git commit -m "docs(api): document molecular weight endpoint"

# Reference issues
git commit -m "fix(auth): resolve JWT expiration handling

Fixes #123 by properly checking token expiration before API calls.
Adds retry logic for expired tokens."
```

---

## 🔄 **Pull Request Process**

### **Before Submitting PR**

1. **Ensure branch is up to date**:
   ```bash
   git checkout main
   git pull upstream main
   git checkout your-feature-branch
   git rebase main
   ```

2. **Run comprehensive checks**:
   ```bash
   # Code quality
   pre-commit run --all-files

   # All tests
   pytest

   # Type checking
   mypy src/

   # Security scan
   bandit -r src/
   ```

3. **Update documentation**:
   - Add/update docstrings for new public APIs
   - Update README if setup/usage changes
   - Add architectural decision records (ADRs) for significant changes

4. **Add changelog entry**:
   ```markdown
   # CHANGELOG.md
   ## [Unreleased]
   ### Added
   - Molecular weight calculation for uploaded compounds (#123)
   ```

### **PR Template**

Use this template for your pull request:

```markdown
## 📋 Description
Brief description of the changes and motivation.

## 🔄 Type of Change
- [ ] 🐛 Bug fix (non-breaking change that fixes an issue)
- [ ] ✨ New feature (non-breaking change that adds functionality)
- [ ] 💥 Breaking change (fix or feature that causes existing functionality to not work as expected)
- [ ] 📚 Documentation update
- [ ] 🧹 Code cleanup/refactoring
- [ ] ⚡ Performance improvement

## ✅ Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] End-to-end tests added/updated (if applicable)
- [ ] All tests pass locally
- [ ] Test coverage maintained/improved

## 📚 Documentation
- [ ] Code is self-documenting with clear naming
- [ ] Public APIs have comprehensive docstrings
- [ ] README updated (if needed)
- [ ] Architecture docs updated (if needed)
- [ ] Changelog entry added

## 🔍 Code Quality
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Complex logic is commented
- [ ] No debugging code left in
- [ ] Security considerations addressed

## 🧪 How Has This Been Tested?
Describe testing approach:
- [ ] Local development testing
- [ ] Unit test coverage: X%
- [ ] Integration test scenarios
- [ ] Manual testing steps (if applicable)

## 📸 Screenshots (if applicable)
<!-- Add screenshots for UI changes -->

## ⚡ Performance Impact
- [ ] No performance degradation
- [ ] Performance improvement (describe)
- [ ] Performance impact acceptable for feature value

## 🔗 Related Issues
Fixes #(issue number)
Related to #(issue number)

## 📝 Additional Notes
Any additional context, concerns, or discussion points.
```

### **Review Process**

1. **Automated checks must pass**:
   - All CI/CD pipeline stages
   - Code quality gates (formatting, linting, type checking)
   - Security scans
   - Test suite (unit, integration, e2e)

2. **Peer review requirements**:
   - At least **one approval** from a maintainer
   - **Two approvals** for significant architectural changes
   - **Security review** for authentication/authorization changes

3. **Review criteria**:
   - Architecture compliance (Clean Architecture principles)
   - Code quality and readability
   - Test coverage and quality
   - Documentation completeness
   - Security considerations
   - Performance impact

### **Addressing Review Feedback**

- **Respond promptly** to review comments
- **Ask questions** if feedback is unclear
- **Make requested changes** in new commits (don't force-push during review)
- **Mark conversations resolved** after addressing them
- **Update PR description** if scope changes significantly

---

## 🐛 **Bug Reports**

### **Before Reporting**

1. **Search existing issues** to avoid duplicates
2. **Try latest version** to see if bug is already fixed
3. **Check documentation** to ensure it's not expected behavior
4. **Minimal reproduction** - create the smallest possible example

### **Bug Report Template**

```markdown
## 🐛 Bug Description
Clear description of what the bug is.

## 🔄 Steps to Reproduce
1. Go to '...'
2. Click on '....'
3. Scroll down to '....'
4. See error

## ✅ Expected Behavior
What you expected to happen.

## ❌ Actual Behavior
What actually happened.

## 📱 Environment
- OS: [e.g. macOS 14.0, Ubuntu 22.04]
- Python Version: [e.g. 3.11.5]
- Package Version: [e.g. 1.2.3]
- Browser (if applicable): [e.g. Chrome 118]

## 📋 Additional Context
- Error messages/logs
- Screenshots (if applicable)
- Related configuration

## 🔧 Possible Solution
If you have suggestions for fixing the bug.
```

---

## 💡 **Feature Requests**

### **Feature Request Template**

```markdown
## 🎯 Problem Statement
What problem does this feature solve? Who benefits?

## 💡 Proposed Solution
Detailed description of your proposed feature.

## 🔄 Alternative Solutions
Other approaches you've considered.

## 📋 Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3

## 🏗️ Implementation Considerations
- Impact on existing architecture
- Performance implications
- Security considerations
- Testing requirements

## 📚 Use Cases
Specific examples of how this feature would be used.

## 🎨 Mockups/Examples
<!-- Screenshots, diagrams, or code examples -->
```

### **Feature Discussion Process**

1. **Community discussion** in GitHub Discussions
2. **Technical feasibility** assessment by maintainers
3. **Architecture review** for complex features
4. **Implementation planning** and task breakdown
5. **Assignment** to contributor (could be you!)

---

## 🤝 **Code of Conduct**

### **Our Standards**

**Positive behaviors**:
- Being respectful and inclusive
- Gracefully accepting constructive criticism
- Focusing on what's best for the community
- Helping newcomers and sharing knowledge
- Being patient with questions and mistakes

**Unacceptable behaviors**:
- Harassment, discrimination, or personal attacks
- Public or private harassment
- Publishing private information without permission
- Trolling, insulting, or derogatory comments
- Spam or off-topic content

### **Enforcement**

Violations may result in:
1. **Warning** - Private message explaining the issue
2. **Temporary ban** - Time-limited exclusion from project spaces
3. **Permanent ban** - Indefinite exclusion for severe or repeated violations

**Reporting**: Contact maintainers privately via GitHub or email.

---

## 🏆 **Recognition**

### **Contributors Are Recognized In**:

- **CONTRIBUTORS.md** - All contributors listed
- **Release notes** - Significant contributions highlighted
- **GitHub contributors graph** - Automatic contribution tracking
- **Documentation** - Author attribution for major features
- **Community showcases** - Notable contributions featured

### **Types of Contributions Valued**:

- **Code contributions** (features, fixes, optimizations)
- **Documentation improvements** (guides, examples, API docs)
- **Testing** (test cases, bug reports, QA)
- **Design** (UI/UX improvements, architectural input)
- **Community support** (helping users, answering questions)
- **Project maintenance** (issue triage, release management)

---

## 📞 **Getting Help**

### **Resources**

1. **Documentation**: Start with our [Developer Guide](developer-guide.md)
2. **GitHub Discussions**: Community Q&A and general discussions
3. **GitHub Issues**: Bug reports and feature requests
4. **Code Examples**: Check existing tests and implementation patterns

### **Communication Channels**

- **GitHub Discussions**: General questions and community interaction
- **GitHub Issues**: Specific problems and feature requests
- **Pull Request Comments**: Code-specific discussions
- **Email**: For private security issues or code of conduct violations

### **Response Times**

- **Critical bugs**: Within 24 hours
- **General issues**: Within 1 week
- **Feature requests**: Within 2 weeks (for initial feedback)
- **Pull requests**: Within 1 week (for initial review)

---

## 🎉 **Thank You!**

Your contributions make this project better for everyone. Whether you're:

- 🐛 **Reporting bugs** to help us improve quality
- 💡 **Suggesting features** to enhance functionality
- 📝 **Improving documentation** to help other users
- 🧪 **Writing tests** to increase reliability
- 💻 **Contributing code** to add new capabilities
- 🤝 **Helping others** in discussions and support

**Every contribution matters!** We appreciate your time and effort in making the Molecular Analysis Dashboard better.

---

**Ready to contribute?** Start with our [Quick Start](#quick-start-for-contributors) guide above! 🚀
