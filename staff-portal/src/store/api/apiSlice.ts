import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';
import type { RootState } from '../index';
import { API_ENDPOINTS } from '../../constants';

// Base query with session-based authentication
const baseQuery = fetchBaseQuery({
  baseUrl: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  credentials: 'include', // Include cookies for session authentication
  prepareHeaders: (headers, { getState }) => {
    const token = (getState() as RootState).auth.token;
    // Only add Token if it's not session-based auth
    if (token && token !== 'session_based_auth') {
      headers.set('authorization', `Token ${token}`);
    }
    headers.set('content-type', 'application/json');
    return headers;
  },
});

// Base query with re-authentication and network error handling
const baseQueryWithReauth = async (args: any, api: any, extraOptions: any) => {
  // Maximum number of retries for network errors
  const MAX_RETRIES = 3;
  let retries = 0;
  
  const executeQuery = async () => {
    try {
      return await baseQuery(args, api, extraOptions);
    } catch (error) {
      // Rethrow non-network errors
      if (!(error instanceof Error) || 
          !(error.message.includes('network') || 
            error.message.includes('ERR_NETWORK_CHANGED') || 
            error.message.includes('Failed to fetch'))) {
        throw error;
      }
      
      // For network errors, retry with exponential backoff if under max retries
      if (retries < MAX_RETRIES) {
        retries++;
        const delay = Math.pow(2, retries) * 1000; // Exponential backoff: 2s, 4s, 8s
        
        // Check if network is available before retrying
        if (navigator.onLine) {
          await new Promise(resolve => setTimeout(resolve, delay));
          return executeQuery(); // Recursive retry
        } else {
          // Wait for online status before retrying
          await new Promise(resolve => {
            const handleOnline = () => {
              window.removeEventListener('online', handleOnline);
              setTimeout(resolve, 1000); // Small delay after coming back online
            };
            window.addEventListener('online', handleOnline);
          });
          return executeQuery();
        }
      }
      
      throw error; // Max retries exceeded
    }
  };
  
  let result;
  try {
    result = await executeQuery();
  } catch (error) {
    // Handle network errors that exceeded max retries
    return {
      error: {
        status: 'NETWORK_ERROR',
        data: { message: 'Network connection error. Please check your connection and try again.' }
      }
    };
  }
  
  // Handle authentication errors
  if (result.error && result.error.status === 401) {
    // Try to get a new token
    const refreshResult = await baseQuery(
      {
        url: API_ENDPOINTS.AUTH.REFRESH,
        method: 'POST',
        body: {
          refreshToken: (api.getState() as RootState).auth.refreshToken,
        },
      },
      api,
      extraOptions
    );
    
    if (refreshResult.data) {
      // Store the new token
      api.dispatch({ type: 'auth/loginSuccess', payload: refreshResult.data });
      // Retry the original query with new token
      result = await baseQuery(args, api, extraOptions);
    } else {
      api.dispatch({ type: 'auth/logout' });
    }
  }
  
  return result;
};

