# Proposed Code Structure

This project will strictly adhere to the **Clean Structure** (also known as Hexagonal or Ports & Adapters) principles established by the repository template. This ensures a clear separation of concerns, making the system maintainable, testable, and adaptable to future changes.

For component diagrams and framework mapping, see [`FRAMEWORK_DESIGN.md`](./FRAMEWORK_DESIGN.md).

### Core Principles:

1.  **The Dependency Rule**: Source code dependencies can only point inwards. Nothing in an inner circle can know anything at all about something in an outer circle.
2.  **Entities are Central**: The `domain` layer, containing the core business logic and entities, is the heart of the application and has no external dependencies.
3.  **Adapters are Plugins**: External technologies like databases, frameworks, and third-party services are treated as plugins (Adapters) that connect to the application core via stable interfaces (Ports).

### Architectural Layers:

The code will be organized into the following distinct layers, each with a specific responsibility:

```
src/molecular_analysis_dashboard/
│
├──  presentation/ (Backend Presentation)
│   └── api/ (FastAPI routers, schemas)
│
frontend/
│
├── src/ (Frontend Application)
│   ├── components/ (React components)
│   ├── pages/ (Page-level components)
│   ├── hooks/ (Custom React hooks)
│   ├── services/ (API client functions)
│   ├── types/ (TypeScript type definitions)
│   └── utils/ (Utility functions)
│
├── infrastructure/ (Infrastructure)
│   ├── config.py, database.py, security.py, celery_app.py
│
├── adapters/ (Adapters)
│   ├── database/ (PostgreSQL repositories)
│   ├── external/ (AutoDock Vina, RDKit adapters)
│   └── messaging/ (Celery task implementations)
│
├── ports/ (Ports)
│   ├── repository/ (Abstract database interfaces)
│   └── external/ (Abstract external service interfaces)
│
├── use_cases/ (Use Cases)
│   ├── commands/ (Write operations)
│   └── queries/ (Read operations)
│
└── domain/ (Domain)
    ├── entities/ (Core business objects: Molecule, DockingJob)
    └── services/ (Domain-specific logic)
```

1.  **`domain` (Domain Layer)**:
    - **Purpose**: Contains the enterprise-wide business rules and entities. This is the most independent layer.
    - **Content**: Pure Python objects representing concepts like `Molecule`, `DockingJob`, and `Pipeline`. It knows nothing about databases, APIs, or any external service.

2.  **`use_cases` (Use Case Layer)**:
    - **Purpose**: Orchestrates the flow of data to and from the domain entities to achieve specific application goals (e.g., `CreateDockingJobUseCase`).
    - **Content**: Application-specific business rules. It depends on the `Domain` layer but has no knowledge of the `Presentation` or `Infrastructure` layers.

3.  **`ports` (Ports Layer)**:
    - **Purpose**: Defines the abstract interfaces that the `Use Cases` depend on. These are the "ports" through which data enters and leaves the application core.
    - **Content**: Abstract Base Classes (ABCs) or Protocols defining contracts for repositories (`MoleculeRepositoryPort`) or external services (`DockingEnginePort`).

4.  **`adapters` (Adapters Layer)**:
    - **Purpose**: Provides the concrete implementations of the `Ports`. This is where the outside world is "adapted" to fit the application's needs.
    - **Content**: `PostgreSQLMoleculeRepository` which implements `MoleculeRepositoryPort`, or `AutoDockVinaAdapter` which implements `DockingEnginePort`.

5.  **`infrastructure` (Infrastructure Layer)**:
    - **Purpose**: Manages the setup and configuration of all external tools and frameworks.
    - **Content**: Database connection setup, Celery app configuration, security context, and dependency injection wiring.

6.  **`presentation` (Presentation Layer)**:
    - **Purpose**: The entry point for external actors (users, other systems). Its job is to parse incoming requests, pass them to the appropriate `Use Case`, and format the output.
    - **Content**: FastAPI routers, request/response schemas (Pydantic models), and WebSocket handlers.

### Logical Separation for Scalability:

-   **API vs. Workers**: The backend `Presentation` layer (FastAPI) runs in separate containers from the computational workers (Celery). They communicate via a shared message broker (Redis), ensuring that long-running docking jobs do not block user-facing API requests.
-   **Frontend-Backend Separation**: The backend exposes a pure REST API, while the frontend is a completely separate React TypeScript application that consumes this API. This allows the frontend and backend to be:
    - Developed independently by different teams
    - Deployed and scaled separately
    - Versioned independently
    - Technology stacks can evolve independently
-   **Frontend Architecture**: The React application follows modern patterns:
    - Component-based architecture with TypeScript for type safety
    - State management via React Query for server state and React Context for client state
    - Modular structure with clear separation between UI, business logic, and API communication
-   **Adapter Swapping**: To change the docking engine from AutoDock Vina to OpenEye, only a new adapter needs to be created in the `adapters/external` directory. No changes are needed in the `Domain`, `Use Case` layers, or the frontend application, demonstrating the plug-and-play nature of the architecture.
