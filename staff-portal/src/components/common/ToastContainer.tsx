import React, { useEffect } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import {
  Snackbar,
  Alert,
  AlertTitle,
  Button,
  Box,
  Slide,
} from '@mui/material';
import type { SlideProps } from '@mui/material/Slide';
import type { RootState } from '../../store';
import { removeToast } from '../../store/slices/uiSlice';

function SlideTransition(props: SlideProps) {
  return <Slide {...props} direction="up" />;
}

export const ToastContainer: React.FC = () => {
  const dispatch = useDispatch();
  const { toasts } = useSelector((state: RootState) => state.ui);

  const handleClose = (toastId: string) => {
    dispatch(removeToast(toastId));
  };

  // Auto-remove toasts after their duration
  useEffect(() => {
    const timers: NodeJS.Timeout[] = [];

    toasts.forEach((toast) => {
      if (toast.duration && toast.duration > 0) {
        const timer = setTimeout(() => {
          handleClose(toast.id);
        }, toast.duration);
        timers.push(timer);
      }
    });

    return () => {
      timers.forEach(timer => clearTimeout(timer));
    };
  }, [toasts]);

  return (
    <>
      {toasts.map((toast, index) => (
        <Snackbar
          key={toast.id}
          open={true}
          onClose={() => handleClose(toast.id)}
          TransitionComponent={SlideTransition}
          anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
          sx={{
            // Stack multiple toasts
            bottom: `${16 + index * 80}px !important`,
            zIndex: (theme) => theme.zIndex.snackbar + index,
          }}
        >
          <Alert
            onClose={() => handleClose(toast.id)}
            severity={toast.type}
            variant="filled"
            sx={{
              width: '100%',
              minWidth: 300,
              maxWidth: 500,
            }}
            action={
              toast.action ? (
                <Button
                  color="inherit"
                  size="small"
                  onClick={() => {
                    toast.action?.onClick();
                    handleClose(toast.id);
                  }}
                >
                  {toast.action.label}
                </Button>
              ) : undefined
            }
          >
            {toast.title && (
              <AlertTitle sx={{ mb: toast.message ? 1 : 0 }}>
                {toast.title}
              </AlertTitle>
            )}
            {toast.message && (
              <Box component="div">
                {toast.message}
              </Box>
            )}
          </Alert>
        </Snackbar>
      ))}
    </>
  );
};