# 🧬 Universal Molecular Analysis Provider Integration Framework

**Document Version:** 3.0
**Created:** September 24, 2025
**Author:** Architecture Team
**Status:** Requirements & Domain Modeling Phase

---

## 📋 **Executive Summary**

This document presents a comprehensive framework for integrating any molecular analysis service provider (internal or external) into the Molecular Analysis Dashboard. The framework defines clear domain concepts for Tasks, Pipelines, and Jobs, establishes provider-agnostic service integration patterns, and creates a unified API for molecular analysis operations regardless of the underlying service provider.

**Key Framework Components:**
- **Domain Modeling:** Clear definitions of Task, Pipeline, Job, and Provider concepts
- **Provider Architecture:** Standardized components for any service provider integration
- **Molecular Task Taxonomy:** Comprehensive categorization of molecular analysis operations
- **Unified Service Interface:** Provider-agnostic API for consistent user experience
- **Template-Based Integration:** Configurable service adapters with minimal custom coding

---

## 🎯 **Domain Modeling & Core Definitions**

### **1. Task Definition**
```python
@dataclass
class MolecularTask:
    """
    A Task represents a single, atomic molecular analysis operation.
    Examples: Docking, Structure Prediction, Property Calculation
    """
    task_id: UUID
    task_type: TaskType  # DOCKING, STRUCTURE_PREDICTION, PROPERTY_CALC, etc.
    name: str
    description: str
    category: TaskCategory  # COMPUTATIONAL_CHEMISTRY, STRUCTURAL_BIOLOGY, etc.

    # Input/Output Specifications
    input_schema: TaskInputSchema
    output_schema: TaskOutputSchema

    # Execution Requirements
    computational_requirements: ComputationalRequirements
    estimated_runtime: TimeRange
    resource_usage: ResourceUsage

    # Provider Information
    provider_id: str
    service_id: str
    version: str

    # Task Metadata
    units: Dict[str, str]  # e.g., {"energy": "kcal/mol", "time": "seconds"}
    parameters: Dict[str, ParameterDefinition]
    quality_metrics: List[QualityMetric]

    def is_compatible_with(self, input_data: TaskInput) -> bool:
        """Validate if input data matches task requirements."""
        pass

    def estimate_cost(self, input_data: TaskInput) -> CostEstimate:
        """Estimate computational cost for given input."""
        pass

@dataclass
class TaskInputSchema:
    """Defines what inputs a task expects."""
    required_inputs: Dict[str, InputSpecification]
    optional_inputs: Dict[str, InputSpecification]
    validation_rules: List[ValidationRule]

@dataclass
class TaskOutputSchema:
    """Defines what outputs a task produces."""
    primary_outputs: Dict[str, OutputSpecification]
    secondary_outputs: Dict[str, OutputSpecification]
    metadata_outputs: Dict[str, MetadataSpecification]
```

### **2. Pipeline Definition**
```python
@dataclass
class MolecularPipeline:
    """
    A Pipeline represents a workflow of interconnected Tasks.
    Examples: Drug Discovery Workflow, Protein Analysis Pipeline
    """
    pipeline_id: UUID
    name: str
    description: str
    category: PipelineCategory

    # Workflow Structure
    tasks: List[PipelineTask]
    dependencies: Dict[UUID, List[UUID]]  # task_id -> prerequisite_task_ids
    data_flow: Dict[str, DataFlowMapping]  # output -> input mappings

    # Pipeline Configuration
    parallel_execution: bool
    failure_handling: FailureHandlingStrategy
    optimization_strategy: OptimizationStrategy

    # Validation & Execution
    def validate_workflow(self) -> List[ValidationError]:
        """Validate pipeline structure and data flow."""
        pass

    def estimate_total_runtime(self) -> TimeRange:
        """Calculate estimated pipeline execution time."""
        pass

    def get_execution_plan(self) -> ExecutionPlan:
        """Generate optimized execution plan."""
        pass

@dataclass
class PipelineTask:
    """Task within a pipeline context."""
    task_id: UUID
    task_reference: MolecularTask
    position: int
    conditional_execution: Optional[ExecutionCondition]
    parameter_overrides: Dict[str, Any]
    retry_policy: RetryPolicy
```

### **3. Job Definition**
```python
@dataclass
class MolecularJob:
    """
    A Job represents a specific execution instance of a Task or Pipeline.
    """
    job_id: UUID
    org_id: UUID
    user_id: UUID

    # Job Type
    job_type: JobType  # SINGLE_TASK, PIPELINE_EXECUTION
    task_reference: Optional[UUID]  # For single tasks
    pipeline_reference: Optional[UUID]  # For pipeline executions

    # Execution State
    status: JobStatus
    priority: JobPriority
    submitted_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]

    # Input/Output Data
    input_data: JobInputData
    output_data: Optional[JobOutputData]
    intermediate_results: Dict[str, Any]

    # Execution Details
    provider_job_id: Optional[str]  # External provider's job identifier
    execution_log: List[JobLogEntry]
    resource_usage: ResourceUsageRecord
    cost_tracking: CostRecord

    # Error Handling
    error_details: Optional[JobError]
    retry_count: int
    max_retries: int

    def can_be_retried(self) -> bool:
        return self.retry_count < self.max_retries and self.status == JobStatus.FAILED

    def get_progress_percentage(self) -> float:
        """Calculate job completion percentage."""
        pass
```

---

## 🔬 **Molecular Analysis Task Taxonomy**

### **Primary Task Categories**

#### **1. Molecular Docking & Binding**
```python
class DockingTaskTypes(Enum):
    PROTEIN_LIGAND_DOCKING = "protein_ligand_docking"
    PROTEIN_PROTEIN_DOCKING = "protein_protein_docking"
    DNA_PROTEIN_DOCKING = "dna_protein_docking"
    COVALENT_DOCKING = "covalent_docking"
    ENSEMBLE_DOCKING = "ensemble_docking"
    FREE_ENERGY_PERTURBATION = "free_energy_perturbation"

# Example Task Definition
VINA_DOCKING_TASK = MolecularTask(
    task_type=TaskType.DOCKING,
    name="AutoDock Vina Molecular Docking",
    category=TaskCategory.COMPUTATIONAL_CHEMISTRY,
    input_schema=TaskInputSchema(
        required_inputs={
            "receptor": InputSpecification(
                type="file",
                formats=["pdb", "pdbqt"],
                max_size="100MB",
                validation=["valid_protein_structure"]
            ),
            "ligand": InputSpecification(
                type="file",
                formats=["sdf", "mol2", "pdbqt"],
                max_size="10MB",
                validation=["valid_molecule"]
            ),
            "search_space": InputSpecification(
                type="object",
                required_fields=["center_x", "center_y", "center_z", "size_x", "size_y", "size_z"]
            )
        },
        optional_inputs={
            "exhaustiveness": InputSpecification(type="integer", default=8, range=(1, 32)),
            "num_modes": InputSpecification(type="integer", default=9, range=(1, 100)),
            "energy_range": InputSpecification(type="float", default=3.0, range=(1.0, 10.0))
        }
    ),
    output_schema=TaskOutputSchema(
        primary_outputs={
            "docked_poses": OutputSpecification(
                type="file",
                format="pdbqt",
                description="Generated docking poses"
            ),
            "binding_affinities": OutputSpecification(
                type="array",
                format="json",
                description="Binding affinity scores",
                units="kcal/mol"
            )
        },
        secondary_outputs={
            "rmsd_values": OutputSpecification(type="array", format="json"),
            "interaction_report": OutputSpecification(type="file", format="html")
        }
    ),
    units={
        "energy": "kcal/mol",
        "distance": "angstrom",
        "time": "seconds"
    }
)
```

#### **2. Structure Prediction & Analysis**
```python
class StructureTaskTypes(Enum):
    PROTEIN_FOLDING = "protein_folding"
    HOMOLOGY_MODELING = "homology_modeling"
    AB_INITIO_PREDICTION = "ab_initio_prediction"
    CONFORMATIONAL_ANALYSIS = "conformational_analysis"
    SECONDARY_STRUCTURE = "secondary_structure_prediction"
    BINDING_SITE_PREDICTION = "binding_site_prediction"

# Example: AlphaFold3 Structure Prediction
ALPHAFOLD3_TASK = MolecularTask(
    task_type=TaskType.STRUCTURE_PREDICTION,
    input_schema=TaskInputSchema(
        required_inputs={
            "sequence": InputSpecification(
                type="string",
                format="fasta",
                validation=["valid_amino_acid_sequence"],
                min_length=20,
                max_length=10000
            )
        },
        optional_inputs={
            "ligand_structure": InputSpecification(
                type="file",
                formats=["sdf", "mol2"]
            ),
            "confidence_cutoff": InputSpecification(
                type="float",
                default=70.0,
                range=(50.0, 100.0)
            )
        }
    ),
    output_schema=TaskOutputSchema(
        primary_outputs={
            "predicted_structure": OutputSpecification(type="file", format="pdb"),
            "confidence_scores": OutputSpecification(type="file", format="json")
        }
    ),
    computational_requirements=ComputationalRequirements(
        min_memory_gb=8,
        min_cpu_cores=4,
        gpu_required=True,
        estimated_time_range=TimeRange(min_minutes=5, max_minutes=120)
    )
)
```

