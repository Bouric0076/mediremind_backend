import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Grid,
  Divider,
  Alert,
  CircularProgress,
  IconButton,
  Card,
  CardContent,
  FormControlLabel,
  Switch,
  InputAdornment,
} from '@mui/material';
import {
  ArrowBack as ArrowBackIcon,
  Save as SaveIcon,
  Person as PersonIcon,
  Phone as PhoneIcon,
  Email as EmailIcon,
  Home as HomeIcon,
  LocalHospital as MedicalIcon,
  Visibility as VisibilityIcon,
  VisibilityOff as VisibilityOffIcon,
  AccountCircle as AccountIcon,
} from '@mui/icons-material';
import { setBreadcrumbs, setCurrentPage } from '../../store/slices/uiSlice';
import type { RootState } from '../../store';

interface PatientFormData {
  firstName: string;
  lastName: string;
  email: string;
  phone: string;
  dateOfBirth: string;
  gender: 'male' | 'female' | 'other' | '';
  address: {
    street: string;
    city: string;
    state: string;
    zipCode: string;
    country: string;
  };
  emergencyContact: {
    name: string;
    relationship: string;
    phone: string;
  };
  medicalInfo: {
    bloodType: string;
    allergies: string;
    medications: string;
    medicalHistory: string;
  };
  insurance: {
    provider: string;
    policyNumber: string;
    groupNumber: string;
  };
  account: {
    password: string;
    confirmPassword: string;
    createAccount: boolean;
  };
}

const initialFormData: PatientFormData = {
  firstName: '',
  lastName: '',
  email: '',
  phone: '',
  dateOfBirth: '',
  gender: '',
  address: {
    street: '',
    city: '',
    state: '',
    zipCode: '',
    country: 'USA',
  },
  emergencyContact: {
    name: '',
    relationship: '',
    phone: '',
  },
  medicalInfo: {
    bloodType: '',
    allergies: '',
    medications: '',
    medicalHistory: '',
  },
  insurance: {
    provider: '',
    policyNumber: '',
    groupNumber: '',
  },
  account: {
    password: '',
    confirmPassword: '',
    createAccount: true,
  },
};

