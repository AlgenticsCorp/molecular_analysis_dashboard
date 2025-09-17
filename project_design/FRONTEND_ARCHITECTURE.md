# Frontend Architecture - React TypeScript

This document outlines the frontend architecture for the Molecular Analysis Dashboard, built with React and TypeScript to provide a modern, type-safe, and maintainable user interface.

---

## **Technology Stack**

### **Core Framework**
- **React 18+**: Modern frontend framework with hooks, concurrent features, and automatic batching
- **TypeScript 5+**: Strict typing for enhanced developer experience and runtime safety
- **Vite**: Fast build tool with hot module replacement and optimized production builds

### **UI Components & Styling**
- **Material-UI (MUI) v5**: React component library for consistent design system
- **MUI Icons**: Comprehensive icon set for molecular analysis interface
- **Emotion**: CSS-in-JS styling solution (MUI's default)
- **MUI Lab**: Experimental components for advanced data visualization

### **State Management**
- **React Query (TanStack Query)**: Server state management and caching
- **React Context**: Client-side state for user preferences and UI state
- **Local Storage**: Persistence for user settings and draft data

### **Routing & Navigation**
- **React Router v6**: Declarative routing with data loading
- **Protected Routes**: Authentication-based route protection

### **Development Tools**
- **ESLint**: Code linting with React and TypeScript rules
- **Prettier**: Code formatting for consistent style
- **Husky**: Git hooks for pre-commit validation
- **Jest + React Testing Library**: Unit and integration testing

---

## **Project Structure**

```
frontend/
├── public/
│   ├── index.html
│   └── assets/
├── src/
│   ├── components/          # Reusable UI components
│   │   ├── common/         # Generic components (Button, Modal, etc.)
│   │   ├── forms/          # Form components with validation
│   │   ├── layout/         # Layout components (Header, Sidebar, etc.)
│   │   ├── molecular/      # Molecular-specific components
│   │   └── data-display/   # Tables, charts, result displays
│   │
│   ├── pages/              # Page-level components
│   │   ├── Dashboard/      # Dashboard overview
│   │   ├── Pipelines/      # Pipeline management
│   │   ├── Jobs/           # Job monitoring and results
│   │   ├── Molecules/      # Molecule library management
│   │   └── Settings/       # User and organization settings
│   │
│   ├── hooks/              # Custom React hooks
│   │   ├── api/           # API interaction hooks
│   │   ├── auth/          # Authentication hooks
│   │   └── ui/            # UI state management hooks
│   │
│   ├── services/           # API client and external services
│   │   ├── api/           # REST API client functions
│   │   ├── auth/          # Authentication service
│   │   └── storage/       # Local storage utilities
│   │
│   ├── types/              # TypeScript type definitions
│   │   ├── api.ts         # API response/request types
│   │   ├── entities.ts    # Domain entity types
│   │   └── ui.ts          # UI-specific types
│   │
│   ├── utils/              # Utility functions
│   │   ├── formatting/    # Data formatting utilities
│   │   ├── validation/    # Client-side validation
│   │   └── constants/     # Application constants
│   │
│   ├── contexts/           # React Context providers
│   │   ├── AuthContext.tsx     # User authentication state
│   │   ├── ThemeContext.tsx    # UI theme management
│   │   └── OrganizationContext.tsx # Multi-tenancy context
│   │
│   ├── App.tsx             # Root application component
│   ├── main.tsx            # Application entry point
│   └── vite-env.d.ts       # Vite environment types
│
├── package.json            # Dependencies and scripts
├── tsconfig.json           # TypeScript configuration
├── vite.config.ts          # Vite build configuration
├── eslint.config.js        # ESLint configuration
├── prettier.config.js      # Prettier configuration
└── jest.config.js          # Jest testing configuration
```

---

## **Type Safety Strategy**

### **API Integration**
```typescript
// types/api.ts
export interface DockingJob {
  job_id: string;
  status: 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED';
  created_at: string;
  updated_at: string;
  pipeline_id: string;
  input_molecules: MoleculeReference[];
  results?: DockingResult[];
}

export interface CreateJobRequest {
  pipeline_id: string;
  ligand_id: string;
  protein_id: string;
  parameters?: Record<string, unknown>;
}

export interface ApiResponse<T> {
  data: T;
  message?: string;
  errors?: string[];
}
```

### **React Query Integration**
```typescript
// hooks/api/useJobs.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { jobsApi } from '../../services/api/jobs';
import type { DockingJob, CreateJobRequest } from '../../types/api';

export const useJobs = (organizationId: string) => {
  return useQuery({
    queryKey: ['jobs', organizationId],
    queryFn: () => jobsApi.getJobs(organizationId),
    staleTime: 30000, // 30 seconds
  });
};

export const useCreateJob = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: CreateJobRequest) => jobsApi.createJob(request),
    onSuccess: (newJob: DockingJob) => {
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
    },
  });
};
```

---

## **Component Architecture**

### **Molecular Visualization Component**
```typescript
// components/molecular/MolecularViewer.tsx
import React, { useEffect, useRef } from 'react';
import { Box, CircularProgress, Alert } from '@mui/material';
import type { MoleculeData } from '../../types/entities';

interface MolecularViewerProps {
  moleculeData: MoleculeData;
  height?: number;
  showControls?: boolean;
  onSelectionChange?: (selection: string[]) => void;
}

export const MolecularViewer: React.FC<MolecularViewerProps> = ({
  moleculeData,
  height = 400,
  showControls = true,
  onSelectionChange,
}) => {
  const viewerRef = useRef<HTMLDivElement>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!viewerRef.current || !moleculeData) return;

    try {
      // Initialize 3Dmol.js viewer
      const viewer = window.$3Dmol.createViewer(viewerRef.current);

      // Load molecule data
      viewer.addModel(moleculeData.content, moleculeData.format);
      viewer.setStyle({}, { stick: {} });
      viewer.zoomTo();
      viewer.render();

      setLoading(false);
    } catch (err) {
      setError(`Failed to load molecule: ${err.message}`);
      setLoading(false);
    }
  }, [moleculeData]);

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" height={height}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return <Alert severity="error">{error}</Alert>;
  }

  return (
    <Box>
      <div ref={viewerRef} style={{ height, width: '100%' }} />
      {showControls && (
        <MolecularViewerControls onSelectionChange={onSelectionChange} />
      )}
    </Box>
  );
};
```

### **Data Table with Filtering**
```typescript
// components/data-display/JobsTable.tsx
import React from 'react';
import {
  DataGrid,
  GridColDef,
  GridValueGetterParams,
  GridActionsCellItem,
} from '@mui/x-data-grid';
import { Chip, IconButton } from '@mui/material';
import { Visibility, Download } from '@mui/icons-material';
import type { DockingJob } from '../../types/api';

interface JobsTableProps {
  jobs: DockingJob[];
  loading?: boolean;
  onViewResults: (jobId: string) => void;
  onDownloadResults: (jobId: string) => void;
}

export const JobsTable: React.FC<JobsTableProps> = ({
  jobs,
  loading = false,
  onViewResults,
  onDownloadResults,
}) => {
  const columns: GridColDef[] = [
    {
      field: 'job_id',
      headerName: 'Job ID',
      width: 200,
      renderCell: (params) => (
        <code style={{ fontSize: '0.875rem' }}>
          {params.value.slice(0, 8)}...
        </code>
      ),
    },
    {
      field: 'status',
      headerName: 'Status',
      width: 120,
      renderCell: (params) => (
        <Chip
          label={params.value}
          color={getStatusColor(params.value)}
          size="small"
        />
      ),
    },
    {
      field: 'created_at',
      headerName: 'Created',
      width: 180,
      type: 'dateTime',
      valueGetter: (params: GridValueGetterParams) =>
        new Date(params.row.created_at),
    },
    {
      field: 'actions',
      type: 'actions',
      headerName: 'Actions',
      width: 120,
      getActions: (params) => [
        <GridActionsCellItem
          icon={<Visibility />}
          label="View Results"
          onClick={() => onViewResults(params.row.job_id)}
          disabled={params.row.status !== 'COMPLETED'}
        />,
        <GridActionsCellItem
          icon={<Download />}
          label="Download"
          onClick={() => onDownloadResults(params.row.job_id)}
          disabled={params.row.status !== 'COMPLETED'}
        />,
      ],
    },
  ];

  return (
    <DataGrid
      rows={jobs}
      columns={columns}
      loading={loading}
      getRowId={(row) => row.job_id}
      pageSizeOptions={[10, 25, 50]}
      initialState={{
        pagination: { paginationModel: { pageSize: 25 } },
      }}
      checkboxSelection
      disableRowSelectionOnClick
    />
  );
};

const getStatusColor = (status: string): 'default' | 'primary' | 'secondary' | 'error' | 'info' | 'success' | 'warning' => {
  switch (status) {
    case 'COMPLETED': return 'success';
    case 'RUNNING': return 'primary';
    case 'PENDING': return 'warning';
    case 'FAILED': return 'error';
    default: return 'default';
  }
};
```

---

## **Authentication Integration**

### **Auth Context**
```typescript
// contexts/AuthContext.tsx
import React, { createContext, useContext, useReducer, useEffect } from 'react';
import { authService } from '../services/auth/authService';
import type { User, AuthState } from '../types/auth';

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshToken: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [state, dispatch] = useReducer(authReducer, {
    user: null,
    isLoading: true,
    isAuthenticated: false,
  });

  useEffect(() => {
    // Initialize auth state from stored tokens
    authService.initializeAuth().then((user) => {
      dispatch({ type: 'AUTH_SUCCESS', payload: user });
    }).catch(() => {
      dispatch({ type: 'AUTH_FAILURE' });
    });
  }, []);

  const login = async (email: string, password: string) => {
    dispatch({ type: 'AUTH_REQUEST' });
    try {
      const user = await authService.login(email, password);
      dispatch({ type: 'AUTH_SUCCESS', payload: user });
    } catch (error) {
      dispatch({ type: 'AUTH_FAILURE' });
      throw error;
    }
  };

  const logout = async () => {
    await authService.logout();
    dispatch({ type: 'AUTH_LOGOUT' });
  };

  const refreshToken = async () => {
    try {
      const user = await authService.refreshToken();
      dispatch({ type: 'AUTH_SUCCESS', payload: user });
    } catch (error) {
      dispatch({ type: 'AUTH_FAILURE' });
      throw error;
    }
  };

  return (
    <AuthContext.Provider
      value={{
        ...state,
        login,
        logout,
        refreshToken,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};
```

---

## **Development Workflow**

### **Local Development**
```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Run type checking
npm run type-check

# Run linting
npm run lint

# Run tests
npm run test

# Build for production
npm run build
```

### **Code Quality Gates**
- **Pre-commit**: ESLint, Prettier, TypeScript compilation
- **CI/CD**: Unit tests, integration tests, type checking, build verification
- **Type Safety**: Strict TypeScript configuration with no implicit any
- **Bundle Analysis**: Vite bundle analyzer for performance optimization

### **Testing Strategy**
- **Unit Tests**: Component logic, utility functions, custom hooks
- **Integration Tests**: API integration, user interactions
- **E2E Tests**: Critical user flows using Playwright
- **Visual Regression**: Component library testing with Storybook

---

## **Production Considerations**

### **Performance Optimization**
- **Code Splitting**: Route-based and component-based lazy loading
- **Bundle Optimization**: Tree shaking, module federation for micro-frontends
- **Caching Strategy**: React Query for server state, service worker for assets
- **Image Optimization**: WebP format, responsive images for molecular structures

### **Security**
- **CSP Headers**: Content Security Policy for XSS protection
- **Token Management**: Secure storage and automatic refresh
- **API Validation**: Client-side validation as UX enhancement, not security
- **HTTPS Only**: Strict transport security for production

### **Deployment**
- **Static Hosting**: CDN deployment for optimal performance
- **Environment Configuration**: Runtime environment variables
- **Health Checks**: Frontend health monitoring and error boundary implementation
- **Progressive Web App**: Service worker for offline molecular data viewing

This React TypeScript frontend architecture provides a robust, type-safe, and maintainable foundation for the molecular analysis dashboard, with clear separation of concerns and modern development practices.