#### **3. Molecular Property Calculation**
```python
class PropertyTaskTypes(Enum):
    PHYSICOCHEMICAL_PROPERTIES = "physicochemical_properties"
    ADMET_PREDICTION = "admet_prediction"
    LIPINSKI_DESCRIPTORS = "lipinski_descriptors"
    TOXICITY_PREDICTION = "toxicity_prediction"
    SOLUBILITY_PREDICTION = "solubility_prediction"
    LOG_P_CALCULATION = "log_p_calculation"

CHEMAXON_PROPERTIES_TASK = MolecularTask(
    task_type=TaskType.PROPERTY_CALCULATION,
    input_schema=TaskInputSchema(
        required_inputs={
            "molecules": InputSpecification(
                type="array",
                format="smiles_array",
                validation=["valid_smiles_strings"]
            )
        }
    ),
    output_schema=TaskOutputSchema(
        primary_outputs={
            "molecular_descriptors": OutputSpecification(
                type="file",
                format="json",
                fields=["molecular_weight", "log_p", "hbd", "hba", "tpsa"]
            )
        }
    )
)
```

#### **4. File Format Conversion & Processing**
```python
class ConversionTaskTypes(Enum):
    FORMAT_CONVERSION = "format_conversion"
    STRUCTURE_OPTIMIZATION = "structure_optimization"
    PROTONATION_STATE = "protonation_state"
    TAUTOMER_GENERATION = "tautomer_generation"
    CONFORMER_GENERATION = "conformer_generation"

BABEL_CONVERSION_TASK = MolecularTask(
    task_type=TaskType.FORMAT_CONVERSION,
    input_schema=TaskInputSchema(
        required_inputs={
            "input_file": InputSpecification(
                type="file",
                formats=["sdf", "mol2", "pdb", "xyz", "smiles"]
            ),
            "output_format": InputSpecification(
                type="string",
                enum=["sdf", "mol2", "pdb", "pdbqt", "xyz"]
            )
        }
    ),
    computational_requirements=ComputationalRequirements(
        min_memory_gb=1,
        min_cpu_cores=1,
        estimated_time_range=TimeRange(min_seconds=1, max_seconds=30)
    )
)
```

#### **5. Molecular Dynamics & Simulation**
```python
class SimulationTaskTypes(Enum):
    MOLECULAR_DYNAMICS = "molecular_dynamics"
    MONTE_CARLO = "monte_carlo_simulation"
    FREE_ENERGY_CALCULATION = "free_energy_calculation"
    UMBRELLA_SAMPLING = "umbrella_sampling"
    METADYNAMICS = "metadynamics"
```

---

## 🏗️ **Provider Integration Architecture**

### **Provider Component Structure**
Each service provider (internal or external) must implement these standardized components:

#### **1. Provider Configuration**
```python
@dataclass
class ProviderConfiguration:
    """Configuration for any service provider."""

    provider_id: str
    name: str
    provider_type: ProviderType  # INTERNAL, EXTERNAL_API, CLOUD_SERVICE
    description: str
    version: str

    # Authentication Configuration
    auth_config: AuthenticationConfig

    # API Configuration (for external providers)
    api_config: Optional[ApiConfiguration]

    # Available Services
    supported_tasks: List[MolecularTask]

    # Provider Capabilities
    capabilities: ProviderCapabilities

    # Resource Management
    resource_limits: ResourceLimits
    cost_model: CostModel

@dataclass
class AuthenticationConfig:
    """Authentication configuration for provider."""
    auth_type: AuthType  # API_KEY, OAUTH2, BASIC_AUTH, CERTIFICATE, NONE
    auth_endpoint: Optional[str]
    token_refresh_endpoint: Optional[str]
    credentials_schema: Dict[str, str]

    # For API Key authentication
    api_key_header: Optional[str] = "X-API-KEY"

    # For OAuth2
    client_id: Optional[str] = None
    scopes: Optional[List[str]] = None
```

#### **2. Service Adapter Interface**
```python
class ServiceProviderAdapter(ABC):
    """Generic interface that all providers must implement."""

    @abstractmethod
    async def authenticate(self, credentials: Dict[str, str]) -> AuthenticationResult:
        """Authenticate with the service provider."""
        pass

    @abstractmethod
    async def list_available_tasks(self) -> List[MolecularTask]:
        """List all available tasks from this provider."""
        pass

    @abstractmethod
    async def validate_task_input(self, task_id: str, input_data: TaskInput) -> ValidationResult:
        """Validate input data for a specific task."""
        pass

    @abstractmethod
    async def submit_job(self, task_id: str, input_data: TaskInput, job_config: JobConfig) -> JobSubmissionResult:
        """Submit a job to the provider."""
        pass

    @abstractmethod
    async def get_job_status(self, provider_job_id: str) -> JobStatusResult:
        """Get current status of a job."""
        pass

    @abstractmethod
    async def get_job_results(self, provider_job_id: str) -> JobResults:
        """Retrieve job results."""
        pass

    @abstractmethod
    async def cancel_job(self, provider_job_id: str) -> CancellationResult:
        """Cancel a running job."""
        pass

    @abstractmethod
    async def estimate_job_cost(self, task_id: str, input_data: TaskInput) -> CostEstimate:
        """Estimate job execution cost."""
        pass
```

#### **3. Input/Output Transformation Tools**
Each provider needs transformation tools to adapt between our internal format and provider-specific formats:

```python
class ProviderDataTransformer(ABC):
    """Transforms data between internal format and provider format."""

    @abstractmethod
    async def transform_input(self, task_id: str, internal_data: TaskInput) -> ProviderInput:
        """Transform internal input format to provider-specific format."""
        pass

    @abstractmethod
    async def transform_output(self, task_id: str, provider_data: ProviderOutput) -> TaskOutput:
        """Transform provider output to internal format."""
        pass

    @abstractmethod
    async def transform_parameters(self, task_id: str, internal_params: Dict[str, Any]) -> Dict[str, Any]:
        """Transform parameter names and values to provider format."""
        pass

# Example: Neurosnap Data Transformer
class NeurosnapDataTransformer(ProviderDataTransformer):

    async def transform_input(self, task_id: str, internal_data: TaskInput) -> ProviderInput:
        if task_id == "alphafold3_structure_prediction":
            return self._transform_alphafold3_input(internal_data)
        elif task_id == "gnina_docking":
            return self._transform_gnina_input(internal_data)
        else:
            raise UnsupportedTaskError(f"Task {task_id} not supported")

    def _transform_alphafold3_input(self, data: TaskInput) -> ProviderInput:
        fields = {
            "Input Sequences": json.dumps({
                "aa": {"port1": data.get("sequence")}
            }),
            "Model Version": data.get("model_version", "Boltz-1x (with potentials)")
        }

        if "ligand_file" in data:
            ligand_content = data["ligand_file"].content
            fields["Input Molecules"] = json.dumps([{
                "type": "sdf",
                "data": ligand_content.decode("utf-8")
            }])

        return ProviderInput(
            fields=fields,
            files={},
            content_type="multipart/form-data"
        )
```

#### **4. Provider-Specific Configuration Templates**
```json
{
  "provider_id": "neurosnap",
  "name": "Neurosnap AI Platform",
  "provider_type": "EXTERNAL_API",
  "version": "1.0.0",
  "auth_config": {
    "auth_type": "API_KEY",
    "api_key_header": "X-API-KEY",
    "credentials_schema": {
      "api_key": "string"
    }
  },
  "api_config": {
    "base_url": "https://neurosnap.ai",
    "timeout": 300,
    "retry_attempts": 3,
    "endpoints": {
      "submit_job": "/api/job/submit/{service_name}",
      "job_status": "/api/job/status/{job_id}",
      "job_results": "/api/job/files/{job_id}/out",
      "job_download": "/api/job/file/{job_id}/out/{filename}"
    }
  },
  "supported_tasks": [
    {
      "task_id": "alphafold3_structure_prediction",
      "service_name": "Boltz-1 (AlphaFold3)",
      "task_type": "STRUCTURE_PREDICTION",
      "input_mapping": {
        "sequence": {
          "target_field": "Input Sequences",
          "format": "json_template",
          "template": "{\"aa\": {\"port1\": \"{{sequence}}\"}}"
        }
      },
      "output_mapping": {
        "predicted_structure": {
          "source_file": "predicted_structure.pdb",
          "target_format": "pdb"
        }
      }
    }
  ],
  "cost_model": {
    "pricing_type": "per_job",
    "base_cost": 0.10,
    "size_multiplier": 0.001
  }
}
```

---

## 🔧 **Generic Service Functions**

