/**
 * Authentication service for handling login, logout, and token management.
 *
 * Provides centralized authentication logic with automatic token refresh
 * and secure storage management.
 */

import { apiClient } from '@/services/api/client';
import type { User, LoginRequest, LoginResponse, RefreshTokenRequest } from '@/types/api';

class AuthService {
  private readonly ACCESS_TOKEN_KEY = 'mad_access_token';
  private readonly REFRESH_TOKEN_KEY = 'mad_refresh_token';
  private readonly USER_KEY = 'mad_user';

  /**
   * Initialize authentication state from stored tokens.
   * @returns User object if valid session exists, null otherwise
   */
  async initializeAuth(): Promise<User | null> {
    const accessToken = this.getAccessToken();
    const user = this.getStoredUser();

    if (!accessToken || !user) {
      this.clearTokens();
      return null;
    }

    try {
      // Verify token validity by making a test request
      await apiClient.get('/auth/me');
      return user;
    } catch {
      // Token might be expired, try to refresh
      try {
        return await this.refreshToken();
      } catch {
        this.clearTokens();
        return null;
      }
    }
  }

  /**
   * Authenticate user with email, password, and organization ID.
   */
  async login(email: string, password: string, orgId: string): Promise<User> {
    const request: LoginRequest = {
      email,
      password,
      org_id: orgId,
    };

    try {
      const response = await apiClient.post<LoginResponse>('/auth/login', request);
      const { access_token, refresh_token, user } = response.data;

      this.setTokens(access_token, refresh_token);
      this.setUser(user);

      return user;
    } catch (error) {
      this.clearTokens();
      throw new Error(this.getErrorMessage(error, 'Login failed'));
    }
  }

  /**
   * Log out user and clear all stored authentication data.
   */
  async logout(): Promise<void> {
    try {
      const refreshToken = this.getRefreshToken();
      if (refreshToken) {
        await apiClient.post('/auth/logout', { refresh_token: refreshToken });
      }
    } catch (error) {
      console.warn('Logout request failed:', error);
    } finally {
      this.clearTokens();
    }
  }

  /**
   * Refresh access token using stored refresh token.
   */
  async refreshToken(): Promise<User> {
    const refreshToken = this.getRefreshToken();
    if (!refreshToken) {
      throw new Error('No refresh token available');
    }

    try {
      const request: RefreshTokenRequest = { refresh_token: refreshToken };
      const response = await apiClient.post<LoginResponse>('/auth/refresh', request);
      const { access_token, refresh_token: newRefreshToken, user } = response.data;

      this.setTokens(access_token, newRefreshToken);
      this.setUser(user);

      return user;
    } catch (error) {
      this.clearTokens();
      throw new Error(this.getErrorMessage(error, 'Token refresh failed'));
    }
  }

  /**
   * Get stored access token.
   */
  getAccessToken(): string | null {
    return localStorage.getItem(this.ACCESS_TOKEN_KEY);
  }

  /**
   * Get stored refresh token.
   */
  getRefreshToken(): string | null {
    return localStorage.getItem(this.REFRESH_TOKEN_KEY);
  }

  /**
   * Get stored user data.
   */
  getStoredUser(): User | null {
    const userStr = localStorage.getItem(this.USER_KEY);
    if (!userStr) return null;

    try {
      return JSON.parse(userStr) as User;
    } catch {
      return null;
    }
  }

  /**
   * Store authentication tokens securely.
   */
  private setTokens(accessToken: string, refreshToken: string): void {
    localStorage.setItem(this.ACCESS_TOKEN_KEY, accessToken);
    localStorage.setItem(this.REFRESH_TOKEN_KEY, refreshToken);
  }

  /**
   * Store user data.
   */
  private setUser(user: User): void {
    localStorage.setItem(this.USER_KEY, JSON.stringify(user));
  }

  /**
   * Clear all stored authentication data.
   */
  private clearTokens(): void {
    localStorage.removeItem(this.ACCESS_TOKEN_KEY);
    localStorage.removeItem(this.REFRESH_TOKEN_KEY);
    localStorage.removeItem(this.USER_KEY);
  }

  /**
   * Extract error message from API error response.
   */
  private getErrorMessage(error: unknown, defaultMessage: string): string {
    if (error && typeof error === 'object' && 'response' in error) {
      const apiError = error as { response?: { data?: { message?: string } } };
      return apiError.response?.data?.message || defaultMessage;
    }

    if (error instanceof Error) {
      return error.message;
    }

    return defaultMessage;
  }
}

export const authService = new AuthService();
