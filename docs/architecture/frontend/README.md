# Frontend Architecture Documentation

*React TypeScript application architecture, UI patterns, and component organization.*

## Overview

This section documents the frontend architecture including React component patterns, state management, UI/UX design systems, and client-side application structure for the molecular analysis dashboard.

## Frontend Components

### **[Frontend Architecture](architecture.md)**
React application architecture and design patterns
- Component hierarchy and organization
- State management strategies with React Query
- Routing and navigation patterns
- Performance optimization techniques

### **[Admin Panel Implementation](admin-panel-plan.md)**
Administrative interface design and implementation
- User management and organization administration
- System configuration and settings management
- Analytics dashboard and reporting interfaces
- Role-based UI adaptation patterns

### **[Frontend Description](frontend-description.md)**
Comprehensive frontend feature description and capabilities
- Application overview and user workflows
- Feature specifications and user interactions
- UI/UX design principles and guidelines
- Technical requirements and browser support

## Architecture Patterns

### React Component Architecture
```
┌─────────────────────────────────────┐
│            App Shell               │ ← Main application layout
├─────────────────────────────────────┤
│  Pages    │  Components │ Services  │ ← Feature organization
├─────────────────────────────────────┤
│       Shared Components            │ ← Reusable UI components
├─────────────────────────────────────┤
│        State Management            │ ← React Query + Context
└─────────────────────────────────────┘
```

### State Management Strategy
```
┌─────────────────────────────────────┐
│         React Query                │ ← Server state management
├─────────────────────────────────────┤
│      React Context/Reducer         │ ← Client state management
├─────────────────────────────────────┤
│      Component Local State         │ ← UI-specific state
├─────────────────────────────────────┤
│         URL State                  │ ← Router state persistence
└─────────────────────────────────────┘
```

### Component Organization
```
frontend/src/
├── components/              # Reusable UI components
│   ├── common/             # Generic components (Button, Input, etc.)
│   ├── forms/              # Form components and validation
│   ├── layout/             # Layout components (Header, Sidebar)
│   ├── molecular/          # Molecule-specific components
│   └── visualization/      # 3D visualization components
├── pages/                  # Application pages/routes
│   ├── dashboard/          # Dashboard pages
│   ├── molecules/          # Molecule management pages
│   ├── jobs/              # Job management pages
│   ├── admin/             # Administrative pages
│   └── auth/              # Authentication pages
├── services/               # API client services
├── hooks/                  # Custom React hooks
├── types/                  # TypeScript type definitions
├── utils/                  # Utility functions
└── styles/                 # Global styles and themes
```

## Key Features

### 🎨 **Modern UI Framework**
- **Material-UI (MUI)**: Comprehensive design system with theming
- **TypeScript**: Full type safety throughout the application
- **Responsive Design**: Mobile-first responsive layouts
- **Accessibility**: WCAG 2.1 AA compliance standards
- **Dark/Light Mode**: User-configurable theme switching

### 🔄 **State Management**
- **React Query**: Server state management with caching and synchronization
- **React Context**: Global application state management
- **Form State**: React Hook Form for complex form handling
- **URL State**: Router-based state persistence
- **Local Storage**: Client-side preference persistence

### 🧬 **Molecular Visualization**
- **3Dmol.js Integration**: Interactive 3D molecular visualization
- **Real-time Rendering**: Dynamic molecule structure display
- **Docking Result Visualization**: Binding site and affinity visualization
- **Export Capabilities**: Image and data export functionality
- **Performance Optimization**: Efficient rendering for large molecules

### 📱 **User Experience**
- **Progressive Web App**: Offline capabilities and app-like experience
- **Real-time Updates**: WebSocket integration for live job status
- **Drag & Drop**: Intuitive file upload and organization
- **Keyboard Navigation**: Full keyboard accessibility
- **Loading States**: Comprehensive loading and skeleton screens

## Development Guidelines

### Component Development
```typescript
// Component template with TypeScript and proper typing
interface MoleculeViewerProps {
  molecule: Molecule;
  showControls?: boolean;
  onStructureSelect?: (selection: AtomSelection) => void;
}

export const MoleculeViewer: React.FC<MoleculeViewerProps> = ({
  molecule,
  showControls = true,
  onStructureSelect
}) => {
  // Implementation with hooks and proper error handling
  const { data: structure, isLoading, error } = useQuery({
    queryKey: ['molecule-structure', molecule.id],
    queryFn: () => fetchMoleculeStructure(molecule.id)
  });

  if (isLoading) return <StructureSkeleton />;
  if (error) return <ErrorDisplay error={error} />;

  return (
    <Box sx={{ position: 'relative' }}>
      <Structure3DViewer
        structure={structure}
        onAtomSelect={onStructureSelect}
      />
      {showControls && <ViewerControls />}
    </Box>
  );
};
```

