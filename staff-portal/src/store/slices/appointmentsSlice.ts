import { createSlice } from '@reduxjs/toolkit';
import type { PayloadAction } from '@reduxjs/toolkit';

export interface Appointment {
  id: string;
  patientId: string;
  patientName: string;
  doctorId: string;
  doctorName: string;
  appointmentDate: string;
  startTime: string;
  endTime: string;
  duration: number; // in minutes
  type: 'consultation' | 'follow-up' | 'procedure' | 'emergency';
  status: 'scheduled' | 'confirmed' | 'in-progress' | 'completed' | 'cancelled' | 'no-show';
  priority: 'low' | 'medium' | 'high' | 'urgent';
  reason: string;
  notes?: string;
  room?: string;
  equipment?: string[];
  reminders: {
    email: boolean;
    sms: boolean;
    push: boolean;
    reminderTimes: number[]; // hours before appointment
  };
  createdAt: string;
  updatedAt: string;
}

export interface TimeSlot {
  start: string;
  end: string;
  available: boolean;
  doctorId?: string;
  room?: string;
}

interface AppointmentsState {
  calendar: Appointment[];
  upcoming: Appointment[];
  selected: Appointment | null;
  loading: boolean;
  error: string | null;
  filters: {
    doctorId?: string;
    patientId?: string;
    status?: string;
    type?: string;
    dateRange?: { start: string; end: string };
  };
  timeSlots: TimeSlot[];
  waitlist: {
    patientId: string;
    patientName: string;
    preferredDate: string;
    preferredTime: string;
    reason: string;
    priority: 'low' | 'medium' | 'high';
    createdAt: string;
  }[];
  view: 'day' | 'week' | 'month';
  selectedDate: string;
}

const initialState: AppointmentsState = {
  calendar: [],
  upcoming: [],
  selected: null,
  loading: false,
  error: null,
  filters: {},
  timeSlots: [],
  waitlist: [],
  view: 'week',
  selectedDate: new Date().toISOString().split('T')[0],
};

const appointmentsSlice = createSlice({
  name: 'appointments',
  initialState,
  reducers: {
    fetchAppointmentsStart: (state) => {
      state.loading = true;
      state.error = null;
    },
    fetchAppointmentsSuccess: (state, action: PayloadAction<Appointment[]>) => {
      state.loading = false;
      state.calendar = action.payload;
      state.upcoming = action.payload
        .filter(apt => new Date(apt.appointmentDate) >= new Date())
        .sort((a, b) => new Date(a.appointmentDate).getTime() - new Date(b.appointmentDate).getTime())
        .slice(0, 10);
      state.error = null;
    },
    fetchAppointmentsFailure: (state, action: PayloadAction<string>) => {
      state.loading = false;
      state.error = action.payload;
    },
    selectAppointment: (state, action: PayloadAction<Appointment>) => {
      state.selected = action.payload;
    },
    clearSelectedAppointment: (state) => {
      state.selected = null;
    },
    addAppointment: (state, action: PayloadAction<Appointment>) => {
      state.calendar.push(action.payload);
      // Update upcoming appointments if the new appointment is in the future
      if (new Date(action.payload.appointmentDate) >= new Date()) {
        state.upcoming = [...state.upcoming, action.payload]
          .sort((a, b) => new Date(a.appointmentDate).getTime() - new Date(b.appointmentDate).getTime())
          .slice(0, 10);
      }
    },
    updateAppointment: (state, action: PayloadAction<Appointment>) => {
      const index = state.calendar.findIndex(apt => apt.id === action.payload.id);
      if (index !== -1) {
        state.calendar[index] = action.payload;
      }
      
      const upcomingIndex = state.upcoming.findIndex(apt => apt.id === action.payload.id);
      if (upcomingIndex !== -1) {
        state.upcoming[upcomingIndex] = action.payload;
      }
      
      if (state.selected?.id === action.payload.id) {
        state.selected = action.payload;
      }
    },
    deleteAppointment: (state, action: PayloadAction<string>) => {
      state.calendar = state.calendar.filter(apt => apt.id !== action.payload);
      state.upcoming = state.upcoming.filter(apt => apt.id !== action.payload);
      if (state.selected?.id === action.payload) {
        state.selected = null;
      }
    },
    setFilters: (state, action: PayloadAction<Partial<AppointmentsState['filters']>>) => {
      state.filters = { ...state.filters, ...action.payload };
    },
    clearFilters: (state) => {
      state.filters = {};
    },
    setTimeSlots: (state, action: PayloadAction<TimeSlot[]>) => {
      state.timeSlots = action.payload;
    },
    addToWaitlist: (state, action: PayloadAction<AppointmentsState['waitlist'][0]>) => {
      state.waitlist.push(action.payload);
    },
    removeFromWaitlist: (state, action: PayloadAction<string>) => {
      state.waitlist = state.waitlist.filter(item => item.patientId !== action.payload);
    },
    setView: (state, action: PayloadAction<'day' | 'week' | 'month'>) => {
      state.view = action.payload;
    },
    setSelectedDate: (state, action: PayloadAction<string>) => {
      state.selectedDate = action.payload;
    },
    updateAppointmentStatus: (state, action: PayloadAction<{ id: string; status: Appointment['status'] }>) => {
      const appointment = state.calendar.find(apt => apt.id === action.payload.id);
      if (appointment) {
        appointment.status = action.payload.status;
        appointment.updatedAt = new Date().toISOString();
      }
      
      const upcomingAppointment = state.upcoming.find(apt => apt.id === action.payload.id);
      if (upcomingAppointment) {
        upcomingAppointment.status = action.payload.status;
        upcomingAppointment.updatedAt = new Date().toISOString();
      }
    },
    clearError: (state) => {
      state.error = null;
    },
  },
});

export const {
  fetchAppointmentsStart,
  fetchAppointmentsSuccess,
  fetchAppointmentsFailure,
  selectAppointment,
  clearSelectedAppointment,
  addAppointment,
  updateAppointment,
  deleteAppointment,
  setFilters,
  clearFilters,
  setTimeSlots,
  addToWaitlist,
  removeFromWaitlist,
  setView,
  setSelectedDate,
  updateAppointmentStatus,
  clearError,
} = appointmentsSlice.actions;

export default appointmentsSlice.reducer;