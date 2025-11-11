# Multi-Provider Organization Strategy

## 🎯 **Strategic Question**
> "Is service-first organization the best way to logically separate services when planning to add several providers including domestic services?"

## ✅ **Answer: YES - Service-First with Provider-Aware URLs**

The current service-first organization is optimal for multi-provider scalability, but needs **provider-aware URL structure** underneath for true flexibility.

## 🏗️ **Recommended Architecture Evolution**

### **Phase 1: Current State (Optimal Foundation)**
```
🧬 Structure Folding
├─ ☁️ NeuroSnap Cloud
│  ├─ IntelliFold
│  └─ Boltz-2

🎯 Molecular Docking  
├─ ☁️ NeuroSnap Cloud
│  └─ GNINA

🔬 Molecular Dynamics
├─ ☁️ NeuroSnap Cloud
│  └─ AMBER
```

### **Phase 2: Provider-Aware URLs (Next 2-4 weeks)**
```bash
# Current URLs
POST /api/v1/folding/intellifold/submit
POST /api/v1/docking/gnina/submit

# Provider-Aware URLs (Recommended)
POST /api/v1/providers/neurosnap/folding/intellifold/submit
POST /api/v1/providers/domestic/folding/alphafold3/submit
POST /api/v1/providers/domestic/docking/vina/submit

# Universal Service URLs (Provider Selection Hidden)
POST /api/v1/folding/submit        # Auto-selects best provider
POST /api/v1/docking/submit        # Based on org preferences
```

### **Phase 3: Multi-Provider Integration (Next 1-2 months)**
```
🧬 Structure Folding
├─ ☁️ NeuroSnap Cloud
│  ├─ IntelliFold
│  └─ Boltz-2
├─ 🏠 Domestic Services
│  ├─ AlphaFold3 Local
│  ├─ ColabFold Local
│  └─ ESMFold Local
├─ 🌐 Other Cloud Services (Future)
│  ├─ AWS SageMaker
│  └─ Google Cloud Life Sciences

🎯 Molecular Docking
├─ ☁️ NeuroSnap Cloud
│  └─ GNINA
├─ 🏠 Domestic Services  
│  ├─ AutoDock Vina
│  ├─ LeDock
│  └─ PLANTS
├─ 🌐 Other Cloud Services
│  └─ Azure Molecular Dynamics

🔬 Molecular Dynamics
├─ ☁️ NeuroSnap Cloud
│  └─ AMBER
├─ 🏠 Domestic Services
│  ├─ GROMACS Local
│  ├─ NAMD Local
│  └─ OpenMM Local
```

## 📁 **File Organization Strategy**

### **Current Structure (Good Foundation)**
```
src/presentation/api/routes/
├─ folding.py                    # Service-focused
├─ docking.py                    # Service-focused  
├─ molecular_dynamics.py         # Service-focused
├─ neurosnap_unified.py         # Provider-specific utilities
└─ task_execution.py            # Cross-service job management
```

### **Recommended Evolution**
```
src/presentation/api/routes/
├─ services/                     # Service-first organization
│  ├─ folding.py                # Unified folding endpoints
│  ├─ docking.py               # Unified docking endpoints
│  └─ molecular_dynamics.py    # Unified MD endpoints
├─ providers/                   # Provider-specific implementations
│  ├─ neurosnap/
│  │  ├─ folding.py
│  │  ├─ docking.py  
│  │  └─ molecular_dynamics.py
│  ├─ domestic/
│  │  ├─ folding.py
│  │  ├─ docking.py
│  │  └─ molecular_dynamics.py
│  └─ factory.py               # Provider selection logic
└─ unified/
   ├─ job_management.py        # Cross-provider job ops
   └─ task_execution.py        # Universal task interface
```

## 🔧 **Provider Factory Implementation**

### **1. Provider Factory Pattern**
```python
# infrastructure/providers/provider_factory.py
class ServiceProviderFactory:
    """Factory for creating service providers based on configuration."""
    
    def __init__(self):
        self._providers = {
            "neurosnap": {
                "folding": NeuroSnapFoldingAdapter,
                "docking": NeuroSnapDockingAdapter,
                "molecular_dynamics": NeuroSnapMDAdapter,
            },
            "domestic": {
                "folding": DomesticAlphaFoldAdapter,
                "docking": DomesticVinaAdapter,
                "molecular_dynamics": DomesticGromacsAdapter,
            },
            "aws": {
                "folding": AWSFoldingAdapter,
                "docking": AWSBatchDockingAdapter,
            }
        }
    
    def create_provider(self, provider_type: str, service_type: str):
        """Create appropriate provider adapter."""
        if provider_type not in self._providers:
            raise ProviderNotFoundError(f"Provider {provider_type} not registered")
            
        if service_type not in self._providers[provider_type]:
            raise ServiceNotSupportedError(f"Service {service_type} not supported by {provider_type}")
            
        adapter_class = self._providers[provider_type][service_type]
        return adapter_class()
    
    def get_best_provider(self, service_type: str, org_id: UUID) -> str:
        """Select optimal provider based on org preferences, cost, availability."""
        preferences = await self._get_org_preferences(org_id)
        
        # Check organization preferences
        if preferences.prefer_domestic and self._is_domestic_available(service_type):
            return "domestic"
            
        if preferences.cost_sensitive:
            return self._get_cheapest_provider(service_type)
            
        if preferences.performance_critical:
            return self._get_fastest_provider(service_type)
            
        # Default to most reliable provider
        return self._get_most_reliable_provider(service_type)
```

