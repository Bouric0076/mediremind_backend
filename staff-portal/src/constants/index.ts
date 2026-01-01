// API Configuration
export const API_CONFIG = {
  BASE_URL: import.meta.env.VITE_API_URL || process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000',
  TIMEOUT: 30000,
  RETRY_ATTEMPTS: 3,
  RETRY_DELAY: 1000,
} as const;

// API Endpoints
export const API_ENDPOINTS = {
  // Authentication
  AUTH: {
    LOGIN: '/api/auth/login/',
    LOGOUT: '/api/auth/logout/',
    REFRESH: '/api/auth/refresh/',
    ME: '/api/auth/me/',
    PROFILE: '/api/auth/profile/',
    CHANGE_PASSWORD: '/api/auth/change-password/',
    FORGOT_PASSWORD: '/api/auth/forgot-password/',
    RESET_PASSWORD: '/api/auth/reset-password/',
  },
  
  // Users
  USERS: {
    LIST: '/api/users',
    CREATE: '/api/users',
    GET: (id: string) => `/api/users/${id}`,
    UPDATE: (id: string) => `/api/users/${id}`,
    DELETE: (id: string) => `/api/users/${id}`,
    ACTIVATE: (id: string) => `/api/users/${id}/activate`,
    DEACTIVATE: (id: string) => `/api/users/${id}/deactivate`,
  },
  
  // Patients
  PATIENTS: {
    LIST: '/api/accounts/patients/',
    CREATE: '/api/accounts/patients/create/',
    GET: (id: string) => `/api/accounts/patients/${id}/`,
    UPDATE: (id: string) => `/api/accounts/patients/${id}/update/`,
    DELETE: (id: string) => `/api/accounts/patients/${id}/delete/`,
    SEARCH: '/api/accounts/patients/search/',
    MEDICAL_HISTORY: (id: string) => `/api/accounts/patients/${id}/medical-history/`,
    APPOINTMENTS: (id: string) => `/api/accounts/patients/${id}/appointments/`,
  },
  
  // Appointments
  APPOINTMENTS: {
    LIST: '/api/appointments/',
    CREATE: '/api/appointments/',
    GET: (id: string) => `/api/appointments/${id}/`,
    UPDATE: (id: string) => `/api/appointments/${id}/update/`,
    DELETE: (id: string) => `/api/appointments/${id}/`,
    CANCEL: (id: string) => `/api/appointments/${id}/cancel/`,
    RESCHEDULE: (id: string) => `/api/appointments/${id}/reschedule/`,
    CONFIRM: (id: string) => `/api/appointments/${id}/confirm/`,
    CHECK_IN: (id: string) => `/api/appointments/${id}/check-in/`,
    COMPLETE: (id: string) => `/api/appointments/${id}/complete/`,
    SEND_SMS_REMINDER: (id: string) => `/api/appointments/${id}/send-sms-reminder/`,
    TODAY: '/api/appointments/today/',
    UPCOMING: '/api/appointments/upcoming/',
    CALENDAR: '/api/appointments/calendar/',
    TYPES: '/api/appointments/types/',
  },
  
  // Notifications
  NOTIFICATIONS: {
    LIST: '/api/notifications',
    CREATE: '/api/notifications',
    GET: (id: string) => `/api/notifications/${id}`,
    UPDATE: (id: string) => `/api/notifications/${id}`,
    DELETE: (id: string) => `/api/notifications/${id}`,
    SEND: (id: string) => `/api/notifications/${id}/send`,
    MARK_READ: (id: string) => `/api/notifications/${id}/read`,
    MARK_UNREAD: (id: string) => `/api/notifications/${id}/unread`,
    BULK_SEND: '/api/notifications/bulk-send',
    STATS: '/api/notifications/stats',
    TEMPLATES: '/api/notifications/templates',
  },
  
  // Medical Records
  MEDICAL_RECORDS: {
    LIST: '/api/medical-records',
    CREATE: '/api/medical-records',
    GET: (id: string) => `/api/medical-records/${id}`,
    UPDATE: (id: string) => `/api/medical-records/${id}`,
    DELETE: (id: string) => `/api/medical-records/${id}`,
    BY_PATIENT: (patientId: string) => `/api/medical-records/patient/${patientId}`,
  },
  
  // Prescriptions
  PRESCRIPTIONS: {
    LIST: '/api/prescriptions',
    CREATE: '/api/prescriptions',
    GET: (id: string) => `/api/prescriptions/${id}`,
    UPDATE: (id: string) => `/api/prescriptions/${id}`,
    DELETE: (id: string) => `/api/prescriptions/${id}`,
    BY_PATIENT: (patientId: string) => `/api/prescriptions/patient/${patientId}`,
  },
  
  // Analytics
  ANALYTICS: {
    DASHBOARD: '/api/analytics/dashboard/',
    APPOINTMENTS: '/api/analytics/appointments/',
    REVENUE: '/api/analytics/revenue/',
    USERS: '/api/analytics/users/',
    PERFORMANCE: '/api/analytics/performance/',
  },
  
  // File Upload
  UPLOAD: {
    SINGLE: '/api/upload/single',
    MULTIPLE: '/api/upload/multiple',
    AVATAR: '/api/upload/avatar',
    MEDICAL_DOCUMENT: '/api/upload/medical-document',
  },
  
  // Staff Management
  STAFF: {
    LIST: '/api/accounts/staff/',
    CREATE: '/api/accounts/staff/create/',
    GET: (id: string) => `/api/accounts/staff/${id}/`,
    UPDATE: (id: string) => `/api/accounts/staff/${id}/update/`,
    DELETE: (id: string) => `/api/accounts/staff/${id}/delete/`,
  },
  
  // Care Teams
  CARE_TEAMS: {
    LIST: '/api/accounts/care-teams/',
    CREATE: '/api/accounts/care-teams/create/',
    GET: (id: string) => `/api/accounts/care-teams/${id}/`,
    UPDATE: (id: string) => `/api/accounts/care-teams/${id}/update/`,
    DELETE: (id: string) => `/api/accounts/care-teams/${id}/delete/`,
  },
  
  // Staff Credentials
  STAFF_CREDENTIALS: {
    LIST: (staffId: string) => `/api/accounts/staff/${staffId}/credentials/`,
    GET: (id: string) => `/api/accounts/credentials/${id}/`,
  },
} as const;

