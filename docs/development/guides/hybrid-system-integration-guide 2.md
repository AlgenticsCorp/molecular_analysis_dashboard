# Hybrid System Integration Guide

**Version:** 1.0  
**Date:** November 11, 2025  
**Scope:** External Cloud + Domestic Container Service Integration

This guide documents how external (NeuroSnap) and domestic (containerized) services are integrated transparently through the unified Swagger API, with hybrid database and storage management.

## 🎯 **Core Principle: Provider Transparency**

**The frontend and API consumers see ONE unified interface**, regardless of whether services run externally (NeuroSnap cloud) or domestically (local containers).

```
Frontend ─── Swagger API ─── Provider Factory ─── External Adapter (NeuroSnap)
                                               └─── Domestic Adapter (Containers)
```

## 🏗️ **Architecture Pattern**

### **1. Provider Factory Pattern**
```python
# infrastructure/providers/provider_factory.py
class ServiceProviderFactory:
    """Factory for creating service providers based on configuration."""
    
    def __init__(self):
        self._providers = {
            "external": {
                "gnina": NeuroSnapGninaAdapter,
                "docking": NeuroSnapDockingAdapter,
                "folding": NeuroSnapFoldingAdapter,
            },
            "domestic": {
                "gnina": DomesticGninaAdapter,
                "docking": DomesticVinaAdapter,
                "folding": DomesticAlphaFoldAdapter,
            }
        }
    
    def create_provider(self, service_type: str, provider_type: str):
        """Create appropriate provider adapter."""
        adapter_class = self._providers[provider_type][service_type]
        return adapter_class()
```

### **2. Unified Service Interface**
```python
# ports/external/molecular_analysis_port.py
class MolecularAnalysisPort(ABC):
    """Unified interface for all molecular analysis services."""
    
    @abstractmethod
    async def submit_job(self, input_data: JobInput) -> str:
        """Submit job - works for external AND domestic services."""
        
    @abstractmethod  
    async def get_job_status(self, job_id: str) -> JobStatus:
        """Get status - unified across all providers."""
        
    @abstractmethod
    async def get_job_results(self, job_id: str) -> JobResults:
        """Get results - same interface regardless of provider."""
```

### **3. Transparent API Layer**
```python
# presentation/api/routes/unified_molecular_analysis.py
@router.post("/api/v1/providers/neurosnap/docking/submit")
async def submit_docking_job(request: DockingRequest):
    """Provider-aware docking endpoint for NeuroSnap integration."""
    
    # Use NeuroSnap provider explicitly
    provider_type = "neurosnap"
    
    # Create NeuroSnap adapter
    provider = provider_factory.create_provider("docking", provider_type)
    
    # Submit job using unified interface
    external_job_id = await provider.submit_job(request.to_job_input())
    
    # Store in hybrid database with provider information
    job = await job_repository.create_job(
        job_id=uuid4(),
        external_job_id=external_job_id,
        provider_type=provider_type,
        service_type="docking",
        inputs=request.inputs,
        org_id=request.org_id
    )
    
    return JobResponse(job_id=job.job_id, status="SUBMITTED")
```

## 📊 **Hybrid Database Integration**

### **Job Storage Pattern**
```python
# Database stores provider information transparently
class Job(Base):
    job_id: UUID = primary_key
    external_job_id: str  # Provider's job ID (NeuroSnap or container service)
    provider_type: str    # "external" or "domestic" 
    service_type: str     # "docking", "folding", "dynamics"
    provider_config: JSONB  # Provider-specific configuration
    
    # Inputs/outputs stored the same regardless of provider
    inputs: List[JobInput] = relationship(...)
    outputs: List[JobOutput] = relationship(...)
```

