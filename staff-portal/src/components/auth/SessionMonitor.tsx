import React, { useEffect, useRef } from 'react';
import { useSelector } from 'react-redux';
import type { RootState } from '../../store';
import { validateAndCleanupSession, isTokenValid } from '../../utils/sessionUtils';

/**
 * SessionMonitor component that periodically checks for expired sessions
 * and automatically cleans up invalid sessions
 */
export const SessionMonitor: React.FC = () => {
  const { isAuthenticated, token } = useSelector((state: RootState) => state.auth);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const lastValidationRef = useRef<number>(0);

  useEffect(() => {
    // Only monitor if user is authenticated
    if (isAuthenticated && token) {
      // Check session validity every 30 seconds
      intervalRef.current = setInterval(() => {
        const now = Date.now();
        
        // Avoid too frequent validations (minimum 10 seconds between checks)
        if (now - lastValidationRef.current < 10000) {
          return;
        }
        
        lastValidationRef.current = now;
        
        // Validate current session
        if (!isTokenValid(token)) {
          console.log('Session expired, cleaning up...');
          validateAndCleanupSession(true);
        }
      }, 30000); // Check every 30 seconds

      // Also check immediately when component mounts
      if (!isTokenValid(token)) {
        validateAndCleanupSession(true);
      }
    }

    // Cleanup interval when component unmounts or user logs out
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [isAuthenticated, token]);

  // Handle page visibility change to check session when user returns to tab
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (!document.hidden && isAuthenticated && token) {
        // Check session when user returns to the tab
        if (!isTokenValid(token)) {
          validateAndCleanupSession(true);
        }
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);

    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [isAuthenticated, token]);

  // Handle storage events to sync logout across tabs
  useEffect(() => {
    const handleStorageChange = (event: StorageEvent) => {
      // If token was removed in another tab, logout in this tab too
      if (event.key === 'token' && event.newValue === null && isAuthenticated) {
        validateAndCleanupSession(false); // Don't show notification as it was already handled in other tab
      }
    };

    window.addEventListener('storage', handleStorageChange);

    return () => {
      window.removeEventListener('storage', handleStorageChange);
    };
  }, [isAuthenticated]);

  // This component doesn't render anything
  return null;
};