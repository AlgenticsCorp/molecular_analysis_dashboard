# Code Structure (See ARCHITECTURE.md)

This file is a brief pointer to the authoritative architecture documents for the Molecular Analysis Dashboard.

- Start with: [ARCHITECTURE.md](./ARCHITECTURE.md) — Clean Architecture layers and responsibilities
- Visuals: [FRAMEWORK_DESIGN.md](./FRAMEWORK_DESIGN.md) — component, sequence, deployment, and class diagrams
- Workflow/stack: [TOOLS_AND_WORKFLOW.md](./TOOLS_AND_WORKFLOW.md)
- Use cases: [USE_CASES.md](./USE_CASES.md)

Quick reference layout:

```
src/molecular_analysis_dashboard/
├── presentation/      # FastAPI routers, schemas
├── infrastructure/    # settings, db, security, celery
├── adapters/          # repositories (PostgreSQL), engines (Vina/Smina/Gnina/RDKit), messaging
├── ports/             # repository/external interfaces
├── use_cases/         # commands & queries
└── domain/            # entities & domain services
```

Notes:
- Adapters are pluggable; the core depends only on ports (interfaces).
- Storage is abstracted behind a Storage Adapter (local FS for dev, S3/MinIO for prod).
- Long-running work runs in Celery workers; API remains stateless and responsive.