// User Roles
export const USER_ROLES = {
  ADMIN: 'admin',
  DOCTOR: 'doctor',
  NURSE: 'nurse',
  RECEPTIONIST: 'receptionist',
  MANAGER: 'manager',
} as const;

export const ROLE_PERMISSIONS = {
  [USER_ROLES.ADMIN]: [
    'users:read', 'users:write', 'users:delete',
    'patients:read', 'patients:write', 'patients:delete',
    'appointments:read', 'appointments:write', 'appointments:delete',
    'notifications:read', 'notifications:write', 'notifications:delete',
    'medical-records:read', 'medical-records:write', 'medical-records:delete',
    'prescriptions:read', 'prescriptions:write', 'prescriptions:delete',
    'analytics:read', 'settings:read', 'settings:write',
  ],
  [USER_ROLES.DOCTOR]: [
    'patients:read', 'patients:write',
    'appointments:read', 'appointments:write',
    'medical-records:read', 'medical-records:write',
    'prescriptions:read', 'prescriptions:write',
    'notifications:read', 'notifications:write',
  ],
  [USER_ROLES.NURSE]: [
    'patients:read', 'patients:write',
    'appointments:read', 'appointments:write',
    'medical-records:read',
    'notifications:read', 'notifications:write',
  ],
  [USER_ROLES.RECEPTIONIST]: [
    'patients:read', 'patients:write',
    'appointments:read', 'appointments:write',
    'notifications:read',
  ],
  [USER_ROLES.MANAGER]: [
    'patients:read',
    'appointments:read',
    'notifications:read', 'notifications:write',
    'analytics:read',
  ],
} as const;

// Appointment Statuses
export const APPOINTMENT_STATUS = {
  SCHEDULED: 'scheduled',
  CONFIRMED: 'confirmed',
  IN_PROGRESS: 'in_progress',
  COMPLETED: 'completed',
  CANCELLED: 'cancelled',
  NO_SHOW: 'no_show',
  RESCHEDULED: 'rescheduled',
} as const;

export const APPOINTMENT_STATUS_LABELS = {
  [APPOINTMENT_STATUS.SCHEDULED]: 'Scheduled',
  [APPOINTMENT_STATUS.CONFIRMED]: 'Confirmed',
  [APPOINTMENT_STATUS.IN_PROGRESS]: 'In Progress',
  [APPOINTMENT_STATUS.COMPLETED]: 'Completed',
  [APPOINTMENT_STATUS.CANCELLED]: 'Cancelled',
  [APPOINTMENT_STATUS.NO_SHOW]: 'No Show',
  [APPOINTMENT_STATUS.RESCHEDULED]: 'Rescheduled',
} as const;

