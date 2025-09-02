# Contributing to this Project

We welcome contributions to this professional Python template! This guide will help you get started with contributing effectively.

## 🚀 Quick Start for Contributors

### 1. Fork and Clone

```bash
git clone https://github.com/your-username/code_template.git
cd code_template
```

### 2. Set Up Development Environment

```bash
# Bootstrap the project with a package name (creates venv, installs deps, configures hooks)
chmod +x bootstrap.sh
./bootstrap.sh contributing_test_package
```

### 3. Create Feature Branch

```bash
git checkout -b feature/your-feature-name
```

## 📋 Development Guidelines

### Code Standards

This project enforces strict quality standards:

- **Architecture**: Follow Clean Architecture/Hexagonal patterns
- **Documentation**: All public APIs must have Google-style docstrings
- **Type Hints**: All functions must be fully type-annotated
- **Testing**: Maintain ≥80% test coverage
- **Complexity**: Keep cyclomatic complexity ≤10 per function

### Before Making Changes

1. **Read the docs**: Review `DEVELOPER_GUIDE.md`
2. **Understand dependencies**: Check `docs/atlas/*.svg` graphs
3. **Review existing code**: Look at similar implementations
4. **Plan your changes**: Consider impact on architecture

### Making Changes

1. **Write tests first** (TDD approach recommended)
2. **Implement feature** following existing patterns
3. **Add comprehensive docstrings**
4. **Update documentation** if needed
5. **Run quality checks**:
   ```bash
   pre-commit run --all-files
   pytest
   ```

### Commit Guidelines

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Test additions or changes
- `chore`: Maintenance tasks

**Examples:**
```
feat(domain): add order validation logic
fix(adapters): handle database connection timeout
docs: update API documentation for new endpoints
test(use_cases): add edge cases for payment processing
```

## 🧪 Testing Guidelines

### Test Structure

Mirror the `src/` structure in `tests/`:

```
tests/
├── unit/           # Fast, isolated tests
│   ├── domain/
│   ├── use_cases/
│   └── ...
├── integration/    # Service integration tests
└── e2e/           # End-to-end tests
```

### Test Categories

Mark tests appropriately:

```python
import pytest

@pytest.mark.unit
def test_order_validation():
    """Unit test for order validation logic."""
    pass

@pytest.mark.integration
def test_database_integration():
    """Integration test with database."""
    pass

@pytest.mark.e2e
def test_complete_workflow():
    """End-to-end test of entire workflow."""
    pass
```

### Running Tests

```bash
# All tests
pytest

# Specific categories
pytest -m unit
pytest -m integration
pytest -m e2e

# With coverage
pytest --cov=src/your_package_name --cov-report=html
```

## 📚 Documentation Standards

### Docstring Requirements

All public APIs must have comprehensive docstrings:

```python
def process_payment(
    amount: Decimal,
    payment_method: PaymentMethod,
    customer_id: str
) -> PaymentResult:
    """
    Process a customer payment using the specified method.

    This function handles payment processing through various payment
    gateways while ensuring PCI compliance and proper error handling.

    Args:
        amount: Payment amount in the system currency.
        payment_method: Method to use for payment (card, bank, etc.).
        customer_id: Unique identifier for the customer.

    Returns:
        PaymentResult containing transaction ID, status, and metadata.

    Raises:
        InvalidAmountError: If amount is negative or zero.
        PaymentMethodError: If payment method is not supported.
        CustomerNotFoundError: If customer_id doesn't exist.

    Example:
        >>> result = process_payment(
        ...     Decimal("99.99"),
        ...     PaymentMethod.CREDIT_CARD,
        ...     "CUST-123"
        ... )
        >>> result.status
        PaymentStatus.COMPLETED
    """
```

### Documentation Updates

When adding features:

1. Update relevant docstrings
2. Add examples to README if needed
3. Update architecture diagrams if structure changes
4. Add to CHANGELOG.md

## 🔧 Architecture Guidelines

### Layer Responsibilities

- **Domain**: Pure business logic, no external dependencies
- **Use Cases**: Application services orchestrating domain objects
- **Ports**: Abstract interfaces for external dependencies
- **Adapters**: Concrete implementations of ports
- **Infrastructure**: DI containers, configuration, logging
- **Presentation**: Controllers, CLI commands, API endpoints

### Dependency Rules

- **Domain** depends on nothing
- **Use Cases** depend only on Domain and Ports
- **Adapters** implement Ports and may depend on external libraries
- **Infrastructure** wires everything together
- **Presentation** depends on Use Cases through dependency injection

### Adding New Features

1. **Start with domain**: Define entities and business rules
2. **Create use cases**: Implement application logic
3. **Define ports**: Abstract external dependencies
4. **Implement adapters**: Create concrete implementations
5. **Wire in infrastructure**: Configure dependency injection
6. **Add presentation layer**: Create controllers or CLI commands

## 🚦 Quality Gates

All pull requests must pass:

### Automated Checks

- ✅ Code formatting (black, isort)
- ✅ Type checking (mypy)
- ✅ Linting (flake8, pylint)
- ✅ Security scanning (bandit)
- ✅ Docstring compliance (pydocstyle)
- ✅ Complexity analysis (radon)
- ✅ Test coverage ≥80%
- ✅ All tests passing

### Manual Review

- ✅ Architecture compliance
- ✅ Code clarity and maintainability
- ✅ Comprehensive tests
- ✅ Documentation completeness
- ✅ Backwards compatibility

## 📝 Pull Request Process

### Before Submitting

1. **Rebase on main**: Ensure your branch is up to date
2. **Run full test suite**: `pytest`
3. **Run quality checks**: `pre-commit run --all-files`
4. **Update documentation**: If needed
5. **Add changelog entry**: In `CHANGELOG.md`

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] All tests pass locally

## Documentation
- [ ] Docstrings added/updated
- [ ] README updated (if needed)
- [ ] Architecture docs updated (if needed)

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Code is commented where needed
- [ ] Changes generate no new warnings
```

### Review Process

1. **Automated checks** must pass
2. **At least one maintainer** must approve
3. **Address feedback** promptly and professionally
4. **Squash commits** before merging (if requested)

## 🐛 Bug Reports

Use the issue template with:

- **Environment details** (OS, Python version, etc.)
- **Steps to reproduce**
- **Expected vs actual behavior**
- **Relevant logs or error messages**
- **Minimal reproduction case**

## 💡 Feature Requests

For new features:

- **Describe the problem** you're trying to solve
- **Explain your proposed solution**
- **Consider alternative approaches**
- **Discuss impact** on existing architecture
- **Provide use cases** and examples

## 🤝 Code of Conduct

We are committed to providing a welcoming and inclusive environment:

- **Be respectful** and professional
- **Be constructive** in feedback
- **Be patient** with newcomers
- **Be collaborative** and helpful
- **Focus on the code**, not the person

## 🏆 Recognition

Contributors are recognized in:

- **CONTRIBUTORS.md** file
- **Release notes** for significant contributions
- **GitHub contributors** graph

## 📞 Getting Help

- **Documentation**: Start with `DEVELOPER_GUIDE.md`
- **Discussions**: Use GitHub Discussions for questions
- **Issues**: For bugs and feature requests
- **Direct contact**: Maintainer contact information in README

Thank you for contributing to this project! 🎉
