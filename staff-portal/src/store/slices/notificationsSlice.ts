import { createSlice } from '@reduxjs/toolkit';
import type { PayloadAction } from '@reduxjs/toolkit';

export interface Notification {
  id: string;
  type: 'appointment' | 'reminder' | 'alert' | 'system' | 'message';
  title: string;
  message: string;
  priority: 'low' | 'medium' | 'high' | 'urgent';
  status: 'unread' | 'read' | 'archived';
  channels: ('email' | 'sms' | 'push' | 'in-app')[];
  recipients: {
    id: string;
    name: string;
    email?: string;
    phone?: string;
    type: 'patient' | 'staff';
  }[];
  scheduledFor?: string;
  sentAt?: string;
  deliveryStatus: {
    email?: 'pending' | 'sent' | 'delivered' | 'failed';
    sms?: 'pending' | 'sent' | 'delivered' | 'failed';
    push?: 'pending' | 'sent' | 'delivered' | 'failed';
  };
  metadata?: {
    appointmentId?: string;
    patientId?: string;
    doctorId?: string;
    templateId?: string;
  };
  createdAt: string;
  updatedAt: string;
}

export interface NotificationTemplate {
  id: string;
  name: string;
  type: 'appointment' | 'reminder' | 'alert' | 'system';
  subject: string;
  emailTemplate: string;
  smsTemplate: string;
  pushTemplate: string;
  variables: string[];
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
}

interface NotificationsState {
  unread: Notification[];
  history: Notification[];
  selected: Notification | null;
  loading: boolean;
  error: string | null;
  templates: NotificationTemplate[];
  settings: {
    emailEnabled: boolean;
    smsEnabled: boolean;
    pushEnabled: boolean;
    defaultReminderTimes: number[]; // hours before appointment
    autoSendReminders: boolean;
    quietHours: {
      enabled: boolean;
      start: string; // HH:mm format
      end: string; // HH:mm format
    };
  };
  filters: {
    type?: string;
    priority?: string;
    status?: string;
    dateRange?: { start: string; end: string };
  };
  stats: {
    totalSent: number;
    deliveryRate: number;
    openRate: number;
    clickRate: number;
  };
}

const initialState: NotificationsState = {
  unread: [],
  history: [],
  selected: null,
  loading: false,
  error: null,
  templates: [],
  settings: {
    emailEnabled: true,
    smsEnabled: true,
    pushEnabled: true,
    defaultReminderTimes: [24, 2], // 24 hours and 2 hours before
    autoSendReminders: true,
    quietHours: {
      enabled: true,
      start: '22:00',
      end: '08:00',
    },
  },
  filters: {},
  stats: {
    totalSent: 0,
    deliveryRate: 0,
    openRate: 0,
    clickRate: 0,
  },
};

const notificationsSlice = createSlice({
  name: 'notifications',
  initialState,
  reducers: {
    fetchNotificationsStart: (state) => {
      state.loading = true;
      state.error = null;
    },
    fetchNotificationsSuccess: (state, action: PayloadAction<{
      unread: Notification[];
      history: Notification[];
    }>) => {
      state.loading = false;
      state.unread = action.payload.unread;
      state.history = action.payload.history;
      state.error = null;
    },
    fetchNotificationsFailure: (state, action: PayloadAction<string>) => {
      state.loading = false;
      state.error = action.payload;
    },
    addNotification: (state, action: PayloadAction<Notification>) => {
      if (action.payload.status === 'unread') {
        state.unread.unshift(action.payload);
      } else {
        state.history.unshift(action.payload);
      }
    },
    markAsRead: (state, action: PayloadAction<string>) => {
      const notification = state.unread.find(n => n.id === action.payload);
      if (notification) {
        notification.status = 'read';
        notification.updatedAt = new Date().toISOString();
        // Move from unread to history
        state.unread = state.unread.filter(n => n.id !== action.payload);
        state.history.unshift(notification);
      }
    },
    markAllAsRead: (state) => {
      state.unread.forEach(notification => {
        notification.status = 'read';
        notification.updatedAt = new Date().toISOString();
      });
      state.history = [...state.unread, ...state.history];
      state.unread = [];
    },
    archiveNotification: (state, action: PayloadAction<string>) => {
      const unreadIndex = state.unread.findIndex(n => n.id === action.payload);
      if (unreadIndex !== -1) {
        state.unread[unreadIndex].status = 'archived';
        state.unread[unreadIndex].updatedAt = new Date().toISOString();
      }
      
      const historyIndex = state.history.findIndex(n => n.id === action.payload);
      if (historyIndex !== -1) {
        state.history[historyIndex].status = 'archived';
        state.history[historyIndex].updatedAt = new Date().toISOString();
      }
    },
    deleteNotification: (state, action: PayloadAction<string>) => {
      state.unread = state.unread.filter(n => n.id !== action.payload);
      state.history = state.history.filter(n => n.id !== action.payload);
      if (state.selected?.id === action.payload) {
        state.selected = null;
      }
    },
    selectNotification: (state, action: PayloadAction<Notification>) => {
      state.selected = action.payload;
    },
    clearSelectedNotification: (state) => {
      state.selected = null;
    },
    updateNotificationStatus: (state, action: PayloadAction<{
      id: string;
      deliveryStatus: Partial<Notification['deliveryStatus']>;
    }>) => {
      const updateNotification = (notification: Notification) => {
        if (notification.id === action.payload.id) {
          notification.deliveryStatus = {
            ...notification.deliveryStatus,
            ...action.payload.deliveryStatus,
          };
          notification.updatedAt = new Date().toISOString();
        }
      };
      
      state.unread.forEach(updateNotification);
      state.history.forEach(updateNotification);
    },
    setTemplates: (state, action: PayloadAction<NotificationTemplate[]>) => {
      state.templates = action.payload;
    },
    addTemplate: (state, action: PayloadAction<NotificationTemplate>) => {
      state.templates.push(action.payload);
    },
    updateTemplate: (state, action: PayloadAction<NotificationTemplate>) => {
      const index = state.templates.findIndex(t => t.id === action.payload.id);
      if (index !== -1) {
        state.templates[index] = action.payload;
      }
    },
    deleteTemplate: (state, action: PayloadAction<string>) => {
      state.templates = state.templates.filter(t => t.id !== action.payload);
    },
    updateSettings: (state, action: PayloadAction<Partial<NotificationsState['settings']>>) => {
      state.settings = { ...state.settings, ...action.payload };
    },
    setFilters: (state, action: PayloadAction<Partial<NotificationsState['filters']>>) => {
      state.filters = { ...state.filters, ...action.payload };
    },
    clearFilters: (state) => {
      state.filters = {};
    },
    updateStats: (state, action: PayloadAction<Partial<NotificationsState['stats']>>) => {
      state.stats = { ...state.stats, ...action.payload };
    },
    clearError: (state) => {
      state.error = null;
    },
  },
});

export const {
  fetchNotificationsStart,
  fetchNotificationsSuccess,
  fetchNotificationsFailure,
  addNotification,
  markAsRead,
  markAllAsRead,
  archiveNotification,
  deleteNotification,
  selectNotification,
  clearSelectedNotification,
  updateNotificationStatus,
  setTemplates,
  addTemplate,
  updateTemplate,
  deleteTemplate,
  updateSettings,
  setFilters,
  clearFilters,
  updateStats,
  clearError,
} = notificationsSlice.actions;

export default notificationsSlice.reducer;