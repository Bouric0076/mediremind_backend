import { store } from '../store';
import { logout } from '../store/slices/authSlice';
import { addToast } from '../store/slices/uiSlice';

/**
 * Validates if a token is valid - handles both Django tokens and JWT tokens
 * @param token - Token to validate (Django token, JWT token, or 'session_based_auth' indicator)
 * @returns boolean indicating if token is valid (not expired)
 */
export const isTokenValid = (token: string | null): boolean => {
  if (!token) {
    return false;
  }

  // For session-based authentication, we rely on the server-side session
  // The session validity is checked via the session_expires field in user data
  if (token === 'session_based_auth') {
    const state = store.getState();
    const user = state.auth.user;
    
    if (!user || !user.session_expires) {
      return false;
    }
    
    try {
      const sessionExpires = new Date(user.session_expires);
      const currentTime = new Date();
      
      // Check if session is expired (with 30 second buffer)
      return sessionExpires.getTime() > (currentTime.getTime() + 30000);
    } catch (error) {
      console.error('Error validating session expiration:', error);
      return false;
    }
  }

  // Check if it's a JWT token (has 3 parts separated by dots)
  if (token.includes('.') && token.split('.').length === 3) {
    try {
      // Decode JWT token to check expiration
      const payload = JSON.parse(atob(token.split('.')[1]));
      const currentTime = Math.floor(Date.now() / 1000);
      
      // Check if token is expired (with 30 second buffer)
      return payload.exp && payload.exp > (currentTime + 30);
    } catch (error) {
      console.error('Error validating JWT token:', error);
      return false;
    }
  }

  // For Django authentication tokens (simple strings), check if user session is valid
  const state = store.getState();
  const user = state.auth.user;
  
  if (!user) {
    return false;
  }

  // If user has session_expires, use that for validation
  if (user.session_expires) {
    try {
      const sessionExpires = new Date(user.session_expires);
      const currentTime = new Date();
      
      // Check if session is expired (with 30 second buffer)
      return sessionExpires.getTime() > (currentTime.getTime() + 30000);
    } catch (error) {
      console.error('Error validating session expiration:', error);
      return false;
    }
  }

  // For Django tokens without explicit expiration, assume valid if user exists
  // The server will validate the actual token on each request
  return true;
};

/**
 * Checks if the current session is valid
 * @returns boolean indicating if session is valid
 */
export const isSessionValid = (): boolean => {
  const state = store.getState();
  const { token, isAuthenticated } = state.auth;
  
  if (!isAuthenticated || !token) {
    return false;
  }
  
  return isTokenValid(token);
};

/**
 * Clears expired or invalid session data from localStorage and Redux store
 * @param showNotification - Whether to show a notification to the user
 */
export const clearInvalidSession = (showNotification: boolean = true): void => {
  // Clear localStorage
  localStorage.removeItem('token');
  localStorage.removeItem('refreshToken');
  localStorage.removeItem('user');
  
  // Clear Redux store
  store.dispatch(logout());
  
  if (showNotification) {
    store.dispatch(addToast({
      type: 'warning',
      title: 'Session Expired',
      message: 'Your session has expired. Please log in again.',
    }));
  }
};

/**
 * Validates current session and clears if invalid
 * @param showNotification - Whether to show notification on invalid session
 * @returns boolean indicating if session is valid
 */
export const validateAndCleanupSession = (showNotification: boolean = true): boolean => {
  const valid = isSessionValid();
  
  if (!valid) {
    clearInvalidSession(showNotification);
  }
  
  return valid;
};

/**
 * Gets the current user from the Redux store
 * @returns User object or null
 */
export const getCurrentUser = () => {
  const state = store.getState();
  return state.auth.user;
};

/**
 * Checks if user has specific permission
 * @param permission - Permission to check
 * @returns boolean indicating if user has permission
 */
export const hasPermission = (permission: string): boolean => {
  const user = getCurrentUser();
  return user?.permissions?.includes(permission) || false;
};

/**
 * Gets the redirect path after login based on user role
 * @returns string path to redirect to
 */
export const getDefaultRedirectPath = (): string => {
  const user = getCurrentUser();
  
  if (!user) {
    return '/app/dashboard';
  }
  
  // Role-based default redirects
  const role = user.role as string;
  
  // Handle both legacy and current role names
  if (role === 'system_admin' || role === 'admin') {
    return '/app/dashboard';
  }
  if (role === 'physician' || role === 'doctor') {
    return '/app/patients';
  }
  if (role === 'nurse' || role === 'nurse_practitioner' || role === 'physician_assistant') {
    return '/app/patients';
  }
  if (role === 'receptionist') {
    return '/app/appointments';
  }
  
  return '/app/dashboard';
};