export const APPOINTMENT_STATUS_COLORS = {
  [APPOINTMENT_STATUS.SCHEDULED]: '#2196f3',
  [APPOINTMENT_STATUS.CONFIRMED]: '#4caf50',
  [APPOINTMENT_STATUS.IN_PROGRESS]: '#ff9800',
  [APPOINTMENT_STATUS.COMPLETED]: '#8bc34a',
  [APPOINTMENT_STATUS.CANCELLED]: '#f44336',
  [APPOINTMENT_STATUS.NO_SHOW]: '#9e9e9e',
  [APPOINTMENT_STATUS.RESCHEDULED]: '#9c27b0',
} as const;

// Appointment Types
export const APPOINTMENT_TYPES = {
  CONSULTATION: 'consultation',
  FOLLOW_UP: 'follow_up',
  EMERGENCY: 'emergency',
  SURGERY: 'surgery',
  THERAPY: 'therapy',
  DIAGNOSTIC: 'diagnostic',
  VACCINATION: 'vaccination',
} as const;

export const APPOINTMENT_TYPE_LABELS = {
  [APPOINTMENT_TYPES.CONSULTATION]: 'Consultation',
  [APPOINTMENT_TYPES.FOLLOW_UP]: 'Follow-up',
  [APPOINTMENT_TYPES.EMERGENCY]: 'Emergency',
  [APPOINTMENT_TYPES.SURGERY]: 'Surgery',
  [APPOINTMENT_TYPES.THERAPY]: 'Therapy',
  [APPOINTMENT_TYPES.DIAGNOSTIC]: 'Diagnostic',
  [APPOINTMENT_TYPES.VACCINATION]: 'Vaccination',
} as const;

// Priority Levels
export const PRIORITY_LEVELS = {
  LOW: 'low',
  MEDIUM: 'medium',
  HIGH: 'high',
  URGENT: 'urgent',
  EMERGENCY: 'emergency',
} as const;

export const PRIORITY_LABELS = {
  [PRIORITY_LEVELS.LOW]: 'Low',
  [PRIORITY_LEVELS.MEDIUM]: 'Medium',
  [PRIORITY_LEVELS.HIGH]: 'High',
  [PRIORITY_LEVELS.URGENT]: 'Urgent',
  [PRIORITY_LEVELS.EMERGENCY]: 'Emergency',
} as const;

export const PRIORITY_COLORS = {
  [PRIORITY_LEVELS.LOW]: '#4caf50',
  [PRIORITY_LEVELS.MEDIUM]: '#ff9800',
  [PRIORITY_LEVELS.HIGH]: '#f44336',
  [PRIORITY_LEVELS.URGENT]: '#9c27b0',
  [PRIORITY_LEVELS.EMERGENCY]: '#d32f2f',
} as const;

// Notification Types
export const NOTIFICATION_TYPES = {
  APPOINTMENT_REMINDER: 'appointment_reminder',
  APPOINTMENT_CONFIRMATION: 'appointment_confirmation',
  APPOINTMENT_CANCELLATION: 'appointment_cancellation',
  MEDICATION_REMINDER: 'medication_reminder',
  TEST_RESULTS: 'test_results',
  SYSTEM_ALERT: 'system_alert',
  BILLING: 'billing',
  GENERAL: 'general',
} as const;

export const NOTIFICATION_TYPE_LABELS = {
  [NOTIFICATION_TYPES.APPOINTMENT_REMINDER]: 'Appointment Reminder',
  [NOTIFICATION_TYPES.APPOINTMENT_CONFIRMATION]: 'Appointment Confirmation',
  [NOTIFICATION_TYPES.APPOINTMENT_CANCELLATION]: 'Appointment Cancellation',
  [NOTIFICATION_TYPES.MEDICATION_REMINDER]: 'Medication Reminder',
  [NOTIFICATION_TYPES.TEST_RESULTS]: 'Test Results',
  [NOTIFICATION_TYPES.SYSTEM_ALERT]: 'System Alert',
  [NOTIFICATION_TYPES.BILLING]: 'Billing',
  [NOTIFICATION_TYPES.GENERAL]: 'General',
} as const;

