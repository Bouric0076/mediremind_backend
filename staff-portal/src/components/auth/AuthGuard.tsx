import React, { useEffect } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useSelector, useDispatch } from 'react-redux';
import { Box, CircularProgress, Typography } from '@mui/material';
import type { RootState } from '../../store';
import { useGetCurrentUserQuery } from '../../store/api/apiSlice';
import { loginSuccess } from '../../store/slices/authSlice';
import { validateAndCleanupSession, isTokenValid } from '../../utils/sessionUtils';

interface AuthGuardProps {
  children: React.ReactNode;
}

export const AuthGuard: React.FC<AuthGuardProps> = ({ children }) => {
  const dispatch = useDispatch();
  const location = useLocation();
  const { isAuthenticated, token, user } = useSelector((state: RootState) => state.auth);
  
  // Validate session on component mount and when token changes
  useEffect(() => {
    if (token && !isTokenValid(token)) {
      validateAndCleanupSession(true);
    }
  }, [token]);
  
  const {
    data: currentUser,
    error,
    isLoading,
    refetch,
  } = useGetCurrentUserQuery(undefined, {
    skip: !token || !!user || !isTokenValid(token), // Skip if no token, user already loaded, or token invalid
  });

  useEffect(() => {
    if (currentUser && !user) {
      dispatch(loginSuccess({ user: currentUser, token: token!, refreshToken: '' }));
    }
  }, [currentUser, user, token, dispatch]);

  useEffect(() => {
    if (error && 'status' in error && (error.status === 401 || error.status === 403)) {
      // Session is invalid, clear it with notification
      validateAndCleanupSession(true);
    }
  }, [error, dispatch]);

  // If not authenticated or token is invalid, redirect to login
  if (!isAuthenticated || !token || !isTokenValid(token)) {
    return (
      <Navigate
        to="/login"
        state={{ from: location }}
        replace
      />
    );
  }

  // If authenticated but user data is loading
  if (isLoading || (token && !user)) {
    return (
      <Box
        display="flex"
        flexDirection="column"
        alignItems="center"
        justifyContent="center"
        minHeight="100vh"
        gap={2}
      >
        <CircularProgress size={40} />
        <Typography variant="body2" color="text.secondary">
          Loading user data...
        </Typography>
      </Box>
    );
  }

  // If there's an error loading user data (other than 401)
  if (error && !('status' in error && error.status === 401)) {
    return (
      <Box
        display="flex"
        flexDirection="column"
        alignItems="center"
        justifyContent="center"
        minHeight="100vh"
        gap={2}
      >
        <Typography variant="h6" color="error">
          Failed to load user data
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Please try refreshing the page
        </Typography>
        <button onClick={() => refetch()}>Retry</button>
      </Box>
    );
  }

  // User is authenticated and data is loaded
  return <>{children}</>;
};