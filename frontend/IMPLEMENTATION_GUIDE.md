# React TypeScript Frontend Implementation Guide

Based on the design images in the `Frontend Design` folder, this document outlines the complete React TypeScript frontend implementation for the Molecular Analysis Dashboard.

## 🎨 Design Analysis

From the design files, the frontend should include:

1. **Platform_Dashboard_Page.png** - Main dashboard with statistics, recent activity, and quick actions
2. **Task_Library.png** - Pipeline management interface for viewing and managing molecular analysis tasks
3. **Execute_Service_Example.png** - Service execution interface for running docking jobs

## 🏗️ Complete Frontend Structure

```
frontend/
├── public/
│   ├── index.html              # Main HTML template
│   └── assets/                 # Static assets
├── src/
│   ├── components/             # Reusable UI components
│   │   ├── common/            # Generic components
│   │   │   ├── LoadingSpinner.tsx
│   │   │   ├── ErrorBoundary.tsx
│   │   │   ├── ConfirmDialog.tsx
│   │   │   └── DataTable.tsx
│   │   ├── forms/             # Form components
│   │   │   ├── MoleculeUpload.tsx
│   │   │   ├── PipelineForm.tsx
│   │   │   └── JobForm.tsx
│   │   ├── layout/            # Layout components
│   │   │   ├── Layout.tsx
│   │   │   ├── Header.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   └── Footer.tsx
│   │   ├── molecular/         # Molecular-specific components
│   │   │   ├── MolecularViewer.tsx
│   │   │   ├── MoleculeCard.tsx
│   │   │   └── DockingResults.tsx
│   │   ├── data-display/      # Data visualization
│   │   │   ├── JobsTable.tsx
│   │   │   ├── StatsCard.tsx
│   │   │   ├── ProgressChart.tsx
│   │   │   └── ResultsVisualization.tsx
│   │   └── auth/              # Authentication components
│   │       ├── LoginForm.tsx
│   │       ├── ProtectedRoute.tsx
│   │       └── UserMenu.tsx
│   │
│   ├── pages/                 # Page-level components
│   │   ├── Dashboard.tsx      # Platform dashboard (main overview)
│   │   ├── TaskLibrary.tsx    # Pipeline management
│   │   ├── ExecuteService.tsx # Job execution interface
│   │   ├── LoginPage.tsx      # User authentication
│   │   ├── Molecules/         # Molecule management
│   │   │   ├── MoleculeList.tsx
│   │   │   └── MoleculeDetail.tsx
│   │   ├── Jobs/              # Job monitoring
│   │   │   ├── JobList.tsx
│   │   │   ├── JobDetail.tsx
│   │   │   └── JobResults.tsx
│   │   └── Settings/          # User settings
│   │       ├── Profile.tsx
│   │       └── Organization.tsx
│   │
│   ├── hooks/                 # Custom React hooks
│   │   ├── api/              # API interaction hooks
│   │   │   ├── useJobs.tsx
│   │   │   ├── usePipelines.tsx
│   │   │   ├── useMolecules.tsx
│   │   │   └── useDashboard.tsx
│   │   ├── auth/             # Authentication hooks
│   │   │   ├── useAuth.tsx
│   │   │   └── usePermissions.tsx
│   │   └── ui/               # UI state hooks
│   │       ├── useLocalStorage.tsx
│   │       ├── useDebounce.tsx
│   │       └── useNotifications.tsx
│   │
│   ├── services/             # API services
│   │   ├── api/             # REST API clients
│   │   │   ├── client.ts    # Axios configuration
│   │   │   ├── auth.ts      # Authentication API
│   │   │   ├── jobs.ts      # Jobs API
│   │   │   ├── pipelines.ts # Pipelines API
│   │   │   ├── molecules.ts # Molecules API
│   │   │   └── dashboard.ts # Dashboard API
│   │   ├── auth/            # Authentication service
│   │   │   └── authService.ts
│   │   └── storage/         # Local storage utilities
│   │       └── localStorage.ts
│   │
│   ├── types/               # TypeScript definitions
│   │   ├── api.ts          # API types
│   │   ├── entities.ts     # Domain entities
│   │   └── ui.ts           # UI types
│   │
│   ├── utils/              # Utility functions
│   │   ├── formatting/     # Data formatting
│   │   │   ├── dateUtils.ts
│   │   │   ├── numberUtils.ts
│   │   │   └── moleculeUtils.ts
│   │   ├── validation/     # Form validation
│   │   │   ├── schemas.ts
│   │   │   └── validators.ts
│   │   └── constants/      # App constants
│   │       ├── endpoints.ts
│   │       ├── statusCodes.ts
│   │       └── themes.ts
│   │
│   ├── contexts/           # React contexts
│   │   ├── AuthContext.tsx
│   │   ├── ThemeContext.tsx
│   │   └── NotificationContext.tsx
│   │
│   ├── App.tsx             # Root component
│   ├── main.tsx            # Entry point
│   └── vite-env.d.ts       # Vite environment types
│
├── package.json            # Dependencies
├── tsconfig.json           # TypeScript config
├── vite.config.ts          # Vite config
├── eslint.config.js        # ESLint config
├── prettier.config.js      # Prettier config
└── jest.config.js          # Jest config
```

## 🎯 Key Page Implementations

### 1. Platform Dashboard (`Dashboard.tsx`)

**Features based on design:**
- Statistics cards showing job counts, molecule counts, pipeline usage
- Recent activity feed with job status updates
- Quick action buttons for common tasks
- System health indicators
- Performance metrics visualization