// Notification Channels
export const NOTIFICATION_CHANNELS = {
  EMAIL: 'email',
  SMS: 'sms',
  PUSH: 'push',
  IN_APP: 'in_app',
} as const;

export const NOTIFICATION_CHANNEL_LABELS = {
  [NOTIFICATION_CHANNELS.EMAIL]: 'Email',
  [NOTIFICATION_CHANNELS.SMS]: 'SMS',
  [NOTIFICATION_CHANNELS.PUSH]: 'Push Notification',
  [NOTIFICATION_CHANNELS.IN_APP]: 'In-App',
} as const;

// Notification Status
export const NOTIFICATION_STATUS = {
  DRAFT: 'draft',
  SCHEDULED: 'scheduled',
  SENDING: 'sending',
  SENT: 'sent',
  DELIVERED: 'delivered',
  FAILED: 'failed',
  CANCELLED: 'cancelled',
} as const;

export const NOTIFICATION_STATUS_LABELS = {
  [NOTIFICATION_STATUS.DRAFT]: 'Draft',
  [NOTIFICATION_STATUS.SCHEDULED]: 'Scheduled',
  [NOTIFICATION_STATUS.SENDING]: 'Sending',
  [NOTIFICATION_STATUS.SENT]: 'Sent',
  [NOTIFICATION_STATUS.DELIVERED]: 'Delivered',
  [NOTIFICATION_STATUS.FAILED]: 'Failed',
  [NOTIFICATION_STATUS.CANCELLED]: 'Cancelled',
} as const;

// Gender Options
export const GENDER_OPTIONS = {
  MALE: 'male',
  FEMALE: 'female',
  OTHER: 'other',
  PREFER_NOT_TO_SAY: 'prefer_not_to_say',
} as const;

export const GENDER_LABELS = {
  [GENDER_OPTIONS.MALE]: 'Male',
  [GENDER_OPTIONS.FEMALE]: 'Female',
  [GENDER_OPTIONS.OTHER]: 'Other',
  [GENDER_OPTIONS.PREFER_NOT_TO_SAY]: 'Prefer not to say',
} as const;

// Medical Record Types
export const MEDICAL_RECORD_TYPES = {
  CONSULTATION_NOTE: 'consultation_note',
  DIAGNOSIS: 'diagnosis',
  TREATMENT_PLAN: 'treatment_plan',
  LAB_RESULT: 'lab_result',
  IMAGING: 'imaging',
  SURGERY_NOTE: 'surgery_note',
  DISCHARGE_SUMMARY: 'discharge_summary',
} as const;

export const MEDICAL_RECORD_TYPE_LABELS = {
  [MEDICAL_RECORD_TYPES.CONSULTATION_NOTE]: 'Consultation Note',
  [MEDICAL_RECORD_TYPES.DIAGNOSIS]: 'Diagnosis',
  [MEDICAL_RECORD_TYPES.TREATMENT_PLAN]: 'Treatment Plan',
  [MEDICAL_RECORD_TYPES.LAB_RESULT]: 'Lab Result',
  [MEDICAL_RECORD_TYPES.IMAGING]: 'Imaging',
  [MEDICAL_RECORD_TYPES.SURGERY_NOTE]: 'Surgery Note',
  [MEDICAL_RECORD_TYPES.DISCHARGE_SUMMARY]: 'Discharge Summary',
} as const;

// Prescription Status
export const PRESCRIPTION_STATUS = {
  ACTIVE: 'active',
  COMPLETED: 'completed',
  CANCELLED: 'cancelled',
  EXPIRED: 'expired',
} as const;

export const PRESCRIPTION_STATUS_LABELS = {
  [PRESCRIPTION_STATUS.ACTIVE]: 'Active',
  [PRESCRIPTION_STATUS.COMPLETED]: 'Completed',
  [PRESCRIPTION_STATUS.CANCELLED]: 'Cancelled',
  [PRESCRIPTION_STATUS.EXPIRED]: 'Expired',
} as const;

// Date and Time Formats
export const DATE_FORMATS = {
  DISPLAY: 'MMM dd, yyyy',
  INPUT: 'yyyy-MM-dd',
  FULL: 'EEEE, MMMM dd, yyyy',
  SHORT: 'MM/dd/yyyy',
  ISO: "yyyy-MM-dd'T'HH:mm:ss.SSSxxx",
} as const;

