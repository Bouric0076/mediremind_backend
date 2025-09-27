// Standardized error response interface matching backend CalendarErrorCodes
export interface CalendarErrorResponse {
  error: string;
  error_code: string;
  details?: any;
  redirect_to_login?: boolean;
}

// Calendar error class for standardized error handling
export class CalendarError extends Error {
  public readonly errorCode: string;
  public readonly details?: any;
  public readonly redirectToLogin?: boolean;

  constructor(errorResponse: CalendarErrorResponse) {
    super(errorResponse.error);
    this.name = 'CalendarError';
    this.errorCode = errorResponse.error_code;
    this.details = errorResponse.details;
    this.redirectToLogin = errorResponse.redirect_to_login;
  }
}

export interface ExternalCalendarEvent {
  id: string;
  title: string;
  description?: string;
  start_time: string;
  end_time: string;
  location?: string;
  is_medical_appointment: boolean;
  external_event_id: string;
  integration_id: number;
  last_modified: string;
  created_at: string;
  updated_at: string;
}

// Updated to match exact backend API response format from CalendarIntegrationsView
export interface CalendarIntegration {
  id: number;
  user_id: string;
  provider: 'google' | 'outlook';
  calendar_id: string;
  calendar_name: string;
  status: 'active' | 'inactive' | 'error' | 'pending';
  sync_enabled: boolean;
  last_sync_at: string | null;
  access_token: string; // Always empty in API responses for security
  refresh_token: string; // Always empty in API responses for security
  token_expiry: string | null;
  sync_status: string; // Maps to status field from backend
  last_sync: string | null; // Maps to last_sync_at from backend
  next_sync: string | null; // Maps to next_sync_at from backend
  created_at: string;
  updated_at: string;
}

export interface SyncConflict {
  id: string;
  integration_id: number;
  external_event_id: string;
  conflict_type: 'overlap' | 'duplicate';
  mediremind_appointment_id?: string;
  conflict_details: any;
  is_resolved: boolean;
  resolution_action?: string;
  resolved_at?: string;
  created_at: string;
}

// Calendar sync status interface matching backend response
export interface CalendarSyncStatus {
  integration_id: number;
  status: 'syncing' | 'completed' | 'error';
  last_sync: string | null;
  events_synced: number;
  conflicts_found: number;
  error_message?: string;
}

// OAuth callback data interface
export interface OAuthCallbackData {
  code: string;
  state: string;
  integration?: {
    calendar_id: string;
    calendar_name: string;
    token_expiry?: string;
  };
}