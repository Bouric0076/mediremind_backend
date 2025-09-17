import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { useForm, Controller } from 'react-hook-form';
import { yupResolver } from '@hookform/resolvers/yup';
import * as yup from 'yup';
import {
  Box,
  Paper,
  TextField,
  Button,
  Typography,
  Container,
  Alert,
  InputAdornment,
  IconButton,
  Divider,
  Link,
  CircularProgress,
} from '@mui/material';
import {
  Visibility,
  VisibilityOff,
  Email as EmailIcon,
  Lock as LockIcon,
  LocalHospital as HospitalIcon,
} from '@mui/icons-material';
import type { RootState } from '../../store';
import { useLoginMutation } from '../../store/api/apiSlice';
import { loginSuccess } from '../../store/slices/authSlice';
import { addToast } from '../../store/slices/uiSlice';
import { validateAndCleanupSession, getDefaultRedirectPath, isSessionValid } from '../../utils/sessionUtils';
import { medicalColors, easings, durations } from '../../theme/colors';

interface LoginFormData {
  email: string;
  password: string;
}

const loginSchema = yup.object({
  email: yup
    .string()
    .email('Please enter a valid email address')
    .required('Email is required'),
  password: yup
    .string()
    .min(6, 'Password must be at least 6 characters')
    .required('Password is required'),
});

