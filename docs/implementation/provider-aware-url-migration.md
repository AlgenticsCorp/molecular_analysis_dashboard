# Provider-Aware URL Migration Guide

## 🎯 **Current State Analysis**

### **Existing URL Structure**
```
/api/v1/folding/submit              → NeuroSnap IntelliFold
/api/v1/folding/submit-boltz2       → NeuroSnap Boltz-2
/api/v1/docking/submit              → NeuroSnap GNINA  
/api/v1/molecular-dynamics/submit   → NeuroSnap AMBER
/api/v1/neurosnap/status/{job_id}   → Universal job status
```

### **Migration Complexity: MODERATE** ⚠️

**Easy Changes (1-2 hours):**
- ✅ Router prefix updates (simple string changes)
- ✅ Adding new route structures
- ✅ Swagger documentation updates

**Complex Changes (1-2 days):**
- ⚠️ Provider factory implementation
- ⚠️ Backward compatibility layer
- ⚠️ Frontend API client updates
- ⚠️ Decoupling NeuroSnap-specific logic

## 📋 **Migration Plan**

### **Phase 1: Add Provider-Aware URLs (Keep Existing)**
```python
# 1. Keep existing routes for backward compatibility
prefix="/api/v1/folding"                    # KEEP - existing clients

# 2. Add new provider-aware routes  
prefix="/api/v1/providers/neurosnap/folding"       # NEW
prefix="/api/v1/providers/domestic/folding"        # NEW (future)
```

### **Phase 2: Create Provider Factory Pattern**
```python
# 3. Extract provider logic into adapters
class NeuroSnapFoldingAdapter:
    async def submit_job(self, request): 
        # Move NeuroSnap-specific logic here
        
class DomesticFoldingAdapter:  
    async def submit_job(self, request):
        # Future domestic implementation
```

### **Phase 3: Universal Service Endpoints**
```python
# 4. Add universal endpoints with automatic provider selection
prefix="/api/v1/services/folding"          # NEW - provider auto-selection
prefix="/api/v1/services/docking"          # NEW - provider auto-selection
```

## 🔧 **Implementation Examples**

### **Example 1: Update Folding Router (Simple)**

**Current Code:**
```python
# folding.py
router = APIRouter(
    prefix="/api/v1/folding",
    tags=["🧬 Structure Folding", "☁️ NeuroSnap Cloud"],
)
```

**Updated Code (Phase 1 - Add Provider Prefix):**
```python
# folding.py -> neurosnap_folding.py  
router = APIRouter(
    prefix="/api/v1/providers/neurosnap/folding",
    tags=["🧬 Structure Folding", "☁️ NeuroSnap Cloud"],
)

# Keep existing route for compatibility
legacy_router = APIRouter(
    prefix="/api/v1/folding", 
    tags=["🧬 Structure Folding", "☁️ NeuroSnap Cloud"],
    deprecated=True  # Mark as deprecated
)
```

### **Example 2: Provider Factory (Moderate Complexity)**

**New File: `providers/factory.py`**
```python
from abc import ABC, abstractmethod
from typing import Dict, Type

class FoldingProvider(ABC):
    @abstractmethod
    async def submit_job(self, request): pass
    
    @abstractmethod 
    async def get_status(self, job_id: str): pass

class NeuroSnapFoldingProvider(FoldingProvider):
    async def submit_job(self, request):
        # Move call_neurosnap_intellifold logic here
        return await call_neurosnap_intellifold(request)
        
    async def get_status(self, job_id: str):
        # NeuroSnap status logic
        pass

class ProviderFactory:
    def __init__(self):
        self._providers: Dict[str, Dict[str, Type[FoldingProvider]]] = {
            "neurosnap": {
                "folding": NeuroSnapFoldingProvider,
            },
            "domestic": {
                "folding": DomesticFoldingProvider,  # Future
            }
        }
    
    def create_folding_provider(self, provider_type: str) -> FoldingProvider:
        if provider_type not in self._providers:
            raise ValueError(f"Unknown provider: {provider_type}")
        return self._providers[provider_type]["folding"]()
```

### **Example 3: Universal Service Endpoint (Complex)**

