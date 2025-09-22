## 📋 Pull Request Summary
<!-- Provide a clear, concise description of the changes -->

**Type of Change:**
- [ ] 🐛 Bug fix (non-breaking change that fixes an issue)
- [ ] ✨ New feature (non-breaking change that adds functionality)
- [ ] 💥 Breaking change (fix or feature that causes existing functionality to change)
- [ ] 📚 Documentation update
- [ ] 🏗️ Refactoring (no functional changes)
- [ ] ⚡ Performance improvement
- [ ] 🧪 Test updates
- [ ] 🔧 Infrastructure/tooling changes

## 🔗 Related Issues
<!-- Link to related issues using GitHub keywords -->
- Closes #[issue_number]
- Fixes #[issue_number]
- Resolves #[issue_number]
- Related to #[issue_number]

## 🧬 Molecular Analysis Context
<!-- Check if applicable to your changes -->
**Affected Components:**
- [ ] Docking Engine Integration (Vina/Smina/Gnina)
- [ ] Molecule Processing Pipeline
- [ ] Results Visualization (3Dmol.js)
- [ ] Multi-tenant Architecture
- [ ] Authentication/Authorization
- [ ] Job Queue/Processing
- [ ] Database Operations
- [ ] API Endpoints
- [ ] Frontend Components
- [ ] File Storage/Retrieval

**Molecular Workflows Impacted:**
- [ ] Molecule Upload/Validation
- [ ] Pipeline Configuration
- [ ] Docking Job Execution
- [ ] Results Analysis
- [ ] Organization Management
- [ ] User Authentication

## 🏗️ Architecture Changes
**Clean Architecture Layers Modified:**
- [ ] Domain (entities, business rules)
- [ ] Use Cases (application services)
- [ ] Ports (abstract interfaces)
- [ ] Adapters (implementations)
- [ ] Infrastructure (framework, external services)
- [ ] Presentation (API routes, schemas)
- [ ] Frontend (React components, pages)

**Key Files Changed:**
```
src/molecular_analysis_dashboard/
├── domain/[entity/service].py
├── use_cases/[use_case].py
├── adapters/[adapter].py
└── presentation/api/routes/[routes].py

frontend/src/
├── components/[Component].tsx
├── pages/[Page].tsx
└── services/[service].ts
```

## 🔄 Changes Made
<!-- Describe the technical changes in detail -->

### Backend Changes
```python
# Example: Key code changes or new patterns
class NewUseCase:
    async def execute(self, request: RequestModel) -> ResponseModel:
        # Implementation details
        pass
```

### Frontend Changes
```typescript
// Example: Component or service changes
const NewComponent: React.FC<Props> = ({ prop }) => {
  // Implementation details
  return <div>{prop}</div>;
};
```

### Database Changes
```sql
-- Include any schema changes
ALTER TABLE molecules ADD COLUMN new_field VARCHAR(255);
CREATE INDEX idx_molecules_new_field ON molecules(new_field);
```

### Configuration Changes
```yaml
# Include any config file changes
docking:
  new_setting: value
```

## 🧪 Testing Strategy

### Test Coverage
- [ ] **Unit Tests:** Domain logic, use cases, adapters
- [ ] **Integration Tests:** API endpoints, database operations
- [ ] **E2E Tests:** Complete user workflows
- [ ] **Performance Tests:** Load testing if applicable
- [ ] **Security Tests:** Authentication, authorization, data isolation

### Test Results
```bash
# Include test results
pytest tests/ --cov=src/molecular_analysis_dashboard --cov-report=term-missing
# Coverage: 85% (target: 80%+)

# Frontend tests
npm test -- --coverage
# Coverage: 90% (target: 80%+)
```

### Manual Testing
**Tested Scenarios:**
- [ ] Happy path: [describe main workflow]
- [ ] Error conditions: [describe error scenarios tested]
- [ ] Edge cases: [describe boundary conditions]
- [ ] Cross-browser testing (if frontend changes)
- [ ] Mobile responsiveness (if UI changes)

## ✅ Pre-Deployment Checklist

### Code Quality
- [ ] **Type Checking:** mypy passes without errors
- [ ] **Linting:** flake8, black, isort pass
- [ ] **Security:** bandit security scan passes
- [ ] **Dependencies:** No vulnerable dependencies
- [ ] **Code Review:** At least one approval from team member

### Documentation
- [ ] **Code Comments:** Complex logic documented
- [ ] **API Docs:** OpenAPI/Swagger updated
- [ ] **User Docs:** README/guides updated if needed
- [ ] **CHANGELOG:** Entry added for user-facing changes
- [ ] **Migration Guide:** Breaking changes documented

### Deployment Readiness
- [ ] **Database Migrations:** Tested and backwards compatible
- [ ] **Environment Variables:** New configs documented
- [ ] **Docker:** Containers build successfully
- [ ] **CI/CD:** All GitHub Actions pass
- [ ] **Rollback Plan:** Revert strategy identified

## 🚨 Risk Assessment

### Deployment Risk
- [ ] **Low Risk:** Minor changes, well-tested
- [ ] **Medium Risk:** Some complexity, good test coverage
- [ ] **High Risk:** Major changes, requires careful monitoring

### Potential Impact
**Positive Impact:**
- [Describe benefits and improvements]

**Potential Issues:**
- [Describe any risks or concerns]
- [Mitigation strategies]

### Monitoring Plan
- [ ] **Metrics to Watch:** [specific metrics post-deployment]
- [ ] **Alerts Configured:** [any new alerts needed]
- [ ] **Rollback Triggers:** [conditions that would trigger rollback]

## 🎯 Implementation Stage
**Related Milestone:** [Stage 0-9 from implementation plan]
**Priority:** [P0/P1/P2/P3]

## 📸 Screenshots/Demo
<!-- Include screenshots for UI changes or demo videos for complex features -->

### Before
[Screenshots or description of current state]

### After
[Screenshots or description of new state]

## 🔍 Reviewer Focus Areas
<!-- Help reviewers know what to focus on -->

**Please Pay Special Attention To:**
- [ ] Security implications of changes
- [ ] Performance impact
- [ ] Error handling and edge cases
- [ ] Clean Architecture principles adherence
- [ ] Multi-tenant data isolation
- [ ] API contract compatibility
- [ ] Database migration safety

**Specific Questions for Reviewers:**
1. [Specific question about implementation choice]
2. [Question about performance implications]
3. [Question about architecture decisions]

## 📚 Additional Context
<!-- Any other context that would be helpful for reviewers -->

**Design Decisions:**
- [Explain any non-obvious design choices]
- [Link to relevant design documents]

**Alternative Approaches Considered:**
- [Describe other approaches considered and why this was chosen]

**Future Work:**
- [Any follow-up work planned]
- [Technical debt that could be addressed later]

**References:**
- Design docs: `project_design/[relevant].md`
- External resources: [links]
- Related PRs: [links to related work]
