# GitHub Workflow Guide

This guide provides step-by-step instructions for pushing code to GitHub and handling CI/CD pipeline requirements.

## 🚀 **Standard GitHub Push Workflow**

### 1. **Before You Start**
```bash
# Ensure you're on the latest main branch
git checkout main
git pull origin main

# Create a feature branch
git checkout -b feature/your-feature-name
# or
git checkout -b fix/bug-description
```

### 2. **Make Your Changes**
Follow the development guidelines in `DEVELOPER_GUIDE.md` and `LLM_AGENT_GUIDE.md`.

### 3. **Pre-Push Validation (CRITICAL)**
```bash
# Run all quality checks locally BEFORE pushing
pre-commit run --all-files

# Run tests to ensure nothing breaks
pytest

# Optional: Generate dependency graphs (done automatically in CI)
python tools/render_graphs.py

# If everything passes, you're ready to push
```

### 4. **Commit and Push**
```bash
# Stage your changes
git add .

# Commit with conventional commit format
git commit -m "feat(domain): add order validation logic"

# Push to GitHub
git push origin feature/your-feature-name
```

### 5. **Create Pull Request**
1. Go to GitHub repository
2. Click "Compare & pull request"
3. Fill out the PR template
4. Wait for CI checks to pass
5. Request review from maintainers

## 🔍 **GitHub Actions CI Pipeline**

When you push, the following checks run automatically:

### **Quality Gates (Must Pass)**
- ✅ **Code Formatting**: Black, isort
- ✅ **Type Checking**: MyPy with strict settings
- ✅ **Linting**: Flake8, Pylint, Bandit
- ✅ **Security**: Bandit security scanning
- ✅ **Documentation**: Docstring compliance
- ✅ **Testing**: All tests must pass
- ✅ **Coverage**: ≥80% test coverage required

### **Generated Artifacts**
- 📊 Code complexity reports
- 📈 Test coverage reports
- 🗺️ Dependency graphs
- 📚 API documentation

## 🚨 **Handling CI Failures**

### **If Pre-commit Checks Fail**
```bash
# See what failed
pre-commit run --all-files

# Fix formatting issues automatically
black src/ tests/
isort src/ tests/

# Fix other issues manually, then retry
pre-commit run --all-files
```

### **If Tests Fail**
```bash
# Run tests locally to debug
pytest -v

# Run specific failing test
pytest tests/path/to/failing_test.py::test_function -v

# Fix the issue, then verify
pytest
```

### **If MyPy Type Checking Fails**
```bash
# Run mypy locally to see errors
mypy src/

# Common fixes:
# 1. Add missing type hints
# 2. Import proper types
# 3. Add # type: ignore for unavoidable issues
```

### **If Coverage Is Too Low**
```bash
# Check coverage report
pytest --cov=src/ --cov-report=html

# View detailed report
open htmlcov/index.html

# Add tests for uncovered code
```

## 📝 **Commit Message Standards**

Use [Conventional Commits](https://www.conventionalcommits.org/) format:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### **Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Test additions/changes
- `chore`: Maintenance tasks

### **Examples:**
```bash
git commit -m "feat(auth): add JWT token validation"
git commit -m "fix(database): handle connection timeout errors"
git commit -m "docs: update API documentation for new endpoints"
git commit -m "test(orders): add edge cases for payment processing"
```

## 🔄 **Emergency Procedures**

### **If You Need to Push Despite Failing Checks**
```bash
# Only for genuine emergencies - use sparingly!
git commit -m "fix: critical security patch" --no-verify
git push origin main
```

### **If CI is Broken Due to External Issues**
1. Check GitHub Status page
2. Contact maintainers
3. Consider temporary workarounds
4. Document the issue

## 🛡️ **Branch Protection Rules**

This repository enforces:

- ✅ **Required status checks**: All CI checks must pass
- ✅ **Required reviews**: At least 1 maintainer approval
- ✅ **Up-to-date branches**: Must be current with main
- ✅ **No force push**: Protects main branch history
- ✅ **Admin enforcement**: Even admins follow the rules

## 🤖 **For LLM Agents: Automated Workflow**

### **Quick Validation Script**
```bash
#!/bin/bash
# validate_before_push.sh

echo "🔍 Running pre-push validation..."

# 1. Format code
echo "📝 Formatting code..."
black src/ tests/
isort src/ tests/

# 2. Run quality checks
echo "🧹 Running quality checks..."
pre-commit run --all-files || exit 1

# 3. Run tests
echo "🧪 Running tests..."
pytest || exit 1

# 4. Check coverage
echo "📊 Checking coverage..."
pytest --cov=src/ --cov-fail-under=80 || exit 1

echo "✅ All checks passed! Ready to push."
```

### **Usage:**
```bash
chmod +x validate_before_push.sh
./validate_before_push.sh && git push origin feature-branch
```

## 📞 **Getting Help**

### **If You're Stuck:**
1. **Check documentation**: Start with `DEVELOPER_GUIDE.md`
2. **Search issues**: Look for similar problems
3. **Ask maintainers**: Create an issue or discussion
4. **Debug locally**: Run the same checks CI runs

### **Useful Debug Commands:**
```bash
# Check current branch and status
git status
git branch -v

# See what CI will run
pre-commit run --all-files --verbose

# Test specific hooks
pre-commit run black --all-files
pre-commit run mypy --all-files

# Check test status
pytest --tb=short
```

---

**💡 Remember**: The goal of these checks is to maintain code quality and prevent bugs. If something seems overly strict, discuss it with the team rather than bypassing it!