### State Management Patterns
```typescript
// React Query for server state
const useJobs = () => {
  return useQuery({
    queryKey: ['jobs'],
    queryFn: fetchJobs,
    staleTime: 30000,
    refetchInterval: 5000 // Real-time updates
  });
};

// Context for global state
interface AppState {
  user: User | null;
  organization: Organization | null;
  theme: 'light' | 'dark';
}

const AppContext = createContext<AppState | undefined>(undefined);
```

### Form Handling
```typescript
// React Hook Form with Zod validation
const jobSchema = z.object({
  moleculeId: z.string().min(1, 'Molecule is required'),
  targetProtein: z.string().min(1, 'Target protein is required'),
  engine: z.enum(['vina', 'smina', 'gnina'])
});

type JobFormData = z.infer<typeof jobSchema>;

const CreateJobForm = () => {
  const { control, handleSubmit, formState: { errors } } = useForm<JobFormData>({
    resolver: zodResolver(jobSchema)
  });

  const mutation = useMutation({
    mutationFn: createJob,
    onSuccess: () => {
      // Handle success
    }
  });

  return (
    <form onSubmit={handleSubmit(mutation.mutate)}>
      {/* Form fields with Controller components */}
    </form>
  );
};
```

## Testing Strategies

### Component Testing
```typescript
// Example component test with React Testing Library
import { render, screen, fireEvent } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MoleculeUpload } from './MoleculeUpload';

describe('MoleculeUpload', () => {
  it('uploads file successfully', async () => {
    const queryClient = new QueryClient();
    const onSuccess = jest.fn();

    render(
      <QueryClientProvider client={queryClient}>
        <MoleculeUpload onSuccess={onSuccess} />
      </QueryClientProvider>
    );

    const file = new File(['molecule data'], 'test.sdf', { type: 'chemical/x-sdf' });
    const input = screen.getByLabelText(/upload/i);

    fireEvent.change(input, { target: { files: [file] } });
    fireEvent.click(screen.getByRole('button', { name: /upload/i }));

    await waitFor(() => {
      expect(onSuccess).toHaveBeenCalledWith(expect.objectContaining({
        name: 'test.sdf'
      }));
    });
  });
});
```

### E2E Testing
```typescript
// Playwright E2E test example
import { test, expect } from '@playwright/test';

test('molecular docking workflow', async ({ page }) => {
  await page.goto('/dashboard');

  // Upload molecule
  await page.click('[data-testid=upload-molecule]');
  await page.setInputFiles('[data-testid=file-input]', 'tests/fixtures/molecule.sdf');

  // Create docking job
  await page.click('[data-testid=create-job]');
  await page.selectOption('[data-testid=engine-select]', 'vina');
  await page.click('[data-testid=submit-job]');

  // Verify job creation
  await expect(page.locator('[data-testid=job-status]')).toContainText('Running');
});
```

## Performance Optimization

### Bundle Optimization
- **Code Splitting**: Route-based and component-based code splitting
- **Tree Shaking**: Eliminate unused code from bundles
- **Dynamic Imports**: Load components and libraries on demand
- **Service Workers**: Cache assets and API responses for offline use

### Runtime Performance
- **React.memo**: Prevent unnecessary re-renders
- **useMemo/useCallback**: Optimize expensive calculations
- **Virtual Scrolling**: Handle large lists efficiently
- **Image Optimization**: Lazy loading and responsive images

## Related Documentation

- **[System Architecture](../system-design/README.md)** - Overall system design context
- **[API Integration](../../api/README.md)** - Backend service integration
- **[Development Setup](../../development/getting-started/setup.md)** - Frontend development environment
- **[Testing Workflows](../../development/workflows/testing-workflows.md)** - Frontend testing strategies
- **[Deployment](../../deployment/docker/setup.md)** - Frontend deployment configuration

## Design Assets

### UI Mockups
Located in `../../assets/frontend-mockups/`:
- `Platform_Dashboard_Page.png` - Main dashboard design
- `Task_Library.png` - Task library interface
- `Execute_Service_Example.png` - Job execution workflow

### Design System
- **Color Palette**: Material-UI theme with custom molecular analysis colors
- **Typography**: Roboto font family with custom molecular notation support
- **Icons**: Material-UI icons + custom molecular structure icons
- **Spacing**: 8px grid system for consistent layouts
