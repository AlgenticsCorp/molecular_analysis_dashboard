# LLM Agent Development Guide

This file provides step-by-step instructions specifically for AI/LLM agents working with this codebase. Follow this workflow for all development tasks.

## 🚀 Prerequisites & Setup

### **Step 1: Determine Project State**
```bash
# Check if this is a fresh template or existing project
ls -la src/
```

**If you see `src/yourpkg/`**: This is a fresh template - proceed to Step 2
**If you see `src/some_other_name/`**: This is an existing project - skip to Step 3

### **Step 2: Bootstrap New Project (Template Users Only)**
```bash
# Replace 'actual_package_name' with the real package name
# Must be lowercase with underscores (snake_case)
./bootstrap.sh actual_package_name

# Examples:
# ./bootstrap.sh order_service
# ./bootstrap.sh data_processor
# ./bootstrap.sh web_api
```

⚠️ **Critical Package Naming Rules:**
- ✅ Use lowercase letters, numbers, underscores only
- ✅ Examples: `user_service`, `data_api`, `ml_pipeline`
- ❌ Avoid: hyphens, dots, CamelCase, starting with numbers

### **Step 3: Environment Setup**
```bash
# Activate virtual environment (created by bootstrap or existing)
source .venv/bin/activate

# Install all dependencies (if not already done)
pip install -e ".[dev,docs,tools]"

# Install pre-commit hooks
pre-commit install
```

**THEN**: Ensure complete setup by reviewing **[SETUP.md](SETUP.md)** - the single source of truth for installation instructions.

## 🤖 Quick Start for LLM Agents

### Phase 1: Repository Analysis (ALWAYS START HERE)

```bash
# 1. Read the architecture guide
cat DEVELOPER_GUIDE.md

# 2. Analyze current codebase structure
python tools/extract_schema.py
cat docs/schema.json | jq '.modules[] | {module: .module, functions: .functions[].name, classes: .classes[].name}'

# 3. Review dependency relationships
python tools/render_graphs.py
# Generated: docs/atlas/calls.svg and docs/atlas/imports.svg

# 4. Check for existing patterns
find src/ -name "*.py" -exec head -20 {} \; | grep -E "(class|def|import)"
```

### Phase 2: Pre-Development Checklist

Before making ANY changes:

- [ ] **Read docstrings** of related components
- [ ] **Check dependency graphs** for impact analysis
- [ ] **Review test coverage** in relevant areas
- [ ] **Identify similar patterns** in the existing codebase
- [ ] **Validate architecture compliance** with layer rules

### Phase 3: Development Workflow

```bash
# 1. Create feature branch
git checkout -b feature/your-feature-name

# 2. Make changes following patterns (see sections below)

# 3. Validate changes
pre-commit run --all-files
pytest

# 4. Update documentation artifacts
python tools/extract_schema.py
python tools/render_graphs.py

# 5. Commit with descriptive message
git add .
git commit -m "feat(domain): add order validation logic"
```

## 🏗️ **Clean Architecture Layer Rules**

**Critical**: Always follow dependency directions:

### File Placement Rules

**When adding new code, place files according to:**

- **Domain Logic** → `src/your_package_name/domain/`
  - Entities (business objects)
  - Domain services (business rules)
  - Value objects
  - Domain events

- **Application Logic** → `src/your_package_name/use_cases/`
  - Application services
  - Command/query handlers
  - Workflow orchestration

- **Interfaces** → `src/your_package_name/ports/`
  - Repository interfaces
  - Service interfaces
  - Event publisher interfaces

- **External Integrations** → `src/your_package_name/adapters/`
  - Database implementations
  - HTTP clients
  - File system adapters
  - Message queue adapters

- **Configuration** → `src/your_package_name/infrastructure/`
  - Dependency injection
  - Configuration loading
  - Logging setup

- **Controllers** → `src/your_package_name/presentation/`
  - HTTP controllers
  - CLI commands
  - Event handlers

## 📝 **Code Patterns & Examples**

⚠️ **Note**: In all code examples below, replace `yourpkg` with your actual package name (e.g., `order_service`, `data_api`, etc.).

### 1. Adding New Domain Entity

```python
# File: src/yourpkg/domain/entities/order.py
"""
Order entity representing a customer purchase.

Details:
- Core business entity
- Contains business rules and validations
- No external dependencies
"""
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from yourpkg.domain.value_objects import OrderStatus, OrderItem


@dataclass
class Order:
    """
    Customer order entity.

    Attributes:
        id: Unique order identifier.
        customer_id: Customer who placed the order.
        items: List of items in the order.
        status: Current order status.
        created_at: Order creation timestamp.
        total_amount: Total order value.
    """
    id: UUID
    customer_id: UUID
    items: List[OrderItem]
    status: OrderStatus
    created_at: datetime
    total_amount: Optional[float] = None

    def calculate_total(self) -> float:
        """Calculate total order amount from items."""
        return sum(item.price * item.quantity for item in self.items)

    def can_be_cancelled(self) -> bool:
        """Check if order can be cancelled based on status."""
        return self.status in [OrderStatus.PENDING, OrderStatus.CONFIRMED]
```

### 2. Adding New Use Case

