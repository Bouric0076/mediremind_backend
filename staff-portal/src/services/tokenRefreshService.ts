import type { CalendarIntegration } from '../types/calendar';

export interface TokenRefreshResult {
  success: boolean;
  integration?: CalendarIntegration;
  error?: string;
}

class TokenRefreshService {
  private refreshPromises: Map<string, Promise<TokenRefreshResult>> = new Map();
  private refreshIntervals: Map<string, NodeJS.Timeout> = new Map();
  private baseURL: string;

  constructor() {
    this.baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
  }

  /**
   * Check if a token needs refreshing (within 5 minutes of expiry)
   */
  needsRefresh(integration: CalendarIntegration): boolean {
    if (!integration.token_expiry) {
      return false;
    }

    const expiryTime = new Date(integration.token_expiry);
    const now = new Date();
    const fiveMinutesFromNow = new Date(now.getTime() + 5 * 60 * 1000);

    return expiryTime <= fiveMinutesFromNow;
  }

  /**
   * Refresh token for a specific integration
   */
  async refreshToken(integrationId: number | string): Promise<TokenRefreshResult> {
    const id = integrationId.toString();
    
    // Check if refresh is already in progress
    const existingPromise = this.refreshPromises.get(id);
    if (existingPromise) {
      return existingPromise;
    }

    // Create refresh promise
    const refreshPromise = this.performTokenRefresh(id);
    this.refreshPromises.set(id, refreshPromise);

    try {
      const result = await refreshPromise;
      return result;
    } finally {
      // Clean up promise
      this.refreshPromises.delete(id);
    }
  }

  /**
   * Perform the actual token refresh
   */
  private async performTokenRefresh(integrationId: string): Promise<TokenRefreshResult> {
    try {
      const token = localStorage.getItem('token') || sessionStorage.getItem('token');
      
      const response = await fetch(`${this.baseURL}/api/calendar/integrations/${integrationId}/refresh/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token && { Authorization: `Token ${token}` }),
        },
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error || `HTTP ${response.status}`);
      }

      const integration: CalendarIntegration = await response.json();
      
      console.log(`Successfully refreshed token for integration ${integrationId}`);
      
      return {
        success: true,
        integration,
      };
    } catch (error) {
      console.error(`Failed to refresh token for integration ${integrationId}:`, error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
      };
    }
  }

  /**
   * Check and refresh tokens for all integrations if needed
   */
  async checkAndRefreshAll(): Promise<TokenRefreshResult[]> {
    try {
      // Import here to avoid circular dependency
      const { calendarIntegrationService } = await import('./calendarIntegrationService');
      
      // Get all integrations using the original method to avoid circular dependency
      const integrations = await calendarIntegrationService.getIntegrationsOriginal();
      
      // Filter integrations that need refresh
      const integrationsToRefresh = integrations.filter(integration => 
        integration.status === 'active' && this.needsRefresh(integration)
      );

      if (integrationsToRefresh.length === 0) {
        return [];
      }

      console.log(`Refreshing tokens for ${integrationsToRefresh.length} integrations`);

      // Refresh tokens in parallel
      const refreshPromises = integrationsToRefresh.map(integration =>
        this.refreshToken(integration.id)
      );

      const results = await Promise.all(refreshPromises);
      
      // Log results
      const successful = results.filter(r => r.success).length;
      const failed = results.length - successful;
      
      if (successful > 0) {
        console.log(`Successfully refreshed ${successful} tokens`);
      }
      if (failed > 0) {
        console.warn(`Failed to refresh ${failed} tokens`);
      }

      return results;
    } catch (error) {
      console.error('Failed to check and refresh tokens:', error);
      return [];
    }
  }

  /**
   * Start automatic token refresh for an integration
   */
  startAutoRefresh(integration: CalendarIntegration): void {
    // Clear existing interval if any
    this.stopAutoRefresh(integration.id.toString());

    if (!integration.token_expiry || integration.status !== 'active') {
      return;
    }

    const expiryTime = new Date(integration.token_expiry);
    const now = new Date();
    
    // Calculate when to start refreshing (5 minutes before expiry)
    const refreshTime = new Date(expiryTime.getTime() - 5 * 60 * 1000);
    const timeUntilRefresh = refreshTime.getTime() - now.getTime();

    if (timeUntilRefresh <= 0) {
      // Token needs immediate refresh
      this.refreshToken(integration.id);
      return;
    }

    // Set timeout to refresh token
    const timeout = setTimeout(() => {
      this.refreshToken(integration.id).then(result => {
        if (result.success && result.integration) {
          // Schedule next refresh
          this.startAutoRefresh(result.integration);
        }
      });
    }, timeUntilRefresh);

    this.refreshIntervals.set(integration.id.toString(), timeout);
    console.log(`Scheduled token refresh for integration ${integration.id} in ${Math.round(timeUntilRefresh / 1000 / 60)} minutes`);
  }

  /**
   * Stop automatic token refresh for an integration
   */
  stopAutoRefresh(integrationId: number | string): void {
    const id = integrationId.toString();
    const interval = this.refreshIntervals.get(id);
    if (interval) {
      clearTimeout(interval);
      this.refreshIntervals.delete(id);
    }
  }

  /**
   * Start automatic refresh for all active integrations
   */
  async startAutoRefreshForAll(): Promise<void> {
    try {
      // Import here to avoid circular dependency
      const { calendarIntegrationService } = await import('./calendarIntegrationService');
      
      // Use the original method to avoid circular dependency
      const integrations = await calendarIntegrationService.getIntegrationsOriginal();
      
      integrations
        .filter(integration => integration.status === 'active')
        .forEach(integration => this.startAutoRefresh(integration));
        
    } catch (error) {
      console.error('Failed to start auto refresh for all integrations:', error);
    }
  }

  /**
   * Stop all automatic refresh timers
   */
  stopAllAutoRefresh(): void {
    this.refreshIntervals.forEach((interval) => {
      clearTimeout(interval);
    });
    this.refreshIntervals.clear();
  }

  /**
   * Initialize the token refresh service
   */
  async initialize(): Promise<void> {
    // Start auto refresh for all integrations
    await this.startAutoRefreshForAll();

    // Set up periodic check (every 30 minutes)
    setInterval(() => {
      this.checkAndRefreshAll();
    }, 30 * 60 * 1000);

    console.log('Token refresh service initialized');
  }
}

export const tokenRefreshService = new TokenRefreshService();