export const apiSlice = createApi({
  reducerPath: 'api',
  baseQuery: baseQueryWithReauth,
  tagTypes: [
    'User',
    'Patient',
    'Appointment',
    'AppointmentType',
    'Notification',
    'Template',
    'Prescription',
    'MedicalRecord',
    'Doctor',
    'Department',
    'Report',
    'Analytics',
    'Staff',
    'CareTeam',
    'StaffCredential',
  ],
  endpoints: (builder) => ({
    // Authentication endpoints
    login: builder.mutation<
      { user: any; token: string; refreshToken: string },
      { email: string; password: string }
    >({
      query: (credentials) => ({
        url: API_ENDPOINTS.AUTH.LOGIN,
        method: 'POST',
        body: credentials,
      }),
    }),
    
    logout: builder.mutation<void, void>({
      query: () => ({
        url: API_ENDPOINTS.AUTH.LOGOUT,
        method: 'POST',
      }),
    }),
    
    refreshToken: builder.mutation<
      { token: string; refreshToken: string },
      { refreshToken: string }
    >({
      query: (body) => ({
        url: API_ENDPOINTS.AUTH.REFRESH,
        method: 'POST',
        body,
      }),
    }),
    
    registerHospital: builder.mutation<
      { message: string; hospital_id: string; admin_user_id: string },
      {
        hospital_name: string;
        hospital_type: string;
        hospital_email: string;
        hospital_phone: string;
        hospital_website?: string;
        address_line_1: string;
        address_line_2?: string;
        city: string;
        state: string;
        postal_code: string;
        country: string;
        license_number?: string;
        tax_id?: string;
        timezone: string;
        admin_first_name: string;
        admin_last_name: string;
        admin_email: string;
        admin_password: string;
        admin_phone?: string;
      }
    >({
      query: (registrationData) => ({
        url: '/api/accounts/register-hospital/',
        method: 'POST',
        body: registrationData,
      }),
    }),
    
    // User management
    getCurrentUser: builder.query<any, void>({
      query: () => API_ENDPOINTS.AUTH.ME,
      providesTags: ['User'],
    }),
    
    updateProfile: builder.mutation<any, Partial<any>>({
      query: (updates) => ({
        url: API_ENDPOINTS.AUTH.PROFILE,
        method: 'PATCH',
        body: updates,
      }),
      invalidatesTags: ['User'],
    }),
    
    // Patient endpoints
    getPatients: builder.query<
      { patients: any[]; total: number; page: number; limit: number },
      { page?: number; limit?: number; search?: string; filters?: any }
    >({
      query: ({ page = 1, limit = 25, search, filters }) => {
        const params = new URLSearchParams({
          page: page.toString(),
          limit: limit.toString(),
          ...(search && { search }),
          ...(filters && { filters: JSON.stringify(filters) }),
        });
        return `${API_ENDPOINTS.PATIENTS.LIST}?${params}`;
      },
      providesTags: (result) =>
        result
          ? [
              ...result.patients.map(({ id }) => ({ type: 'Patient' as const, id })),
              { type: 'Patient', id: 'LIST' },
            ]
          : [{ type: 'Patient', id: 'LIST' }],
    }),
    
    getPatient: builder.query<any, string>({
      query: (id) => API_ENDPOINTS.PATIENTS.GET(id),
      providesTags: (_, __, id) => [{ type: 'Patient', id }],
    }),
    
    createPatient: builder.mutation<any, Partial<any>>({
      query: (patient) => ({
        url: API_ENDPOINTS.PATIENTS.CREATE,
        method: 'POST',
        body: patient,
      }),
      invalidatesTags: [{ type: 'Patient', id: 'LIST' }],
    }),
    
    updatePatient: builder.mutation<any, { id: string; updates: Partial<any> }>({
      query: ({ id, updates }) => ({
        url: API_ENDPOINTS.PATIENTS.UPDATE(id),
        method: 'PATCH',
        body: updates,
      }),
      invalidatesTags: (_, __, { id }) => [{ type: 'Patient', id }],
    }),
    
    deletePatient: builder.mutation<void, string>({
      query: (id) => ({
        url: API_ENDPOINTS.PATIENTS.DELETE(id),
        method: 'DELETE',
      }),
      invalidatesTags: [{ type: 'Patient', id: 'LIST' }],
    }),
    
    // Appointment endpoints
    getAppointments: builder.query<
      { appointments: any[]; total: number },
      { date?: string; doctorId?: string; status?: string; patientId?: string }
    >({
      query: (params) => {
        const searchParams = new URLSearchParams();
        Object.entries(params).forEach(([key, value]) => {
          if (value) searchParams.append(key, value);
        });
        return `${API_ENDPOINTS.APPOINTMENTS.LIST}?${searchParams}`;
      },
      providesTags: (result) =>
        result
          ? [
              ...result.appointments.map(({ id }) => ({ type: 'Appointment' as const, id })),
              { type: 'Appointment', id: 'LIST' },
            ]
          : [{ type: 'Appointment', id: 'LIST' }],
    }),
    
    getAppointment: builder.query<any, string>({
      query: (id) => API_ENDPOINTS.APPOINTMENTS.GET(id),
      providesTags: (_, __, id) => [{ type: 'Appointment', id }],
    }),
    
    createAppointment: builder.mutation<any, {
      patient_id: string;
      provider_id: string;
      appointment_type_id: string;
      appointment_date: string;
      start_time: string;
      reason: string;
      priority?: 'low' | 'medium' | 'high' | 'urgent';
      notes?: string;
      title?: string;
    }>({
      query: (appointment) => ({
        url: API_ENDPOINTS.APPOINTMENTS.CREATE,
        method: 'POST',
        body: appointment,
      }),
      invalidatesTags: [{ type: 'Appointment', id: 'LIST' }],
    }),
    
    updateAppointment: builder.mutation<any, { id: string; updates: Partial<any> }>({
      query: ({ id, updates }) => ({
        url: API_ENDPOINTS.APPOINTMENTS.UPDATE(id),
        method: 'PATCH',
        body: updates,
      }),
      invalidatesTags: (_, __, { id }) => [{ type: 'Appointment', id }],
    }),
    
    cancelAppointment: builder.mutation<any, { id: string; reason?: string }>({
      query: ({ id, reason }) => ({
        url: API_ENDPOINTS.APPOINTMENTS.CANCEL(id),
        method: 'POST',
        body: { reason },
      }),
      invalidatesTags: (_, __, { id }) => [{ type: 'Appointment', id }],
    }),
    
    // Manual SMS reminder endpoint
    sendManualSmsReminder: builder.mutation<{
      message: string;
      phone_number: string;
      appointment_id: string;
      response: string;
    }, string>({
      query: (appointmentId) => ({
        url: API_ENDPOINTS.APPOINTMENTS.SEND_SMS_REMINDER(appointmentId),
        method: 'POST',
      }),
    }),
    
    getAppointmentTypes: builder.query<
      { appointment_types: any[] },
      void
    >({
      query: () => API_ENDPOINTS.APPOINTMENTS.TYPES,
      providesTags: ['AppointmentType'],
    }),
    
    // Notification endpoints
    getNotifications: builder.query<
      { notifications: any[]; pagination: any },
      { page?: number; page_size?: number; status?: string; task_type?: string; delivery_method?: string }
    >({
      query: (params) => {
        const searchParams = new URLSearchParams();
        Object.entries(params).forEach(([key, value]) => {
          if (value) searchParams.append(key, value.toString());
        });
        return `/api/notifications/list?${searchParams}`;
      },
      providesTags: ['Notification'],
    }),
    
    sendNotification: builder.mutation<any, any>({
      query: (notification) => ({
        url: '/api/notifications/send',
        method: 'POST',
        body: notification,
      }),
      invalidatesTags: ['Notification'],
    }),
    
    markNotificationAsRead: builder.mutation<void, string>({
      query: (id) => ({
        url: `/api/notifications/${id}/read`,
        method: 'PATCH',
      }),
      invalidatesTags: ['Notification'],
    }),
    
    // Template endpoints
    getTemplates: builder.query<{ templates: any[]; total_count: number }, void>({
      query: () => '/api/notifications/templates',
      providesTags: ['Template'],
    }),
    
    createTemplate: builder.mutation<any, Partial<any>>({
      query: (template) => ({
        url: '/api/notifications/templates',
        method: 'POST',
        body: template,
      }),
      invalidatesTags: ['Template'],
    }),
    
    updateTemplate: builder.mutation<any, { id: string; updates: Partial<any> }>({
      query: ({ id, updates }) => ({
        url: `/api/notifications/templates/${id}`,
        method: 'PATCH',
        body: updates,
      }),
      invalidatesTags: ['Template'],
    }),
    
    // Medical Records
    getMedicalRecords: builder.query<any[], string>({
      query: (patientId) => `/api/accounts/patients/${patientId}/medical-records`,
      providesTags: (_, __, patientId) => [
        { type: 'MedicalRecord', id: patientId },
      ],
    }),
    
    addMedicalRecord: builder.mutation<any, { patientId: string; record: any }>({
      query: ({ patientId, record }) => ({
        url: `/api/accounts/patients/${patientId}/medical-records`,
        method: 'POST',
        body: record,
      }),
      invalidatesTags: (_, __, { patientId }) => [
        { type: 'MedicalRecord', id: patientId },
      ],
    }),
    
    // Prescriptions
    getPrescriptions: builder.query<any[], { patientId?: string; doctorId?: string }>({
      query: (params) => {
        const searchParams = new URLSearchParams();
        Object.entries(params).forEach(([key, value]) => {
          if (value) searchParams.append(key, value);
        });
        return `/api/prescriptions?${searchParams}`;
      },
      providesTags: ['Prescription'],
    }),
    
    createPrescription: builder.mutation<any, any>({
      query: (prescription) => ({
        url: '/api/prescriptions',
        method: 'POST',
        body: prescription,
      }),
      invalidatesTags: ['Prescription'],
    }),
    
    // Analytics and Reports
    getDashboardStats: builder.query<any, { period?: string }>({
      query: ({ period = '7d' }) => `/api/analytics/dashboard/?period=${period}`,
      providesTags: ['Analytics'],
    }),
    
    getReports: builder.query<any[], { type?: string; dateRange?: any }>({
      query: (params) => {
        const searchParams = new URLSearchParams();
        Object.entries(params).forEach(([key, value]) => {
          if (value) {
            searchParams.append(key, typeof value === 'object' ? JSON.stringify(value) : value);
          }
        });
        return `/reports?${searchParams}`;
      },
      providesTags: ['Report'],
    }),
    
    generateReport: builder.mutation<any, { type: string; params: any }>({
      query: ({ type, params }) => ({
        url: `/reports/generate`,
        method: 'POST',
        body: { type, params },
      }),
      invalidatesTags: ['Report'],
    }),
    
    // Staff Management endpoints
    getStaff: builder.query<any[], void>({
      query: () => API_ENDPOINTS.STAFF.LIST,
      transformResponse: (response: { staff: any[]; total: number }) => {
        // Transform the API response to return just the staff array
        return response.staff || [];
      },
      providesTags: (result) =>
        result
          ? [
              ...result.map(({ id }) => ({ type: 'Staff' as const, id })),
              { type: 'Staff', id: 'LIST' },
            ]
          : [{ type: 'Staff', id: 'LIST' }],
    }),
    
    getStaffMember: builder.query<any, string>({
      query: (id) => API_ENDPOINTS.STAFF.GET(id),
      providesTags: (_, __, id) => [{ type: 'Staff', id }],
    }),
    
    createStaff: builder.mutation<any, Partial<any>>({
      query: (staff) => ({
        url: API_ENDPOINTS.STAFF.CREATE,
        method: 'POST',
        body: staff,
      }),
      invalidatesTags: [{ type: 'Staff', id: 'LIST' }],
    }),
    
    updateStaff: builder.mutation<any, { id: string; updates: Partial<any> }>({
      query: ({ id, updates }) => ({
        url: API_ENDPOINTS.STAFF.UPDATE(id),
        method: 'PATCH',
        body: updates,
      }),
      invalidatesTags: (_, __, { id }) => [{ type: 'Staff', id }],
    }),
    
    // Care Team endpoints
    getCareTeams: builder.query<any[], void>({
      query: () => API_ENDPOINTS.CARE_TEAMS.LIST,
      providesTags: (result) =>
        result
          ? [
              ...result.map(({ id }) => ({ type: 'CareTeam' as const, id })),
              { type: 'CareTeam', id: 'LIST' },
            ]
          : [{ type: 'CareTeam', id: 'LIST' }],
    }),
    
    createCareTeam: builder.mutation<any, Partial<any>>({
      query: (careTeam) => ({
        url: API_ENDPOINTS.CARE_TEAMS.CREATE,
        method: 'POST',
        body: careTeam,
      }),
      invalidatesTags: [{ type: 'CareTeam', id: 'LIST' }],
    }),
    
    // Staff Credentials endpoints
    getStaffCredentials: builder.query<any[], string>({
      query: (staffId) => API_ENDPOINTS.STAFF_CREDENTIALS.LIST(staffId),
      providesTags: (result, _, staffId) =>
        result
          ? [
              ...result.map(({ id }) => ({ type: 'StaffCredential' as const, id })),
              { type: 'StaffCredential', id: `LIST-${staffId}` },
            ]
          : [{ type: 'StaffCredential', id: `LIST-${staffId}` }],
    }),
    
    getStaffCredential: builder.query<any, string>({
      query: (id) => API_ENDPOINTS.STAFF_CREDENTIALS.GET(id),
      providesTags: (_, __, id) => [{ type: 'StaffCredential', id }],
    }),
  }),
});

