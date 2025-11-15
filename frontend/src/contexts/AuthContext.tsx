/* eslint-disable react-refresh/only-export-components */
/**
 * Authentication context for managing user state and authentication.
 *
 * Provides centralized authentication state management using React Context
 * with TypeScript support and automatic token refresh capabilities.
 */

import React, { createContext, useContext, useReducer, useEffect, ReactNode } from 'react';
import { authService } from '@/services/auth/authService';
import type { User } from '@/types/api';

interface AuthState {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  error: string | null;
}

interface AuthContextType extends AuthState {
  login: (email: string, password: string, orgId: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshToken: () => Promise<void>;
  clearError: () => void;
}

type AuthAction =
  | { type: 'AUTH_REQUEST' }
  | { type: 'AUTH_SUCCESS'; payload: User }
  | { type: 'AUTH_FAILURE'; payload: string }
  | { type: 'AUTH_LOGOUT' }
  | { type: 'CLEAR_ERROR' };

const initialState: AuthState = {
  user: null,
  isLoading: true,
  isAuthenticated: false,
  error: null,
};

export const authReducer = (state: AuthState, action: AuthAction): AuthState => {
  switch (action.type) {
    case 'AUTH_REQUEST':
      return {
        ...state,
        isLoading: true,
        error: null,
      };
    case 'AUTH_SUCCESS':
      return {
        ...state,
        user: action.payload,
        isLoading: false,
        isAuthenticated: true,
        error: null,
      };
    case 'AUTH_FAILURE':
      return {
        ...state,
        user: null,
        isLoading: false,
        isAuthenticated: false,
        error: action.payload,
      };
    case 'AUTH_LOGOUT':
      return {
        ...state,
        user: null,
        isLoading: false,
        isAuthenticated: false,
        error: null,
      };
    case 'CLEAR_ERROR':
      return {
        ...state,
        error: null,
      };
    default:
      return state;
  }
};

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [state, dispatch] = useReducer(authReducer, initialState);

  useEffect(() => {
    // Initialize auth state from stored tokens
    const initializeAuth = async () => {
      const isDemoAuthEnabled = String(import.meta.env.VITE_ENABLE_DEMO_AUTH ?? 'false')
        .toLowerCase()
        .trim() === 'true';
      try {
        const user = await authService.initializeAuth();
        if (user) {
          dispatch({ type: 'AUTH_SUCCESS', payload: user });
          return;
        }

        if (isDemoAuthEnabled) {
          const now = new Date().toISOString();
          const demoUser: User = {
            user_id: (
              import.meta.env.VITE_DEMO_USER_ID || '00000000-0000-0000-0000-000000000000'
            ).toString(),
            email: (import.meta.env.VITE_DEMO_USER_EMAIL || 'demo@local.dev').toString(),
            org_id: (import.meta.env.VITE_DEMO_ORG_ID || 'demo-org').toString(),
            roles: (import.meta.env.VITE_DEMO_USER_ROLES || 'admin')
              .split(',')
              .map((role) => role.trim())
              .filter(Boolean),
            created_at: now,
            updated_at: now,
          };

          const demoAccessToken = import.meta.env.VITE_DEMO_ACCESS_TOKEN;
          const demoRefreshToken = import.meta.env.VITE_DEMO_REFRESH_TOKEN;

          localStorage.setItem('mad_user', JSON.stringify(demoUser));

          if (demoAccessToken) {
            localStorage.setItem('mad_access_token', demoAccessToken.toString());
          }

          if (demoRefreshToken) {
            localStorage.setItem('mad_refresh_token', demoRefreshToken.toString());
          }

          dispatch({ type: 'AUTH_SUCCESS', payload: demoUser });
          return;
        }

        dispatch({ type: 'AUTH_FAILURE', payload: 'No valid session found' });
      } catch (error) {
        dispatch({
          type: 'AUTH_FAILURE',
          payload: error instanceof Error ? error.message : 'Authentication failed',
        });
      }
    };

    initializeAuth();
  }, []);

  const login = async (email: string, password: string, orgId: string): Promise<void> => {
    dispatch({ type: 'AUTH_REQUEST' });
    try {
      const user = await authService.login(email, password, orgId);
      dispatch({ type: 'AUTH_SUCCESS', payload: user });
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Login failed';
      dispatch({ type: 'AUTH_FAILURE', payload: errorMessage });
      throw error;
    }
  };

  const logout = async (): Promise<void> => {
    try {
      await authService.logout();
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      dispatch({ type: 'AUTH_LOGOUT' });
    }
  };

  const refreshToken = async (): Promise<void> => {
    try {
      const user = await authService.refreshToken();
      dispatch({ type: 'AUTH_SUCCESS', payload: user });
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Token refresh failed';
      dispatch({ type: 'AUTH_FAILURE', payload: errorMessage });
      throw error;
    }
  };

  const clearError = (): void => {
    dispatch({ type: 'CLEAR_ERROR' });
  };

  const value: AuthContextType = {
    ...state,
    login,
    logout,
    refreshToken,
    clearError,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