export const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const dispatch = useDispatch();
  
  const [showPassword, setShowPassword] = useState(false);
  const { isAuthenticated, token } = useSelector((state: RootState) => state.auth);
  
  const [login, { isLoading, error }] = useLoginMutation();
  
  // Check for existing valid session on component mount
  useEffect(() => {
    if (token && !isSessionValid()) {
      // Clear invalid session without notification on login page
      validateAndCleanupSession(false);
    }
  }, [token]);
  
  const {
    control,
    handleSubmit,
    formState: { errors, isValid },
  } = useForm<LoginFormData>({
    resolver: yupResolver(loginSchema),
    mode: 'onChange',
    defaultValues: {
      email: '',
      password: '',
    },
  });

  // Redirect if already authenticated with valid session
  useEffect(() => {
    if (isAuthenticated && isSessionValid()) {
      const from = (location.state as any)?.from?.pathname || getDefaultRedirectPath();
      navigate(from, { replace: true });
    }
  }, [isAuthenticated, navigate, location]);

  const onSubmit = async (data: LoginFormData) => {
    try {
      const result = await login(data).unwrap();
      
      dispatch(loginSuccess({
          user: result.user,
          token: result.token,
          refreshToken: result.refreshToken,
        }));
      
      dispatch(addToast({
        type: 'success',
        title: 'Welcome back!',
        message: `Logged in as ${result.user.firstName} ${result.user.lastName}`,
      }));
      
      const from = (location.state as any)?.from?.pathname || getDefaultRedirectPath();
      navigate(from, { replace: true });
    } catch (err: any) {
      dispatch(addToast({
        type: 'error',
        title: 'Login Failed',
        message: err.data?.message || 'Invalid email or password',
      }));
    }
  };

  const handleTogglePasswordVisibility = () => {
    setShowPassword(!showPassword);
  };

  return (
    <Box
      sx={{
        minHeight: '100vh',
        background: medicalColors.gradients.backgroundHero,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        py: 3,
      }}
    >
      <Container component="main" maxWidth="sm">
        <Box
          sx={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
          }}
        >
          <Paper
            elevation={0}
            sx={{
              padding: { xs: 3, sm: 5 },
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              width: '100%',
              borderRadius: 3,
              background: medicalColors.gradients.glass,
              backdropFilter: 'blur(20px)',
              border: `1px solid ${medicalColors.neutral[200]}`,
              boxShadow: medicalColors.shadows.large,
            }}
          >
            <Box
              sx={{
                width: 80,
                height: 80,
                borderRadius: '50%',
                background: medicalColors.gradients.medicalAccent,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                mb: 2,
                boxShadow: medicalColors.shadows.primary,
              }}
            >
              <HospitalIcon sx={{ fontSize: 40, color: 'white' }} />
            </Box>
            <Typography 
              component="h1" 
              variant="h4" 
              sx={{ 
                fontWeight: 700,
                color: medicalColors.medical.textPrimary,
                mb: 1,
                textAlign: 'center',
              }}
            >
              Welcome Back
            </Typography>
            <Typography 
              variant="body1" 
              sx={{ 
                color: medicalColors.medical.textSecondary,
                mb: 3,
                textAlign: 'center',
              }}
            >
              Sign in to access your medical dashboard
            </Typography>

          {/* Error Alert */}
          {error && 'data' in error && (
            <Alert 
              severity="error" 
              sx={{ 
                width: '100%', 
                mb: 3,
                borderRadius: 2,
                '& .MuiAlert-icon': {
                  color: '#d32f2f',
                },
              }}
            >
              {(error.data as any)?.message || 'Login failed. Please try again.'}
            </Alert>
          )}

          {/* Login Form */}
          <Box
            component="form"
            onSubmit={handleSubmit(onSubmit)}
            sx={{ width: '100%' }}
          >
            <Controller
              name="email"
              control={control}
              render={({ field }) => (
                <TextField
                  {...field}
                  fullWidth
                  label="Email Address"
                  type="email"
                  autoComplete="email"
                  autoFocus
                  error={!!errors.email}
                  helperText={errors.email?.message}
                  sx={{ 
                    mb: 2,
                    '& .MuiOutlinedInput-root': {
                      borderRadius: 2,
                      backgroundColor: medicalColors.medical.backgroundSecondary,
                      '&:hover .MuiOutlinedInput-notchedOutline': {
                        borderColor: medicalColors.primary.main,
                      },
                      '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
                        borderColor: medicalColors.primary.main,
                        borderWidth: 2,
                      },
                    },
                    '& .MuiInputLabel-root.Mui-focused': {
                      color: medicalColors.primary.main,
                    },
                  }}
                  InputProps={{
                    startAdornment: (
                      <InputAdornment position="start">
                        <EmailIcon color="action" />
                      </InputAdornment>
                    ),
                  }}
                />
              )}
            />

            <Controller
              name="password"
              control={control}
              render={({ field }) => (
                <TextField
                  {...field}
                  fullWidth
                  label="Password"
                  type={showPassword ? 'text' : 'password'}
                  autoComplete="current-password"
                  error={!!errors.password}
                  helperText={errors.password?.message}
                  sx={{ 
                    mb: 3,
                    '& .MuiOutlinedInput-root': {
                      borderRadius: 2,
                      backgroundColor: medicalColors.medical.backgroundSecondary,
                      '&:hover .MuiOutlinedInput-notchedOutline': {
                        borderColor: medicalColors.primary.main,
                      },
                      '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
                        borderColor: medicalColors.primary.main,
                        borderWidth: 2,
                      },
                    },
                    '& .MuiInputLabel-root.Mui-focused': {
                      color: medicalColors.primary.main,
                    },
                  }}
                  InputProps={{
                    startAdornment: (
                      <InputAdornment position="start">
                        <LockIcon color="action" />
                      </InputAdornment>
                    ),
                    endAdornment: (
                      <InputAdornment position="end">
                        <IconButton
                          aria-label="toggle password visibility"
                          onClick={handleTogglePasswordVisibility}
                          edge="end"
                          sx={{
                            color: medicalColors.medical.textSecondary,
                            '&:hover': {
                              color: medicalColors.primary.main,
                            },
                          }}
                        >
                          {showPassword ? <VisibilityOff /> : <Visibility />}
                        </IconButton>
                      </InputAdornment>
                    ),
                  }}
                />
              )}
            />

            <Button
              type="submit"
              fullWidth
              variant="contained"
              size="large"
              disabled={!isValid || isLoading}
              sx={{ 
                mb: 3, 
                py: 1.5,
                borderRadius: 2,
                background: medicalColors.gradients.medicalAccent,
                boxShadow: medicalColors.shadows.primary,
                fontWeight: 600,
                fontSize: '1.1rem',
                textTransform: 'none',
                '&:hover': {
                  background: medicalColors.gradients.primary,
                  boxShadow: medicalColors.shadows.hoverLarge,
                  transform: 'translateY(-2px)',
                },
                '&:disabled': {
                  background: medicalColors.neutral[400],
                  boxShadow: 'none',
                },
                transition: `all ${durations.standard}ms ${easings.easeOut}`,
              }}
            >
              {isLoading ? (
                <CircularProgress size={24} sx={{ color: 'white' }} />
              ) : (
                'Sign In to Dashboard'
              )}
            </Button>

            <Box sx={{ textAlign: 'center', mb: 3 }}>
              <Link
                component="button"
                variant="body2"
                onClick={() => {
                  dispatch(addToast({
                    type: 'info',
                    title: 'Password Reset',
                    message: 'Please contact your system administrator to reset your password.',
                  }));
                }}
                sx={{
                  color: medicalColors.primary.main,
                  textDecoration: 'none',
                  fontWeight: 500,
                  '&:hover': {
                    textDecoration: 'underline',
                    color: medicalColors.primary.dark,
                  },
                }}
              >
                Forgot your password?
              </Link>
            </Box>
          </Box>

          <Divider sx={{ width: '100%', my: 3 }}>
            <Typography 
              variant="body2" 
              sx={{ 
                color: medicalColors.medical.textSecondary,
                fontWeight: 500,
                px: 2,
              }}
            >
              Demo Credentials
            </Typography>
          </Divider>

          {/* Demo Credentials */}
          <Box 
            sx={{ 
              textAlign: 'center', 
              width: '100%',
              p: 2,
              backgroundColor: medicalColors.medical.backgroundSecondary,
              borderRadius: 2,
              border: `1px solid ${medicalColors.neutral[200]}`,
            }}
          >
            <Typography variant="body2" sx={{ color: medicalColors.medical.textPrimary, mb: 1 }}>
              <strong>Email:</strong> admin@mediremind.test
            </Typography>
            <Typography variant="body2" sx={{ color: medicalColors.medical.textPrimary }}>
              <strong>Password:</strong> TestAdmin123!
            </Typography>
          </Box>
        </Paper>

        {/* Footer */}
        <Box sx={{ mt: 4, textAlign: 'center' }}>
          <Typography 
            variant="body2" 
            sx={{ 
              color: medicalColors.medical.textSecondary,
              fontWeight: 500,
            }}
          >
            {'© '}
            <Box component="span" sx={{ fontWeight: 700 }}>
              MediRemind
            </Box>
            {' ' + new Date().getFullYear() + '. All rights reserved.'}
          </Typography>
        </Box>
      </Box>
    </Container>
  </Box>
  );
};