### **Provider Registry & Discovery**
```python
class ProviderRegistry:
    """Central registry for all service providers."""

    def __init__(self):
        self.providers: Dict[str, ServiceProviderAdapter] = {}
        self.provider_configs: Dict[str, ProviderConfiguration] = {}

    async def register_provider(self, config: ProviderConfiguration, adapter: ServiceProviderAdapter):
        """Register a new service provider."""
        # Validate provider configuration
        await self._validate_provider_config(config)

        # Test provider connectivity
        test_result = await self._test_provider_connectivity(adapter)
        if not test_result.success:
            raise ProviderRegistrationError(f"Provider connectivity test failed: {test_result.error}")

        self.providers[config.provider_id] = adapter
        self.provider_configs[config.provider_id] = config

    async def list_providers(self, filters: Optional[Dict[str, Any]] = None) -> List[ProviderInfo]:
        """List all registered providers with optional filtering."""
        providers = []
        for provider_id, config in self.provider_configs.items():
            if self._matches_filters(config, filters):
                providers.append(ProviderInfo.from_config(config))
        return providers

    async def get_available_tasks(self, provider_id: Optional[str] = None) -> List[MolecularTask]:
        """Get all available tasks from providers."""
        if provider_id:
            if provider_id not in self.providers:
                raise ProviderNotFoundError(f"Provider {provider_id} not found")
            return await self.providers[provider_id].list_available_tasks()

        # Get tasks from all providers
        all_tasks = []
        for provider in self.providers.values():
            tasks = await provider.list_available_tasks()
            all_tasks.extend(tasks)

        return all_tasks

    async def find_providers_for_task(self, task_type: TaskType) -> List[str]:
        """Find all providers that support a specific task type."""
        compatible_providers = []
        for provider_id, config in self.provider_configs.items():
            for task in config.supported_tasks:
                if task.task_type == task_type:
                    compatible_providers.append(provider_id)
                    break
        return compatible_providers
```

### **Universal Job Submission & Management**
```python
class UniversalJobManager:
    """Manages job execution across all providers."""

    def __init__(
        self,
        provider_registry: ProviderRegistry,
        job_repository: JobRepositoryPort,
        result_storage: ResultStoragePort
    ):
        self.provider_registry = provider_registry
        self.job_repository = job_repository
        self.result_storage = result_storage

    async def submit_job(self, job_request: JobSubmissionRequest) -> MolecularJob:
        """Submit a job to the appropriate provider."""

        # 1. Validate job request
        validation_result = await self._validate_job_request(job_request)
        if not validation_result.is_valid:
            raise JobValidationError(validation_result.errors)

        # 2. Select optimal provider
        provider_id = await self._select_optimal_provider(job_request)
        provider = self.provider_registry.get_provider(provider_id)

        # 3. Create internal job entity
        job = MolecularJob(
            job_id=uuid4(),
            org_id=job_request.org_id,
            user_id=job_request.user_id,
            job_type=JobType.SINGLE_TASK,
            task_reference=job_request.task_id,
            status=JobStatus.CREATED,
            input_data=job_request.input_data,
            priority=job_request.priority
        )

        # 4. Submit to provider
        try:
            submission_result = await provider.submit_job(
                job_request.task_id,
                job_request.input_data,
                job_request.job_config
            )

            job.provider_job_id = submission_result.provider_job_id
            job.status = JobStatus.SUBMITTED
            job.submitted_at = datetime.utcnow()

        except ProviderError as e:
            job.status = JobStatus.FAILED
            job.error_details = JobError(
                error_type="PROVIDER_SUBMISSION_ERROR",
                message=str(e),
                details=e.details if hasattr(e, 'details') else {}
            )

        # 5. Persist job
        return await self.job_repository.save(job)

    async def monitor_job(self, job_id: UUID) -> JobStatusResult:
        """Monitor job status and update internal state."""
        job = await self.job_repository.get_by_id(job_id)
        if not job:
            raise JobNotFoundError(f"Job {job_id} not found")

        if job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
            return JobStatusResult(status=job.status, progress=100.0)

        # Get status from provider
        provider = self.provider_registry.get_provider_for_job(job)
        provider_status = await provider.get_job_status(job.provider_job_id)

        # Update internal job state
        job.status = self._map_provider_status(provider_status.status)

        if job.status == JobStatus.COMPLETED:
            await self._handle_job_completion(job, provider)
        elif job.status == JobStatus.FAILED:
            await self._handle_job_failure(job, provider_status.error)

        await self.job_repository.save(job)

        return JobStatusResult(
            status=job.status,
            progress=provider_status.progress,
            estimated_completion=provider_status.estimated_completion
        )

    async def _select_optimal_provider(self, job_request: JobSubmissionRequest) -> str:
        """Select the best provider for a job based on multiple factors."""
        compatible_providers = await self.provider_registry.find_providers_for_task(
            job_request.task_type
        )

        if not compatible_providers:
            raise NoCompatibleProviderError(f"No providers found for task type {job_request.task_type}")

        # Score providers based on multiple criteria
        provider_scores = {}
        for provider_id in compatible_providers:
            score = await self._score_provider(provider_id, job_request)
            provider_scores[provider_id] = score

        # Return provider with highest score
        return max(provider_scores, key=provider_scores.get)

    async def _score_provider(self, provider_id: str, job_request: JobSubmissionRequest) -> float:
        """Score a provider based on cost, performance, reliability, etc."""
        provider = self.provider_registry.get_provider(provider_id)
        config = self.provider_registry.get_provider_config(provider_id)

        # Factor 1: Cost (lower is better)
        cost_estimate = await provider.estimate_job_cost(job_request.task_id, job_request.input_data)
        cost_score = 1.0 / (1.0 + cost_estimate.total_cost)

        # Factor 2: Historical reliability
        reliability_score = await self._get_provider_reliability_score(provider_id)

        # Factor 3: Performance (faster is better)
        performance_score = await self._get_provider_performance_score(provider_id, job_request.task_id)

        # Factor 4: Current load (lower load is better)
        load_score = await self._get_provider_load_score(provider_id)

        # Weighted combination
        total_score = (
            cost_score * 0.3 +
            reliability_score * 0.3 +
            performance_score * 0.2 +
            load_score * 0.2
        )

        return total_score
```

### **Failure Handling & Resilience**
```python
class FailureHandlingService:
    """Handles failures, retries, and fallback strategies."""

    async def handle_job_failure(self, job: MolecularJob, error: JobError) -> FailureHandlingResult:
        """Handle job failure with appropriate strategy."""

        # Determine failure type
        failure_type = self._classify_failure(error)

        # Apply handling strategy based on failure type
        if failure_type == FailureType.TRANSIENT_ERROR and job.can_be_retried():
            return await self._retry_job(job)
        elif failure_type == FailureType.PROVIDER_UNAVAILABLE:
            return await self._fallback_to_alternative_provider(job)
        elif failure_type == FailureType.RESOURCE_EXHAUSTED:
            return await self._schedule_for_later(job)
        else:
            return await self._mark_as_permanent_failure(job, error)

    async def _fallback_to_alternative_provider(self, job: MolecularJob) -> FailureHandlingResult:
        """Try to execute job on alternative provider."""
        alternative_providers = await self.provider_registry.find_providers_for_task(
            job.get_task_type()
        )

        # Remove current provider from alternatives
        current_provider = self._get_current_provider(job)
        alternative_providers = [p for p in alternative_providers if p != current_provider]

        if not alternative_providers:
            return FailureHandlingResult(
                action=FailureAction.PERMANENT_FAILURE,
                message="No alternative providers available"
            )

        # Select best alternative
        best_alternative = alternative_providers[0]  # Simplified selection

        # Submit to alternative provider
        try:
            await self.job_manager.resubmit_job(job, best_alternative)
            return FailureHandlingResult(
                action=FailureAction.FALLBACK_SUCCESS,
                message=f"Job resubmitted to provider {best_alternative}"
            )
        except Exception as e:
            return FailureHandlingResult(
                action=FailureAction.FALLBACK_FAILED,
                message=f"Fallback failed: {str(e)}"
            )
```

---

## 📊 **Implementation Roadmap**

### **Phase 0: API Interface Design (Week 1) - FOUNDATION FIRST**
**Priority: Critical - All subsequent development depends on this**

#### **0.1 Unified API Contract Definition**
- [ ] **REST API Specification**: Define OpenAPI 3.0 specification for all molecular tasks
- [ ] **Request/Response Models**: Standardized Pydantic models for all operations
- [ ] **Error Handling Schema**: Consistent error response format across all services
- [ ] **Authentication & Authorization**: JWT-based org-scoped access patterns
- [ ] **API Versioning Strategy**: Future-proof versioning for backward compatibility

#### **0.2 Core API Endpoints Design**
```python
# Unified Molecular Analysis API - Target Interface

# Task Discovery & Information
GET    /api/v1/tasks                           # List all available molecular tasks
GET    /api/v1/tasks/{task_id}                 # Get specific task details
GET    /api/v1/tasks/categories                # Get task categories and taxonomy

# Provider Management (Admin/Root)
GET    /api/v1/providers                       # List available service providers
POST   /api/v1/providers                       # Register new provider
PUT    /api/v1/providers/{provider_id}         # Update provider configuration
DELETE /api/v1/providers/{provider_id}         # Remove provider

# Organization Provider Configuration
GET    /api/v1/org/providers                   # List org-enabled providers
POST   /api/v1/org/providers/{provider_id}     # Enable provider for organization
PUT    /api/v1/org/providers/{provider_id}/credentials  # Update org credentials
DELETE /api/v1/org/providers/{provider_id}     # Disable provider for organization

# Unified Job Management
POST   /api/v1/jobs                           # Submit any molecular analysis job
GET    /api/v1/jobs                           # List user's jobs with filtering
GET    /api/v1/jobs/{job_id}                  # Get job details and status
GET    /api/v1/jobs/{job_id}/results          # Get job results
GET    /api/v1/jobs/{job_id}/logs             # Get execution logs
DELETE /api/v1/jobs/{job_id}                  # Cancel job
POST   /api/v1/jobs/{job_id}/retry            # Retry failed job

# Pipeline Management
POST   /api/v1/pipelines                      # Create pipeline from tasks
GET    /api/v1/pipelines                      # List user's pipelines
GET    /api/v1/pipelines/{pipeline_id}        # Get pipeline definition
POST   /api/v1/pipelines/{pipeline_id}/execute # Execute pipeline
GET    /api/v1/pipelines/templates            # Get pipeline templates

# File Management & Results
POST   /api/v1/files/upload                   # Upload molecular files
GET    /api/v1/files/{file_id}               # Download file
GET    /api/v1/jobs/{job_id}/files/{filename} # Download job result file
POST   /api/v1/files/{file_id}/convert       # Convert file format

# Real-time Updates
WebSocket /ws/jobs/{job_id}/status            # Real-time job status updates
```

