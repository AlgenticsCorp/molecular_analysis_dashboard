# Implementation Guide Template

**Phase**: [Phase Name and Number]
**Status**: [In Progress | Testing | Complete]
**Last Updated**: [YYYY-MM-DD]
**Owner**: [Primary developer/team]

## 🎯 Implementation Overview

### **Phase Objectives Recap**
- [Brief summary of main objectives from planning document]
- [Success criteria overview]

### **Implementation Approach**
[High-level description of how this phase will be implemented, key strategies]

---

## 🛠️ Development Environment Setup

### **Prerequisites**
- [ ] [Prerequisite 1 - e.g., Docker installed]
- [ ] [Prerequisite 2 - e.g., Node.js 18+]
- [ ] [Prerequisite 3 - e.g., Database migrations up to date]

### **Environment Configuration**
```bash
# Clone and setup (if new developer)
git clone https://github.com/AlgenticsCorp/molecular_analysis_dashboard.git
cd molecular_analysis_dashboard

# Environment setup for this phase
cp .env.example .env
# Update .env with phase-specific configuration

# Install dependencies
# [Phase-specific dependency installation commands]
```

### **Phase-Specific Setup**
```bash
# [Any additional setup commands specific to this phase]
# [Database migrations, service configurations, etc.]
```

---

## 📋 Implementation Steps

### **Step 1: [Step Name]**
**Estimated Time**: [Hours/Days]
**Dependencies**: [Prerequisites for this step]

