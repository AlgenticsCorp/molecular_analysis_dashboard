/**
 * Feature Flag Service
 *
 * Manages feature flags for controlled rollout of new functionality,
 * including the ability to toggle between API and static data sources.
 */

import { FeatureFlags } from '../types/tasks';

export class FeatureFlagService {
  private flags: FeatureFlags;
  private listeners: Set<(flags: FeatureFlags) => void> = new Set();

  constructor() {
    this.flags = this.loadFlags();
  }

  /**
   * Load feature flags from environment variables and localStorage.
   * Environment variables take precedence over localStorage.
   */
  private loadFlags(): FeatureFlags {
    const defaultFlags: FeatureFlags = {
      useApiTasks: false, // Default to static data for safety
      enableTaskCache: true,
      debugMode: false,
    };

    // Load from environment variables (for build-time configuration)
    const envFlags: Partial<FeatureFlags> = {};

    const useApiTasks = this.getBooleanEnv('VITE_USE_API_TASKS');
    if (useApiTasks !== undefined) envFlags.useApiTasks = useApiTasks;

    const enableTaskCache = this.getBooleanEnv('VITE_ENABLE_TASK_CACHE');
    if (enableTaskCache !== undefined) envFlags.enableTaskCache = enableTaskCache;

    const debugMode = this.getBooleanEnv('VITE_DEBUG_MODE');
    if (debugMode !== undefined) envFlags.debugMode = debugMode;

    // Load from localStorage (for runtime configuration)
    const localFlags = this.loadFromLocalStorage();

    // Merge flags: localStorage > env > defaults
    return {
      ...defaultFlags,
      ...envFlags,
      ...localFlags,
    };
  }

  /**
   * Get boolean value from environment variable.
   */
  private getBooleanEnv(key: string): boolean | undefined {
    const value = import.meta.env[key];
    if (value === undefined) return undefined;
    return value === 'true' || value === '1';
  }

  /**
   * Load flags from localStorage.
   */
  private loadFromLocalStorage(): Partial<FeatureFlags> {
    try {
      const stored = localStorage.getItem('feature-flags');
      if (!stored) return {};

      const parsed = JSON.parse(stored);
      return this.validateFlags(parsed);
    } catch (error) {
      console.warn('Failed to load feature flags from localStorage:', error);
      return {};
    }
  }

  /**
   * Validate and sanitize flags object.
   */
  private validateFlags(flags: any): Partial<FeatureFlags> {
    const validated: Partial<FeatureFlags> = {};

    if (typeof flags.useApiTasks === 'boolean') {
      validated.useApiTasks = flags.useApiTasks;
    }

    if (typeof flags.enableTaskCache === 'boolean') {
      validated.enableTaskCache = flags.enableTaskCache;
    }

    if (typeof flags.debugMode === 'boolean') {
      validated.debugMode = flags.debugMode;
    }

    return validated;
  }

  /**
   * Save flags to localStorage.
   */
  private saveToLocalStorage(): void {
    try {
      localStorage.setItem('feature-flags', JSON.stringify(this.flags));
    } catch (error) {
      console.warn('Failed to save feature flags to localStorage:', error);
    }
  }

  /**
   * Get current feature flags.
   */
  getFlags(): FeatureFlags {
    return { ...this.flags };
  }

  /**
   * Get specific flag value.
   */
  getFlag(key: keyof FeatureFlags): boolean {
    return this.flags[key];
  }

  /**
   * Set specific flag value.
   */
  setFlag(key: keyof FeatureFlags, value: boolean): void {
    const oldValue = this.flags[key];
    this.flags[key] = value;

    if (oldValue !== value) {
      this.saveToLocalStorage();
      this.notifyListeners();

      if (this.flags.debugMode) {
        console.log(`Feature flag changed: ${key} = ${value}`);
      }
    }
  }

