# Proposed Code Structure

This project will strictly adhere to the **Clean Structure** (also known as Hexagonal or Ports & Adapters) principles established by the repository template. This ensures a clear separation of concerns, making the system maintainable, testable, and adaptable to future changes.

For component diagrams and framework mapping, see [`FRAMEWORK_DESIGN.md`](./FRAMEWORK_DESIGN.md).

### Core Principles:

1.  **The Dependency Rule**: Source code dependencies can only point inwards. Nothing in an inner circle can know anything at all about something in an outer circle.
2.  **Entities are Central**: The `domain` layer, containing the core business logic and entities, is the heart of the application and has no external dependencies.
3.  **Adapters are Plugins**: External technologies like databases, frameworks, and third-party services are treated as plugins (Adapters) that connect to the application core via stable interfaces (Ports).
4.  **Dynamic Task System**: Tasks are defined in the database with OpenAPI specifications, enabling runtime addition of new computational workflows without code deployment.

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
│   ├── components/ (React components with dynamic task support)
│   ├── pages/ (Page-level components)
│   ├── hooks/ (Custom React hooks for task management)
│   ├── services/ (API client functions for dynamic tasks)
│   ├── types/ (TypeScript type definitions including OpenAPI)
│   └── utils/ (Utility functions, OpenAPI form generators)
│
├── infrastructure/ (Infrastructure)
│   ├── config.py, database.py, security.py, celery_app.py
│   └── task_discovery.py (Service discovery and orchestration)
│
├── adapters/ (Adapters)
│   ├── database/ (PostgreSQL repositories including task registry)
│   ├── external/ (Dynamic task service adapters)
│   ├── messaging/ (Celery task implementations)
│   └── task_services/ (Task-specific service adapters)
│
├── ports/ (Ports)
│   ├── repository/ (Abstract database interfaces)
│   ├── external/ (Abstract external service interfaces)
│   └── task_registry/ (Dynamic task definition interfaces)
│
├── use_cases/ (Use Cases)
│   ├── commands/ (Write operations including task execution)
│   ├── queries/ (Read operations including task discovery)
│   └── task_management/ (Dynamic task CRUD operations)
│
└── domain/ (Domain)
    ├── entities/ (Core business objects: Molecule, DockingJob, TaskDefinition)
    ├── services/ (Domain-specific logic)
    └── task_specs/ (Task interface specifications and validation)
```

1.  **`domain` (Domain Layer)**:
    - **Purpose**: Contains the enterprise-wide business rules and entities. This is the most independent layer.
    - **Content**: Pure Python objects representing concepts like `Molecule`, `DockingJob`, `Pipeline`, and `TaskDefinition`. Includes OpenAPI schema validation and task interface specifications.

2.  **`use_cases` (Use Case Layer)**:
    - **Purpose**: Orchestrates the flow of data to and from the domain entities to achieve specific application goals (e.g., `CreateDockingJobUseCase`, `ExecuteDynamicTaskUseCase`).
    - **Content**: Application-specific business rules including dynamic task discovery, validation, and execution orchestration.

3.  **`ports` (Ports Layer)**:
    - **Purpose**: Defines the abstract interfaces that the `Use Cases` depend on. These are the "ports" through which data enters and leaves the application core.
    - **Content**: Abstract Base Classes (ABCs) or Protocols defining contracts for repositories (`TaskRegistryPort`), external services (`DockingEnginePort`), and service discovery (`ServiceDiscoveryPort`).

4.  **`adapters` (Adapters Layer)**:
    - **Purpose**: Provides the concrete implementations of the `Ports`. This is where the outside world is "adapted" to fit the application's needs.
    - **Content**: `PostgreSQLTaskRegistryAdapter`, `KubernetesServiceDiscoveryAdapter`, and dynamic task service adapters that communicate with containerized task services via HTTP APIs.

5.  **`infrastructure` (Infrastructure Layer)**:
    - **Purpose**: Manages the setup and configuration of all external tools and frameworks.
    - **Content**: Database connection setup, Celery app configuration, security context, dependency injection wiring, and service discovery infrastructure.

6.  **`presentation` (Presentation Layer)**:
    - **Purpose**: The entry point for external actors (users, other systems). Its job is to parse incoming requests, pass them to the appropriate `Use Case`, and format the output.
    - **Content**: FastAPI routers for both static API endpoints and dynamic task execution, request/response schemas (Pydantic models), and WebSocket handlers for real-time task status.

### Dynamic Task Architecture:

-   **Task Registry**: Task definitions are stored in the database with full OpenAPI 3.0 specifications, enabling runtime discovery and interface generation.
-   **Service Discovery**: Running task services are registered and discovered dynamically, supporting auto-scaling and load balancing.
-   **Microservice Execution**: Each task type can run as an independent containerized service, enabling horizontal scaling and technology diversity.
-   **Frontend Adaptation**: The React frontend automatically generates forms and interfaces based on task OpenAPI specifications loaded from the database.

### Logical Separation for Scalability:

-   **API vs. Workers vs. Task Services**: The system now has three distinct service types:
    - **API Services** (FastAPI): Handle user requests and orchestration
    - **Worker Services** (Celery): Handle background processing and workflow coordination
    - **Task Services** (Containerized): Execute specific computational tasks (docking, analysis, etc.)
-   **Dynamic Service Scaling**: Task services can be scaled independently based on demand, with automatic service discovery and load balancing.
-   **Frontend-Backend Separation**: Enhanced with dynamic task interface generation, allowing the frontend to adapt to new tasks without code changes.
-   **Technology Flexibility**: Task services can be implemented in any language/framework, as long as they expose the standard OpenAPI interface.
-   **Adapter Evolution**: The adapter pattern is enhanced to support dynamic task loading while maintaining the plug-and-play nature for different computational engines.

### Multi-Tenant Task Customization:

-   **Organization-Scoped Tasks**: Each organization can define custom tasks while accessing shared system tasks.
-   **Task Versioning**: Multiple versions of tasks can coexist, enabling gradual migration and A/B testing.
-   **Resource Management**: Task execution resources (CPU, memory, GPU) are managed per organization with quotas and billing integration.
