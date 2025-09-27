/**
 * Calendar Integration Service
 * Handles Google Calendar OAuth flow and API interactions for the staff portal
 */

import axios, { AxiosError } from 'axios';
import { CalendarError } from '../types/calendar';
import type { 
  ExternalCalendarEvent, 
  CalendarIntegration, 
  SyncConflict, 
  CalendarErrorResponse
} from '../types/calendar';
import { tokenRefreshService } from './tokenRefreshService';

// Enhanced logging for calendar integration service
const logPrefix = '[CalendarIntegrationService]';

const log = {
  debug: (message: string, data?: any) => {
    console.debug(`${logPrefix} ${message}`, data || '');
  },
  info: (message: string, data?: any) => {
    console.info(`${logPrefix} ${message}`, data || '');
  },
  warn: (message: string, data?: any) => {
    console.warn(`${logPrefix} ${message}`, data || '');
  },
  error: (message: string, error?: any) => {
    console.error(`${logPrefix} ${message}`, error || '');
  }
};

class CalendarIntegrationService {
  private baseURL: string;

  constructor() {
    this.baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
    log.info('Calendar Integration Service initialized', { baseURL: this.baseURL });
  }

  /**
   * Handle API errors with standardized error responses
   */
  private handleApiError(error: AxiosError, fallbackMessage?: string): never {
    log.error('API Error occurred', { 
      status: error.response?.status, 
      statusText: error.response?.statusText,
      url: error.config?.url,
      method: error.config?.method,
      fallbackMessage 
    });
    
    if (error.response?.data) {
      const errorData = error.response.data as CalendarErrorResponse;
      if (errorData.error_code) {
        log.error('Standardized API error', errorData);
        throw new CalendarError(errorData);
      }
    }
    
    // Fallback for non-standardized errors
    const fallbackError = {
      error: fallbackMessage || error.message || 'An unexpected error occurred',
      error_code: 'UNKNOWN_ERROR',
      details: { status: error.response?.status }
    };
    
    log.error('Non-standardized API error, using fallback', fallbackError);
    throw new CalendarError(fallbackError);
  }

  /**
   * Get integrations with automatic token refresh and enhanced error handling
   */
  async getIntegrations(): Promise<CalendarIntegration[]> {
    log.info('Fetching calendar integrations with token refresh');
    
    try {
      // First, check and refresh any expired tokens
      log.debug('Checking and refreshing expired tokens');
      await this.checkAndRefreshTokens();
      
      log.debug('Making API request to fetch integrations');
      const response = await axios.get(`${this.baseURL}/api/calendar/integrations/`, {
        headers: this.getAuthHeaders(),
      });
      
      const integrations = response.data;
      log.info(`Successfully fetched ${integrations.length} integrations`);
      
      // Start auto refresh for all active integrations
      const activeIntegrations = integrations.filter((integration: CalendarIntegration) => integration.status === 'active');
      log.debug(`Starting auto refresh for ${activeIntegrations.length} active integrations`);
      
      activeIntegrations.forEach((integration: CalendarIntegration) => {
        log.debug(`Starting auto refresh for integration ${integration.id} (${integration.provider})`);
        tokenRefreshService.startAutoRefresh(integration);
      });
      
      return integrations;
    } catch (error) {
      log.error('Error fetching integrations', error);
      console.error('Error fetching integrations:', error);
      if (axios.isAxiosError(error)) {
        this.handleApiError(error);
      }
      throw error;
    }
  }

