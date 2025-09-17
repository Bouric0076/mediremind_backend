import { createSlice } from '@reduxjs/toolkit';
import type { PayloadAction } from '@reduxjs/toolkit';

export interface Modal {
  id: string;
  type: 'confirm' | 'form' | 'info' | 'error' | 'custom';
  title: string;
  content?: string;
  component?: string;
  props?: Record<string, any>;
  onConfirm?: () => void;
  onCancel?: () => void;
  confirmText?: string;
  cancelText?: string;
  size?: 'small' | 'medium' | 'large' | 'fullscreen';
}

export interface Toast {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message?: string;
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

interface UIState {
  // Theme and appearance
  theme: 'light' | 'dark' | 'system';
  sidebarCollapsed: boolean;
  sidebarMobile: boolean;
  
  // Loading states
  globalLoading: boolean;
  loadingStates: Record<string, boolean>;
  
  // Modals and dialogs
  modals: Modal[];
  
  // Toast notifications
  toasts: Toast[];
  
  // Navigation
  breadcrumbs: Breadcrumb[];
  currentPage: string;
  
  // Layout preferences
  preferences: {
    density: 'comfortable' | 'compact' | 'spacious';
    animations: boolean;
    soundEnabled: boolean;
    autoSave: boolean;
    defaultView: 'grid' | 'list' | 'card';
    itemsPerPage: number;
    language: string;
    timezone: string;
  };
  
  // Search and filters
  globalSearch: {
    query: string;
    isOpen: boolean;
    results: any[];
    loading: boolean;
  };
  
  // Quick actions
  quickActions: {
    isOpen: boolean;
    recent: string[];
  };
  
  // Error handling
  errors: {
    id: string;
    message: string;
    code?: string;
    timestamp: string;
  }[];
  
  // Connection status
  isOnline: boolean;
  lastSync: string | null;
}

const initialState: UIState = {
  theme: 'system',
  sidebarCollapsed: false,
  sidebarMobile: false,
  globalLoading: false,
  loadingStates: {},
  modals: [],
  toasts: [],
  breadcrumbs: [],
  currentPage: 'dashboard',
  preferences: {
    density: 'comfortable',
    animations: true,
    soundEnabled: true,
    autoSave: true,
    defaultView: 'list',
    itemsPerPage: 25,
    language: 'en',
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
  },
  globalSearch: {
    query: '',
    isOpen: false,
    results: [],
    loading: false,
  },
  quickActions: {
    isOpen: false,
    recent: [],
  },
  errors: [],
  isOnline: navigator.onLine,
  lastSync: null,
};

const uiSlice = createSlice({
  name: 'ui',
  initialState,
  reducers: {
    // Theme and layout
    setTheme: (state, action: PayloadAction<'light' | 'dark' | 'system'>) => {
      state.theme = action.payload;
    },
    toggleSidebar: (state) => {
      state.sidebarCollapsed = !state.sidebarCollapsed;
    },
    setSidebarCollapsed: (state, action: PayloadAction<boolean>) => {
      state.sidebarCollapsed = action.payload;
    },
    setSidebarMobile: (state, action: PayloadAction<boolean>) => {
      state.sidebarMobile = action.payload;
    },
    
    // Loading states
    setGlobalLoading: (state, action: PayloadAction<boolean>) => {
      state.globalLoading = action.payload;
    },
    setLoadingState: (state, action: PayloadAction<{ key: string; loading: boolean }>) => {
      state.loadingStates[action.payload.key] = action.payload.loading;
    },
    clearLoadingState: (state, action: PayloadAction<string>) => {
      delete state.loadingStates[action.payload];
    },
    
    // Modals
    openModal: (state, action: PayloadAction<Modal>) => {
      state.modals.push(action.payload);
    },
    closeModal: (state, action: PayloadAction<string>) => {
      state.modals = state.modals.filter(modal => modal.id !== action.payload);
    },
    closeAllModals: (state) => {
      state.modals = [];
    },
    
    // Toasts
    addToast: (state, action: PayloadAction<Omit<Toast, 'id'>>) => {
      const toast: Toast = {
        id: Date.now().toString(),
        duration: 5000,
        ...action.payload,
      };
      state.toasts.push(toast);
    },
    removeToast: (state, action: PayloadAction<string>) => {
      state.toasts = state.toasts.filter(toast => toast.id !== action.payload);
    },
    clearToasts: (state) => {
      state.toasts = [];
    },
    
    // Navigation
    setBreadcrumbs: (state, action: PayloadAction<Breadcrumb[]>) => {
      state.breadcrumbs = action.payload;
    },
    setCurrentPage: (state, action: PayloadAction<string>) => {
      state.currentPage = action.payload;
    },
    
    // Preferences
    updatePreferences: (state, action: PayloadAction<Partial<UIState['preferences']>>) => {
      state.preferences = { ...state.preferences, ...action.payload };
    },
    
    // Global search
    setGlobalSearchQuery: (state, action: PayloadAction<string>) => {
      state.globalSearch.query = action.payload;
    },
    setGlobalSearchOpen: (state, action: PayloadAction<boolean>) => {
      state.globalSearch.isOpen = action.payload;
      if (!action.payload) {
        state.globalSearch.query = '';
        state.globalSearch.results = [];
      }
    },
    setGlobalSearchResults: (state, action: PayloadAction<any[]>) => {
      state.globalSearch.results = action.payload;
    },
    setGlobalSearchLoading: (state, action: PayloadAction<boolean>) => {
      state.globalSearch.loading = action.payload;
    },
    
    // Quick actions
    setQuickActionsOpen: (state, action: PayloadAction<boolean>) => {
      state.quickActions.isOpen = action.payload;
    },
    addRecentAction: (state, action: PayloadAction<string>) => {
      const recent = state.quickActions.recent.filter(item => item !== action.payload);
      recent.unshift(action.payload);
      state.quickActions.recent = recent.slice(0, 10); // Keep only last 10
    },
    
    // Error handling
    addError: (state, action: PayloadAction<{ message: string; code?: string }>) => {
      const error = {
        id: Date.now().toString(),
        message: action.payload.message,
        code: action.payload.code,
        timestamp: new Date().toISOString(),
      };
      state.errors.push(error);
      // Keep only last 50 errors
      if (state.errors.length > 50) {
        state.errors = state.errors.slice(-50);
      }
    },
    removeError: (state, action: PayloadAction<string>) => {
      state.errors = state.errors.filter(error => error.id !== action.payload);
    },
    clearErrors: (state) => {
      state.errors = [];
    },
    
    // Connection status
    setOnlineStatus: (state, action: PayloadAction<boolean>) => {
      state.isOnline = action.payload;
    },
    setLastSync: (state, action: PayloadAction<string>) => {
      state.lastSync = action.payload;
    },
  },
});

export const {
  setTheme,
  toggleSidebar,
  setSidebarCollapsed,
  setSidebarMobile,
  setGlobalLoading,
  setLoadingState,
  clearLoadingState,
  openModal,
  closeModal,
  closeAllModals,
  addToast,
  removeToast,
  clearToasts,
  setBreadcrumbs,
  setCurrentPage,
  updatePreferences,
  setGlobalSearchQuery,
  setGlobalSearchOpen,
  setGlobalSearchResults,
  setGlobalSearchLoading,
  setQuickActionsOpen,
  addRecentAction,
  addError,
  removeError,
  clearErrors,
  setOnlineStatus,
  setLastSync,
} = uiSlice.actions;

export default uiSlice.reducer;