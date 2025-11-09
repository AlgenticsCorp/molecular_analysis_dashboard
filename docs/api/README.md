# 🔗 API Documentation

This section contains comprehensive API documentation for the Molecular Analysis Dashboard, including REST contracts, gateway configuration, and integration patterns.

## 🏗️ **API Architecture Overview**

The Molecular Analysis Dashboard provides a **comprehensive molecular analysis platform** with:
- **5 Integrated Computational Services**: Structure folding, molecular dynamics, docking, task framework, unified management
- **Multi-Service REST API**: 15+ endpoints across molecular biology workflow categories
- **NeuroSnap Cloud Integration**: Enterprise-grade computational engines via cloud APIs
- **Multi-Tenant Architecture**: Organization-scoped data and access control
- **OpenAPI Integration**: Self-documenting with interactive Swagger UI testing
- **Gateway-Based Routing**: Centralized security, rate limiting, and load balancing

```
Research Applications
        │
        │ HTTPS/JWT Authentication
        │
  ┌─────────────┐
  │ API Gateway   │  ← Authentication, Rate Limiting, Service Routing
  └─────────────┘
        │
        │ Internal Service Mesh
        │
  ┌─────────────┐
  │ FastAPI Core  │  ← Multi-Service Orchestration, Business Logic
  └─────────────┘
        │
        │ NeuroSnap Cloud APIs
        │
  ┌──────────────────────────────────────┐
  │ Molecular Analysis Services (5 Integrated)  │
  │ • Structure Folding (IntelliFold/Boltz-2)     │
  │ • Molecular Dynamics (AMBER Relaxation)     │
  │ • Molecular Docking (GNINA)                │
  │ • Task Execution Framework               │
  │ • Unified Job Management                  │
  └──────────────────────────────────────┘
```

## 🗂️ **API Documentation Sections**

