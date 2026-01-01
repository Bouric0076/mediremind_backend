import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import {
  Box,
  Typography,
  TextField,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Grid,
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
import { API_CONFIG } from '../../constants';

// Custom debounce hook
const useDebounce = (value: string, delay: number) => {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
};

interface EmergencyContact {
  name: string;
  relationship: string;
  phone: string;
  email: string;
  priority: number;
}

interface PatientFormData {
  firstName: string;
  lastName: string;
  email: string;
  nationalId: string;
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
  emergencyContacts: EmergencyContact[];
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
  notificationPreferences: {
    emergencyContactNotifications: boolean;
    emergencyContactEmail: boolean;
    emergencyContactSms: boolean;
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
  nationalId: '',
  phone: '',
  dateOfBirth: '',
  gender: '',
  address: {
    street: '',
    city: '',
    state: '',
    zipCode: '',
    country: 'Kenya',
  },
  emergencyContacts: [
    { name: '', relationship: '', phone: '', email: '', priority: 1 }, // Primary contact
    { name: '', relationship: '', phone: '', email: '', priority: 2 }, // Secondary contact
    { name: '', relationship: '', phone: '', email: '', priority: 3 }, // Tertiary contact
  ],
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
  notificationPreferences: {
    emergencyContactNotifications: true, // Default to enabled as per user request
    emergencyContactEmail: true,
    emergencyContactSms: true,
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
  const [existingPatientFound, setExistingPatientFound] = useState(false);
  const [checkingExistingPatient, setCheckingExistingPatient] = useState(false);
  const [showLoadingIndicator, setShowLoadingIndicator] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [passwordErrors, setPasswordErrors] = useState<string[]>([]);
  const [patientAge, setPatientAge] = useState<number | null>(null);
  const [nationalIdRequired, setNationalIdRequired] = useState(true);
  const [autoFilledFields, setAutoFilledFields] = useState<Set<string>>(new Set());
  const [noPatientFound, setNoPatientFound] = useState(false);
  
  // Ref to track the current check request for cancellation
  const currentCheckRequest = useRef<AbortController | null>(null);
  
  // Helper function to check if a field is auto-filled
  const isFieldAutoFilled = (fieldName: string): boolean => {
    return autoFilledFields.has(fieldName);
  };
  
  // Helper function to get field styling for auto-filled fields
  const getAutoFilledFieldProps = (fieldName: string) => {
    return isFieldAutoFilled(fieldName) ? {
      sx: {
        '& .MuiOutlinedInput-root': {
          backgroundColor: '#e3f2fd', // Light blue background
          '& fieldset': {
            borderColor: '#2196f3', // Blue border
          },
        },
        '& .MuiInputLabel-root': {
          color: '#1976d2', // Darker blue for label
        },
      },
      InputProps: {
        endAdornment: (
          <InputAdornment position="end">
            <Typography variant="caption" color="primary" sx={{ fontSize: '0.7rem' }}>
              AUTO-FILLED
            </Typography>
          </InputAdornment>
        ),
      },
    } : {};
  };

  // Helper function for auto-filled Select components
  const getAutoFilledSelectProps = (fieldName: string) => {
    return isFieldAutoFilled(fieldName) ? {
      sx: {
        backgroundColor: '#e3f2fd', // Light blue background
        '& .MuiOutlinedInput-notchedOutline': {
          borderColor: '#2196f3', // Blue border
        },
      },
    } : {};
  };
  
  // Debounced values for real-time lookup
  const debouncedEmail = useDebounce(formData.email, 1200); // 1200ms delay - better for user experience
  const debouncedNationalId = useDebounce(formData.nationalId, 1200);

  useEffect(() => {
    dispatch(setCurrentPage('patients'));
    dispatch(setBreadcrumbs([
      { label: 'Patients', path: '/app/patients' },
      { label: 'Add New Patient', path: '/app/patients/new' }
    ]));
    
    // Cleanup function to abort any pending requests when component unmounts
    return () => {
      if (currentCheckRequest.current) {
        currentCheckRequest.current.abort();
      }
    };
  }, [dispatch]);

  // Real-time patient lookup when email or national ID changes
  useEffect(() => {
    if (debouncedEmail || debouncedNationalId) {
      checkExistingPatient(debouncedNationalId, debouncedEmail);
    }
  }, [debouncedEmail, debouncedNationalId]);

  const calculateAge = (birthDate: string): number => {
    const today = new Date();
    const birth = new Date(birthDate);
    let age = today.getFullYear() - birth.getFullYear();
    const monthDiff = today.getMonth() - birth.getMonth();
    
    if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birth.getDate())) {
      age--;
    }
    
    return age;
  };

  const checkExistingPatient = async (nationalId: string, email: string) => {
    // Reset states
    setExistingPatientFound(false);
    setNoPatientFound(false);
    setAutoFilledFields(new Set());
    
    // Check if we have enough information to look up an existing patient
    if (!email?.trim() && !nationalId?.trim()) {
      return;
    }
    
    // Cancel any previous request
    if (currentCheckRequest.current) {
      currentCheckRequest.current.abort();
    }
    
    // Create new abort controller for this request
    currentCheckRequest.current = new AbortController();
    
    setCheckingExistingPatient(true);
    
    // Show loading indicator after a short delay to avoid flickering for fast responses
    const loadingTimeout = setTimeout(() => {
      setShowLoadingIndicator(true);
    }, 300);
    
    try {
      const token = localStorage.getItem('token');
      const headers: HeadersInit = {
        'Content-Type': 'application/json',
      };
      
      if (token && token !== 'session_based_auth') {
        headers['Authorization'] = `Token ${token}`;
      }
      
      // Prepare request data based on what's available
      const requestData: Record<string, string> = {};
      if (email?.trim()) requestData.email = email.trim();
      if (nationalId?.trim()) requestData.nationalId = nationalId.trim();
      
      const response = await fetch(`${API_CONFIG.BASE_URL}/api/accounts/patients/check-existing/`, {
        method: 'POST',
        headers,
        credentials: 'include',
        body: JSON.stringify(requestData),
        signal: currentCheckRequest.current.signal,
      });
      
      if (response.ok) {
        const data = await response.json();
        setExistingPatientFound(data.exists);
        
        if (!data.exists) {
          setNoPatientFound(true);
        }
        
        // Auto-fill form data if patient exists
        if (data.exists && data.patient_data) {
          const patientData = data.patient_data;
          const newAutoFilledFields = new Set<string>();
          
          setFormData(prev => {
            const updatedData = { ...prev };
            
            // Auto-fill basic information
            if (patientData.first_name) {
              updatedData.firstName = patientData.first_name;
              newAutoFilledFields.add('firstName');
            }
            if (patientData.last_name) {
              updatedData.lastName = patientData.last_name;
              newAutoFilledFields.add('lastName');
            }
            if (patientData.email) {
              updatedData.email = patientData.email;
              newAutoFilledFields.add('email');
            }
            if (patientData.national_id) {
              updatedData.nationalId = patientData.national_id;
              newAutoFilledFields.add('nationalId');
            }
            if (patientData.phone) {
              updatedData.phone = patientData.phone;
              newAutoFilledFields.add('phone');
            }
            if (patientData.date_of_birth) {
              updatedData.dateOfBirth = patientData.date_of_birth;
              newAutoFilledFields.add('dateOfBirth');
            }
            if (patientData.gender) {
              updatedData.gender = patientData.gender;
              newAutoFilledFields.add('gender');
            }
            
            // Auto-fill address
            if (patientData.address) {
              if (patientData.address.street) {
                updatedData.address.street = patientData.address.street;
                newAutoFilledFields.add('address.street');
              }
              if (patientData.address.city) {
                updatedData.address.city = patientData.address.city;
                newAutoFilledFields.add('address.city');
              }
              if (patientData.address.state) {
                updatedData.address.state = patientData.address.state;
                newAutoFilledFields.add('address.state');
              }
              if (patientData.address.zip_code) {
                updatedData.address.zipCode = patientData.address.zip_code;
                newAutoFilledFields.add('address.zipCode');
              }
              if (patientData.address.country) {
                updatedData.address.country = patientData.address.country;
                newAutoFilledFields.add('address.country');
              }
            }
            
            // Auto-fill emergency contact
            if (patientData.emergency_contact) {
              // Auto-fill primary emergency contact (priority 1)
              if (patientData.emergency_contact.name) {
                updatedData.emergencyContacts[0].name = patientData.emergency_contact.name;
                newAutoFilledFields.add('emergencyContacts.0.name');
              }
              if (patientData.emergency_contact.relationship) {
                updatedData.emergencyContacts[0].relationship = patientData.emergency_contact.relationship;
                newAutoFilledFields.add('emergencyContacts.0.relationship');
              }
              if (patientData.emergency_contact.phone) {
                updatedData.emergencyContacts[0].phone = patientData.emergency_contact.phone;
                newAutoFilledFields.add('emergencyContacts.0.phone');
              }
              if (patientData.emergency_contact.email) {
                updatedData.emergencyContacts[0].email = patientData.emergency_contact.email;
                newAutoFilledFields.add('emergencyContacts.0.email');
              }
            }
            
            // Auto-fill medical info
            if (patientData.medical_info) {
              if (patientData.medical_info.blood_type) {
                updatedData.medicalInfo.bloodType = patientData.medical_info.blood_type;
                newAutoFilledFields.add('medicalInfo.bloodType');
              }
              if (patientData.medical_info.allergies) {
                updatedData.medicalInfo.allergies = patientData.medical_info.allergies;
                newAutoFilledFields.add('medicalInfo.allergies');
              }
              if (patientData.medical_info.medications) {
                updatedData.medicalInfo.medications = patientData.medical_info.medications;
                newAutoFilledFields.add('medicalInfo.medications');
              }
              if (patientData.medical_info.medical_history) {
                updatedData.medicalInfo.medicalHistory = patientData.medical_info.medical_history;
                newAutoFilledFields.add('medicalInfo.medicalHistory');
              }
            }
            
            // Auto-fill insurance
            if (patientData.insurance) {
              if (patientData.insurance.provider) {
                updatedData.insurance.provider = patientData.insurance.provider;
                newAutoFilledFields.add('insurance.provider');
              }
              if (patientData.insurance.policy_number) {
                updatedData.insurance.policyNumber = patientData.insurance.policy_number;
                newAutoFilledFields.add('insurance.policyNumber');
              }
              if (patientData.insurance.group_number) {
                updatedData.insurance.groupNumber = patientData.insurance.group_number;
                newAutoFilledFields.add('insurance.groupNumber');
              }
            }
            
            return updatedData;
          });
          
          setAutoFilledFields(newAutoFilledFields);
          
          // Calculate age if date of birth is available
          if (patientData.date_of_birth) {
            const age = calculateAge(patientData.date_of_birth);
            setPatientAge(age);
            setNationalIdRequired(age >= 18);
          }
        }
      }
    } catch (error) {
      // Don't log errors for aborted requests - this is expected behavior
      if (error instanceof Error && error.name !== 'AbortError') {
        console.error('Error checking existing patient:', error);
      }
      setExistingPatientFound(false);
    } finally {
      setCheckingExistingPatient(false);
      // Clear the loading timeout and hide indicator
      clearTimeout(loadingTimeout);
      setShowLoadingIndicator(false);
      // Clear the current request reference
      if (currentCheckRequest.current) {
        currentCheckRequest.current = null;
      }
    }
  };

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
    
    // Calculate age and update national ID requirement when date of birth changes
    if (field === 'dateOfBirth' && value) {
      const age = calculateAge(value as string);
      setPatientAge(age);
      // National ID is typically required for adults (18+), optional for minors
      setNationalIdRequired(age >= 18);
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
    if (nationalIdRequired && !formData.nationalId.trim()) {
      setError('National ID is required for patients 18 years and older');
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

    // Password validation (only if creating account and patient doesn't exist)
    if (formData.account.createAccount && !existingPatientFound) {
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
        // Transform emergency contacts for backend API
        emergencyContact: formData.emergencyContacts[0], // Primary contact goes to existing field
        additionalEmergencyContacts: formData.emergencyContacts.slice(1).filter(contact => 
          contact.name.trim() || contact.relationship.trim() || contact.phone.trim() || contact.email.trim()
        ), // Additional contacts (2-3) go to new field
        // Only include account data if creating an account and patient doesn't exist
        account: formData.account.createAccount && !existingPatientFound ? {
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

      const response = await fetch(`${API_CONFIG.BASE_URL}/api/accounts/patients/create/`, {
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
      
      // Handle existing patient case
      if (data.existing_patient) {
        setError(null);
        // Show success message for existing patient association
        // You could show a different success message here
      }
      
      // Show success message with account creation info
      if (formData.account.createAccount && data.account_created) {
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

  const clearAutoFilledFields = () => {
    setAutoFilledFields(new Set());
    setExistingPatientFound(false);
    setNoPatientFound(false);
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

      {patientAge !== null && (
        <Alert severity="info" sx={{ mb: 2 }}>
          Patient age: {patientAge} years old
          {patientAge < 18 ? ' (National ID optional for minors)' : ' (National ID required for adults)'}
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

      {existingPatientFound && autoFilledFields.size > 0 && (
        <Alert 
          severity="info" 
          sx={{ mb: 2 }}
          action={
            <Button color="inherit" size="small" onClick={clearAutoFilledFields}>
              Clear Auto-filled
            </Button>
          }
        >
          Found existing patient! {autoFilledFields.size} field{autoFilledFields.size !== 1 ? 's' : ''} auto-filled from existing records.
        </Alert>
      )}

      {noPatientFound && (
        <Alert severity="info" sx={{ mb: 2 }}>
          No existing patient found. Please fill in all required information.
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
                      label="Email"
                      type="email"
                      value={formData.email}
                      onChange={(e) => handleInputChange('email', e.target.value)}
                      required
                      InputProps={{
                        endAdornment: showLoadingIndicator ? (
                          <InputAdornment position="end">
                            <CircularProgress size={20} color="primary" />
                          </InputAdornment>
                        ) : null,
                      }}
                      helperText={formData.email ? "We'll check for existing patient records" : "Enter email to check for existing patient"}
                      {...getAutoFilledFieldProps('email')}
                    />
                  </Grid>
                  <Grid size={{ xs: 12, sm: 6 }}>
                    <TextField
                      fullWidth
                      label="First Name"
                      value={formData.firstName}
                      onChange={(e) => handleInputChange('firstName', e.target.value)}
                      required
                      {...getAutoFilledFieldProps('firstName')}
                    />
                  </Grid>
                  <Grid size={{ xs: 12, sm: 6 }}>
                    <TextField
                      fullWidth
                      label="Last Name"
                      value={formData.lastName}
                      onChange={(e) => handleInputChange('lastName', e.target.value)}
                      required
                      {...getAutoFilledFieldProps('lastName')}
                    />
                  </Grid>
                  <Grid size={{ xs: 12, sm: 6 }}>
                    <TextField
                      fullWidth
                      label="National ID Number"
                      value={formData.nationalId}
                      onChange={(e) => handleInputChange('nationalId', e.target.value)}
                      required={nationalIdRequired}
                      helperText={
                        nationalIdRequired 
                          ? "Required for patients 18 years and older" 
                          : "Optional for minors - can be added later when they obtain ID"
                      }
                      disabled={!nationalIdRequired && existingPatientFound}
                      {...getAutoFilledFieldProps('nationalId')}
                    />
                  </Grid>
                  <Grid size={{ xs: 12, sm: 6 }}>
                    <TextField
                      fullWidth
                      label="Phone Number"
                      value={formData.phone}
                      onChange={(e) => handleInputChange('phone', e.target.value)}
                      required
                      {...getAutoFilledFieldProps('phone')}
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
                      {...getAutoFilledFieldProps('dateOfBirth')}
                    />
                  </Grid>
                  <Grid size={{ xs: 12, sm: 6 }}>
                    <FormControl fullWidth required>
                      <InputLabel>Gender</InputLabel>
                      <Select
                        value={formData.gender}
                        label="Gender"
                        onChange={(e) => handleInputChange('gender', e.target.value)}
                        {...getAutoFilledSelectProps('gender')}
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

          {/* Emergency Contacts */}
          <Grid size={12}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <PhoneIcon sx={{ mr: 1, color: 'primary.main' }} />
                  <Typography variant="h6">Emergency Contacts</Typography>
                </Box>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                  You can add up to 3 emergency contacts. The primary contact (priority 1) is required.
                </Typography>
                
                {formData.emergencyContacts.map((contact, index) => (
                  <Box key={index} sx={{ mb: 3, p: 2, border: '1px solid #e0e0e0', borderRadius: 1, bgcolor: '#fafafa' }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                      <Typography variant="subtitle1" sx={{ flexGrow: 1 }}>
                        {index === 0 ? 'Primary Contact' : index === 1 ? 'Secondary Contact' : 'Tertiary Contact'} 
                        (Priority {contact.priority})
                      </Typography>
                      {index > 0 && (
                        <Button
                          size="small"
                          color="error"
                          onClick={() => {
                            const updatedContacts = [...formData.emergencyContacts];
                            updatedContacts[index] = { name: '', relationship: '', phone: '', email: '', priority: contact.priority };
                            setFormData(prev => ({ ...prev, emergencyContacts: updatedContacts }));
                          }}
                        >
                          Clear
                        </Button>
                      )}
                    </Box>
                    
                    <Grid container spacing={2}>
                      <Grid size={{ xs: 12, sm: 6 }}>
                        <TextField
                          fullWidth
                          label="Contact Name"
                          value={contact.name}
                          onChange={(e) => {
                            const updatedContacts = [...formData.emergencyContacts];
                            updatedContacts[index].name = e.target.value;
                            setFormData(prev => ({ ...prev, emergencyContacts: updatedContacts }));
                          }}
                          required={index === 0}
                          error={index === 0 && !contact.name.trim()}
                          helperText={index === 0 && !contact.name.trim() ? 'Primary contact name is required' : ''}
                        />
                      </Grid>
                      <Grid size={{ xs: 12, sm: 6 }}>
                        <TextField
                          fullWidth
                          label="Relationship"
                          value={contact.relationship}
                          onChange={(e) => {
                            const updatedContacts = [...formData.emergencyContacts];
                            updatedContacts[index].relationship = e.target.value;
                            setFormData(prev => ({ ...prev, emergencyContacts: updatedContacts }));
                          }}
                          required={index === 0}
                          error={index === 0 && !contact.relationship.trim()}
                          helperText={index === 0 && !contact.relationship.trim() ? 'Primary contact relationship is required' : ''}
                        />
                      </Grid>
                      <Grid size={{ xs: 12, sm: 6 }}>
                        <TextField
                          fullWidth
                          label="Phone Number"
                          value={contact.phone}
                          onChange={(e) => {
                            const updatedContacts = [...formData.emergencyContacts];
                            updatedContacts[index].phone = e.target.value;
                            setFormData(prev => ({ ...prev, emergencyContacts: updatedContacts }));
                          }}
                          required={index === 0}
                          error={index === 0 && !contact.phone.trim()}
                          helperText={index === 0 && !contact.phone.trim() ? 'Primary contact phone is required' : ''}
                        />
                      </Grid>
                      <Grid size={{ xs: 12, sm: 6 }}>
                        <TextField
                          fullWidth
                          label="Email Address"
                          type="email"
                          value={contact.email}
                          onChange={(e) => {
                            const updatedContacts = [...formData.emergencyContacts];
                            updatedContacts[index].email = e.target.value;
                            setFormData(prev => ({ ...prev, emergencyContacts: updatedContacts }));
                          }}
                          placeholder="Optional - for notifications"
                        />
                      </Grid>
                    </Grid>
                  </Box>
                ))}
                
                <Box sx={{ mt: 2 }}>
                  <Typography variant="body2" color="text.secondary">
                    💡 Tip: Emergency contacts will receive appointment notifications when enabled below.
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          {/* Notification Preferences */}
          <Grid size={12}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <EmailIcon sx={{ mr: 1, color: 'primary.main' }} />
                  <Typography variant="h6">Emergency Contact Notifications</Typography>
                </Box>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                  Configure when the emergency contact should receive appointment notifications. 
                  By default, emergency contacts will be notified of all appointment activities.
                </Typography>
                
                <Grid container spacing={2}>
                  <Grid size={12}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={formData.notificationPreferences.emergencyContactNotifications}
                          onChange={(e) => handleInputChange('notificationPreferences.emergencyContactNotifications', e.target.checked.toString())}
                          color="primary"
                        />
                      }
                      label="Enable emergency contact notifications"
                      sx={{ mb: 2 }}
                    />
                    <Typography variant="body2" color="text.secondary" sx={{ ml: 4, mb: 2 }}>
                      When enabled, the emergency contact will receive notifications about appointment confirmations, 
                      reminders, changes, and no-show alerts.
                    </Typography>
                  </Grid>
                  
                  {formData.notificationPreferences.emergencyContactNotifications && (
                    <>
                      <Grid size={{ xs: 12, sm: 6 }}>
                        <FormControlLabel
                          control={
                            <Switch
                              checked={formData.notificationPreferences.emergencyContactEmail}
                              onChange={(e) => handleInputChange('notificationPreferences.emergencyContactEmail', e.target.checked.toString())}
                              color="primary"
                            />
                          }
                          label="Email notifications"
                        />
                        <Typography variant="body2" color="text.secondary" sx={{ ml: 4 }}>
                          Send detailed email notifications to emergency contact
                        </Typography>
                      </Grid>
                      
                      <Grid size={{ xs: 12, sm: 6 }}>
                        <FormControlLabel
                          control={
                            <Switch
                              checked={formData.notificationPreferences.emergencyContactSms}
                              onChange={(e) => handleInputChange('notificationPreferences.emergencyContactSms', e.target.checked.toString())}
                              color="primary"
                            />
                          }
                          label="SMS notifications"
                        />
                        <Typography variant="body2" color="text.secondary" sx={{ ml: 4 }}>
                          Send SMS alerts to emergency contact's phone
                        </Typography>
                      </Grid>
                    </>
                  )}
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
                      disabled={existingPatientFound}
                    />
                  }
                  label={existingPatientFound ? "Patient account already exists" : "Create patient login account"}
                  sx={{ mb: 2 }}
                />

                {existingPatientFound && (
                  <Alert severity="info" sx={{ mb: 2 }}>
                    A patient with this national ID or email already exists in the system. 
                    The patient will be associated with your hospital without creating a new account.
                  </Alert>
                )}

                {checkingExistingPatient && (
                  <Alert severity="info" sx={{ mb: 2 }}>
                    Checking for existing patient account...
                  </Alert>
                )}

                {formData.account.createAccount && !existingPatientFound && (
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

export default AddPatientPage;