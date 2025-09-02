# Welcome to Your Professional Python Project

This project template implements **Clean Architecture** principles with comprehensive tooling for AI agent-assisted development.

## 🚀 Quick Navigation

- **[Getting Started](getting-started/quick-start.md)** - Set up your development environment
- **[Architecture Guide](getting-started/architecture.md)** - Understand the project structure
- **[Developer Guide](DEVELOPER_GUIDE.md)** - Development workflow and standards
- **[LLM Agent Guide](LLM_AGENT_GUIDE.md)** - AI agent development instructions
- **[API Reference](api.md)** - Generated API documentation
- **[Contributing](CONTRIBUTING.md)** - How to contribute to this project

## 🏗️ Architecture Overview

This template enforces **SOLID principles** and **Clean Architecture** patterns:

```
src/your_package_name/
├── domain/          # Business entities and domain services
├── use_cases/       # Application services (business logic)
├── ports/           # Abstract interfaces (dependency inversion)
├── adapters/        # Concrete implementations (DB, HTTP, CLI)
├── infrastructure/  # DI containers, configuration, logging
├── presentation/    # Controllers, CLI, API endpoints
└── shared/          # Cross-cutting utilities
```

## 🤖 For AI Agents

This project is optimized for AI-assisted development:

1. **Read** the [LLM Agent Guide](LLM_AGENT_GUIDE.md) for step-by-step instructions
2. **Analyze** the [API Schema](schema.md) for current codebase structure
3. **Review** [Dependency Graphs](graphs.md) before making changes
4. **Follow** established patterns and quality gates

## 📊 Quality Metrics

- **Test Coverage**: ≥80% required
- **Type Coverage**: 100% (mypy strict mode)
- **Docstring Coverage**: 100% (Google style)
- **Complexity**: ≤10 per function (radon)
- **Security**: Bandit scanning enabled

## 🛠️ Development Tools

- **Code Atlas**: Automated dependency visualization
- **Schema Extraction**: Machine-readable API documentation
- **Quality Gates**: Pre-commit hooks with multiple linters
- **CI/CD**: GitHub Actions with comprehensive testing
- **Documentation**: Auto-generated from docstrings

---

Ready to start? Head to the **[Quick Start Guide](getting-started/quick-start.md)**!