#### **0.3 Request/Response Schema Design**
```python
# Core API Models - Contract Definition

class TaskSubmissionRequest(BaseModel):
    """Universal request model for any molecular analysis task."""
    task_id: str
    task_parameters: Dict[str, Any]
    input_files: List[FileReference]
    job_config: JobConfiguration
    pipeline_context: Optional[PipelineContext] = None

class JobConfiguration(BaseModel):
    """Job execution configuration."""
    priority: JobPriority = JobPriority.NORMAL
    timeout_minutes: Optional[int] = None
    provider_preference: Optional[str] = None  # Force specific provider
    cost_limit: Optional[float] = None
    notification_settings: NotificationSettings

class TaskSubmissionResponse(BaseModel):
    """Response for job submission."""
    job_id: UUID
    estimated_completion_time: datetime
    estimated_cost: float
    selected_provider: str
    queue_position: Optional[int]

class JobStatusResponse(BaseModel):
    """Job status information."""
    job_id: UUID
    status: JobStatus
    progress_percentage: float
    current_stage: str
    estimated_completion: Optional[datetime]
    resource_usage: ResourceUsage
    cost_so_far: float
    error_details: Optional[ErrorDetails]

class JobResultsResponse(BaseModel):
    """Job results information."""
    job_id: UUID
    completion_time: datetime
    results: Dict[str, Any]
    output_files: List[FileReference]
    quality_metrics: Dict[str, float]
    execution_summary: ExecutionSummary
```

#### **0.4 Error Handling & Status Codes**
```python
# Standardized Error Response Format
class APIErrorResponse(BaseModel):
    error_code: str           # VALIDATION_ERROR, PROVIDER_ERROR, etc.
    error_type: str          # CLIENT_ERROR, SERVER_ERROR, PROVIDER_ERROR
    message: str             # Human-readable message
    details: Dict[str, Any]  # Detailed error information
    request_id: str          # For debugging and support
    suggestions: List[str]   # Actionable suggestions for user

# HTTP Status Code Standards
200 OK                    # Successful operation
202 Accepted             # Job submitted successfully
400 Bad Request          # Invalid request format/parameters
401 Unauthorized         # Authentication required
403 Forbidden            # Insufficient permissions
404 Not Found           # Resource doesn't exist
409 Conflict            # Resource conflict (e.g., duplicate job)
422 Unprocessable Entity # Validation failed
429 Too Many Requests   # Rate limit exceeded
500 Internal Server Error # Server-side error
502 Bad Gateway         # Provider service error
503 Service Unavailable # Provider temporarily unavailable
```

#### **0.5 API Documentation & Testing**
- [ ] **Interactive API Documentation**: Auto-generated Swagger/OpenAPI docs
- [ ] **API Testing Suite**: Comprehensive test cases for all endpoints
- [ ] **Mock API Server**: For frontend development and testing
- [ ] **API Client Libraries**: Python and JavaScript/TypeScript clients
- [ ] **Postman Collection**: Ready-to-use API testing collection

### **Phase 3: Backend API Implementation (Week 2-3)**
**Prerequisites: Phase 3B Service Implementation must be complete**
**Build the unified API interface before any provider integration**

#### **1.1 FastAPI Application Structure**
```python
# API Routes Implementation - Contract Fulfillment
from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import StreamingResponse

app = FastAPI(
    title="Molecular Analysis API",
    version="1.0.0",
    description="Unified API for molecular analysis tasks"
)

@app.post("/api/v1/jobs", response_model=TaskSubmissionResponse)
async def submit_job(
    request: TaskSubmissionRequest,
    current_user: User = Depends(get_current_user),
    job_manager: JobManager = Depends(get_job_manager)
):
    """Submit any molecular analysis job through unified interface."""

    # Validate request against task schema
    validation_result = await validate_task_request(request)
    if not validation_result.is_valid:
        raise HTTPException(
            status_code=422,
            detail=APIErrorResponse(
                error_code="VALIDATION_ERROR",
                error_type="CLIENT_ERROR",
                message="Invalid task parameters",
                details=validation_result.errors,
                request_id=generate_request_id(),
                suggestions=validation_result.suggestions
            )
        )

    # Submit job through universal job manager
    try:
        job = await job_manager.submit_job(request, current_user)

        return TaskSubmissionResponse(
            job_id=job.job_id,
            estimated_completion_time=job.estimated_completion,
            estimated_cost=job.estimated_cost,
            selected_provider=job.selected_provider,
            queue_position=job.queue_position
        )

    except ProviderError as e:
        raise HTTPException(
            status_code=502,
            detail=APIErrorResponse(
                error_code="PROVIDER_ERROR",
                error_type="PROVIDER_ERROR",
                message=f"Provider service error: {e.message}",
                details={"provider": e.provider_id, "error": str(e)},
                request_id=generate_request_id(),
                suggestions=["Try again later", "Use different provider"]
            )
        )

@app.get("/api/v1/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(
    job_id: UUID,
    current_user: User = Depends(get_current_user),
    job_manager: JobManager = Depends(get_job_manager)
):
    """Get unified job status regardless of provider."""
    job = await job_manager.get_job_with_status(job_id, current_user)

    return JobStatusResponse(
        job_id=job.job_id,
        status=job.status,
        progress_percentage=job.progress_percentage,
        current_stage=job.current_stage,
        estimated_completion=job.estimated_completion,
        resource_usage=job.resource_usage,
        cost_so_far=job.cost_tracking.total_cost,
        error_details=job.error_details
    )
```

#### **1.2 Unified Job Manager Interface**
```python
# Job Manager - Implements the unified API contract
class UniversalJobManager:
    """Implements the unified API contract for all molecular tasks."""

    async def submit_job(
        self,
        request: TaskSubmissionRequest,
        user: User
    ) -> MolecularJob:
        """Universal job submission matching API contract."""

        # 1. Task Discovery & Validation
        task_definition = await self.task_registry.get_task(request.task_id)
        if not task_definition:
            raise TaskNotFoundError(f"Task {request.task_id} not supported")

        # 2. Provider Selection & Optimization
        optimal_provider = await self.provider_selector.select_optimal_provider(
            task_definition,
            request.task_parameters,
            user_preferences=request.job_config.provider_preference,
            cost_limit=request.job_config.cost_limit
        )

        # 3. Parameter Transformation
        provider_parameters = await self.parameter_transformer.transform(
            task_definition,
            request.task_parameters,
            optimal_provider
        )

        # 4. Job Creation & Submission
        job = MolecularJob.create_from_api_request(request, user, optimal_provider)
        provider_job_id = await optimal_provider.submit_job(
            task_definition.provider_task_id,
            provider_parameters
        )

        job.provider_job_id = provider_job_id
        job.status = JobStatus.SUBMITTED

        return await self.job_repository.save(job)

    async def get_job_with_status(self, job_id: UUID, user: User) -> JobWithStatus:
        """Get job status matching API contract."""

        job = await self.job_repository.get_by_id_and_user(job_id, user.id)
        if not job:
            raise JobNotFoundError(f"Job {job_id} not found")

        # Fetch real-time status from provider
        if job.status in [JobStatus.RUNNING, JobStatus.SUBMITTED]:
            provider_status = await self._get_provider_status(job)
            job = await self._update_job_from_provider_status(job, provider_status)

        return JobWithStatus(
            job=job,
            progress_percentage=self._calculate_progress(job),
            current_stage=self._determine_current_stage(job),
            estimated_completion=self._estimate_completion_time(job)
        )
```

#### **1.3 Mock Provider Implementation**
```python
# Mock Provider - For API testing before real providers are ready
class MockMolecularProvider(ServiceProviderAdapter):
    """Mock provider implementing the standard interface for testing."""

    def __init__(self):
        self.mock_jobs: Dict[str, MockJob] = {}

    async def submit_job(
        self,
        task_id: str,
        input_data: TaskInput,
        job_config: JobConfig
    ) -> JobSubmissionResult:
        """Mock job submission for API testing."""

        mock_job_id = f"mock_{uuid4().hex[:8]}"

        # Simulate different task types with appropriate delays
        if "docking" in task_id.lower():
            estimated_time = timedelta(minutes=random.randint(5, 15))
        elif "structure_prediction" in task_id.lower():
            estimated_time = timedelta(minutes=random.randint(10, 30))
        else:
            estimated_time = timedelta(minutes=random.randint(2, 8))

        mock_job = MockJob(
            job_id=mock_job_id,
            task_id=task_id,
            status="submitted",
            estimated_completion=datetime.utcnow() + estimated_time,
            progress=0.0
        )

        self.mock_jobs[mock_job_id] = mock_job

        # Start background task to simulate job progress
        asyncio.create_task(self._simulate_job_progress(mock_job_id))

        return JobSubmissionResult(
            provider_job_id=mock_job_id,
            estimated_completion_time=mock_job.estimated_completion,
            queue_position=random.randint(0, 5)
        )
```

