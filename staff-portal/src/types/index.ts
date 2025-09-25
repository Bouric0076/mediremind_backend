// User and Authentication Types
export interface User {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  department?: string;
  phone?: string;
  avatar?: string;
  isActive: boolean;
  lastLogin?: string;
  createdAt: string;
  updatedAt: string;
  profile?: {
    type: string;
    id: string;
    specialization?: string;
    license_number?: string;
    department?: string;
  };
  permissions?: string[];
}

export type UserRole = 'admin' | 'doctor' | 'nurse' | 'receptionist' | 'manager';

export interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

export interface LoginCredentials {
  email: string;
  password: string;
  rememberMe?: boolean;
}

export interface LoginResponse {
  user: User;
  token: string;
  refreshToken: string;
}

// Gender Type
export type Gender = 'male' | 'female' | 'other' | 'prefer_not_to_say';

// Patient Types
export interface Patient {
  id: string;
  name: string;
  date_of_birth: string;
  gender: Gender;
  contact: {
    phone?: string;
    email?: string;
    address?: string;
  };
  emergency_contact?: {
    name?: string;
    relationship?: string;
    phone?: string;
    email?: string;
  };
  medical_history?: {
    conditions?: string;
    allergies?: string;
    medications?: string;
    surgical_history?: string;
    family_medical_history?: string;
  };
  lifestyle?: {
    smoking_status?: string;
    alcohol_use?: string;
    exercise_frequency?: string;
  };
  insurance?: {
    provider?: string;
    type?: string;
    policy_number?: string;
    group_number?: string;
  };
  preferences?: {
    language?: string;
    communication?: string;
  };
  primary_care_physician?: string;
  status: string;
  registration_completed: boolean;
  created_at: string;
  updated_at: string;
}

export interface Address {
  street: string;
  city: string;
  state: string;
  zipCode: string;
  country: string;
}

export interface EmergencyContact {
  name: string;
  relationship: string;
  phone: string;
  email?: string;
}

export interface MedicalHistory {
  id: string;
  condition: string;
  diagnosedDate: string;
  status: 'active' | 'resolved' | 'chronic';
  notes?: string;
}

export interface InsuranceInfo {
  provider: string;
  policyNumber: string;
  groupNumber?: string;
  expiryDate: string;
}

// Appointment Types
export interface Appointment {
  id: string;
  patientId: string;
  patient: Patient;
  doctorId: string;
  doctor: User;
  title: string;
  description?: string;
  startTime: string;
  endTime: string;
  status: AppointmentStatus;
  type: AppointmentType;
  priority: Priority;
  location?: string;
  notes?: string;
  reminders: Reminder[];
  createdAt: string;
  updatedAt: string;
}

export type AppointmentStatus = 
  | 'scheduled' 
  | 'confirmed' 
  | 'in_progress' 
  | 'completed' 
  | 'cancelled' 
  | 'no_show' 
  | 'rescheduled';

export type AppointmentType = 
  | 'consultation' 
  | 'follow_up' 
  | 'emergency' 
  | 'surgery' 
  | 'therapy' 
  | 'diagnostic' 
  | 'vaccination';

export type Priority = 'low' | 'medium' | 'high' | 'urgent' | 'emergency';

export interface Reminder {
  id: string;
  appointmentId: string;
  type: ReminderType;
  scheduledFor: string;
  status: ReminderStatus;
  message?: string;
  sentAt?: string;
}

export type ReminderType = 'email' | 'sms' | 'push' | 'call';
export type ReminderStatus = 'pending' | 'sent' | 'delivered' | 'failed';

// Notification Types
export interface Notification {
  id: string;
  title: string;
  message: string;
  type: NotificationType;
  priority: Priority;
  recipientId: string;
  recipientType: 'user' | 'patient';
  channels: NotificationChannel[];
  status: NotificationStatus;
  scheduledFor?: string;
  sentAt?: string;
  readAt?: string;
  metadata?: Record<string, any>;
  createdAt: string;
  updatedAt: string;
}

export type NotificationType = 
  | 'appointment_reminder' 
  | 'appointment_confirmation' 
  | 'appointment_cancellation' 
  | 'medication_reminder' 
  | 'test_results' 
  | 'system_alert' 
  | 'billing' 
  | 'general';

export type NotificationChannel = 'email' | 'sms' | 'push' | 'in_app';

export type NotificationStatus = 
  | 'draft' 
  | 'scheduled' 
  | 'sending' 
  | 'sent' 
  | 'delivered' 
  | 'failed' 
  | 'cancelled';

export interface NotificationTemplate {
  id: string;
  name: string;
  type: NotificationType;
  subject: string;
  content: string;
  channels: NotificationChannel[];
  variables: TemplateVariable[];
  isActive: boolean;
  createdBy: string;
  createdAt: string;
  updatedAt: string;
}

export interface TemplateVariable {
  name: string;
  description: string;
  type: 'string' | 'number' | 'date' | 'boolean';
  required: boolean;
  defaultValue?: string;
}