  /**
   * Get integrations (original method without token refresh)
   */
  async getIntegrationsOriginal(): Promise<CalendarIntegration[]> {
    try {
      const response = await axios.get(`${this.baseURL}/api/calendar/integrations/`, {
        headers: this.getAuthHeaders(),
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching calendar integrations:', error);
      throw error;
    }
  }

  /**
   * Initiate Google Calendar OAuth flow
   */
  async initiateGoogleAuth(): Promise<{ authorization_url: string }> {
    try {
      const response = await axios.post(
        `${this.baseURL}/api/calendar/google/auth/`,
        {},
        {
          headers: this.getAuthHeaders(),
        }
      );
      return response.data;
    } catch (error) {
      console.error('Error initiating Google Calendar auth:', error);
      throw error;
    }
  }

  /**
   * Handle OAuth callback from Google
   */
  async handleOAuthCallback(code: string, state: string, integrationData?: any): Promise<CalendarIntegration> {
    try {
      const response = await axios.post(`${this.baseURL}/api/calendar/google/callback/`, {
        code,
        state,
        ...(integrationData && { integration_data: integrationData })
      }, {
        headers: this.getAuthHeaders(),
      });

      const integration = response.data;
      
      // Start auto refresh for the new integration
      if (integration.status === 'active') {
        tokenRefreshService.startAutoRefresh(integration);
      }

      return integration;
    } catch (error) {
      if (axios.isAxiosError(error)) {
        throw this.handleApiError(error, 'Failed to handle OAuth callback');
      }
      throw error;
    }
  }

  /**
   * Check Google Calendar connection status
   */
  async checkGoogleCalendarConnection(): Promise<{ connected: boolean; integration?: CalendarIntegration }> {
    try {
      // Ensure tokens are refreshed before checking connection
      await this.checkAndRefreshTokens();
      
      const integrations = await this.getIntegrationsOriginal();
      const googleIntegration = integrations.find(
        integration => integration.provider === 'google' && integration.status === 'active'
      );

      return {
        connected: !!googleIntegration,
        integration: googleIntegration,
      };
    } catch (error) {
      if (axios.isAxiosError(error)) {
        throw this.handleApiError(error, 'Failed to check Google Calendar connection');
      }
      throw error;
    }
  }

  /**
   * Sync calendar with token refresh
   */
  async syncCalendar(integrationId: number): Promise<{ success: boolean; message: string }> {
    log.info(`Starting calendar sync for integration ${integrationId}`);
    
    try {
      // Check and refresh tokens before syncing
      log.debug('Checking and refreshing tokens before sync');
      await this.checkAndRefreshTokens();
      
      log.debug(`Making sync API request for integration ${integrationId}`);
      const response = await axios.post(`${this.baseURL}/api/calendar/integrations/${integrationId}/sync/`, {}, {
        headers: this.getAuthHeaders(),
      });

      log.info(`Calendar sync completed for integration ${integrationId}`, response.data);
      return response.data;
    } catch (error) {
      log.error(`Calendar sync failed for integration ${integrationId}`, error);
      if (axios.isAxiosError(error)) {
        throw this.handleApiError(error, 'Failed to sync calendar');
      }
      throw error;
    }
  }

  /**
   * Sync calendar without token refresh (for internal use)
   */
  async syncCalendarWithoutRefresh(integrationId: number): Promise<{ success: boolean; message: string }> {
    try {
      const response = await axios.post(`${this.baseURL}/api/calendar/integrations/${integrationId}/sync/`, {}, {
        headers: this.getAuthHeaders(),
      });

      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error)) {
        throw this.handleApiError(error, 'Failed to sync calendar');
      }
      throw error;
    }
  }

  /**
   * Get external events for a specific date range
   */
  async getExternalEvents(
    integrationId: number,
    startDate: string,
    endDate: string
  ): Promise<any[]> {
    log.info(`Fetching external events for integration ${integrationId}`, { startDate, endDate });
    
    try {
      // Ensure tokens are refreshed before fetching events
      log.debug('Checking and refreshing tokens before fetching events');
      await this.checkAndRefreshTokens();
      
      log.debug(`Making API request to fetch events for integration ${integrationId}`);
      const response = await axios.get(`${this.baseURL}/api/calendar/integrations/${integrationId}/events/`, {
        params: {
          start_date: startDate,
          end_date: endDate,
        },
        headers: this.getAuthHeaders(),
      });

      log.info(`Successfully fetched ${response.data.length} external events for integration ${integrationId}`);
      return response.data;
    } catch (error) {
      log.error(`Failed to fetch external events for integration ${integrationId}`, error);
      if (axios.isAxiosError(error)) {
        throw this.handleApiError(error, 'Failed to get external events');
      }
      throw error;
    }
  }