### **Phase 4: Adapter Framework Implementation (Week 3-4)**
**Build adapters to match providers to our unified API**

#### **2.1 Provider Adapter Interface**
```python
# Standard interface that all providers must implement to match our API
class ServiceProviderAdapter(ABC):
    """Interface that adapts any provider to our unified API contract."""

    @abstractmethod
    async def submit_job(
        self,
        internal_task_id: str,
        unified_parameters: Dict[str, Any],
        job_config: JobConfiguration
    ) -> JobSubmissionResult:
        """
        Adapt our unified API request to provider-specific format.
        This method must transform our standard request into whatever
        format the provider expects.
        """
        pass

    @abstractmethod
    async def get_job_status(self, provider_job_id: str) -> UnifiedJobStatus:
        """
        Adapt provider's status response to our unified format.
        Must return status information that matches our API contract.
        """
        pass

    @abstractmethod
    async def get_job_results(self, provider_job_id: str) -> UnifiedJobResults:
        """
        Adapt provider's results to our unified format.
        Must transform provider outputs to match our API response schema.
        """
        pass

# Concrete Implementation for Neurosnap
class NeurosnapProviderAdapter(ServiceProviderAdapter):
    """Adapts Neurosnap API to our unified interface."""

    async def submit_job(
        self,
        internal_task_id: str,
        unified_parameters: Dict[str, Any],
        job_config: JobConfiguration
    ) -> JobSubmissionResult:

        # Transform our unified request to Neurosnap format
        neurosnap_request = self._transform_to_neurosnap_format(
            internal_task_id,
            unified_parameters
        )

        # Call Neurosnap API
        response = await self.neurosnap_client.submit_job(neurosnap_request)

        # Transform Neurosnap response to our unified format
        return JobSubmissionResult(
            provider_job_id=response.job_id,
            estimated_completion_time=self._parse_neurosnap_eta(response),
            queue_position=response.get("queue_position")
        )

    def _transform_to_neurosnap_format(
        self,
        internal_task_id: str,
        unified_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Transform our unified parameters to Neurosnap's expected format."""

        # Task-specific transformations
        if internal_task_id == "alphafold3_structure_prediction":
            return {
                "Input Sequences": json.dumps({
                    "aa": {"port1": unified_params["protein_sequence"]}
                }),
                "Model Version": unified_params.get("model_version", "Boltz-1x")
                # ... more field mappings
            }
        elif internal_task_id == "gnina_docking":
            return {
                "Input Receptor": self._format_receptor_data(unified_params["receptor"]),
                "Input Ligand": self._format_ligand_data(unified_params["ligand"])
                # ... more field mappings
            }
        else:
            raise UnsupportedTaskError(f"Task {internal_task_id} not supported by Neurosnap")
```

### **Phase 5: Domain Implementation (Week 4-5)**
**Build domain layer to support the API contract**

#### **3.1 Task Registry Service**
```python
class TaskRegistryService:
    """Manages available molecular analysis tasks for the API."""

    async def list_available_tasks(self, filters: Optional[Dict[str, Any]] = None) -> List[TaskInfo]:
        """Implementation for GET /api/v1/tasks endpoint."""

        all_tasks = []

        # Aggregate tasks from all registered providers
        for provider in self.provider_registry.get_all_providers():
            provider_tasks = await provider.list_available_tasks()

            # Transform to unified task format for API
            for task in provider_tasks:
                unified_task = TaskInfo(
                    task_id=self._generate_internal_task_id(provider.id, task.id),
                    name=task.name,
                    description=task.description,
                    category=self._map_to_standard_category(task.category),
                    provider_name=provider.name,
                    estimated_cost_range=task.cost_range,
                    typical_runtime=task.runtime_estimate,
                    input_requirements=self._standardize_input_schema(task.input_schema),
                    output_format=self._standardize_output_schema(task.output_schema)
                )

                all_tasks.append(unified_task)

        # Apply filters if provided
        if filters:
            all_tasks = self._apply_task_filters(all_tasks, filters)

        return all_tasks
```

### **Phase 6: Provider Integration (Week 5-6)**
**Integrate actual providers using the established adapter pattern**

This phase focuses on implementing specific provider adapters that conform to the unified API interface established in Phase 3.

**Dependencies:**
- Phase 3B Service Implementation must be complete
- Phase 3C Security Framework should be in progress
- Unified API contract from Phase 0 must be implemented

---

## 🎯 **API-First Benefits**

### **1. Contract-Driven Development**
- **Frontend Development**: Can start immediately with API contract
- **Testing**: Comprehensive API testing before provider integration
- **Documentation**: Clear API documentation from day one
- **Client Libraries**: Auto-generated clients from OpenAPI spec

### **2. Provider Independence**
- **Unified Interface**: Same API regardless of underlying provider
- **Easy Provider Swapping**: Change providers without API changes
- **Multi-Provider Support**: Use different providers seamlessly
- **Provider Competition**: Compare providers objectively

### **3. Development Efficiency**
- **Parallel Development**: API, frontend, and providers can be built in parallel
- **Mock Testing**: Full API testing with mock providers
- **Clear Contracts**: Eliminates ambiguity in implementation
- **Faster Integration**: Providers adapt to existing API vs custom integration

---

## 📋 **Revised Action Plan**

### **Immediate Next Steps (Phase 3B Dependency)**
1. **Complete Phase 3B Service Implementation**: Must be finished before API contract implementation
   - API Port Exposure Fix
   - Basic Task Execution endpoints
   - Gateway Integration
   - Service Discovery Setup

### **Integration Plan Execution (After Phase 3B)**
1. **API Contract Review**: Review and approve the unified API design
2. **OpenAPI Specification**: Create detailed OpenAPI 3.0 specification
3. **Mock Implementation**: Build mock API server for immediate testing
4. **Frontend Planning**: Begin frontend development against API contract
5. **Provider Adapter Planning**: Design adapter interface for providers

### **Phase Dependencies**
- **Phase 3B** → **Integration Phase 0**: Service layer required for API implementation
- **Integration Phase 0** → **Integration Phase 3**: API contract required for backend implementation
- **Integration Phase 3** → **Integration Phase 4**: Backend API required for adapter framework
- **Phase 3C** → **Integration Phase 6**: Security framework needed for production provider integration

---

**This framework provides the solid foundation you requested, with clear domain definitions, standardized provider integration patterns, and comprehensive service management capabilities.**

---

## 🎯 **Integration Objectives**

### **Primary Goals**
1. **Generic Service Framework**: Create a template-driven system for integrating any REST API-based molecular service
2. **Zero-Code Integration**: Allow root users to add new services through JSON configuration files only
3. **Dynamic Task Registration**: Runtime discovery and registration of external service capabilities
4. **Universal Adapter Pattern**: Single generic adapter that handles any HTTP-based molecular service
5. **Template-Based Workflows**: Define service interactions through declarative templates

### **Business Value**
- **Future-Proof Integration**: Add any new molecular service without development cycles
- **Rapid Service Adoption**: Integrate new services in minutes, not months
- **Cost Efficiency**: Eliminate custom development for each external service
- **Competitive Advantage**: Quickly adopt new AI/ML services as they emerge
- **Developer Productivity**: Focus on core platform features instead of service integrations

---

## 🏗️ **Configuration-Driven Architecture**

### **Service Template Structure**

```json
{
  "service_id": "neurosnap-alphafold3",
  "display_name": "AlphaFold3 Structure Prediction",
  "provider": "neurosnap",
  "category": "structure_prediction",
  "version": "1.0.0",
  "description": "AI-powered protein structure prediction with ligand support",
  "api_config": {
    "base_url": "https://neurosnap.ai",
    "auth_type": "api_key",
    "auth_header": "X-API-KEY",
    "content_type": "multipart/form-data",
    "timeout": 300,
    "retry_attempts": 3
  },
  "endpoints": {
    "submit": {
      "method": "POST",
      "path": "/api/job/submit/{service_name}",
      "query_params": {
        "note": "{job_note}"
      }
    },
    "status": {
      "method": "GET",
      "path": "/api/job/status/{job_id}"
    },
    "results": {
      "method": "GET",
      "path": "/api/job/files/{job_id}/out"
    },
    "download": {
      "method": "GET",
      "path": "/api/job/file/{job_id}/out/{filename}"
    }
  },
  "tasks": [
    {
      "task_id": "alphafold3-structure-prediction",
      "display_name": "Protein Structure Prediction",
      "description": "Generate 3D protein structure from amino acid sequence",
      "service_name": "Boltz-1 (AlphaFold3)",
      "input_schema": {
        "sequence_data": {
          "type": "object",
          "required": true,
          "description": "Amino acid sequence data",
          "mapping": {
            "field_name": "Input Sequences",
            "format": "json",
            "template": "{\"aa\": {{sequence_data}}}"
          }
        },
        "model_version": {
          "type": "string",
          "required": false,
          "default": "Boltz-1x (with potentials)",
          "options": ["Boltz-1x (with potentials)", "Boltz-1x"],
          "mapping": {
            "field_name": "Model Version"
          }
        },
        "ligand_file": {
          "type": "file",
          "required": false,
          "formats": ["sdf", "mol2", "pdb"],
          "mapping": {
            "field_name": "Input Molecules",
            "format": "json",
            "template": "[{\"type\": \"{{file_format}}\", \"data\": \"{{file_content}}\"}]"
          }
        }
      },
      "output_schema": {
        "structure_file": {
          "type": "file",
          "format": "pdb",
          "description": "Predicted protein structure"
        },
        "confidence_scores": {
          "type": "file",
          "format": "json",
          "description": "Per-residue confidence scores"
        }
      },
      "parameter_mapping": {
        "msa_mode": {
          "field_name": "MSA Mode",
          "default": "mmseqs2_uniref_env"
        },
        "num_recycles": {
          "field_name": "Number Recycles",
          "type": "string",
          "default": "6"
        }
      }
    }
  ]
}
```