**New File: `services/folding.py`**
```python
from ..providers.factory import ProviderFactory

router = APIRouter(
    prefix="/api/v1/services/folding",
    tags=["🧬 Structure Folding", "🤖 Multi-Provider"],
)

@router.post("/submit")
async def submit_universal_folding_job(
    request: FoldingJobRequest,
    preferred_provider: Optional[str] = None
):
    """Universal folding endpoint - automatically selects best provider."""
    
    # Provider selection logic
    if preferred_provider:
        provider_type = preferred_provider
    else:
        # Auto-select based on availability, cost, performance
        provider_type = await select_best_provider("folding", request.org_id)
    
    # Create provider adapter
    factory = ProviderFactory()
    provider = factory.create_folding_provider(provider_type)
    
    # Submit job using unified interface  
    job_result = await provider.submit_job(request)
    
    return {
        **job_result,
        "provider_used": provider_type,
        "provider_selection": "automatic" if not preferred_provider else "manual"
    }
```

## 📊 **File Changes Required**

### **Minimal Changes (Phase 1 - Add Provider URLs)**

**Files to Modify:**
```
src/presentation/api/routes/
├─ folding.py                    # Update prefix only
├─ docking.py                    # Update prefix only  
├─ molecular_dynamics.py         # Update prefix only
└─ main.py                       # Add new router imports
```

**Estimated Time: 2-4 hours**

### **Full Migration (Phase 2 - Provider Factory)**

**New Files to Create:**
```
src/
├─ providers/
│  ├─ __init__.py
│  ├─ factory.py                 # Provider factory
│  ├─ base.py                    # Abstract interfaces
│  └─ neurosnap/
│     ├─ folding_adapter.py      # Extract NeuroSnap logic
│     ├─ docking_adapter.py      # Extract NeuroSnap logic
│     └─ dynamics_adapter.py     # Extract NeuroSnap logic
└─ presentation/api/routes/
   ├─ services/                  # New universal endpoints
   │  ├─ folding.py             # Multi-provider folding
   │  ├─ docking.py             # Multi-provider docking  
   │  └─ molecular_dynamics.py   # Multi-provider dynamics
   └─ providers/                 # Provider-specific routes
      └─ neurosnap/
         ├─ folding.py
         ├─ docking.py
         └─ molecular_dynamics.py
```

**Estimated Time: 1-2 weeks**

## 🚨 **Key Challenges**

### **1. Tight NeuroSnap Coupling**
**Current Issue:**
```python
# Direct NeuroSnap API calls scattered throughout route handlers
async def call_neurosnap_intellifold(folding_request, ...):
    # 200+ lines of NeuroSnap-specific logic
```

**Solution:** Extract to adapter pattern

### **2. Backward Compatibility** 
**Challenge:** Existing clients expect `/api/v1/folding/submit`
**Solution:** Maintain legacy routes with deprecation warnings

### **3. Frontend Impact**
**Challenge:** React frontend has hardcoded API URLs
**Solution:** Update API client configuration

## ✅ **Migration Execution Steps**

### **Week 1: Provider-Aware URLs**
1. ✅ Create provider-specific route files
2. ✅ Update router prefixes
3. ✅ Add backward compatibility routes
4. ✅ Update Swagger documentation

### **Week 2: Provider Factory** 
1. ✅ Extract NeuroSnap logic to adapters
2. ✅ Implement provider factory pattern
3. ✅ Create universal service endpoints
4. ✅ Add provider selection logic

### **Week 3: Testing & Documentation**
1. ✅ Test all route combinations
2. ✅ Update frontend API clients
3. ✅ Create migration documentation
4. ✅ Deploy with feature flags

## 🎯 **Recommendation**

**START with Phase 1 (Provider-Aware URLs)** - this gives you:
- ✅ Clean provider separation
- ✅ Future-ready structure  
- ✅ Minimal breaking changes
- ✅ Foundation for domestic services

**Phase 2 can be implemented gradually** as you add domestic providers.

**Total Effort: 2-3 weeks for complete migration**
**Immediate Effort: 4-6 hours for provider-aware URLs**