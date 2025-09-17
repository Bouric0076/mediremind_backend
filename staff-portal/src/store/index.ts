import { configureStore } from '@reduxjs/toolkit';
import { setupListeners } from '@reduxjs/toolkit/query';
import authSlice from './slices/authSlice';
import patientsSlice from './slices/patientsSlice';
import appointmentsSlice from './slices/appointmentsSlice';
import notificationsSlice from './slices/notificationsSlice';
import uiSlice from './slices/uiSlice';
import { apiSlice } from './api/apiSlice';

export const store = configureStore({
  reducer: {
    auth: authSlice,
    patients: patientsSlice,
    appointments: appointmentsSlice,
    notifications: notificationsSlice,
    ui: uiSlice,
    api: apiSlice.reducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: ['persist/PERSIST', 'persist/REHYDRATE'],
      },
      immutableCheck: {
        // Disable for large state objects to improve performance
        warnAfter: 128,
      },
    }).concat(apiSlice.middleware),
  devTools: process.env.NODE_ENV !== 'production',
});

// Setup listeners for RTK Query
setupListeners(store.dispatch);

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;

export default store;