### **Input/Output Storage**
```python
# Unified storage regardless of provider
class JobInput(Base):
    job_id: UUID
    key: str        # "receptor_file", "ligand_file", "parameters"
    value: str      # File URI or parameter value
    input_type: str # "file", "parameter"
    
class JobOutput(Base):  
    job_id: UUID
    key: str        # "result_poses", "binding_scores", "log_file"
    uri: str        # Storage location (S3, local, etc.)
    content_type: str
    provider_source: str  # Which provider generated this
```

## 🔄 **Job Lifecycle Management**

### **Unified Job Monitoring**
```python
@router.get("/api/v1/jobs/{job_id}/status")
async def get_job_status(job_id: UUID):
    """Get status regardless of provider type."""
    
    # Get job from database with provider info
    job = await job_repository.get_by_id(job_id)
    
    # Create appropriate provider adapter
    provider = provider_factory.create_provider(
        job.service_type, 
        job.provider_type
    )
    
    # Get status using unified interface
    status = await provider.get_job_status(job.external_job_id)
    
    # Update job in database
    await job_repository.update_status(job_id, status)
    
    return JobStatusResponse(
        job_id=job_id,
        status=status,
        provider_type=job.provider_type,  # Transparent to frontend
        progress=calculate_progress(status)
    )
```

## 🏠 **Domestic Service Implementation**

### **Container Service Pattern**
```python
# adapters/external/domestic/gnina_domestic_adapter.py
class DomesticGninaAdapter(MolecularAnalysisPort):
    """Domestic GNINA container service adapter."""
    
    def __init__(self):
        self.service_url = "http://gnina-service:8080"  # Container service
        
    async def submit_job(self, input_data: JobInput) -> str:
        """Submit to containerized GNINA service."""
        
        # Convert inputs to container service format
        request_data = {
            "receptor_pdb": input_data.get_file_content("receptor"),
            "ligand_sdf": input_data.get_file_content("ligand"),
            "parameters": input_data.parameters
        }
        
        # HTTP call to domestic container service
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.service_url}/api/v1/providers/domestic/docking/submit",
                json=request_data,
                timeout=30.0
            )
            
        return response.json()["job_id"]
    
    async def get_job_status(self, external_job_id: str) -> JobStatus:
        """Get status from container service."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.service_url}/api/v1/jobs/{external_job_id}/status"
            )
            
        status_data = response.json()
        return JobStatus(status_data["status"])
        
    async def get_job_results(self, external_job_id: str) -> JobResults:
        """Download results from container service."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.service_url}/api/v1/jobs/{external_job_id}/results"
            )
            
        return self._parse_domestic_results(response.json())
```

### **Container Service API Spec**
```yaml
# Each domestic service container exposes standard REST API
paths:
  /api/v1/{service_type}/submit:
    post:
      summary: Submit job to domestic service
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                receptor_pdb: {type: string}
                ligand_sdf: {type: string}  
                parameters: {type: object}
                
  /api/v1/jobs/{job_id}/status:
    get:
      summary: Get job status
      responses:
        200:
          content:
            application/json:
              schema:
                type: object
                properties:
                  status: {enum: [pending, running, completed, failed]}
                  progress: {type: number}
                  
  /api/v1/jobs/{job_id}/results:
    get:
      summary: Download results
      responses:
        200:
          content:
            application/json:
              schema:
                type: object
                properties:
                  poses: {type: array}
                  scores: {type: array}
                  files: {type: object}
```

## ☁️ **Provider Selection Logic**

### **Configuration-Driven Selection**
```python
# infrastructure/config/provider_config.py
class ProviderConfig:
    """Configuration for provider selection per organization."""
    
    def get_provider_for_service(self, org_id: UUID, service_type: str) -> str:
        """Determine which provider to use for a service."""
        
        org_preferences = self._get_org_preferences(org_id)
        
        # Check organization preferences
        if org_preferences.prefer_domestic:
            if self._is_domestic_available(service_type):
                return "domestic"
                
        # Check external service availability and credits
        if self._is_external_available(service_type):
            return "external"
            
        # Fallback to any available provider
        return self._get_fallback_provider(service_type)
```

