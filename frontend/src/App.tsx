import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { CssBaseline, Box } from '@mui/material';
import { Layout } from './components/layout/Layout';
import { Dashboard } from './pages/Dashboard';
import { TaskLibrary } from './pages/TaskLibrary';
import { ExecuteTasks } from './pages/ExecuteTasks';
import { Pipelines } from './pages/Pipelines';
import { JobManager } from './pages/JobManager';
import { FileManager } from './pages/FileManager';
import { AdminPanel } from './pages/AdminPanel';
import { Settings } from './pages/Settings';

// Create theme based on molecular analysis design patterns
const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2', // Blue for primary actions
      light: '#42a5f5',
      dark: '#1565c0',
    },
    secondary: {
      main: '#dc004e', // Pink/red for secondary actions
      light: '#f06292',
      dark: '#ad1457',
    },
    background: {
      default: '#f5f7fa',
      paper: '#ffffff',
    },
    text: {
      primary: '#2c3e50',
      secondary: '#7f8c8d',
    },
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
    h4: {
      fontWeight: 600,
      color: '#2c3e50',
    },
    h5: {
      fontWeight: 500,
      color: '#2c3e50',
    },
    h6: {
      fontWeight: 500,
      color: '#34495e',
    },
  },
  components: {
    MuiCard: {
      styleOverrides: {
        root: {
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
          borderRadius: '8px',
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          fontWeight: 500,
        },
      },
    },
  },
});

// Create React Query client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 3,
      staleTime: 5 * 60 * 1000, // 5 minutes
      refetchOnWindowFocus: false,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <Router>
          <Box sx={{ display: 'flex', minHeight: '100vh' }}>
            <Layout>
              <Routes>
                <Route path="/" element={<Navigate to="/dashboard" replace />} />
                <Route path="/dashboard" element={<Dashboard />} />
                <Route path="/task-library" element={<TaskLibrary />} />
                <Route path="/execute-tasks" element={<ExecuteTasks />} />
                <Route path="/pipelines" element={<Pipelines />} />
                <Route path="/job-manager" element={<JobManager />} />
                <Route path="/file-manager" element={<FileManager />} />
                <Route path="/admin-panel" element={<AdminPanel />} />
                <Route path="/settings" element={<Settings />} />
              </Routes>
            </Layout>
          </Box>
        </Router>
      </ThemeProvider>
    </QueryClientProvider>
  );
}

export default App