export const AddPatientPage: React.FC = () => {
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const { token, isAuthenticated } = useSelector((state: RootState) => state.auth);
  const [formData, setFormData] = useState<PatientFormData>(initialFormData);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [passwordErrors, setPasswordErrors] = useState<string[]>([]);

  useEffect(() => {
    dispatch(setCurrentPage('patients'));
    dispatch(setBreadcrumbs([
      { label: 'Patients', path: '/app/patients' },
      { label: 'Add New Patient', path: '/app/patients/new' }
    ]));
  }, [dispatch]);

  const handleInputChange = (field: string, value: string | boolean) => {
    if (field.includes('.')) {
      const [parent, child] = field.split('.');
      setFormData(prev => {
        const parentValue = prev[parent as keyof PatientFormData];
        let processedValue = value;
        
        // Handle boolean conversion for specific fields
        if (field === 'account.createAccount') {
          processedValue = value === 'true' || value === true;
        }
        
        return {
          ...prev,
          [parent]: {
            ...(typeof parentValue === 'object' && parentValue !== null ? parentValue : {}),
            [child]: processedValue,
          },
        };
      });
    } else {
      setFormData(prev => ({
        ...prev,
        [field]: value,
      }));
    }
  };

  const validatePassword = (password: string): string[] => {
    const errors: string[] = [];
    
    if (password.length < 8) {
      errors.push('Password must be at least 8 characters long');
    }
    if (!/(?=.*[a-z])/.test(password)) {
      errors.push('Password must contain at least one lowercase letter');
    }
    if (!/(?=.*[A-Z])/.test(password)) {
      errors.push('Password must contain at least one uppercase letter');
    }
    if (!/(?=.*\d)/.test(password)) {
      errors.push('Password must contain at least one number');
    }
    if (!/(?=.*[@$!%*?&])/.test(password)) {
      errors.push('Password must contain at least one special character (@$!%*?&)');
    }
    
    return errors;
  };

  const validateForm = (): boolean => {
    if (!formData.firstName.trim()) {
      setError('First name is required');
      return false;
    }
    if (!formData.lastName.trim()) {
      setError('Last name is required');
      return false;
    }
    if (!formData.email.trim()) {
      setError('Email is required');
      return false;
    }
    if (!formData.phone.trim()) {
      setError('Phone number is required');
      return false;
    }
    if (!formData.dateOfBirth) {
      setError('Date of birth is required');
      return false;
    }
    if (!formData.gender) {
      setError('Gender is required');
      return false;
    }
    
    // Email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(formData.email)) {
      setError('Please enter a valid email address');
      return false;
    }

    // Password validation (only if creating account)
    if (formData.account.createAccount) {
      if (!formData.account.password.trim()) {
        setError('Password is required when creating an account');
        return false;
      }
      
      const passwordValidationErrors = validatePassword(formData.account.password);
      if (passwordValidationErrors.length > 0) {
        setPasswordErrors(passwordValidationErrors);
        setError('Please fix password requirements');
        return false;
      }
      
      if (formData.account.password !== formData.account.confirmPassword) {
        setError('Passwords do not match');
        return false;
      }
    }

    setPasswordErrors([]);
    return true;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!validateForm()) {
      return;
    }

    setLoading(true);

    try {
      // Check authentication state
      if (!isAuthenticated) {
        setError('Authentication required. Please log in again.');
        setLoading(false);
        return;
      }

      // Prepare the data for submission
      const submissionData = {
        ...formData,
        // Only include account data if creating an account
        account: formData.account.createAccount ? {
          createAccount: true,
          password: formData.account.password,
          // Don't send confirmPassword to the backend
        } : {
          createAccount: false,
        }
      };

      // Prepare headers
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
      };
      
      // Only add Token if it's not session-based auth
      if (token && token !== 'session_based_auth') {
        headers['Authorization'] = `Token ${token}`;
      }

      const response = await fetch('http://localhost:8000/accounts/create/', {
        method: 'POST',
        headers,
        credentials: 'include', // Include cookies for session authentication
        body: JSON.stringify(submissionData),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Failed to create patient');
      }

      setSuccess(true);
      
      // Show success message with account creation info
      if (formData.account.createAccount) {
        setError(null);
        // You could show a different success message here
      }
      
      setTimeout(() => {
        navigate('/app/patients');
      }, 2000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = () => {
    navigate('/app/patients');
  };

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
        <IconButton onClick={handleCancel} sx={{ mr: 2 }}>
          <ArrowBackIcon />
        </IconButton>
        <Typography variant="h4" component="h1">
          Add New Patient
        </Typography>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {success && (
        <Alert severity="success" sx={{ mb: 3 }}>
          {formData.account.createAccount 
            ? 'Patient created successfully with login account! The patient can now log in using their email and password. Redirecting...'
            : 'Patient created successfully! Redirecting...'
          }
        </Alert>
      )}

      <form onSubmit={handleSubmit}>
        <Grid container spacing={3}>
          {/* Personal Information */}
          <Grid size={12}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <PersonIcon sx={{ mr: 1, color: 'primary.main' }} />
                  <Typography variant="h6">Personal Information</Typography>
                </Box>
                <Grid container spacing={2}>
                  <Grid size={{ xs: 12, sm: 6 }}>
                    <TextField
                      fullWidth
                      label="First Name"
                      value={formData.firstName}
                      onChange={(e) => handleInputChange('firstName', e.target.value)}
                      required
                    />
                  </Grid>
                  <Grid size={{ xs: 12, sm: 6 }}>
                    <TextField
                      fullWidth
                      label="Last Name"
                      value={formData.lastName}
                      onChange={(e) => handleInputChange('lastName', e.target.value)}
                      required
                    />
                  </Grid>
                  <Grid size={{ xs: 12, sm: 6 }}>
                    <TextField
                      fullWidth
                      label="Email"
                      type="email"
                      value={formData.email}
                      onChange={(e) => handleInputChange('email', e.target.value)}
                      required
                    />
                  </Grid>
                  <Grid size={{ xs: 12, sm: 6 }}>
                    <TextField
                      fullWidth
                      label="Phone Number"
                      value={formData.phone}
                      onChange={(e) => handleInputChange('phone', e.target.value)}
                      required
                    />
                  </Grid>
                  <Grid size={{ xs: 12, sm: 6 }}>
                    <TextField
                      fullWidth
                      label="Date of Birth"
                      type="date"
                      value={formData.dateOfBirth}
                      onChange={(e) => handleInputChange('dateOfBirth', e.target.value)}
                      InputLabelProps={{ shrink: true }}
                      required
                    />
                  </Grid>
                  <Grid size={{ xs: 12, sm: 6 }}>
                    <FormControl fullWidth required>
                      <InputLabel>Gender</InputLabel>
                      <Select
                        value={formData.gender}
                        label="Gender"
                        onChange={(e) => handleInputChange('gender', e.target.value)}
                      >
                        <MenuItem value="male">Male</MenuItem>
                        <MenuItem value="female">Female</MenuItem>
                        <MenuItem value="other">Other</MenuItem>
                      </Select>
                    </FormControl>
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          </Grid>

          {/* Address Information */}
          <Grid size={12}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <HomeIcon sx={{ mr: 1, color: 'primary.main' }} />
                  <Typography variant="h6">Address Information</Typography>
                </Box>
                <Grid container spacing={2}>
                  <Grid size={12}>
                    <TextField
                      fullWidth
                      label="Street Address"
                      value={formData.address.street}
                      onChange={(e) => handleInputChange('address.street', e.target.value)}
                    />
                  </Grid>
                  <Grid size={{ xs: 12, sm: 6 }}>
                    <TextField
                      fullWidth
                      label="City"
                      value={formData.address.city}
                      onChange={(e) => handleInputChange('address.city', e.target.value)}
                    />
                  </Grid>
                  <Grid size={{ xs: 12, sm: 3 }}>
                    <TextField
                      fullWidth
                      label="State"
                      value={formData.address.state}
                      onChange={(e) => handleInputChange('address.state', e.target.value)}
                    />
                  </Grid>
                  <Grid size={{ xs: 12, sm: 3 }}>
                    <TextField
                      fullWidth
                      label="ZIP Code"
                      value={formData.address.zipCode}
                      onChange={(e) => handleInputChange('address.zipCode', e.target.value)}
                    />
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          </Grid>

          {/* Emergency Contact */}
          <Grid size={12}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <PhoneIcon sx={{ mr: 1, color: 'primary.main' }} />
                  <Typography variant="h6">Emergency Contact</Typography>
                </Box>
                <Grid container spacing={2}>
                  <Grid size={{ xs: 12, sm: 4 }}>
                    <TextField
                      fullWidth
                      label="Contact Name"
                      value={formData.emergencyContact.name}
                      onChange={(e) => handleInputChange('emergencyContact.name', e.target.value)}
                    />
                  </Grid>
                  <Grid size={{ xs: 12, sm: 4 }}>
                    <TextField
                      fullWidth
                      label="Relationship"
                      value={formData.emergencyContact.relationship}
                      onChange={(e) => handleInputChange('emergencyContact.relationship', e.target.value)}
                    />
                  </Grid>
                  <Grid size={{ xs: 12, sm: 4 }}>
                    <TextField
                      fullWidth
                      label="Phone Number"
                      value={formData.emergencyContact.phone}
                      onChange={(e) => handleInputChange('emergencyContact.phone', e.target.value)}
                    />
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          </Grid>

          {/* Medical Information */}
          <Grid size={12}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <MedicalIcon sx={{ mr: 1, color: 'primary.main' }} />
                  <Typography variant="h6">Medical Information</Typography>
                </Box>
                <Grid container spacing={2}>
                  <Grid size={{ xs: 12, sm: 6 }}>
                    <FormControl fullWidth>
                      <InputLabel>Blood Type</InputLabel>
                      <Select
                        value={formData.medicalInfo.bloodType}
                        label="Blood Type"
                        onChange={(e) => handleInputChange('medicalInfo.bloodType', e.target.value)}
                      >
                        <MenuItem value="A+">A+</MenuItem>
                        <MenuItem value="A-">A-</MenuItem>
                        <MenuItem value="B+">B+</MenuItem>
                        <MenuItem value="B-">B-</MenuItem>
                        <MenuItem value="AB+">AB+</MenuItem>
                        <MenuItem value="AB-">AB-</MenuItem>
                        <MenuItem value="O+">O+</MenuItem>
                        <MenuItem value="O-">O-</MenuItem>
                      </Select>
                    </FormControl>
                  </Grid>
                  <Grid size={{ xs: 12, sm: 6 }}>
                    <TextField
                      fullWidth
                      label="Allergies"
                      value={formData.medicalInfo.allergies}
                      onChange={(e) => handleInputChange('medicalInfo.allergies', e.target.value)}
                      placeholder="List any known allergies"
                    />
                  </Grid>
                  <Grid size={12}>
                    <TextField
                      fullWidth
                      label="Current Medications"
                      value={formData.medicalInfo.medications}
                      onChange={(e) => handleInputChange('medicalInfo.medications', e.target.value)}
                      multiline
                      rows={3}
                      placeholder="List current medications and dosages"
                    />
                  </Grid>
                  <Grid size={12}>
                    <TextField
                      fullWidth
                      label="Medical History"
                      value={formData.medicalInfo.medicalHistory}
                      onChange={(e) => handleInputChange('medicalInfo.medicalHistory', e.target.value)}
                      multiline
                      rows={4}
                      placeholder="Brief medical history and relevant conditions"
                    />
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          </Grid>

          {/* Insurance Information */}
          <Grid size={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" sx={{ mb: 2 }}>
                  Insurance Information
                </Typography>
                <Grid container spacing={2}>
                  <Grid size={{ xs: 12, sm: 4 }}>
                    <TextField
                      fullWidth
                      label="Insurance Provider"
                      value={formData.insurance.provider}
                      onChange={(e) => handleInputChange('insurance.provider', e.target.value)}
                    />
                  </Grid>
                  <Grid size={{ xs: 12, sm: 4 }}>
                    <TextField
                      fullWidth
                      label="Policy Number"
                      value={formData.insurance.policyNumber}
                      onChange={(e) => handleInputChange('insurance.policyNumber', e.target.value)}
                    />
                  </Grid>
                  <Grid size={{ xs: 12, sm: 4 }}>
                    <TextField
                      fullWidth
                      label="Group Number"
                      value={formData.insurance.groupNumber}
                      onChange={(e) => handleInputChange('insurance.groupNumber', e.target.value)}
                    />
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          </Grid>

          {/* Account Information */}
          <Grid size={12}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <AccountIcon sx={{ mr: 1, color: 'primary.main' }} />
                  <Typography variant="h6">
                    Account Information
                  </Typography>
                </Box>
                
                <FormControlLabel
                  control={
                    <Switch
                      checked={formData.account.createAccount}
                      onChange={(e) => handleInputChange('account.createAccount', e.target.checked.toString())}
                      color="primary"
                    />
                  }
                  label="Create patient login account"
                  sx={{ mb: 2 }}
                />

                {formData.account.createAccount && (
                  <>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                      Creating an account will allow the patient to log in and access their medical records, appointments, and other information.
                    </Typography>
                    
                    <Grid container spacing={2}>
                      <Grid size={{ xs: 12, sm: 6 }}>
                        <TextField
                          fullWidth
                          label="Password *"
                          type={showPassword ? 'text' : 'password'}
                          value={formData.account.password}
                          onChange={(e) => {
                            handleInputChange('account.password', e.target.value);
                            if (e.target.value) {
                              setPasswordErrors(validatePassword(e.target.value));
                            } else {
                              setPasswordErrors([]);
                            }
                          }}
                          error={passwordErrors.length > 0}
                          helperText={passwordErrors.length > 0 ? passwordErrors[0] : 'Password must meet security requirements'}
                          InputProps={{
                            endAdornment: (
                              <InputAdornment position="end">
                                <IconButton
                                  onClick={() => setShowPassword(!showPassword)}
                                  edge="end"
                                >
                                  {showPassword ? <VisibilityOffIcon /> : <VisibilityIcon />}
                                </IconButton>
                              </InputAdornment>
                            ),
                          }}
                        />
                      </Grid>
                      <Grid size={{ xs: 12, sm: 6 }}>
                        <TextField
                          fullWidth
                          label="Confirm Password *"
                          type={showConfirmPassword ? 'text' : 'password'}
                          value={formData.account.confirmPassword}
                          onChange={(e) => handleInputChange('account.confirmPassword', e.target.value)}
                          error={formData.account.password !== formData.account.confirmPassword && formData.account.confirmPassword.length > 0}
                          helperText={
                            formData.account.password !== formData.account.confirmPassword && formData.account.confirmPassword.length > 0
                              ? 'Passwords do not match'
                              : 'Re-enter the password to confirm'
                          }
                          InputProps={{
                            endAdornment: (
                              <InputAdornment position="end">
                                <IconButton
                                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                                  edge="end"
                                >
                                  {showConfirmPassword ? <VisibilityOffIcon /> : <VisibilityIcon />}
                                </IconButton>
                              </InputAdornment>
                            ),
                          }}
                        />
                      </Grid>
                    </Grid>

                    {passwordErrors.length > 0 && (
                      <Alert severity="info" sx={{ mt: 2 }}>
                        <Typography variant="subtitle2" sx={{ mb: 1 }}>Password Requirements:</Typography>
                        <ul style={{ margin: 0, paddingLeft: '20px' }}>
                          <li>At least 8 characters long</li>
                          <li>At least one lowercase letter</li>
                          <li>At least one uppercase letter</li>
                          <li>At least one number</li>
                          <li>At least one special character (@$!%*?&)</li>
                        </ul>
                      </Alert>
                    )}
                  </>
                )}
              </CardContent>
            </Card>
          </Grid>

          {/* Action Buttons */}
          <Grid size={12}>
            <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
              <Button
                variant="outlined"
                onClick={handleCancel}
                disabled={loading}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                variant="contained"
                startIcon={loading ? <CircularProgress size={20} /> : <SaveIcon />}
                disabled={loading}
              >
                {loading ? 'Creating...' : 'Create Patient'}
              </Button>
            </Box>
          </Grid>
        </Grid>
      </form>
    </Box>
  );
};