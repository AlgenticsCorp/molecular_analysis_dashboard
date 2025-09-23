# Database Design Documentation

*Database schema, data models, and multi-tenant architecture design for molecular data management.*

## Overview

This section contains comprehensive database design documentation including schema definitions, multi-tenant architecture, data relationships, and molecular data modeling strategies.

## Database Design Components

### **[Schema Documentation](schema.md)**
Current database schema and data model specifications
- Complete table definitions and relationships
- Index strategies and performance optimizations
- Data types and constraints
- Migration history and versioning

### **[Entity Relationship Diagram (ERD)](erd.md)**
Visual representation of database structure and relationships
- Entity relationships and cardinalities
- Database normalization and design patterns
- Business rule enforcement through constraints
- Multi-tenant data isolation patterns

### **[Schema Proposal](schema-proposal.md)**
Proposed schema changes and database evolution
- New table structures and modifications
- Migration strategies and data transformation
- Performance impact analysis
- Backward compatibility considerations

### **[Database Overview](databases-overview.md)**
High-level database architecture and technology choices
- PostgreSQL configuration and setup
- Database selection rationale and trade-offs
- Scalability and performance characteristics
- Integration with application layers

## Database Architecture

### Multi-Tenant Data Model
```sql
-- Shared metadata tables (organization-scoped)
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    organization_id UUID REFERENCES organizations(id),
    role VARCHAR(50) DEFAULT 'user'
);

-- Per-organization data tables
CREATE TABLE molecules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES organizations(id),
    name VARCHAR(255) NOT NULL,
    smiles TEXT,
    formula VARCHAR(255),
    molecular_weight DECIMAL(10,4),
    file_path TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Row-level security for multi-tenancy
ALTER TABLE molecules ENABLE ROW LEVEL SECURITY;

CREATE POLICY molecules_org_isolation ON molecules
FOR ALL TO app_role
USING (organization_id = current_setting('app.current_org_id')::uuid);
```

### Data Relationships
```
Organizations (1) ──────── (N) Users
      │
      │
      ├─ (N) Molecules
      ├─ (N) Docking Jobs
      ├─ (N) Pipelines
      ├─ (N) Results
      └─ (N) File Storage
```

### Schema Evolution Strategy
```sql
-- Version-controlled migrations with Alembic
-- Migration naming: YYYY_MM_DD_HHMM_description_of_change.py

"""Add molecular_weight column to molecules

Revision ID: 2024_01_15_1200
Revises: 2024_01_10_0900
Create Date: 2024-01-15 12:00:00.000000
"""

def upgrade():
    op.add_column('molecules',
        sa.Column('molecular_weight', sa.Numeric(10, 4), nullable=True)
    )

    # Populate existing data
    op.execute("""
        UPDATE molecules
        SET molecular_weight = calculate_molecular_weight(smiles)
        WHERE smiles IS NOT NULL
    """)

def downgrade():
    op.drop_column('molecules', 'molecular_weight')
```

## Key Design Principles

### 🏗️ **Multi-Tenant Architecture**
- **Organization Isolation**: Complete data separation per organization
- **Row-Level Security**: Database-enforced access control policies
- **Shared Infrastructure**: Common tables for system-wide data
- **Per-Org Databases**: Separate results databases for large-scale data
- **Backup Strategy**: Organization-specific backup and recovery

### 📊 **Data Modeling**
- **Molecular Entities**: Comprehensive molecular data representation
- **Job Tracking**: Complete computational job lifecycle management
- **Result Storage**: Structured storage for analysis results
- **Audit Logging**: Full audit trail for compliance and debugging
- **Metadata Management**: Rich metadata for search and filtering

### ⚡ **Performance Optimization**
- **Strategic Indexing**: Optimized indexes for common query patterns
- **Partitioning**: Table partitioning for large datasets
- **Connection Pooling**: Efficient database connection management
- **Query Optimization**: Prepared statements and query analysis
- **Caching Layer**: Redis integration for frequently accessed data