### **2. Unified Service Interface**
```python
# presentation/api/routes/services/folding.py
@router.post("/api/v1/folding/submit")
async def submit_folding_job(
    request: FoldingJobRequest,
    org_context: OrganizationContext = Depends(get_org_context)
):
    """Universal folding endpoint - provider selection is transparent."""
    
    # Automatic provider selection
    provider_type = provider_factory.get_best_provider("folding", org_context.org_id)
    
    # Create appropriate adapter
    provider = provider_factory.create_provider(provider_type, "folding")
    
    # Submit job using unified interface
    external_job_id = await provider.submit_job(request.to_job_input())
    
    # Store with provider metadata for tracking
    job = await job_repository.create_job(
        job_id=uuid4(),
        external_job_id=external_job_id,
        provider_type=provider_type,
        service_type="folding",
        inputs=request.inputs,
        org_id=org_context.org_id
    )
    
    return JobSubmissionResponse(
        job_id=job.job_id,
        provider_used=provider_type,
        estimated_completion=provider.estimate_completion_time(request),
        tracking_url=f"/api/v1/jobs/{job.job_id}/status"
    )

# Provider-specific endpoints for advanced users
@router.post("/api/v1/providers/{provider_type}/folding/submit")
async def submit_folding_job_to_provider(
    provider_type: str,
    request: FoldingJobRequest
):
    """Provider-specific endpoint for advanced users."""
    provider = provider_factory.create_provider(provider_type, "folding")
    # ... same logic but forced provider selection
```

### **3. Organization Provider Preferences**
```python
# infrastructure/config/provider_preferences.py
class ProviderPreferences:
    """Per-organization provider selection preferences."""
    
    def __init__(self, org_id: UUID):
        self.org_id = org_id
        self.preferences = self._load_preferences()
    
    def get_provider_priority(self, service_type: str) -> List[str]:
        """Get ordered list of preferred providers for a service."""
        base_priority = ["domestic", "neurosnap", "aws"]
        
        org_prefs = self.preferences.get(service_type, {})
        
        # Apply organization-specific overrides
        if org_prefs.get("cloud_only", False):
            return [p for p in base_priority if p != "domestic"]
            
        if org_prefs.get("cost_optimized", False):
            # Reorder by cost (domestic usually cheapest)
            return sorted(base_priority, key=self._get_cost_score)
            
        if org_prefs.get("compliance_required", False):
            # Domestic first for data sovereignty
            return ["domestic"] + [p for p in base_priority if p != "domestic"]
            
        return base_priority
```

## 📊 **Benefits Analysis**

### **✅ Service-First Organization Benefits**

**User Experience:**
- Scientists choose **what to do**, not **which tool to use**
- Single job tracking interface across all providers
- Provider transparency allows focus on science, not infrastructure

**Technical Benefits:**
- Provider factory pattern enables unlimited provider expansion  
- Frontend remains stable as providers are added
- Automatic failover and load balancing between providers
- Universal job management across heterogeneous providers

**Business Benefits:**
- Cost optimization through provider arbitrage
- Compliance flexibility (domestic vs cloud)
- Reduced vendor lock-in risk
- Easy A/B testing between providers

### **🔄 Migration Strategy**

**Week 1-2: Provider-Aware URLs**
```python
# Add provider-specific routes while maintaining backward compatibility
@router.post("/api/v1/folding/submit")  # Current universal endpoint
@router.post("/api/v1/providers/neurosnap/folding/submit")  # New provider-specific
```

**Week 3-4: Provider Factory Implementation**
```python
# Implement provider factory and selection logic
# Update existing routes to use factory pattern
```

**Week 5-8: Domestic Provider Integration**
```python
# Add domestic service adapters
# Implement local tool interfaces (Vina, GROMACS, AlphaFold3)
# Update Swagger documentation
```

## 🎯 **Implementation Priority**

### **High Priority (Next Sprint)**
1. ✅ Provider factory pattern implementation
2. ✅ Provider-aware URL structure  
3. ✅ Universal job management endpoints
4. ✅ Organization provider preferences

### **Medium Priority (Next Month)**  
1. 🔄 Domestic service adapter interfaces
2. 🔄 Local tool container integration
3. 🔄 Advanced provider selection logic
4. 🔄 Cost and performance monitoring

### **Future Enhancements**
1. 🔮 Multi-cloud provider support (AWS, Azure, GCP)
2. 🔮 ML-based provider recommendation
3. 🔮 Real-time cost optimization
4. 🔮 Predictive scaling and load balancing

## 🚨 **Critical Success Factors**

### **1. Maintain Backward Compatibility**
- Existing NeuroSnap integrations must continue working
- Gradual migration path for existing API consumers
- Version management for breaking changes

### **2. Provider Abstraction**
- All providers implement same core interface
- Provider-specific features available through extensions
- Consistent error handling and status reporting

### **3. Performance Considerations**
- Provider selection logic must be fast (<100ms)
- Job routing overhead minimized
- Efficient provider health monitoring

---

## 🎉 **Conclusion**

**The current service-first organization is the optimal foundation for multi-provider scalability.** The next evolutionary step is implementing provider-aware URLs and the factory pattern while maintaining the service-first user experience.

This approach provides:
- ✅ **User-Friendly**: Scientists focus on tasks, not infrastructure
- ✅ **Scalable**: Easy to add unlimited providers
- ✅ **Flexible**: Runtime provider selection based on cost/performance/compliance  
- ✅ **Future-Proof**: Architecture supports any computational service provider

The documented patterns in this repository already provide the foundation - now it's about implementing the provider factory and selection logic!