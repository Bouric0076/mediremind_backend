import { createSlice } from '@reduxjs/toolkit';
import type { PayloadAction } from '@reduxjs/toolkit';

export interface User {
  id: string;
  email: string;
  firstName: string;
  lastName: string;
  role: 'doctor' | 'nurse' | 'admin' | 'receptionist';
  permissions: string[];
  avatar?: string;
  department?: string;
  specialization?: string;
  phone?: string;
  session_expires?: string;
}

interface AuthState {
  user: User | null;
  token: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

// Helper function to get token from localStorage, excluding session-based tokens
const getStoredToken = () => {
  const token = localStorage.getItem('token');
  return token === 'session_based_auth' ? null : token;
};

const getStoredRefreshToken = () => {
  const refreshToken = localStorage.getItem('refreshToken');
  return refreshToken === 'session_based_auth' ? null : refreshToken;
};

const initialState: AuthState = {
  user: null,
  token: getStoredToken(),
  refreshToken: getStoredRefreshToken(),
  isAuthenticated: false,
  isLoading: false,
  error: null,
};

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    loginStart: (state) => {
      state.isLoading = true;
      state.error = null;
    },
    loginSuccess: (state, action: PayloadAction<{ user: User; token: string; refreshToken: string }>) => {
      state.isLoading = false;
      state.isAuthenticated = true;
      state.user = action.payload.user;
      state.token = action.payload.token;
      state.refreshToken = action.payload.refreshToken;
      state.error = null;
      
      // Only store tokens in localStorage if they're not session-based
      if (action.payload.token !== 'session_based_auth') {
        localStorage.setItem('token', action.payload.token);
        localStorage.setItem('refreshToken', action.payload.refreshToken);
      } else {
        // For session-based auth, remove any existing tokens from localStorage
        localStorage.removeItem('token');
        localStorage.removeItem('refreshToken');
      }
    },
    loginFailure: (state, action: PayloadAction<string>) => {
      state.isLoading = false;
      state.isAuthenticated = false;
      state.user = null;
      state.token = null;
      state.refreshToken = null;
      state.error = action.payload;
      
      // Clear tokens from localStorage
      localStorage.removeItem('token');
      localStorage.removeItem('refreshToken');
    },
    logout: (state) => {
      state.isAuthenticated = false;
      state.user = null;
      state.token = null;
      state.refreshToken = null;
      state.error = null;
      
      // Clear tokens from localStorage
      localStorage.removeItem('token');
      localStorage.removeItem('refreshToken');
    },
    updateUser: (state, action: PayloadAction<Partial<User>>) => {
      if (state.user) {
        state.user = { ...state.user, ...action.payload };
      }
    },
    clearError: (state) => {
      state.error = null;
    },
    setTokens: (state, action: PayloadAction<{ token: string; refreshToken: string }>) => {
      state.token = action.payload.token;
      state.refreshToken = action.payload.refreshToken;
      
      // Only store tokens in localStorage if they're not session-based
      if (action.payload.token !== 'session_based_auth') {
        localStorage.setItem('token', action.payload.token);
        localStorage.setItem('refreshToken', action.payload.refreshToken);
      } else {
        // For session-based auth, remove any existing tokens from localStorage
        localStorage.removeItem('token');
        localStorage.removeItem('refreshToken');
      }
    },
  },
});

export const {
  loginStart,
  loginSuccess,
  loginFailure,
  logout,
  updateUser,
  clearError,
  setTokens,
} = authSlice.actions;

export default authSlice.reducer;