### 🔒 **Security & Compliance**
- **Encryption at Rest**: All sensitive data encrypted in database
- **Access Control**: Fine-grained permissions and role-based access
- **Audit Trails**: Comprehensive logging of all data changes
- **Data Retention**: Configurable retention policies per organization
- **GDPR Compliance**: Data portability and right-to-be-forgotten support

## Database Tables Overview

### Core Entity Tables
```sql
-- Organizations and user management
organizations          -- Organization definitions
users                 -- User accounts and roles
user_sessions         -- Active user sessions

-- Molecular data management
molecules             -- Molecular structures and metadata
molecule_files        -- File storage references
molecule_properties   -- Computed molecular properties

-- Computational workflows
docking_jobs          -- Molecular docking job definitions
job_executions        -- Job execution tracking
job_results          -- Structured result data
pipelines            -- Workflow definitions
pipeline_executions -- Pipeline run tracking

-- System and audit
audit_log            -- Complete audit trail
system_config        -- System configuration
organization_config  -- Per-org configuration
```

### Indexing Strategy
```sql
-- Performance-critical indexes
CREATE INDEX idx_molecules_org_name ON molecules(organization_id, name);
CREATE INDEX idx_jobs_org_status ON docking_jobs(organization_id, status);
CREATE INDEX idx_results_job_created ON job_results(job_id, created_at);
CREATE INDEX idx_audit_org_timestamp ON audit_log(organization_id, timestamp);

-- Full-text search indexes
CREATE INDEX idx_molecules_search ON molecules
USING GIN(to_tsvector('english', name || ' ' || COALESCE(description, '')));
```

## Data Types and Standards

### Molecular Data Types
```sql
-- Custom types for molecular data
CREATE TYPE molecule_format AS ENUM ('sdf', 'pdb', 'mol2', 'smiles', 'pdbqt');
CREATE TYPE job_status AS ENUM ('pending', 'running', 'completed', 'failed', 'cancelled');
CREATE TYPE user_role AS ENUM ('user', 'admin', 'super_admin');

-- Molecular structure storage
CREATE DOMAIN smiles_string AS TEXT
CHECK (VALUE ~ '^[A-Za-z0-9@+\-\[\]()=#$:.%\\\/]+$');

CREATE DOMAIN molecular_weight AS NUMERIC(10,4)
CHECK (VALUE > 0 AND VALUE < 10000);
```

### JSON Data Structures
```sql
-- Flexible metadata storage
ALTER TABLE molecules ADD COLUMN properties JSONB;
ALTER TABLE job_results ADD COLUMN data JSONB;

-- JSON validation constraints
ALTER TABLE molecules ADD CONSTRAINT valid_properties
CHECK (jsonb_typeof(properties) = 'object');

-- JSON indexes for efficient querying
CREATE INDEX idx_molecules_properties ON molecules USING GIN(properties);
```

## Related Documentation

- **[Database Management](../management/README.md)** - Administration and maintenance procedures
- **[Connection Routing](../connection-routing/README.md)** - Multi-tenant connection management
- **[Database Testing](../testing/README.md)** - Testing strategies and data fixtures
- **[System Architecture](../../architecture/system-design/README.md)** - Overall system design context
- **[API Integration](../../api/README.md)** - Database integration with application APIs

## Migration and Evolution

### Schema Migration Process
1. **Design Review**: Peer review of schema changes
2. **Impact Analysis**: Assess performance and compatibility impact
3. **Migration Script**: Create reversible migration scripts
4. **Testing**: Validate migration in staging environment
5. **Deployment**: Apply migration with rollback plan
6. **Monitoring**: Monitor performance after migration

### Version Control
- All schema changes tracked in Alembic migrations
- Migration scripts stored in `database/alembic/versions/`
- Each migration includes upgrade and downgrade paths
- Migration testing automated in CI/CD pipeline

### Best Practices
- **Backward Compatibility**: Maintain compatibility during transitions
- **Incremental Changes**: Small, incremental schema modifications
- **Data Validation**: Comprehensive validation of data integrity
- **Performance Testing**: Load testing after significant changes
- **Documentation**: Update schema documentation with each change