// Medical Records Types
export interface MedicalRecord {
  id: string;
  patientId: string;
  doctorId: string;
  appointmentId?: string;
  type: MedicalRecordType;
  title: string;
  content: string;
  diagnosis?: string;
  treatment?: string;
  prescriptions: Prescription[];
  attachments: Attachment[];
  isConfidential: boolean;
  createdAt: string;
  updatedAt: string;
}

export type MedicalRecordType = 
  | 'consultation_note' 
  | 'diagnosis' 
  | 'treatment_plan' 
  | 'lab_result' 
  | 'imaging' 
  | 'surgery_note' 
  | 'discharge_summary';

export interface Prescription {
  id: string;
  patientId: string;
  doctorId: string;
  medication: string;
  dosage: string;
  frequency: string;
  duration: string;
  instructions?: string;
  refills: number;
  status: PrescriptionStatus;
  prescribedAt: string;
  expiresAt: string;
}

export type PrescriptionStatus = 'active' | 'completed' | 'cancelled' | 'expired';

export interface Attachment {
  id: string;
  filename: string;
  originalName: string;
  mimeType: string;
  size: number;
  url: string;
  uploadedBy: string;
  uploadedAt: string;
}

// UI State Types
export interface Modal {
  id: string;
  type: string;
  isOpen: boolean;
  data?: any;
  props?: Record<string, any>;
}

export interface Toast {
  id: string;
  message: string;
  type: 'success' | 'error' | 'warning' | 'info';
  duration?: number;
  action?: {
    label: string;
    onClick: () => void;
  };
}

export interface Breadcrumb {
  label: string;
  path?: string;
  icon?: string;
}

export interface UIState {
  sidebarOpen: boolean;
  theme: 'light' | 'dark';
  isOnline: boolean;
  loading: Record<string, boolean>;
  modals: Modal[];
  toasts: Toast[];
  breadcrumbs: Breadcrumb[];
  currentPage: string;
}

// API Response Types
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  message?: string;
  errors?: Record<string, string[]>;
  meta?: {
    page?: number;
    limit?: number;
    total?: number;
    totalPages?: number;
  };
}

export interface PaginatedResponse<T> {
  items: T[];
  page: number;
  limit: number;
  total: number;
  totalPages: number;
  hasNext: boolean;
  hasPrev: boolean;
}

// Filter and Search Types
export interface FilterOptions {
  search?: string;
  status?: string[];
  dateRange?: {
    start: string;
    end: string;
  };
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
  page?: number;
  limit?: number;
}

export interface SearchFilters {
  patients?: {
    search?: string;
    gender?: Gender[];
    ageRange?: {
      min: number;
      max: number;
    };
    isActive?: boolean;
  };
  appointments?: {
    search?: string;
    status?: AppointmentStatus[];
    type?: AppointmentType[];
    doctorId?: string;
    dateRange?: {
      start: string;
      end: string;
    };
  };
  notifications?: {
    search?: string;
    type?: NotificationType[];
    status?: NotificationStatus[];
    priority?: Priority[];
    channels?: NotificationChannel[];
  };
}

// Dashboard Types
export interface DashboardStats {
  totalPatients: number;
  totalAppointments: number;
  todayAppointments: number;
  pendingNotifications: number;
  activeUsers: number;
  systemHealth: 'healthy' | 'warning' | 'critical';
}

export interface RecentActivity {
  id: string;
  type: 'appointment' | 'patient' | 'notification' | 'user';
  title: string;
  description: string;
  timestamp: string;
  userId?: string;
  patientId?: string;
}

// Form Types
export interface FormField {
  name: string;
  label: string;
  type: 'text' | 'email' | 'password' | 'number' | 'date' | 'select' | 'textarea' | 'checkbox' | 'radio';
  required?: boolean;
  placeholder?: string;
  options?: { label: string; value: string }[];
  validation?: {
    min?: number;
    max?: number;
    pattern?: string;
    message?: string;
  };
}

export interface FormState {
  values: Record<string, any>;
  errors: Record<string, string>;
  touched: Record<string, boolean>;
  isSubmitting: boolean;
  isValid: boolean;
}

// Error Types
export interface AppError {
  code: string;
  message: string;
  details?: any;
  timestamp: string;
}

export interface ValidationError {
  field: string;
  message: string;
  code?: string;
}

// Settings Types
export interface UserSettings {
  notifications: {
    email: boolean;
    sms: boolean;
    push: boolean;
    appointmentReminders: boolean;
    systemAlerts: boolean;
  };
  appearance: {
    theme: 'light' | 'dark' | 'system';
    language: string;
    timezone: string;
  };
  privacy: {
    profileVisibility: 'public' | 'private';
    dataSharing: boolean;
  };
}

export interface SystemSettings {
  appointmentDuration: number;
  reminderTiming: number[];
  workingHours: {
    start: string;
    end: string;
    days: string[];
  };
  notifications: {
    enabled: boolean;
    channels: NotificationChannel[];
    templates: Record<NotificationType, string>;
  };
}

// Export all types
export type * from './index';