### **Generic Adapter Framework**

Instead of service-specific adapters, we create a **single generic adapter** that interprets JSON templates:

---

## 🔧 **Clean Architecture Implementation**

### **Domain Layer - Generic Entities**

#### **Dynamic Service & Task Entities**

```python
# src/molecular_analysis_dashboard/domain/entities/external_service.py
@dataclass
class ExternalService:
    """Generic external service entity - template-driven."""

    service_id: str
    display_name: str
    provider: str
    category: str  # structure_prediction, docking, protein_design, etc.
    version: str
    description: str
    api_config: ServiceApiConfig
    tasks: List[ExternalTask]
    org_id: UUID
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class ServiceApiConfig:
    """API configuration from template."""
    base_url: str
    auth_type: str  # api_key, bearer, basic
    auth_header: str
    content_type: str
    timeout: int
    retry_attempts: int
    endpoints: Dict[str, EndpointConfig]

@dataclass
class ExternalTask:
    """Generic task definition from template."""
    task_id: str
    display_name: str
    description: str
    service_name: str  # External service's task name
    input_schema: Dict[str, InputParameter]
    output_schema: Dict[str, OutputParameter]
    parameter_mapping: Dict[str, ParameterMapping]

@dataclass
class InputParameter:
    """Dynamic input parameter definition."""
    type: str  # string, file, object, array
    required: bool
    description: str
    default: Optional[Any] = None
    options: Optional[List[str]] = None
    formats: Optional[List[str]] = None  # For file types
    mapping: FieldMapping = None

@dataclass
class FieldMapping:
    """Maps internal parameters to external API fields."""
    field_name: str
    format: str  # direct, json, template
    template: Optional[str] = None  # Jinja2 template for complex mapping
```

#### **Generic Job Execution Entity**

```python
# src/molecular_analysis_dashboard/domain/entities/dynamic_job.py
@dataclass
class DynamicJob:
    """Generic external job execution."""

    job_id: UUID
    external_job_id: str
    service_id: str
    task_id: str
    org_id: UUID
    user_id: UUID
    status: JobStatus
    input_parameters: Dict[str, Any]
    output_results: Dict[str, Any] = field(default_factory=dict)
    execution_metadata: ExecutionMetadata = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    error_details: Optional[str] = None

    def is_completed(self) -> bool:
        return self.status in [JobStatus.COMPLETED, JobStatus.FAILED]

    def can_retry(self) -> bool:
        return self.status == JobStatus.FAILED and self.execution_metadata.retry_count < 3
```

### **Use Cases Layer - Generic Operations**

#### **Template-Driven Service Management**

```python
# src/molecular_analysis_dashboard/use_cases/commands/register_external_service.py
class RegisterExternalServiceCommand:
    """Register new external service from JSON template."""

    def __init__(
        self,
        service_repo: ExternalServiceRepositoryPort,
        template_validator: ServiceTemplateValidator,
        credential_manager: CredentialManagerPort
    ):
        self.service_repo = service_repo
        self.template_validator = template_validator
        self.credential_manager = credential_manager

    async def execute(self, request: RegisterServiceRequest) -> ExternalService:
        # 1. Validate JSON template structure
        template = await self.template_validator.validate(request.template)

        # 2. Create service entity from template
        service = ExternalService.from_template(template, request.org_id)

        # 3. Encrypt and store credentials
        if request.credentials:
            service.api_config.credentials = await self.credential_manager.encrypt(
                request.credentials, request.org_id
            )

        # 4. Test service connectivity
        await self._test_service_connectivity(service)

        # 5. Persist service
        return await self.service_repo.save(service)

# src/molecular_analysis_dashboard/use_cases/commands/execute_dynamic_task.py
class ExecuteDynamicTaskCommand:
    """Execute any external task using generic adapter."""

    def __init__(
        self,
        service_repo: ExternalServiceRepositoryPort,
        job_repo: DynamicJobRepositoryPort,
        generic_adapter: GenericExternalServicePort,
        parameter_mapper: ParameterMapperService
    ):
        self.service_repo = service_repo
        self.job_repo = job_repo
        self.generic_adapter = generic_adapter
        self.parameter_mapper = parameter_mapper

    async def execute(self, request: ExecuteTaskRequest) -> DynamicJob:
        # 1. Load service and task configuration
        service = await self.service_repo.get_by_id(request.service_id)
        task = service.get_task(request.task_id)

        # 2. Map input parameters using template
        external_parameters = await self.parameter_mapper.map_parameters(
            task, request.input_parameters
        )

        # 3. Create job entity
        job = DynamicJob(
            job_id=uuid4(),
            service_id=request.service_id,
            task_id=request.task_id,
            org_id=request.org_id,
            user_id=request.user_id,
            status=JobStatus.CREATED,
            input_parameters=request.input_parameters
        )

        # 4. Submit to external service
        external_job_id = await self.generic_adapter.submit_job(
            service.api_config,
            task.service_name,
            external_parameters
        )

        # 5. Update and persist job
        job.external_job_id = external_job_id
        job.status = JobStatus.SUBMITTED

        return await self.job_repo.save(job)
```

### **Ports Layer - Generic Interfaces**

```python
# src/molecular_analysis_dashboard/ports/external/generic_external_service_port.py
class GenericExternalServicePort(ABC):
    """Generic port for any HTTP-based external service."""

    @abstractmethod
    async def submit_job(
        self,
        api_config: ServiceApiConfig,
        service_name: str,
        parameters: Dict[str, Any]
    ) -> str:
        """Submit job using service configuration template."""
        pass

    @abstractmethod
    async def get_job_status(
        self,
        api_config: ServiceApiConfig,
        job_id: str
    ) -> JobStatus:
        """Get job status using service configuration."""
        pass

    @abstractmethod
    async def get_job_results(
        self,
        api_config: ServiceApiConfig,
        job_id: str
    ) -> Dict[str, Any]:
        """Get job results using service configuration."""
        pass

    @abstractmethod
    async def test_connectivity(
        self,
        api_config: ServiceApiConfig
    ) -> bool:
        """Test service connectivity and credentials."""
        pass

# src/molecular_analysis_dashboard/ports/services/parameter_mapper_port.py
class ParameterMapperPort(ABC):
    """Maps internal parameters to external service format."""

    @abstractmethod
    async def map_parameters(
        self,
        task: ExternalTask,
        input_parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Map parameters using task template."""
        pass

    @abstractmethod
    async def map_results(
        self,
        task: ExternalTask,
        external_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Map external results to internal format."""
        pass
```

### **Adapters Layer - Generic Implementation**

