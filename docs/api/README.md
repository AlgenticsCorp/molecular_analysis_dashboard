# 🔗 API Documentation

This section contains comprehensive API documentation for the Molecular Analysis Dashboard, including REST contracts, gateway configuration, and integration patterns.

## 🏗️ **API Architecture Overview**

The Molecular Analysis Dashboard provides a **modern REST API** with:
- **Dynamic Task System**: Runtime-configurable computational workflows
- **Multi-Tenant Architecture**: Organization-scoped data and access
- **OpenAPI Integration**: Self-documenting with automatic validation
- **Gateway-Based Routing**: Centralized security and load balancing

```
Client Applications
        │
        │ HTTPS/JWT
        │
  ┌─────────────┐
  │ API Gateway   │  ← Authentication, Rate Limiting, Routing
  └─────────────┘
        │
        │ Internal
        │
  ┌─────────────┐
  │ FastAPI Core  │  ← Business Logic, Task Orchestration
  └─────────────┘
        │
        │ Dynamic
        │
  ┌─────────────┐
  │ Task Services │  ← Computational Engines (Docking, Analysis)
  └─────────────┘
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

### **Dynamic Task System**
- ✅ **Runtime Task Registration**: Add new computational tasks without deployment
- ✅ **OpenAPI Integration**: Self-documenting task interfaces
- ✅ **Service Discovery**: Automatic discovery and load balancing of task services
- ✅ **Version Management**: Support multiple task versions simultaneously

### **Multi-Tenant Architecture**
- ✅ **Organization Isolation**: Complete data separation per organization
- ✅ **Role-Based Access**: Fine-grained permission system
- ✅ **Resource Quotas**: Per-organization usage limits
- ✅ **Audit Logging**: Comprehensive activity tracking

### **Molecular Analysis Features**
- ✅ **File Upload**: Support for PDB, SDF, MOL2, PDBQT formats
- ✅ **Docking Engines**: AutoDock Vina, Smina, Gnina integration
- ✅ **Pipeline Templates**: Reusable workflow definitions
- ✅ **Result Caching**: Intelligent caching of computational results

### **Performance & Reliability**
- ✅ **Rate Limiting**: Multi-tier protection (endpoint/user/org)
- ✅ **Async Processing**: Non-blocking task execution
- ✅ **Health Monitoring**: Comprehensive service health checks
- ✅ **Error Recovery**: Graceful error handling and retries

## 📊 **API Statistics**

### **Endpoint Categories**
- **Authentication**: 3 endpoints (register, login, refresh)
- **Task Registry**: 5 endpoints (list, create, interface, services)
- **Task Execution**: 4 endpoints (execute, status, results, cancel)
- **Molecules**: 3 endpoints (upload, list, download)
- **Jobs**: 6 endpoints (create, status, results, events, files, cancel)
- **Pipelines**: 4 endpoints (list templates, instantiate, status, results)
- **Health**: 2 endpoints (health, ready)

### **Response Formats**
- **JSON**: Primary data format for all responses
- **Binary**: File downloads and uploads
- **Server-Sent Events**: Real-time status updates
- **WebSocket**: Bidirectional communication for live monitoring

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