```python
# File: src/yourpkg/use_cases/process_order.py
"""Order processing use case."""
from uuid import UUID
from yourpkg.domain.entities import Order
from yourpkg.domain.exceptions import OrderNotFoundError
from yourpkg.ports.repository import OrderRepositoryPort
from yourpkg.ports.notification import NotificationPort


class ProcessOrderUseCase:
    """
    Use case for processing customer orders.

    Attributes:
        order_repo: Repository for order persistence.
        notifier: Service for sending notifications.
    """

    def __init__(
        self,
        order_repo: OrderRepositoryPort,
        notifier: NotificationPort,
    ) -> None:
        self._order_repo = order_repo
        self._notifier = notifier

    async def execute(self, order_id: UUID) -> Order:
        """
        Process an order through the fulfillment pipeline.

        Args:
            order_id: Unique identifier for the order to process.

        Returns:
            Processed order with updated status.

        Raises:
            OrderNotFoundError: If order doesn't exist.
        """
        # 1. Retrieve order
        order = await self._order_repo.get_by_id(order_id)
        if not order:
            raise OrderNotFoundError(f"Order {order_id} not found")

        # 2. Business logic
        order.calculate_total()

        # 3. Update status
        order.status = OrderStatus.PROCESSING

        # 4. Persist changes
        await self._order_repo.save(order)

        # 5. Send notification
        await self._notifier.send_order_update(order)

        return order
```

### 3. Adding New Port (Interface)

```python
# File: src/yourpkg/ports/repository/order_repository.py
"""Order repository interface."""
from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from yourpkg.domain.entities import Order


class OrderRepositoryPort(ABC):
    """Abstract interface for order persistence."""

    @abstractmethod
    async def get_by_id(self, order_id: UUID) -> Optional[Order]:
        """Retrieve order by ID."""
        ...

    @abstractmethod
    async def save(self, order: Order) -> Order:
        """Save order to persistence."""
        ...

    @abstractmethod
    async def find_by_customer(self, customer_id: UUID) -> List[Order]:
        """Find all orders for a customer."""
        ...

    @abstractmethod
    async def delete(self, order_id: UUID) -> bool:
        """Delete order by ID."""
        ...
```

### 4. Adding New Adapter (Implementation)

```python
# File: src/yourpkg/adapters/database/postgres_order_repository.py
"""PostgreSQL implementation of order repository."""
from typing import List, Optional
from uuid import UUID

from yourpkg.domain.entities import Order
from yourpkg.domain.exceptions import OrderNotFoundError
from yourpkg.use_cases import ProcessOrderUseCase


class PostgreSQLOrderRepository(OrderRepositoryPort):
    """PostgreSQL implementation of order repository."""

    def __init__(self, connection_pool: Any) -> None:
        self._pool = connection_pool

    async def get_by_id(self, order_id: UUID) -> Optional[Order]:
        """Retrieve order by ID from PostgreSQL."""
        # Implementation details...
        pass

    async def save(self, order: Order) -> Order:
        """Save order to PostgreSQL."""
        # Implementation details...
        pass
```

## ✅ **Validation & Testing Workflow**

### 1. Code Quality Validation

```bash
# Run all quality checks
pre-commit run --all-files

# Individual checks
black --check src/
isort --check-only src/
flake8 src/
mypy src/
pylint src/
bandit -r src/
```

### 2. Testing Strategy

```bash
# Run all tests with coverage
pytest --cov=src/your_package_name --cov-fail-under=80

# Run specific test types
pytest -m unit          # Fast unit tests
pytest -m integration   # Integration tests
pytest -m e2e           # End-to-end tests
```

### 3. Documentation Updates

```bash
# Generate API schema
python tools/extract_schema.py

# Generate dependency graphs
python tools/render_graphs.py

# Build documentation site
mkdocs serve
```

## 🚨 **Architecture Compliance Rules**

### Dependency Direction Rules

**✅ ALLOWED dependencies:**
```python
from yourpkg.domain.value_objects import OrderStatus  # ✅
from yourpkg.ports.repository import OrderRepositoryPort  # ✅
```

**❌ FORBIDDEN dependencies:**
```python
from yourpkg.adapters.database import PostgreSQLConnection  # ❌
from yourpkg.adapters.email import SMTPEmailSender  # ❌
```

**Rule**: Inner layers (domain, use_cases) should NOT depend on outer layers (adapters, infrastructure).

### Validation Checklist

Before committing code:

1. **Architecture compliance**: Check dependency directions
2. **Type safety**: `mypy src/your_package_name/`
3. **Test coverage**: Ensure ≥80% coverage
4. **Documentation**: All public APIs have docstrings
5. **Verify types**: `mypy src/your_package_name/specific_module.py`

## 🛠️ **Debugging & Troubleshooting**

### Common Issues

1. **Import errors**: Check that you've replaced `yourpkg` with actual package name
2. **Test failures**: Run `pytest -v` for detailed output
3. **Type errors**: Run `mypy --show-error-codes src/`
4. **Architecture violations**: Review dependency graphs

### Debug Commands

```bash
# Check current package structure
find src/ -name "*.py" | head -10

# Verify imports work
python -c "import sys; sys.path.insert(0, 'src'); import your_package_name"

# Check test discovery
pytest --collect-only

# Analyze complexity
radon cc src/ -a
```

## 📋 **Agent Development Checklist**

For every change:

- [ ] **Understand context**: Read related code and documentation
- [ ] **Follow patterns**: Use existing code patterns and styles
- [ ] **Maintain architecture**: Respect layer boundaries
- [ ] **Add tests**: Write unit tests for new functionality
- [ ] **Update docs**: Add/update docstrings and comments
- [ ] **Validate quality**: Run pre-commit checks
- [ ] **Update artifacts**: Regenerate schema and graphs
- [ ] **Test integration**: Ensure changes don't break existing functionality

---

**💡 Pro Tip**: Always start with `python tools/extract_schema.py` to understand the current codebase before making changes!