```python
# src/molecular_analysis_dashboard/adapters/external/generic_http_adapter.py
class GenericHttpAdapter(GenericExternalServicePort):
    """Universal HTTP adapter for any REST API service."""

    def __init__(self):
        self.session = aiohttp.ClientSession()

    async def submit_job(
        self,
        api_config: ServiceApiConfig,
        service_name: str,
        parameters: Dict[str, Any]
    ) -> str:
        # Build endpoint URL
        endpoint = api_config.endpoints["submit"]
        url = self._build_url(api_config.base_url, endpoint.path, {
            "service_name": service_name
        })

        # Build headers
        headers = self._build_headers(api_config, parameters.get("credentials"))

        # Build request data based on content type
        data = await self._build_request_data(api_config.content_type, parameters)

        # Make request with retry logic
        async with self.session.request(
            endpoint.method,
            url,
            headers=headers,
            data=data,
            timeout=api_config.timeout
        ) as response:
            response.raise_for_status()
            return await self._extract_job_id(response)

    def _build_url(self, base_url: str, path_template: str, variables: Dict[str, str]) -> str:
        """Build URL from template and variables."""
        path = path_template.format(**variables)
        return f"{base_url}{path}"

    def _build_headers(self, api_config: ServiceApiConfig, credentials: Dict[str, str]) -> Dict[str, str]:
        """Build headers from configuration."""
        headers = {}

        if api_config.auth_type == "api_key":
            headers[api_config.auth_header] = credentials.get("api_key")
        elif api_config.auth_type == "bearer":
            headers["Authorization"] = f"Bearer {credentials.get('token')}"

        return headers

    async def _build_request_data(self, content_type: str, parameters: Dict[str, Any]) -> Any:
        """Build request data based on content type."""
        if content_type == "multipart/form-data":
            return MultipartEncoder(fields=parameters.get("fields", {}))
        elif content_type == "application/json":
            return json.dumps(parameters.get("json_data", {}))
        else:
            return parameters.get("raw_data")

# src/molecular_analysis_dashboard/adapters/services/jinja_parameter_mapper.py
class JinjaParameterMapper(ParameterMapperPort):
    """Parameter mapper using Jinja2 templates."""

    def __init__(self):
        self.jinja_env = Environment()

    async def map_parameters(
        self,
        task: ExternalTask,
        input_parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Map parameters using Jinja2 templates from task definition."""
        mapped_fields = {}

        for param_name, param_value in input_parameters.items():
            if param_name in task.input_schema:
                param_def = task.input_schema[param_name]
                mapping = param_def.mapping

                if mapping.format == "direct":
                    mapped_fields[mapping.field_name] = param_value
                elif mapping.format == "json":
                    mapped_fields[mapping.field_name] = json.dumps(param_value)
                elif mapping.format == "template":
                    template = self.jinja_env.from_string(mapping.template)
                    mapped_fields[mapping.field_name] = template.render(**{
                        param_name: param_value,
                        **input_parameters
                    })

        # Add parameter mapping from task definition
        for param_name, mapping in task.parameter_mapping.items():
            if param_name in input_parameters:
                value = input_parameters[param_name]
                if mapping.type == "string":
                    value = str(value)
                mapped_fields[mapping.field_name] = value
            elif "default" in mapping:
                mapped_fields[mapping.field_name] = mapping.default

        return {"fields": mapped_fields}
```

### **Infrastructure Layer - Template Management**

```python
# src/molecular_analysis_dashboard/infrastructure/services/template_loader.py
class ServiceTemplateLoader:
    """Loads and manages service templates."""

    def __init__(self, template_dir: str = "service_templates"):
        self.template_dir = Path(template_dir)

    async def load_template(self, service_id: str) -> Dict[str, Any]:
        """Load service template from JSON file."""
        template_path = self.template_dir / f"{service_id}.json"

        if not template_path.exists():
            raise TemplateNotFoundError(f"Template not found: {service_id}")

        with open(template_path) as f:
            return json.load(f)

    async def validate_template(self, template: Dict[str, Any]) -> bool:
        """Validate template structure using JSON schema."""
        # Load JSON schema for service templates
        schema = await self._load_template_schema()

        try:
            jsonschema.validate(template, schema)
            return True
        except jsonschema.ValidationError as e:
            raise InvalidTemplateError(f"Template validation failed: {e.message}")

    async def list_templates(self) -> List[str]:
        """List all available template IDs."""
        return [
            f.stem for f in self.template_dir.glob("*.json")
            if f.is_file()
        ]
```

---

## 📋 **Implementation Phases**

### **Phase 1: Generic Framework Foundation (Week 1)**

#### **1.1 Template Schema Definition**
- [ ] Define JSON schema for service templates
- [ ] Create validation rules for task definitions
- [ ] Design parameter mapping DSL (Domain Specific Language)
- [ ] Create template versioning system

#### **1.2 Domain Layer Implementation**
- [ ] Create generic `ExternalService` and `DynamicJob` entities
- [ ] Implement template-based service factory
- [ ] Define generic job lifecycle management
- [ ] Create extensible parameter validation

#### **1.3 Core Infrastructure**
- [ ] Design database schema for dynamic services
- [ ] Create template storage and versioning system
- [ ] Implement credential encryption for any auth method
- [ ] Set up configuration management

### **Phase 2: Generic Adapter & Processing Engine (Week 2)**

#### **2.1 Universal HTTP Adapter**
- [ ] Implement `GenericHttpAdapter` for any REST API
- [ ] Create flexible authentication handlers (API key, Bearer, Basic, Custom)
- [ ] Build dynamic request/response processing
- [ ] Add retry logic and error handling

#### **2.2 Template Processing Engine**
- [ ] Implement Jinja2 parameter mapping system
- [ ] Create file format conversion utilities
- [ ] Build dynamic request building from templates
- [ ] Add response parsing and result extraction

#### **2.3 Service Registry & Discovery**
- [ ] Create runtime service registration system
- [ ] Build template validation and loading
- [ ] Implement service capability discovery
- [ ] Add template testing and verification

### **Phase 3: Management Interface (Week 3)**

#### **3.1 Root User Admin Interface**
```typescript
interface ServiceTemplate {
  service_id: string;
  display_name: string;
  provider: string;
  category: string;
  api_config: ApiConfig;
  tasks: TaskDefinition[];
}

// Admin components for root users
- ServiceTemplateEditor: Visual template creation/editing
- ServiceTestRunner: Test templates against live APIs
- ParameterMappingBuilder: Visual parameter mapping interface
- CredentialManager: Secure credential storage per organization
```

#### **3.2 REST API for Template Management**
- [ ] `POST /api/v1/admin/service-templates` - Upload new service template
- [ ] `GET /api/v1/admin/service-templates` - List available templates
- [ ] `PUT /api/v1/admin/service-templates/{id}` - Update template
- [ ] `POST /api/v1/admin/service-templates/{id}/test` - Test template
- [ ] `POST /api/v1/organizations/{org_id}/external-services` - Enable service for org

#### **3.3 Organization Service Management**
- [ ] Enable/disable services per organization
- [ ] Configure organization-specific credentials
- [ ] Set usage limits and quotas per service
- [ ] Monitor service usage and costs

### **Phase 4: Integration & Testing (Week 4)**

#### **4.1 Template Examples & Testing**
- [ ] Create Neurosnap service template (AlphaFold3, GNINA, ProteinMPNN)
- [ ] Create additional example templates (ChemAxon, Schrödinger, etc.)
- [ ] Comprehensive testing with real API endpoints
- [ ] Performance optimization for template processing

#### **4.2 Documentation & Training**
- [ ] Template creation guide for root users
- [ ] Parameter mapping documentation
- [ ] Service integration best practices
- [ ] Troubleshooting guide for template issues

---

## 🗃️ **Service Template Examples**

### **Neurosnap AlphaFold3 Template** (Complete Example)

```json
{
  "service_id": "neurosnap-alphafold3",
  "display_name": "AlphaFold3 Structure Prediction",
  "provider": "neurosnap",
  "category": "structure_prediction",
  "version": "1.0.0",
  "description": "AI-powered protein structure prediction with ligand support",
  "tags": ["protein_structure", "ai_prediction", "alphafold"],
  "api_config": {
    "base_url": "https://neurosnap.ai",
    "auth_type": "api_key",
    "auth_header": "X-API-KEY",
    "content_type": "multipart/form-data",
    "timeout": 300,
    "retry_attempts": 3,
    "endpoints": {
      "submit": {
        "method": "POST",
        "path": "/api/job/submit/{service_name}",
        "query_params": {"note": "{job_note}"}
      },
      "status": {
        "method": "GET",
        "path": "/api/job/status/{job_id}",
        "response_mapping": {
          "status_field": "."
        }
      },
      "results": {
        "method": "GET",
        "path": "/api/job/files/{job_id}/out"
      },
      "download": {
        "method": "GET",
        "path": "/api/job/file/{job_id}/out/{filename}"
      }
    }
  },
  "tasks": [
    {
      "task_id": "structure_prediction",
      "display_name": "Protein Structure Prediction",
      "description": "Generate 3D protein structure from amino acid sequence",
      "service_name": "Boltz-1 (AlphaFold3)",
      "estimated_runtime": "2-10 minutes",
      "cost_estimate": "$0.10-$0.50",
      "input_schema": {
        "protein_sequence": {
          "type": "string",
          "required": true,
          "description": "Amino acid sequence (FASTA format)",
          "validation": {
            "min_length": 10,
            "max_length": 10000,
            "pattern": "^[ACDEFGHIKLMNPQRSTVWY]+$"
          },
          "mapping": {
            "field_name": "Input Sequences",
            "format": "template",
            "template": "{\"aa\": {\"port1\": \"{{protein_sequence}}\"}}"
          }
        },
        "ligand_file": {
          "type": "file",
          "required": false,
          "description": "Optional ligand structure file",
          "formats": ["sdf", "mol2", "pdb"],
          "max_size": "10MB",
          "mapping": {
            "field_name": "Input Molecules",
            "format": "template",
            "template": "[{\"type\": \"{{file_format}}\", \"data\": \"{{file_content}}\"}]",
            "condition": "ligand_file is defined"
          }
        },
        "model_version": {
          "type": "select",
          "required": false,
          "default": "Boltz-1x (with potentials)",
          "options": [
            "Boltz-1x (with potentials)",
            "Boltz-1x"
          ],
          "mapping": {
            "field_name": "Model Version"
          }
        },
        "advanced_options": {
          "type": "object",
          "required": false,
          "properties": {
            "msa_mode": {
              "type": "select",
              "default": "mmseqs2_uniref_env",
              "options": ["mmseqs2_uniref_env", "single_sequence"]
            },
            "num_recycles": {
              "type": "integer",
              "default": 6,
              "min": 1,
              "max": 20
            },
            "sampling_steps": {
              "type": "integer",
              "default": 200,
              "min": 50,
              "max": 1000
            }
          },
          "mapping": {
            "MSA Mode": "{{advanced_options.msa_mode}}",
            "Number Recycles": "{{advanced_options.num_recycles}}",
            "Sampling Steps": "{{advanced_options.sampling_steps}}"
          }
        }
      },
      "output_schema": {
        "structure_file": {
          "type": "file",
          "format": "pdb",
          "description": "Predicted 3D protein structure",
          "filename_pattern": "predicted_structure.pdb"
        },
        "confidence_scores": {
          "type": "file",
          "format": "json",
          "description": "Per-residue confidence scores",
          "filename_pattern": "confidence_scores.json"
        },
        "visualization": {
          "type": "file",
          "format": "png",
          "description": "Structure visualization image",
          "filename_pattern": "structure_viz.png"
        }
      },
      "result_processing": {
        "success_indicators": ["predicted_structure.pdb"],
        "visualization_config": {
          "viewer": "3dmol",
          "default_style": "cartoon",
          "color_by": "confidence"
        }
      }
    }
  ],
  "webhooks": {
    "job_completion": {
      "enabled": true,
      "url_template": "{base_url}/api/v1/webhooks/external-job/{job_id}/complete"
    }
  }
}
```

