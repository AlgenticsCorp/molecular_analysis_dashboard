---
name: Bug report
description: Report a bug in the molecular analysis dashboard
labels: ["type:bug", "status:triage"]
title: "[Bug]: "
assignees: []
---

## 🐛 Bug Description
Provide a clear and concise description of the bug.

## 🔬 Molecular Analysis Context
**Affected Component:**
- [ ] Docking Engine (Vina/Smina/Gnina)
- [ ] Molecule Upload/Processing
- [ ] Pipeline Configuration
- [ ] Job Queue/Processing
- [ ] Results Visualization (3D)
- [ ] Organization/Multi-tenancy
- [ ] Authentication/Authorization
- [ ] File Storage/Retrieval
- [ ] Database Operations
- [ ] API Endpoints
- [ ] Frontend UI
- [ ] Other: ___________

**Docking Engine:** [Vina/Smina/Gnina/N/A]
**Molecular File Format:** [SDF/PDB/MOL2/SMILES/N/A]
**Pipeline Stage:** [Upload/Configure/Submit/Execute/Results/N/A]

## 🏗️ Architecture Layer
**Primary Layer Affected:**
- [ ] Domain (entities, business rules)
- [ ] Use Cases (application services)
- [ ] Ports (abstract interfaces)
- [ ] Adapters (implementations)
- [ ] Infrastructure (framework setup)
- [ ] Presentation (API routes, schemas)
- [ ] Frontend (React components)

**Specific Module:** [e.g., `src/molecular_analysis_dashboard/adapters/external/vina_adapter.py`]

## 📋 Steps to Reproduce
1. **Setup:** [Docker services, auth state, etc.]
2. **Action 1:** [e.g., Upload molecule file via API]
3. **Action 2:** [e.g., Configure docking parameters]
4. **Action 3:** [e.g., Submit docking job]
5. **Observe:** [Error occurs at this step]

**API Endpoint:** [e.g., `POST /api/v1/molecules`]
**Request Payload:**
```json
[Include relevant request data]
```

## ✅ Expected Behavior
Describe what should happen instead.

## ❌ Actual Behavior
**Error Message:**
```
[Paste exact error message]
```

**HTTP Status Code:** [e.g., 500, 422, 404]
**Frontend Console Errors:** [if applicable]

## 📊 Severity Assessment
**Impact:**
- [ ] Critical (blocks core molecular analysis workflow)
- [ ] High (affects major functionality)
- [ ] Medium (workaround available)
- [ ] Low (minor issue)

**User Type Affected:**
- [ ] End Users (molecular researchers)
- [ ] Org Admins
- [ ] System Administrators
- [ ] Developers

## 🖥️ Environment Details
**Infrastructure:**
- OS: [e.g., macOS 14, Ubuntu 22.04]
- Docker version: [e.g., 24.0.6]
- Docker Compose version: [e.g., 2.21.0]

**Backend:**
- Python version: [e.g., 3.12]
- FastAPI version: [e.g., 0.104.1]
- SQLAlchemy version: [e.g., 2.0.23]
- Celery version: [e.g., 5.3.4]
- Redis version: [e.g., 7.2]
- PostgreSQL version: [e.g., 15.4]

**Frontend:**
- Node.js version: [e.g., 18.18.0]
- React version: [e.g., 18.2.0]
- Vite version: [e.g., 4.4.9]
- Browser: [e.g., Chrome 117, Safari 16]

**Docking Engines:**
- AutoDock Vina: [version if relevant]
- Smina: [version if relevant]
- Gnina: [version if relevant]

## 📝 Log Output
**Backend Logs:**
```
[Paste relevant FastAPI/Celery logs]
```

**Worker Logs:**
```
[Paste relevant Celery worker logs]
```

**Database Logs:**
```
[Paste relevant PostgreSQL logs if applicable]
```

**Frontend Console:**
```
[Paste browser console errors]
```

## 🎯 Implementation Stage
**Related Milestone:** [Stage 0-9 from implementation plan]
**Implementation Priority:** [P0/P1/P2/P3]

## 📸 Screenshots/Videos
[If applicable, add screenshots or screen recordings]

## 🔗 Related Issues/PRs
- Related to: #[issue_number]
- Blocks: #[issue_number]
- Blocked by: #[issue_number]

## 💡 Additional Context
**Workaround:** [If any temporary workaround exists]
**Data Size:** [If related to performance - file sizes, molecule count, etc.]
**Organization Context:** [If multi-tenancy related]
**Authentication Method:** [JWT/OIDC/etc. if relevant]
