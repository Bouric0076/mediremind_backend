import { createSlice } from '@reduxjs/toolkit';
import type { PayloadAction } from '@reduxjs/toolkit';
import * as Types from '../../types';

type Patient = Types.Patient;



interface PatientsState {
  list: Patient[];
  selected: Patient | null;
  loading: boolean;
  error: string | null;
  searchQuery: string;
  filters: {
    gender?: string;
    ageRange?: { min: number; max: number };
    isActive?: boolean;
    status?: string;
  };
  pagination: {
    page: number;
    limit: number;
    total: number;
    totalPages: number;
  };
}

const initialState: PatientsState = {
  list: [],
  selected: null,
  loading: false,
  error: null,
  searchQuery: '',
  filters: {},
  pagination: {
    page: 1,
    limit: 25,
    total: 0,
    totalPages: 0,
  },
};

const patientsSlice = createSlice({
  name: 'patients',
  initialState,
  reducers: {
    fetchPatientsStart: (state) => {
      state.loading = true;
      state.error = null;
    },
    fetchPatientsSuccess: (state, action: PayloadAction<{
      patients: Patient[];
      pagination: { page: number; limit: number; total: number; totalPages: number };
    }>) => {
      state.loading = false;
      state.list = action.payload.patients;
      state.pagination = action.payload.pagination;
      state.error = null;
    },
    fetchPatientsFailure: (state, action: PayloadAction<string>) => {
      state.loading = false;
      state.error = action.payload;
    },
    selectPatient: (state, action: PayloadAction<Patient>) => {
      state.selected = action.payload;
    },
    clearSelectedPatient: (state) => {
      state.selected = null;
    },
    addPatient: (state, action: PayloadAction<Patient>) => {
      state.list.unshift(action.payload);
      state.pagination.total += 1;
    },
    updatePatient: (state, action: PayloadAction<Patient>) => {
      const index = state.list.findIndex(patient => patient.id === action.payload.id);
      if (index !== -1) {
        state.list[index] = action.payload;
      }
      if (state.selected?.id === action.payload.id) {
        state.selected = action.payload;
      }
    },
    deletePatient: (state, action: PayloadAction<string>) => {
      state.list = state.list.filter(patient => patient.id !== action.payload);
      if (state.selected?.id === action.payload) {
        state.selected = null;
      }
      state.pagination.total -= 1;
    },
    setSearchQuery: (state, action: PayloadAction<string>) => {
      state.searchQuery = action.payload;
    },
    setFilters: (state, action: PayloadAction<Partial<PatientsState['filters']>>) => {
      state.filters = { ...state.filters, ...action.payload };
    },
    clearFilters: (state) => {
      state.filters = {};
      state.searchQuery = '';
    },
    setPagination: (state, action: PayloadAction<Partial<PatientsState['pagination']>>) => {
      state.pagination = { ...state.pagination, ...action.payload };
    },
    clearError: (state) => {
      state.error = null;
    },
  },
});

export const {
  fetchPatientsStart,
  fetchPatientsSuccess,
  fetchPatientsFailure,
  selectPatient,
  clearSelectedPatient,
  addPatient,
  updatePatient,
  deletePatient,
  setSearchQuery,
  setFilters,
  clearFilters,
  setPagination,
  clearError,
} = patientsSlice.actions;

export default patientsSlice.reducer;