### **[REST API Contracts](contracts/rest-api.md)**
REST API specifications and endpoint definitions
- **[REST API](contracts/rest-api.md)** - Complete API contract with all endpoints
- **[API Authentication](contracts/rest-api.md#authentication)** - JWT and OAuth2 authentication flows
- **[Error Handling](contracts/rest-api.md#error-handling)** - Standardized error responses
- **[Rate Limiting](contracts/rest-api.md#rate-limiting)** - API usage limits and quotas

### **[API Gateway](../architecture/integration/gateway.md)**
API gateway configuration and routing
- **[Gateway Design](../architecture/integration/gateway.md)** - Service routing and load balancing
- **[Gateway Security](../architecture/integration/gateway.md#security)** - Authentication and authorization
- **[Gateway Features](../architecture/integration/gateway.md#features)** - Rate limiting and health monitoring

### **[API Schemas](contracts/rest-api.md)**
Data models and validation schemas
- **[API Specification](contracts/rest-api.md)** - Complete API schema and models
- **[Input Validation](contracts/rest-api.md#validation)** - Request validation and constraints

### **[API Integration](contracts/rest-api.md)**
Client libraries and integration patterns
- **[Client Integration](contracts/rest-api.md#clients)** - SDK usage and examples
- **[Real-time Features](contracts/rest-api.md#websockets)** - WebSocket and webhook integration

---

## 🚀 **Quick Start Guide**

### **1. Authentication**
```bash
# Get access token
curl -X POST "https://api.yourdomain.com/api/v1/auth/token" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "your-password",
    "org_id": "your-org-id"
  }'
```

### **2. Upload Molecule**
```bash
# Upload molecular structure
curl -X POST "https://api.yourdomain.com/api/v1/molecules/upload" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -F "file=@molecule.sdf" \
  -F "name=Aspirin" \
  -F "format=sdf"
```

### **3. Execute Task**
```bash
# Submit docking task
curl -X POST "https://api.yourdomain.com/api/v1/tasks/molecular-docking/execute" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "protein_file": "mad://org/molecules/protein.pdb",
    "ligand_file": "mad://org/molecules/ligand.sdf",
    "binding_site": {
      "center_x": 25.5,
      "center_y": 10.2,
      "center_z": 15.8,
      "size_x": 20.0,
      "size_y": 20.0,
      "size_z": 20.0
    }
  }'
```

### **4. Check Results**
```bash
# Get execution results
curl -X GET "https://api.yourdomain.com/api/v1/executions/$EXECUTION_ID/results" \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

## 📋 **API Features Overview**

### **🧬 Comprehensive Molecular Analysis**
- ✅ **Structure Folding**: IntelliFold & Boltz-2 (AlphaFold3) protein structure prediction
- ✅ **Molecular Dynamics**: AMBER relaxation and energy minimization
- ✅ **Molecular Docking**: GNINA neural network-guided binding analysis
- ✅ **Task Framework**: Generic computational workflow interface
- ✅ **Unified Management**: Centralized job tracking and results retrieval

### **🚀 Multi-Service Integration**
- ✅ **15+ REST Endpoints**: Comprehensive coverage across 5 molecular analysis categories
- ✅ **NeuroSnap Cloud APIs**: Enterprise-grade computational engines
- ✅ **Multi-Format Support**: PDB, SDF, MOL2, FASTA, and custom molecular file formats
- ✅ **Advanced Parameters**: Engine-specific optimization and configuration controls
- ✅ **Real-time Monitoring**: Live job status tracking across all computational services

### **🏗️ Enterprise Architecture**
- ✅ **Multi-Tenant Design**: Complete organization-based data isolation
- ✅ **Role-Based Access**: Fine-grained permission system for research teams
- ✅ **JWT Authentication**: Secure, stateless authentication with org scoping
- ✅ **API Gateway Integration**: Centralized security, rate limiting, and routing
- ✅ **OpenAPI Documentation**: Interactive Swagger UI with live endpoint testing

### **🔍 Research Workflow Support**
- ✅ **End-to-End Pipeline**: Sequence → Structure → Dynamics → Binding analysis
- ✅ **Batch Processing**: Multiple job submission and management
- ✅ **Result Caching**: Intelligent caching of computational results
- ✅ **File Management**: Secure upload, processing, and download of molecular data

## 📊 **API Statistics**

### **🎨 Service Categories**
- **Task Execution Framework**: 2 endpoints (list tasks, execute tasks)
- **Structure Folding Services**: 4 endpoints (IntelliFold, Boltz-2, simple variants)
- **Molecular Dynamics**: 2 endpoints (AMBER relaxation, simple variant)
- **Molecular Docking**: 4 endpoints (GNINA submission, status, results, download)
- **Unified NeuroSnap Management**: 3 endpoints (status, results, download)
- **System Health & Readiness**: 2 endpoints (health, ready)
- **Total Endpoints**: **17 operational endpoints** across 6 service categories

### **🔬 Computational Capabilities**
- **Structure Folding Engines**: IntelliFold (AlphaFold3), Boltz-2 (Advanced AlphaFold3)
- **Molecular Dynamics Engines**: AMBER relaxation and optimization
- **Molecular Docking Engines**: GNINA (neural network-guided docking)
- **File Format Support**: PDB, SDF, MOL2, PDBQT, FASTA, custom formats
- **Cloud Integration**: NeuroSnap enterprise computational platform

### **📋 Response Formats**
- **JSON**: Primary data format for all API responses
- **Binary**: Molecular file downloads (PDB, SDF, CSV results)
- **Multipart**: File uploads with metadata
- **Streaming**: Large result file downloads

## 🔐 **Security Features**

### **Authentication & Authorization**
- **JWT Tokens**: Stateless authentication with organization scoping
- **Role-Based Access**: Researcher, Admin, Root permission levels
- **API Keys**: Alternative authentication for service-to-service
- **Token Refresh**: Secure token renewal without re-authentication

### **Data Protection**
- **Organization Isolation**: All data scoped by organization ID
- **Secure File Access**: Pre-signed URLs for large file downloads
- **Input Validation**: Comprehensive parameter and file validation
- **Audit Trails**: Complete logging of all API operations

### **Rate Limiting & DDoS Protection**
- **Multi-Tier Limits**: Endpoint, user, and organization quotas
- **Sliding Windows**: Accurate rate limit calculations
- **Circuit Breakers**: Automatic failover for failing services
- **Request Throttling**: Graceful degradation under high load

## 🛠️ **Integration Patterns**

### **Client Libraries**
```python
# Python SDK example
from molecular_analysis import Client

client = Client(api_key="your-api-key")

# Upload molecule
molecule = client.molecules.upload(
    file="path/to/molecule.sdf",
    name="Test Compound",
    format="sdf"
)

# Execute docking task
execution = client.tasks.execute(
    task_id="molecular-docking",
    protein_file=molecule.uri,
    ligand_file="path/to/ligand.sdf"
)

# Wait for results
results = execution.wait_for_completion()
print(f"Best affinity: {results.best_affinity}")
```

### **WebSocket Real-Time Updates**
```javascript
// JavaScript WebSocket example
const ws = new WebSocket('wss://api.yourdomain.com/ws/executions');

ws.onmessage = (event) => {
  const update = JSON.parse(event.data);
  console.log(`Task ${update.execution_id}: ${update.status}`);

  if (update.status === 'COMPLETED') {
    displayResults(update.results);
  }
};
```

### **Webhook Integration**
```json
{
  "webhook_url": "https://your-app.com/webhooks/molecular-analysis",
  "events": ["task.completed", "task.failed", "job.completed"],
  "secret": "your-webhook-secret"
}
```

## 📚 **Interactive Documentation**

### **Live API Documentation**
- **Swagger UI**: Interactive API explorer at `/docs`
- **ReDoc**: Beautiful documentation at `/redoc`
- **OpenAPI Schema**: Machine-readable spec at `/openapi.json`

### **Testing Tools**
- **API Playground**: Test endpoints directly in browser
- **Code Generation**: Generate client code for multiple languages
- **Example Requests**: Copy-paste ready API calls
- **Response Schemas**: Detailed response format documentation

## 🔗 **Related Documentation**

- [System Architecture](../architecture/README.md) - Overall system design and patterns
- [Database Schema](../database/README.md) - Data models and relationships
- [Security Architecture](../security/README.md) - Security policies and implementation
- [Deployment Guide](../deployment/README.md) - API deployment and configuration

## 📞 **Support & Community**

### **Getting Help**
- **API Issues**: Report bugs via GitHub issues
- **Feature Requests**: Submit enhancement proposals
- **Integration Support**: Community discussions and examples
- **Status Page**: Real-time API status and incidents

### **API Versioning**
- **Current Version**: v1 (stable)
- **Deprecation Policy**: 12-month notice for breaking changes
- **Migration Guides**: Step-by-step upgrade instructions
- **Changelog**: Detailed release notes for all versions

---

For specific API implementation details, explore the sections above or start with the [REST API contracts](contracts/rest-api.md).