### **Runtime Provider Switching**
```python
@router.post("/api/v1/organizations/{org_id}/provider-preferences")
async def set_provider_preferences(
    org_id: UUID, 
    preferences: ProviderPreferences
):
    """Allow organizations to choose external vs domestic providers."""
    
    await org_repository.update_provider_preferences(org_id, {
        "prefer_domestic": preferences.prefer_domestic,
        "max_external_cost": preferences.max_cost_per_job,
        "domestic_services": preferences.enabled_domestic_services
    })
    
    return {"status": "preferences_updated"}
```

## 📱 **Frontend Integration**

### **Transparent Service Calls**
```typescript
// Frontend sees unified API - provider type is transparent
export class MolecularAnalysisService {
  async submitDockingJob(request: DockingRequest): Promise<JobResponse> {
    // Same endpoint for external and domestic services!
    const response = await api.post('/api/v1/providers/neurosnap/docking/submit', request);
    return response.data;
  }
  
  async getJobStatus(jobId: string): Promise<JobStatus> {
    // Unified status endpoint
    const response = await api.get(`/api/v1/jobs/${jobId}/status`);
    return response.data;
  }
  
  async downloadResults(jobId: string): Promise<JobResults> {
    // Same result format regardless of provider
    const response = await api.get(`/api/v1/jobs/${jobId}/results`);
    return response.data;
  }
}
```

### **Provider Information (Optional)**
```typescript
// Frontend CAN access provider info if needed (for debugging, billing)
interface JobStatus {
  job_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress: number;
  provider_type?: 'external' | 'domestic';  // Optional metadata
  estimated_cost?: number;
  resource_usage?: ResourceUsage;
}
```

## 🔧 **Implementation Steps**

### **Phase 1: Provider Factory (Week 1)**
1. Create `ProviderFactory` with external/domestic routing
2. Implement `MolecularAnalysisPort` unified interface  
3. Update existing NeuroSnap adapters to implement unified interface

### **Phase 2: Domestic Adapters (Week 2-3)**
1. Create domestic service adapters following existing patterns
2. Implement container service HTTP clients
3. Add provider selection logic to API routes

### **Phase 3: Database Integration (Week 4)**
1. Add `provider_type` and `external_job_id` fields to Job table
2. Update job repository to handle provider information
3. Migrate existing NeuroSnap jobs to new schema

### **Phase 4: API Unification (Week 5)**
1. Update all API routes to use provider factory
2. Ensure transparent job lifecycle management
3. Add provider preference management endpoints

### **Phase 5: Frontend Updates (Week 6)**
1. Update frontend services to use unified endpoints
2. Add optional provider information display
3. Implement provider preference management UI

## ✅ **Verification Checklist**

- [ ] **Provider Transparency**: Frontend cannot tell if job runs externally or domestically
- [ ] **Unified Database**: Jobs stored identically regardless of provider type
- [ ] **Status Monitoring**: Single status endpoint works for all providers
- [ ] **Result Retrieval**: Same result format from external and domestic services
- [ ] **Provider Selection**: Organizations can choose preferred provider types
- [ ] **Fallback Logic**: System gracefully handles provider unavailability
- [ ] **Cost Management**: External service usage tracked and limited per organization
- [ ] **Audit Trail**: All job executions logged with provider information

## 📚 **Related Documentation**

- [Service Integration Guide](service-integration-guide.md) - Individual service integration patterns
- [Database Schema](../../database/design/schema.md) - Job storage and organization
- [API Contracts](../../api/contracts/rest-api.md) - Unified API specifications  
- [Provider Configuration](../../infrastructure/configuration.md) - Service selection logic

---

**Next Steps**: This hybrid integration pattern enables seamless scaling between cloud and on-premises computational resources while maintaining a unified development and user experience.