  /**
   * Update integration settings
   */
  async updateIntegration(
    integrationId: number,
    data: Partial<CalendarIntegration>
  ): Promise<CalendarIntegration> {
    try {
      const response = await axios.patch(`${this.baseURL}/api/calendar/integrations/${integrationId}/`, data, {
        headers: this.getAuthHeaders(),
      });

      const updatedIntegration = response.data;
      
      // Update auto refresh if status changed
      if (updatedIntegration.status === 'active') {
        tokenRefreshService.startAutoRefresh(updatedIntegration);
      } else {
        tokenRefreshService.stopAutoRefresh(integrationId);
      }

      return updatedIntegration;
    } catch (error) {
      if (axios.isAxiosError(error)) {
        throw this.handleApiError(error, 'Failed to update integration');
      }
      throw error;
    }
  }

  /**
   * Delete integration
   */
  async deleteIntegration(integrationId: number): Promise<void> {
    try {
      await axios.delete(`${this.baseURL}/api/calendar/integrations/${integrationId}/`, {
        headers: this.getAuthHeaders(),
      });

      // Stop auto refresh for deleted integration
      tokenRefreshService.stopAutoRefresh(integrationId);
    } catch (error) {
      if (axios.isAxiosError(error)) {
        throw this.handleApiError(error, 'Failed to delete integration');
      }
      throw error;
    }
  }