// Export hooks for usage in functional components
export const {
  useLoginMutation,
  useLogoutMutation,
  useRefreshTokenMutation,
  useRegisterHospitalMutation,
  useGetCurrentUserQuery,
  useUpdateProfileMutation,
  useGetPatientsQuery,
  useGetPatientQuery,
  useCreatePatientMutation,
  useUpdatePatientMutation,
  useDeletePatientMutation,
  useGetAppointmentsQuery,
  useGetAppointmentQuery,
  useCreateAppointmentMutation,
  useUpdateAppointmentMutation,
  useCancelAppointmentMutation,
  useGetAppointmentTypesQuery,
  useGetNotificationsQuery,
  useSendNotificationMutation,
  useMarkNotificationAsReadMutation,
  useGetTemplatesQuery,
  useCreateTemplateMutation,
  useUpdateTemplateMutation,
  useGetMedicalRecordsQuery,
  useAddMedicalRecordMutation,
  useGetPrescriptionsQuery,
  useCreatePrescriptionMutation,
  useGetDashboardStatsQuery,
  useGetReportsQuery,
  useGenerateReportMutation,
  useGetStaffQuery,
  useGetStaffMemberQuery,
  useCreateStaffMutation,
  useUpdateStaffMutation,
  useGetCareTeamsQuery,
  useCreateCareTeamMutation,
  useGetStaffCredentialsQuery,
  useGetStaffCredentialQuery,
  useSendManualSmsReminderMutation,
} = apiSlice;