**Key Components:**
```typescript
interface DashboardProps {
  // Dashboard receives no props, fetches its own data
}

const Dashboard: React.FC<DashboardProps> = () => {
  // Uses React Query for data fetching
  // Displays stats cards in responsive grid
  // Shows recent jobs table
  // Provides quick action buttons
};
```

### 2. Task Library (`TaskLibrary.tsx`)

**Features based on design:**
- Grid/list view of available pipelines
- Pipeline cards with engine type, status, and metadata
- Search and filter functionality
- Create new pipeline button
- Pipeline details panel
- Edit/delete pipeline actions

**Key Components:**
```typescript
interface TaskLibraryProps {
  // Task library manages its own state
}

const TaskLibrary: React.FC<TaskLibraryProps> = () => {
  // Pipeline management interface
  // Grid layout with pipeline cards
  // Selection state for detailed view
  // CRUD operations for pipelines
};
```

### 3. Execute Service (`ExecuteService.tsx`)

**Features based on design:**
- Molecule selection interface (ligand and protein)
- Pipeline selection dropdown
- Parameter configuration form
- Job submission interface
- Real-time job progress tracking
- Result preview and download

**Key Components:**
```typescript
interface ExecuteServiceProps {
  initialPipelineId?: string;
}

const ExecuteService: React.FC<ExecuteServiceProps> = () => {
  // Multi-step form for job creation
  // Molecule browser and selector
  // Parameter validation and submission
  // Progress tracking and results display
};
```

## 🎨 Material-UI Theme Implementation

```typescript
const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2', // Blue for primary actions
      light: '#42a5f5',
      dark: '#1565c0',
    },
    secondary: {
      main: '#dc004e', // Red accent for important actions
    },
    success: {
      main: '#4caf50', // Green for completed jobs
    },
    warning: {
      main: '#ff9800', // Orange for pending jobs
    },
    error: {
      main: '#f44336', // Red for failed jobs
    },
    background: {
      default: '#f5f5f5',
      paper: '#ffffff',
    },
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
    h4: {
      fontWeight: 600,
    },
    h6: {
      fontWeight: 500,
    },
  },
  components: {
    MuiCard: {
      styleOverrides: {
        root: {
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
        },
      },
    },
  },
});
```

## 🔌 API Integration Patterns

### React Query Configuration
```typescript
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 3,
      staleTime: 5 * 60 * 1000, // 5 minutes
      refetchOnWindowFocus: false,
    },
    mutations: {
      retry: 1,
    },
  },
});
```

### Custom Hooks for Data Fetching
```typescript
// useJobs.tsx
export const useJobs = (filters?: JobFilters) => {
  return useQuery({
    queryKey: ['jobs', filters],
    queryFn: () => jobsApi.getJobs(filters),
    refetchInterval: 30000, // Refresh every 30 seconds
  });
};

export const useCreateJob = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: jobsApi.createJob,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard-stats'] });
    },
  });
};
```

## 🧪 3Dmol.js Integration

```typescript
interface MolecularViewerProps {
  moleculeData: MoleculeData;
  height?: number;
  showControls?: boolean;
}

const MolecularViewer: React.FC<MolecularViewerProps> = ({
  moleculeData,
  height = 400,
  showControls = true,
}) => {
  const viewerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!viewerRef.current || !moleculeData) return;

    // Initialize 3Dmol.js viewer
    const viewer = window.$3Dmol.createViewer(viewerRef.current);
    viewer.addModel(moleculeData.content, moleculeData.format);
    viewer.setStyle({}, { stick: {} });
    viewer.zoomTo();
    viewer.render();

    return () => viewer.clear();
  }, [moleculeData]);

  return (
    <div>
      <div ref={viewerRef} style={{ height, width: '100%' }} />
      {showControls && <MolecularViewerControls />}
    </div>
  );
};
```

## 🔒 Authentication & Security

```typescript
// Protected route wrapper
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return <LoadingSpinner />;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
};

// JWT token management with automatic refresh
const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  timeout: 30000,
});

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Automatic token refresh logic
      await authService.refreshToken();
      return apiClient.request(error.config);
    }
    return Promise.reject(error);
  }
);
```

## 📱 Responsive Design

The frontend uses Material-UI's responsive breakpoints:
- **xs**: 0px and up (mobile)
- **sm**: 600px and up (tablet)
- **md**: 900px and up (desktop)
- **lg**: 1200px and up (large desktop)

```typescript
// Responsive grid layout example
<Grid container spacing={3}>
  <Grid item xs={12} sm={6} md={4}>
    <StatsCard />
  </Grid>
  <Grid item xs={12} md={8}>
    <RecentJobsTable />
  </Grid>
</Grid>
```

## 🚀 Performance Optimizations

1. **Code Splitting**: Route-based lazy loading
2. **Bundle Optimization**: Vite's tree shaking and module federation
3. **Caching**: React Query for server state management
4. **Image Optimization**: WebP format for molecular structure images
5. **Virtual Scrolling**: For large molecule/job lists

## 🧪 Testing Strategy

```typescript
// Component testing example
describe('Dashboard', () => {
  it('displays statistics correctly', async () => {
    render(<Dashboard />);

    await waitFor(() => {
      expect(screen.getByText('Total Jobs')).toBeInTheDocument();
      expect(screen.getByText('Active Jobs')).toBeInTheDocument();
    });
  });

  it('handles loading states', () => {
    render(<Dashboard />);
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });
});
```

This comprehensive frontend implementation follows all the documented architecture patterns, uses Material-UI for consistent design, integrates with the backend API through typed interfaces, and provides a modern, responsive user experience for molecular analysis workflows.
