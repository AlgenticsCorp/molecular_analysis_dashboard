import '@testing-library/jest-dom';

// Mock 3Dmol.js
global.window = Object.create(window);
const url = 'http://localhost';
Object.defineProperty(window, 'location', {
  value: {
    href: url,
    origin: url,
  },
});

// Mock environment variables
(global as unknown as { import: { meta: { env: Record<string, string> } } }).import = {
  meta: {
    env: {
      VITE_API_BASE_URL: 'http://localhost:8000/api/v1',
      VITE_APP_TITLE: 'Molecular Analysis Dashboard',
      VITE_APP_VERSION: '1.0.0',
    },
  },
};