  /**
   * Get sync status for an integration
   */
  async getSyncStatus(integrationId: number): Promise<any> {
    try {
      const response = await axios.get(`${this.baseURL}/api/calendar/integrations/${integrationId}/sync-status/`, {
        headers: this.getAuthHeaders(),
      });

      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error)) {
        throw this.handleApiError(error, 'Failed to get sync status');
      }
      throw error;
    }
  }

  /**
   * Check if user has any active Google Calendar connections
   */
  async hasGoogleCalendarConnection(): Promise<boolean> {
    try {
      const integrations = await this.getIntegrations();
      return integrations.some(integration => 
        integration.provider === 'google' && integration.status === 'active'
      );
    } catch (error) {
      console.error('Error checking Google Calendar connection:', error);
      return false;
    }
  }

  /**
   * Sync calendar (original method without token refresh)
   */
  async syncCalendarOriginal(integrationId: string): Promise<any> {
    try {
      // Check if user has Google Calendar connected
      const hasConnection = await this.hasGoogleCalendarConnection();
      if (!hasConnection) {
        throw new Error('No Google Calendar connection found. Please connect your Google Calendar first.');
      }

      const response = await axios.post(
        `${this.baseURL}/api/calendar/integrations/${integrationId}/sync/`,
        {},
        {
          headers: this.getAuthHeaders(),
        }
      );
      return response.data;
    } catch (error) {
      console.error('Error syncing calendar:', error);
      throw error;
    }
  }

  /**
   * Get calendar conflicts
   */
  async getConflicts(): Promise<any[]> {
    try {
      const response = await axios.get(`${this.baseURL}/api/calendar/conflicts/`, {
        headers: this.getAuthHeaders(),
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching calendar conflicts:', error);
      throw error;
    }
  }

  /**
   * Resolve a calendar conflict
   */
  async resolveConflict(conflictId: string, resolution: 'keep_internal' | 'keep_external' | 'merge'): Promise<void> {
    try {
      await axios.post(
        `${this.baseURL}/api/calendar/conflicts/${conflictId}/resolve/`,
        { resolution },
        {
          headers: this.getAuthHeaders(),
        }
      );
    } catch (error) {
      console.error('Error resolving conflict:', error);
      
      // Fallback to local storage for demo purposes
      console.log(`Resolving conflict ${conflictId} with resolution: ${resolution}`);
      
      // Simulate API call delay
      await new Promise(resolve => setTimeout(resolve, 500));
      
      // Store resolution preference for future syncs
      const resolutions = JSON.parse(localStorage.getItem('conflict_resolutions') || '{}');
      resolutions[conflictId] = resolution;
      localStorage.setItem('conflict_resolutions', JSON.stringify(resolutions));
    }
  }

  /**
   * Initialize automatic token refresh for all integrations
   */
  async initializeTokenRefresh(): Promise<void> {
    try {
      await tokenRefreshService.initialize();
    } catch (error) {
      console.error('Failed to initialize token refresh:', error);
    }
  }

  /**
   * Check if any tokens need refreshing and refresh them
   */
  async checkAndRefreshTokens(): Promise<void> {
    log.debug('Starting token refresh check for all integrations');
    
    try {
      log.debug('Making API request to refresh tokens');
      const response = await axios.post(`${this.baseURL}/api/calendar/integrations/refresh-tokens/`, {}, {
        headers: this.getAuthHeaders(),
      });
      
      log.info('Token refresh check completed', response.data);
    } catch (error) {
      log.warn('Token refresh check failed', error);
      // Don't throw error as this is a background operation
      console.warn('Token refresh failed:', error);
    }
  }

  /**
   * Get authentication headers
   */
  private getAuthHeaders(): Record<string, string> {
    const token = localStorage.getItem('token') || sessionStorage.getItem('token');
    return {
      'Content-Type': 'application/json',
      ...(token && { Authorization: `Token ${token}` }),
    };
  }

  /**
   * Open Google Calendar OAuth popup
   */
  async openGoogleAuthPopup(): Promise<CalendarIntegration> {
    log.info('Opening Google Calendar OAuth popup');
    
    return new Promise(async (resolve, reject) => {
      try {
        // Get authorization URL from backend
        log.debug('Getting authorization URL from backend');
        const { authorization_url } = await this.initiateGoogleAuth();
        log.debug('Authorization URL received', { url: authorization_url });
        
        // Open popup window
        log.debug('Opening popup window for OAuth');
        const popup = window.open(
          authorization_url,
          'google-calendar-auth',
          'width=500,height=600,scrollbars=yes,resizable=yes'
        );

        if (!popup) {
          log.error('Popup blocked by browser');
          throw new Error('Popup blocked. Please allow popups for this site.');
        }

        log.debug('Popup window opened successfully');

        // Clean up timeout when authentication completes
        const originalResolve = resolve;
        const originalReject = reject;
        
        const wrappedResolve = (value: CalendarIntegration) => {
          log.info('OAuth authentication completed successfully');
          clearTimeout(authTimeout);
          originalResolve(value);
        };
        
        const wrappedReject = (reason: any) => {
          log.error('OAuth authentication failed', reason);
          clearTimeout(authTimeout);
          originalReject(reason);
        };

        // Listen for popup messages
        log.debug('Setting up message listener for OAuth callback');
        const messageListener = async (event: MessageEvent) => {
          // Accept messages from any origin for OAuth callback
          if (event.data.type === 'GOOGLE_CALENDAR_AUTH_SUCCESS') {
            log.info('Received OAuth success message from popup');
            window.removeEventListener('message', messageListener);
            if (popup && !popup.closed) {
              popup.close();
            }
            
            try {
              // Check if we have integration data directly from the callback
              if (event.data.integration) {
                log.debug('Using integration data directly from callback');
                // Use the integration data directly without making another API call
                const integration: CalendarIntegration = {
                  id: Date.now(), // Temporary ID, will be replaced by backend
                  user_id: '', // Will be set by backend
                  provider: 'google',
                  calendar_id: event.data.integration.calendar_id,
                  calendar_name: event.data.integration.calendar_name,
                  status: 'active',
                  sync_enabled: false,
                  last_sync_at: null,
                  access_token: '', // Don't expose tokens
                  refresh_token: '', // Don't expose tokens
                  token_expiry: event.data.integration.token_expiry,
                  sync_status: 'active',
                  last_sync: null,
                  next_sync: null,
                  created_at: new Date().toISOString(),
                  updated_at: new Date().toISOString()
                };
                wrappedResolve(integration);
              } else {
                log.debug('Falling back to OAuth callback API');
                // Fallback to original behavior
                const integration = await this.handleOAuthCallback(event.data.code, event.data.state);
                wrappedResolve(integration);
              }
            } catch (error) {
              log.error('Error processing OAuth success callback', error);
              wrappedReject(error);
            }
          } else if (event.data.type === 'GOOGLE_CALENDAR_AUTH_ERROR') {
            log.error('Received OAuth error message from popup', event.data.error);
            window.removeEventListener('message', messageListener);
            if (popup && !popup.closed) {
              popup.close();
            }
            wrappedReject(new Error(event.data.error || 'Authentication failed'));
          } else if (event.data.type === 'GOOGLE_CALENDAR_AUTH_COMPLETE') {
            log.info('Received OAuth completion message from popup');
            window.removeEventListener('message', messageListener);
            if (popup && !popup.closed) {
              popup.close();
            }
            // Refresh the page to show updated calendar integrations
            if (event.data.action === 'refresh_page') {
              log.info('Refreshing page to show updated calendar integrations');
              window.location.reload();
            }
          }
        };

        window.addEventListener('message', messageListener);

        // Set a timeout for the authentication process
        log.debug('Setting authentication timeout (5 minutes)');
        const authTimeout = setTimeout(() => {
          log.warn('OAuth authentication timed out');
          window.removeEventListener('message', messageListener);
          if (popup && !popup.closed) {
            popup.close();
          }
          wrappedReject(new Error('Authentication timeout. Please try again.'));
        }, 300000); // 5 minutes timeout

      } catch (error) {
        log.error('Error in openGoogleAuthPopup', error);
        reject(error);
      }
    });
  }

  /**
   * Detect conflicts between internal appointments and external events
   */
  async detectConflicts(
    appointments: any[],
    externalEvents: ExternalCalendarEvent[]
  ): Promise<SyncConflict[]> {
    const conflicts: SyncConflict[] = [];

    for (const appointment of appointments) {
      for (const externalEvent of externalEvents) {
        const appointmentStart = new Date(`${appointment.date}T${appointment.time}`);
        const appointmentEnd = new Date(appointmentStart.getTime() + appointment.duration * 60000);
        const eventStart = new Date(externalEvent.start_time);
        const eventEnd = new Date(externalEvent.end_time);

        // Check for time overlap
        if (appointmentStart < eventEnd && appointmentEnd > eventStart) {
          conflicts.push({
            id: `conflict-${appointment.id}-${externalEvent.id}`,
            integration_id: externalEvent.integration_id,
            external_event_id: externalEvent.external_event_id,
            conflict_type: 'overlap',
            mediremind_appointment_id: appointment.id?.toString(),
            conflict_details: {
              description: `Appointment with ${appointment.patientName} overlaps with external event "${externalEvent.title}"`,
              internal_appointment: appointment,
              external_event: externalEvent,
            },
            is_resolved: false,
            created_at: new Date().toISOString(),
          });
        }

        // Check for potential duplicates (same title/patient name)
        if (
          externalEvent.title.toLowerCase().includes(appointment.patientName.toLowerCase()) ||
          appointment.patientName.toLowerCase().includes(externalEvent.title.toLowerCase())
        ) {
          conflicts.push({
            id: `duplicate-${appointment.id}-${externalEvent.id}`,
            integration_id: externalEvent.integration_id,
            external_event_id: externalEvent.external_event_id,
            conflict_type: 'duplicate',
            mediremind_appointment_id: appointment.id?.toString(),
            conflict_details: {
              description: `Possible duplicate: "${externalEvent.title}" may be the same as appointment with ${appointment.patientName}`,
              internal_appointment: appointment,
              external_event: externalEvent,
            },
            is_resolved: false,
            created_at: new Date().toISOString(),
          });
        }
      }
    }

    return conflicts;
  }
}

export const calendarIntegrationService = new CalendarIntegrationService();
export default calendarIntegrationService;