# Tools, Technologies, and Workflow

This document provides an overview of the tools and technologies used in the Molecular Analysis Dashboard project and explains the end-to-end workflow of the solution.

---

## **1. Tools & Technologies**

The technology stack is chosen to build a robust, scalable, and maintainable platform that can handle heavy computational loads while providing a responsive user experience.

### **1.1. Backend**

-   **Python 3.11+**: The core programming language for the backend.
-   **FastAPI**: A modern, high-performance web framework for building the REST API. It's chosen for its speed, automatic interactive documentation (Swagger UI), and dependency injection system, which fits perfectly with the Clean Architecture model.
-   **Uvicorn & Gunicorn**: Uvicorn is the lightning-fast ASGI server that runs the FastAPI application. In production, it is managed by Gunicorn, a battle-tested process manager that allows running multiple worker processes to handle concurrent requests.
-   **Pydantic**: Used by FastAPI for data validation and settings management. It ensures that all data flowing into and out of the API is well-structured and type-safe.

### **1.2. Asynchronous Task & Message Queue**

-   **Celery**: A distributed task queue system used to run long-running, computationally intensive tasks (like molecular docking) in the background. This prevents the API from being blocked and allows the system to scale its computational power independently of the web servers.
-   **Redis**: An in-memory data store used as the message broker for Celery. It facilitates communication between the FastAPI application (which produces tasks) and the Celery workers (which consume them). It's also used for caching frequently accessed data to improve performance.

### **1.3. Database & Storage**

-   **PostgreSQL**: A powerful, open-source object-relational database system. It is used to store structured, relational data such as user information, pipeline configurations, and job metadata. Its robustness and support for complex queries make it ideal for managing the core state of the application.
-   **SQLAlchemy with `asyncpg`**: The primary Object-Relational Mapper (ORM) for interacting with PostgreSQL. The `asyncpg` driver enables fully asynchronous database operations, which is crucial for the performance of the FastAPI backend.
-   **Alembic**: A database migration tool for SQLAlchemy. It allows for versioning the database schema and applying changes incrementally and reversibly.
-   **File Storage**: Initially, a local file system will be used for storing user-uploaded molecular files and job results. The architecture is designed to easily swap this with a cloud-based object storage solution like **Amazon S3** or **MinIO** for production scalability.

### **1.4. Frontend**

-   **React 18+**: Modern frontend framework for building the user interface with component-based architecture
-   **TypeScript 5+**: Primary programming language for the frontend, providing type safety and better developer experience
-   **Vite**: Fast build tool and development server for React TypeScript projects
-   **Material-UI (MUI)**: React component library for consistent and professional UI design
-   **React Query (TanStack Query)**: Data fetching and state management for API interactions
-   **React Router**: Client-side routing for single-page application navigation
-   **3Dmol.js**: Lightweight JavaScript library for interactive, web-based 3D visualization of molecular data without requiring browser plugins

### **1.5. Molecular Computing**

-   **Docking Engines (AutoDock Vina, Smina, Gnina, etc.)**: Pluggable engines used for molecular docking. The platform supports selecting an engine per pipeline or task via adapters.
-   **RDKit**: A collection of cheminformatics and machine-learning software written in C++ and Python. It will be used for pre-processing molecular files, generating descriptors, and analyzing structures.
-   **PyMOL**: A powerful molecular visualization tool for advanced molecular analysis and preparation.

### **1.6. Development & Deployment**

-   **Docker & Docker Compose**: The entire application and its dependencies are containerized using Docker. Docker Compose is used to orchestrate the multi-container setup (API, workers, database, frontend, etc.) for local development, ensuring a consistent and reproducible environment.
-   **Kubernetes (for Production)**: The containerized application is designed to be deployed to a Kubernetes cluster for production. This allows for automated scaling, high availability, and robust management of the microservices architecture.
-   **Testing Frameworks**:
    - **Backend**: Pytest for Python unit, integration, and end-to-end tests
    - **Frontend**: Jest + React Testing Library for component and integration tests
    - **E2E**: Playwright or Cypress for cross-browser end-to-end testing