#### **Objective**
[What this step accomplishes and why it's needed]

#### **Implementation**
1. **[Sub-step 1]**
   ```bash
   # Code examples or commands
   ```

2. **[Sub-step 2]**
   ```python
   # Code examples with explanations
   def example_function():
       """Example implementation."""
       pass
   ```

3. **[Sub-step 3]**
   - [Detailed instructions]
   - [Configuration changes]
   - [File modifications]

#### **Testing This Step**
```bash
# Commands to test this step
# Expected outputs
```

#### **Troubleshooting**
| Issue | Symptoms | Solution |
|-------|----------|----------|
| [Common Issue 1] | [How to identify] | [How to fix] |
| [Common Issue 2] | [How to identify] | [How to fix] |

---

### **Step 2: [Step Name]**
**Estimated Time**: [Hours/Days]
**Dependencies**: [Prerequisites for this step]

[Repeat the same structure as Step 1]

---

### **Step N: [Final Step Name]**
**Estimated Time**: [Hours/Days]
**Dependencies**: [Prerequisites for this step]

[Final implementation step]

---

## 🧪 Testing & Validation

### **Unit Testing**
```bash
# Run unit tests for this phase
pytest tests/unit/[phase-specific-tests]/

# Expected coverage
# Coverage should be >= 80% for new code
```

### **Integration Testing**
```bash
# Run integration tests
pytest tests/integration/[phase-specific-tests]/

# Test specific integrations
# [List key integration points to verify]
```

### **End-to-End Testing**
```bash
# Run E2E tests
# [Commands for E2E testing]

# Manual testing checklist
- [ ] [Key user workflow 1]
- [ ] [Key user workflow 2]
- [ ] [Key user workflow 3]
```

### **Performance Testing**
```bash
# Performance testing commands
# [Load testing, benchmarking commands]

# Performance targets
# [Specific metrics to achieve]
```

---

## 🔧 Configuration & Deployment

### **Configuration Changes**
- **Environment Variables**: [New or modified env vars]
- **Database**: [Schema changes, migrations]
- **Services**: [New services or service modifications]

### **Database Migrations**
```bash
# Run migrations for this phase
alembic upgrade head

# Verify migration success
# [Verification commands]
```

### **Service Deployment**
```bash
# Deploy updated services
docker compose up -d --build

# Verify deployment
docker compose ps
curl http://localhost:8000/health
```

### **Production Deployment Notes**
- **Rollout Strategy**: [How to deploy to production safely]
- **Rollback Plan**: [How to rollback if issues occur]
- **Monitoring**: [What to monitor during deployment]

---

## 📊 Progress Tracking

### **Feature Completion Checklist**
- [ ] **[Feature 1]**: [Brief description] - **Status**: [Not Started | In Progress | Testing | Complete]
- [ ] **[Feature 2]**: [Brief description] - **Status**: [Not Started | In Progress | Testing | Complete]
- [ ] **[Feature 3]**: [Brief description] - **Status**: [Not Started | In Progress | Testing | Complete]

### **Quality Gates Checklist**
- [ ] **Code Review**: All code reviewed and approved
- [ ] **Testing**: All tests passing, coverage requirements met
- [ ] **Documentation**: All documentation updated
- [ ] **Security**: Security review completed (if applicable)
- [ ] **Performance**: Performance requirements verified

### **Integration Checklist**
- [ ] **API Integration**: New/modified APIs tested with frontend
- [ ] **Database Integration**: Data layer changes verified
- [ ] **Service Integration**: Inter-service communication tested
- [ ] **Gateway Integration**: API gateway routing verified (if applicable)

---

## 🚨 Common Issues & Solutions

### **Development Issues**
| Issue | Symptoms | Root Cause | Solution |
|-------|----------|------------|----------|
| [Issue 1] | [How it manifests] | [Why it happens] | [Step-by-step fix] |
| [Issue 2] | [How it manifests] | [Why it happens] | [Step-by-step fix] |

### **Testing Issues**
| Issue | Symptoms | Root Cause | Solution |
|-------|----------|------------|----------|
| [Issue 1] | [Test failures, etc.] | [Why tests fail] | [How to fix] |
| [Issue 2] | [Test failures, etc.] | [Why tests fail] | [How to fix] |

### **Deployment Issues**
| Issue | Symptoms | Root Cause | Solution |
|-------|----------|------------|----------|
| [Issue 1] | [Deployment failures] | [Why deployment fails] | [How to fix] |
| [Issue 2] | [Runtime errors] | [Configuration issues] | [How to fix] |

---

## 📚 Code Examples & Patterns

### **Architecture Pattern Example**
```python
# Example following Clean Architecture patterns
from src.domain.entities.example import ExampleEntity
from src.use_cases.commands.example_use_case import ExampleUseCase
from src.ports.repository.example_repository_port import ExampleRepositoryPort

class ExampleImplementation:
    """Example implementation following project patterns."""

    def __init__(self, repository: ExampleRepositoryPort):
        self.repository = repository

    async def example_method(self, data: dict) -> ExampleEntity:
        """Example method with proper error handling."""
        try:
            # Implementation logic
            pass
        except Exception as e:
            # Proper error handling
            raise
```

### **API Endpoint Example**
```python
# Example API endpoint
from fastapi import APIRouter, Depends, HTTPException
from src.presentation.schemas.example import ExampleRequest, ExampleResponse

router = APIRouter()

@router.post("/example", response_model=ExampleResponse)
async def create_example(
    request: ExampleRequest,
    use_case: ExampleUseCase = Depends()
) -> ExampleResponse:
    """Create example following project patterns."""
    try:
        result = await use_case.execute(request.dict())
        return ExampleResponse.from_domain(result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
```

### **Frontend Component Example**
```typescript
// Example React component
import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Box, Typography, CircularProgress } from '@mui/material';

interface ExampleProps {
  // Component props
}

const ExampleComponent: React.FC<ExampleProps> = (props) => {
  const { data, isLoading, error } = useQuery({
    queryKey: ['example'],
    queryFn: () => fetchExampleData()
  });

  if (isLoading) return <CircularProgress />;
  if (error) return <Typography color="error">Error occurred</Typography>;

  return (
    <Box>
      {/* Component implementation */}
    </Box>
  );
};

export default ExampleComponent;
```

---

## 🔄 Status Updates

### **How to Update Implementation Status**
1. **Update Progress**: Modify the feature completion checklist above
2. **Update Documentation**: Keep this guide current with any changes
3. **Notify Team**: Update team on significant progress or blockers
4. **Update Phase Status**: Update the main phase tracking documents

### **Status Update Template**
```markdown
## Implementation Status Update - [Date]

**Overall Progress**: [X]% complete
**Last Week's Progress**: [What was accomplished]
**This Week's Plan**: [What will be worked on]
**Blockers**: [Any issues preventing progress]
**Help Needed**: [Any assistance required]
```

---

## 📝 Implementation Notes

### **Key Decisions Made**
- **[Date]**: [Decision] - [Rationale and impact]
- **[Date]**: [Decision] - [Rationale and impact]

### **Lessons Learned**
- [Lesson 1]: [What was learned and how it applies going forward]
- [Lesson 2]: [What was learned and how it applies going forward]

### **Optimization Opportunities**
- [Opportunity 1]: [Potential improvement or optimization]
- [Opportunity 2]: [Potential improvement or optimization]

---

## 🔗 References & Resources

### **Related Documentation**
- [Phase Planning Document](./planning.md)
- [Architecture Documentation](../../../architecture/)
- [API Documentation](../../../api/)
- [Development Guidelines](../../../development/guides/)

### **External Resources**
- [Relevant external documentation]
- [Helpful tutorials or guides]
- [Technology-specific documentation]

### **Team Resources**
- **Code Reviews**: [Link to review process]
- **Testing Guidelines**: [Link to testing standards]
- **Deployment Process**: [Link to deployment docs]

---

## ✅ Implementation Completion

### **Completion Criteria**
- [ ] All implementation steps completed
- [ ] All tests passing
- [ ] Code review approved
- [ ] Documentation updated
- [ ] Deployment verified

### **Handoff Checklist**
- [ ] **Code**: All code committed and merged
- [ ] **Documentation**: Implementation guide updated with final state
- [ ] **Deployment**: Services deployed and verified
- [ ] **Monitoring**: Monitoring and alerting configured
- [ ] **Team Notification**: Team notified of completion

### **Next Steps**
[What happens after this phase is complete - next phase preparation, etc.]

---

*This implementation guide should be updated continuously during development to reflect the actual implementation approach and serve as a living document for the team.*