  /**
   * Update multiple flags at once.
   */
  updateFlags(updates: Partial<FeatureFlags>): void {
    let hasChanges = false;

    Object.entries(updates).forEach(([key, value]) => {
      if (key in this.flags && this.flags[key as keyof FeatureFlags] !== value) {
        this.flags[key as keyof FeatureFlags] = value;
        hasChanges = true;
      }
    });

    if (hasChanges) {
      this.saveToLocalStorage();
      this.notifyListeners();

      if (this.flags.debugMode) {
        console.log('Feature flags updated:', updates);
      }
    }
  }

  /**
   * Reset all flags to defaults.
   */
  resetFlags(): void {
    this.flags = {
      useApiTasks: false,
      enableTaskCache: true,
      debugMode: false,
    };

    this.saveToLocalStorage();
    this.notifyListeners();

    if (this.flags.debugMode) {
      console.log('Feature flags reset to defaults');
    }
  }

  /**
   * Subscribe to flag changes.
   */
  subscribe(listener: (flags: FeatureFlags) => void): () => void {
    this.listeners.add(listener);

    // Return unsubscribe function
    return () => {
      this.listeners.delete(listener);
    };
  }

  /**
   * Notify all listeners of flag changes.
   */
  private notifyListeners(): void {
    this.listeners.forEach((listener) => {
      try {
        listener(this.getFlags());
      } catch (error) {
        console.error('Error in feature flag listener:', error);
      }
    });
  }

  /**
   * Check if API tasks should be used.
   */
  shouldUseApiTasks(): boolean {
    return this.flags.useApiTasks;
  }

  /**
   * Check if task caching is enabled.
   */
  isCacheEnabled(): boolean {
    return this.flags.enableTaskCache;
  }

  /**
   * Check if debug mode is enabled.
   */
  isDebugMode(): boolean {
    return this.flags.debugMode;
  }

  /**
   * Enable API tasks (useful for gradual rollout).
   */
  enableApiTasks(): void {
    this.setFlag('useApiTasks', true);
  }

  /**
   * Disable API tasks (fallback to static data).
   */
  disableApiTasks(): void {
    this.setFlag('useApiTasks', false);
  }

  /**
   * Toggle API tasks.
   */
  toggleApiTasks(): void {
    this.setFlag('useApiTasks', !this.flags.useApiTasks);
  }

  /**
   * Get debug information about current flags.
   */
  getDebugInfo(): {
    flags: FeatureFlags;
    environment: Record<string, string>;
    localStorage: string | null;
  } {
    return {
      flags: this.getFlags(),
      environment: {
        VITE_USE_API_TASKS: import.meta.env['VITE_USE_API_TASKS'] || 'undefined',
        VITE_ENABLE_TASK_CACHE: import.meta.env['VITE_ENABLE_TASK_CACHE'] || 'undefined',
        VITE_DEBUG_MODE: import.meta.env['VITE_DEBUG_MODE'] || 'undefined',
      },
      localStorage: localStorage.getItem('feature-flags'),
    };
  }
}

// Global instance
export const featureFlagService = new FeatureFlagService();

// React hook for using feature flags
export const useFeatureFlags = () => {
  const [flags, setFlags] = React.useState(featureFlagService.getFlags());

  React.useEffect(() => {
    const unsubscribe = featureFlagService.subscribe(setFlags);
    return unsubscribe;
  }, []);

  return {
    flags,
    getFlag: (key: keyof FeatureFlags) => featureFlagService.getFlag(key),
    setFlag: (key: keyof FeatureFlags, value: boolean) => featureFlagService.setFlag(key, value),
    updateFlags: (updates: Partial<FeatureFlags>) => featureFlagService.updateFlags(updates),
    resetFlags: () => featureFlagService.resetFlags(),
    shouldUseApiTasks: () => featureFlagService.shouldUseApiTasks(),
    isDebugMode: () => featureFlagService.isDebugMode(),
    enableApiTasks: () => featureFlagService.enableApiTasks(),
    disableApiTasks: () => featureFlagService.disableApiTasks(),
    toggleApiTasks: () => featureFlagService.toggleApiTasks(),
  };
};

// React import (will be resolved by bundler)
import React from 'react';