-   **Code Quality**:
    - **Backend**: Pre-commit hooks with Black, isort, flake8, mypy
    - **Frontend**: ESLint, Prettier, TypeScript compiler for code quality
-   **Build & CI/CD**: GitHub Actions for automated testing, building, and deployment

---

## **2. Solution Workflow: A User's Docking Job**

This section describes the journey of a request through the system, from the user's action to the final result, illustrating how the different architectural layers and components interact.

**Scenario**: A registered user wants to perform a docking analysis between a ligand and a protein they have previously uploaded.

1.  **User Initiates Request (Presentation Layer)**
    -   The user, via a web interface, clicks a button to start a new docking job, selecting their desired ligand and protein.
    -   The frontend sends a `POST` request to the `/api/v1/pipelines/{pipeline_id}/jobs` endpoint with the user's JWT authentication token and the IDs of the molecules.

2.  **API Endpoint Receives Request (Presentation Layer)**
    -   The FastAPI router directs the request to the appropriate endpoint function.
    -   FastAPI's security module decodes the JWT, authenticates the user, and extracts the `user_id` and `tenant_id`.
    -   The request body is parsed and validated by a Pydantic schema.

3.  **Use Case Orchestration (Use Case Layer)**
    -   The API endpoint calls the `CreateDockingJobUseCase`, passing the validated data.
    -   The use case is responsible for orchestrating the business logic. It does *not* know how the database works or how docking is performed; it only knows how to call the interfaces it needs.

4.  **Data Persistence (Ports & Adapters)**
    -   The `CreateDockingJobUseCase` first needs to create a record of the job. It calls the `save()` method on an object that implements the `DockingJobRepositoryPort` (an interface).
    -   Through dependency injection, this port is implemented by the `PostgreSQLDockingJobRepository` (an adapter).
    -   The repository adapter uses SQLAlchemy to create a new row in the `docking_jobs` table with a status of `PENDING` and returns the newly created `DockingJob` entity to the use case.

5.  **Dispatching the Task (Infrastructure & Messaging)**
    -   With the job successfully created in the database, the use case now needs to trigger the actual computation.
    -   It calls a Celery task, `execute_docking_task.delay(job_id=...)`, placing a message onto the **Redis** message queue.
    -   The API immediately returns a `202 Accepted` response to the user with the `job_id`, indicating that the task has been successfully queued. The user's web session is not blocked.

6.  **Background Worker Execution (Celery & Adapters)**
    -   A **Celery worker** process, running in a separate container, is constantly monitoring the Redis queue. It picks up the new task message.
    -   The `execute_docking_task` function begins execution. It first updates the job's status in the database to `RUNNING` via the repository port.
    -   The task then calls the `execute_docking()` method on an object that implements the `DockingEnginePort`.

7.  **Computational Work (Adapters & External Tools)**
    -   The `DockingEnginePort` is implemented by one of the engine adapters (e.g., `AutoDockVinaAdapter`, `SminaAdapter`, `GninaAdapter`).
    -   The adapter prepares the necessary input files (ligand and protein PDBQT files) and then executes the selected engine as a subprocess or containerized command.
    -   The adapter waits for the engine process to complete, which could take minutes or hours.

8.  **Processing and Storing Results (Adapters & Domain)**
    -   Once the engine finishes, the adapter parses the output log files to extract the binding affinity scores and other metrics.
    -   It creates `DockingResult` domain entities.
    -   The `execute_docking_task` receives these results and uses the `DockingJobRepositoryPort` to update the job's status to `COMPLETED` and save the associated results to the database.

9.  **User Views Results (Frontend & API)**
    -   The user, on the React web interface, navigates to the results page for their job using React Router.
    -   The React component uses React Query to make a `GET` request to `/api/v1/jobs/{job_id}/results`.
    -   This API endpoint triggers a `GetDockingResultsUseCase`, which fetches the job and its associated results from the database via the repository port and returns them as JSON.
    -   The React component renders the scores in a Material-UI table and uses `3Dmol.js` to visualize the output molecular files, providing an interactive 3D view of the docked complex.
    -   TypeScript ensures type safety throughout the data flow from API response to UI rendering.