export const TIME_FORMATS = {
  DISPLAY: 'h:mm a',
  INPUT: 'HH:mm',
  FULL: 'h:mm:ss a',
  ISO: 'HH:mm:ss',
} as const;

// Pagination
export const PAGINATION = {
  DEFAULT_PAGE_SIZE: 10,
  PAGE_SIZE_OPTIONS: [5, 10, 25, 50, 100],
  MAX_PAGE_SIZE: 100,
} as const;

// File Upload
export const FILE_UPLOAD = {
  MAX_SIZE: 10 * 1024 * 1024, // 10MB
  ALLOWED_TYPES: {
    IMAGES: ['image/jpeg', 'image/png', 'image/gif', 'image/webp'],
    DOCUMENTS: ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'],
    ALL: ['image/jpeg', 'image/png', 'image/gif', 'image/webp', 'application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'],
  },
} as const;

// Local Storage Keys
export const STORAGE_KEYS = {
  AUTH_TOKEN: 'auth_token',
  REFRESH_TOKEN: 'refresh_token',
  USER_PREFERENCES: 'user_preferences',
  THEME: 'theme',
  SIDEBAR_STATE: 'sidebar_state',
} as const;

// Toast Configuration
export const TOAST_CONFIG = {
  DEFAULT_DURATION: 5000,
  SUCCESS_DURATION: 3000,
  ERROR_DURATION: 7000,
  WARNING_DURATION: 5000,
  INFO_DURATION: 4000,
} as const;

// Validation Rules
export const VALIDATION_RULES = {
  EMAIL: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
  PHONE: /^[\+]?[1-9][\d]{0,15}$/,
  PASSWORD: {
    MIN_LENGTH: 8,
    PATTERN: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]/,
  },
  NAME: /^[a-zA-Z\s'-]{2,50}$/,
} as const;

// Error Messages
export const ERROR_MESSAGES = {
  REQUIRED: 'This field is required',
  INVALID_EMAIL: 'Please enter a valid email address',
  INVALID_PHONE: 'Please enter a valid phone number',
  INVALID_PASSWORD: 'Password must be at least 8 characters with uppercase, lowercase, number, and special character',
  PASSWORDS_DONT_MATCH: 'Passwords do not match',
  NETWORK_ERROR: 'Network error. Please check your connection and try again.',
  UNAUTHORIZED: 'You are not authorized to perform this action',
  FORBIDDEN: 'Access denied',
  NOT_FOUND: 'The requested resource was not found',
  SERVER_ERROR: 'An unexpected error occurred. Please try again later.',
} as const;

// Success Messages
export const SUCCESS_MESSAGES = {
  LOGIN: 'Successfully logged in',
  LOGOUT: 'Successfully logged out',
  SAVE: 'Changes saved successfully',
  CREATE: 'Created successfully',
  UPDATE: 'Updated successfully',
  DELETE: 'Deleted successfully',
  SEND: 'Sent successfully',
} as const;

// Navigation Routes
export const ROUTES = {
  HOME: '/',
  LOGIN: '/login',
  DASHBOARD: '/dashboard',
  PATIENTS: '/patients',
  PATIENT_DETAIL: '/patients/:id',
  APPOINTMENTS: '/appointments',
  APPOINTMENT_DETAIL: '/appointments/:id',
  NOTIFICATIONS: '/notifications',
  MEDICAL_RECORDS: '/medical-records',
  PRESCRIPTIONS: '/prescriptions',
  SETTINGS: '/settings',
  CALENDAR: '/calendar',
  CALENDAR_INTEGRATION: '/calendar/integration',
  PROFILE: '/profile',
} as const;

export default {
  API_CONFIG,
  API_ENDPOINTS,
  USER_ROLES,
  ROLE_PERMISSIONS,
  APPOINTMENT_STATUS,
  APPOINTMENT_TYPES,
  PRIORITY_LEVELS,
  NOTIFICATION_TYPES,
  NOTIFICATION_CHANNELS,
  NOTIFICATION_STATUS,
  GENDER_OPTIONS,
  MEDICAL_RECORD_TYPES,
  PRESCRIPTION_STATUS,
  DATE_FORMATS,
  TIME_FORMATS,
  PAGINATION,
  FILE_UPLOAD,
  STORAGE_KEYS,
  TOAST_CONFIG,
  VALIDATION_RULES,
  ERROR_MESSAGES,
  SUCCESS_MESSAGES,
  ROUTES,
};