### **Generic ChemAxon Template** (Extensibility Example)

```json
{
  "service_id": "chemaxon-calculator",
  "display_name": "ChemAxon Calculator Plugins",
  "provider": "chemaxon",
  "category": "molecular_properties",
  "version": "1.0.0",
  "api_config": {
    "base_url": "https://api.chemaxon.com",
    "auth_type": "bearer",
    "auth_header": "Authorization",
    "content_type": "application/json",
    "endpoints": {
      "submit": {
        "method": "POST",
        "path": "/v2/calculations"
      },
      "status": {
        "method": "GET",
        "path": "/v2/calculations/{job_id}/status"
      },
      "results": {
        "method": "GET",
        "path": "/v2/calculations/{job_id}/results"
      }
    }
  },
  "tasks": [
    {
      "task_id": "logp_calculation",
      "display_name": "LogP Calculation",
      "description": "Calculate lipophilicity (LogP) of molecules",
      "service_name": "logp",
      "input_schema": {
        "molecules": {
          "type": "array",
          "required": true,
          "items": {
            "type": "string",
            "description": "SMILES string"
          },
          "mapping": {
            "field_name": "structures",
            "format": "template",
            "template": "[{% for mol in molecules %}{\"structure\": \"{{mol}}\"}{% if not loop.last %},{% endif %}{% endfor %}]"
          }
        },
        "method": {
          "type": "select",
          "default": "KLOP",
          "options": ["KLOP", "PHYS", "USER"],
          "mapping": {
            "field_name": "parameters.method"
          }
        }
      }
    }
  ]
}
```

---

## 🔒 **Security & Governance**

### **Root User Template Management**
- **Template Validation**: Comprehensive JSON schema validation before activation
- **Security Scanning**: Automatic scanning of templates for security issues
- **Approval Workflow**: Optional approval process for new service templates
- **Version Control**: Full versioning and rollback capability for templates
- **Audit Logging**: Complete audit trail of template changes and usage

### **Organization-Level Security**
- **Service Access Control**: Granular control over which services each organization can access
- **Credential Isolation**: Strong encryption and isolation of API credentials per organization
- **Usage Monitoring**: Real-time monitoring of service usage and cost tracking
- **Rate Limiting**: Configurable rate limits per service per organization
- **Data Residency**: Control over where external job data is processed

### **Dynamic Security Validation**
```python
# Template security validation
class TemplateSecurityValidator:
    def validate_template(self, template: Dict[str, Any]) -> SecurityReport:
        issues = []

        # Check for dangerous template patterns
        if self._contains_code_injection(template):
            issues.append("Template contains potential code injection vectors")

        # Validate API endpoints
        if not self._validate_https_only(template):
            issues.append("Template allows non-HTTPS endpoints")

        # Check parameter sanitization
        if not self._has_input_validation(template):
            issues.append("Template lacks proper input validation")

        return SecurityReport(issues)
```

---

## 📊 **Monitoring & Analytics**

### **Template Performance Metrics**
- **Service Adoption**: Track which templates are most used across organizations
- **Success Rates**: Monitor job success/failure rates per template
- **Performance**: Track average execution times and resource usage
- **Cost Analysis**: Monitor external service costs per organization
- **Error Patterns**: Identify common failure patterns in templates

### **Real-time Dashboard**
```typescript
interface TemplateMetrics {
  service_id: string;
  total_jobs: number;
  success_rate: number;
  avg_runtime: number;
  total_cost: number;
  active_organizations: number;
  error_trends: ErrorTrend[];
}

// Root admin dashboard components
- TemplateUsageChart: Visual usage analytics
- ServiceHealthMonitor: Real-time service status
- CostAnalytics: Cost breakdown per service/org
- ErrorTrendAnalysis: Error pattern identification
```

---

## � **Integration Examples**

### **Adding New Service (Zero Code Required)**

**Step 1**: Root user creates template JSON file
**Step 2**: Upload via admin interface or API
**Step 3**: System validates and tests template
**Step 4**: Service becomes available to organizations
**Step 5**: Organizations configure credentials and enable service

```bash
# Example: Adding new service via CLI
curl -X POST /api/v1/admin/service-templates \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -F "template=@chemaxon-calculator.json" \
  -F "test_credentials=@test_creds.json"

# Response: Service tested and ready for deployment
{
  "service_id": "chemaxon-calculator",
  "status": "validated",
  "test_results": {
    "connectivity": "success",
    "authentication": "success",
    "sample_job": "success"
  },
  "deployment_status": "ready"
}
```

### **Organization Enablement Flow**

```typescript
// Organization admin enables service
const enableService = async (orgId: string, serviceId: string, credentials: Credentials) => {
  // 1. Validate organization permissions
  await validateOrgPermissions(orgId, 'manage_external_services');

  // 2. Encrypt and store credentials
  const encryptedCreds = await encryptCredentials(credentials, orgId);

  // 3. Test service connectivity
  const testResult = await testServiceConnection(serviceId, encryptedCreds);

  if (testResult.success) {
    // 4. Enable service for organization
    await enableExternalService(orgId, serviceId, encryptedCreds);
    return { status: 'enabled', service_id: serviceId };
  } else {
    throw new Error(`Service test failed: ${testResult.error}`);
  }
};
```

---

## 🎯 **Success Criteria**

### **Technical Success Metrics**
- **Template Flexibility**: Successfully integrate 5+ different service providers without code changes
- **Performance**: <2s template processing time, <500ms parameter mapping
- **Reliability**: 99.9% uptime for template processing system
- **Security**: Zero security incidents related to dynamic template processing

### **Business Success Metrics**
- **Integration Speed**: New services integrated in <1 hour vs previous 2-4 weeks
- **Developer Productivity**: 90% reduction in custom integration development time
- **Service Adoption**: 80% of organizations using external services within 6 months
- **Cost Efficiency**: 60% reduction in integration maintenance costs

### **User Experience Metrics**
- **Root User Experience**: Template creation in <30 minutes for experienced users
- **Organization Setup**: Service enablement in <5 minutes
- **Template Quality**: 95% of templates pass validation on first submission
- **Support Reduction**: 80% fewer support tickets related to service integrations

---

## 📋 **Next Steps & Implementation**

### **Immediate Actions (This Week)**
1. **Architecture Review**: Present flexible framework design to team
2. **Template Schema Design**: Finalize JSON schema for service templates
3. **Proof of Concept**: Build minimal template processor for Neurosnap example
4. **Security Analysis**: Review security implications of dynamic template execution

### **Phase 1 Kickoff (Next Week)**
1. **Generic Domain Modeling**: Create flexible entity framework
2. **Template Validation System**: Implement JSON schema validation with security checks
3. **Universal HTTP Adapter**: Build generic REST API adapter
4. **Database Schema**: Design schema for dynamic service storage

### **Long-term Vision**
- **Template Marketplace**: Community-driven template sharing platform
- **AI Template Generation**: AI-assisted template creation from API documentation
- **Template Analytics**: ML-powered optimization of templates based on usage patterns
- **Multi-Protocol Support**: Expand beyond HTTP to GraphQL, gRPC, WebSocket services

---

## 🎯 **Conclusion**

This **configuration-driven integration framework** transforms the Molecular Analysis Dashboard into a truly extensible platform where any REST API-based molecular service can be integrated through simple JSON templates. By eliminating the need for custom code for each service integration, we enable:

- **Rapid Innovation**: Quickly adopt new AI/ML services as they emerge
- **Cost Efficiency**: Eliminate development cycles for service integrations
- **Future-Proofing**: Handle unknown future services through flexible templates
- **Community Growth**: Enable the community to contribute service integrations

The framework maintains strict adherence to Clean Architecture while providing the flexibility needed for a rapidly evolving molecular analysis ecosystem.

**Next Step**: Begin proof-of-concept implementation with Neurosnap template as validation case.
