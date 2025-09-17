import { useDispatch, useSelector } from 'react-redux';
import type { TypedUseSelectorHook } from 'react-redux';
import type { RootState, AppDispatch } from './index';
import type { Appointment } from './slices/appointmentsSlice';
import type { Notification } from './slices/notificationsSlice';

// Use throughout your app instead of plain `useDispatch` and `useSelector`
export const useAppDispatch = () => useDispatch<AppDispatch>();
export const useAppSelector: TypedUseSelectorHook<RootState> = useSelector;

// Custom hooks for common selectors
export const useAuth = () => {
  return useAppSelector((state) => state.auth);
};

export const useCurrentUser = () => {
  return useAppSelector((state) => state.auth.user);
};

export const useIsAuthenticated = () => {
  return useAppSelector((state) => state.auth.isAuthenticated);
};

export const useUI = () => {
  return useAppSelector((state) => state.ui);
};

export const useTheme = () => {
  return useAppSelector((state) => state.ui.theme);
};

export const useSidebarOpen = () => {
  return useAppSelector((state) => !state.ui.sidebarCollapsed);
};

export const useIsOnline = () => {
  return useAppSelector((state) => state.ui.isOnline);
};

export const useLoading = (key?: string) => {
  return useAppSelector((state) => {
    if (key) {
      return state.ui.loadingStates[key] || false;
    }
    return Object.values(state.ui.loadingStates).some(Boolean);
  });
};

export const useToasts = () => {
  return useAppSelector((state) => state.ui.toasts);
};

export const useModals = () => {
  return useAppSelector((state) => state.ui.modals);
};

export const useBreadcrumbs = () => {
  return useAppSelector((state) => state.ui.breadcrumbs);
};

export const usePatients = () => {
  return useAppSelector((state) => state.patients);
};

export const useAppointments = () => {
  return useAppSelector((state) => state.appointments);
};

export const useNotifications = () => {
  return useAppSelector((state) => state.notifications);
};

// Memoized selectors for better performance
export const useFilteredPatients = () => {
  return useAppSelector((state) => {
    const { list: patients, searchQuery, filters } = state.patients;

    if (!searchQuery && !filters.gender && !filters.isActive) {
      return patients;
    }

    return patients.filter((patient) => {
      const matchesSearch = !searchQuery || 
        patient.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        patient.contact.email?.toLowerCase().includes(searchQuery.toLowerCase());
      
      const matchesGender = !filters.gender || patient.gender === filters.gender;
      const matchesActive = filters.isActive === undefined || patient.status === 'active';
      
      return matchesSearch && matchesGender && matchesActive;
    });
  });
};

export const useFilteredAppointments = () => {
  return useAppSelector((state) => {
    const { calendar, filters } = state.appointments;
    if (!filters.status && !filters.dateRange) {
      return calendar;
    }
    
    return calendar.filter((appointment: Appointment) => {
      const matchesStatus = !filters.status || appointment.status === filters.status;
      
      const matchesDateRange = !filters.dateRange || 
        (new Date(appointment.startTime) >= new Date(filters.dateRange.start) &&
         new Date(appointment.startTime) <= new Date(filters.dateRange.end));
      
      return matchesStatus && matchesDateRange;
    });
  });
};

export const useUnreadNotifications = () => {
  return useAppSelector((state) => 
    state.notifications.unread.filter((notification: Notification) => notification.status === 'unread')
  );
};

export const useNotificationStats = () => {
  return useAppSelector((state) => state.notifications.stats);
};