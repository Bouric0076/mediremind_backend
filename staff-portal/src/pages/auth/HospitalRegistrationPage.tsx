import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useForm, Controller } from 'react-hook-form';
import { yupResolver } from '@hookform/resolvers/yup';
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
  Grid,
  MenuItem,
  CircularProgress,
  Stepper,
  Step,
  StepLabel,
  Card,
  CardContent,
  Chip,
} from '@mui/material';
import {
  Visibility,
  VisibilityOff,
  Business as BusinessIcon,
  Email as EmailIcon,
  Phone as PhoneIcon,
  Lock as LockIcon,
  LocalHospital as HospitalIcon,
  ArrowBack as ArrowBackIcon,
  ArrowForward as ArrowForwardIcon,
  CheckCircle as CheckCircleIcon,
} from '@mui/icons-material';
import { useRegisterHospitalMutation } from '../../store/api/apiSlice';
import { medicalColors } from '../../theme/colors';
import {
  hospitalInfoSchema,
  addressBusinessSchema,
  administratorSchema,
  type HospitalInfoData,
  type AddressBusinessData,
  type AdministratorData,
  type CompleteRegistrationData
} from './hospitalRegistrationSchemas';



const hospitalTypes = [
  { value: 'general_hospital', label: 'General Hospital' },
  { value: 'clinic', label: 'Clinic' },
  { value: 'emergency_center', label: 'Emergency Center' },
  { value: 'specialty_hospital', label: 'Specialty Hospital' },
  { value: 'rehabilitation_center', label: 'Rehabilitation Center' },
  { value: 'mental_health_facility', label: 'Mental Health Facility' },
  { value: 'maternity_hospital', label: 'Maternity Hospital' },
  { value: 'pediatric_hospital', label: 'Pediatric Hospital' },
  { value: 'surgical_center', label: 'Surgical Center' },
  { value: 'diagnostic_center', label: 'Diagnostic Center' },
  { value: 'urgent_care', label: 'Urgent Care' },
  { value: 'specialty_clinic', label: 'Specialty Clinic' },
  { value: 'dental_clinic', label: 'Dental Clinic' },
  { value: 'veterinary_clinic', label: 'Veterinary Clinic' },
];

const steps = ['Hospital Information', 'Address & Business', 'Administrator Account'];

export const HospitalRegistrationPage: React.FC = () => {
  const navigate = useNavigate();
  const [activeStep, setActiveStep] = useState(0);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [registrationSuccess, setRegistrationSuccess] = useState(false);
  
  // Store data from each step
  const [hospitalInfoData, setHospitalInfoData] = useState<HospitalInfoData | null>(null);
  const [addressBusinessData, setAddressBusinessData] = useState<AddressBusinessData | null>(null);
  const [administratorData, setAdministratorData] = useState<AdministratorData | null>(null);
  
  const [registerHospital, { isLoading, error }] = useRegisterHospitalMutation();
  
  // Separate forms for each step
  const hospitalInfoForm = useForm<HospitalInfoData>({
    resolver: yupResolver(hospitalInfoSchema) as any,
    mode: 'onChange',
    defaultValues: {
      hospital_name: '',
      hospital_type: '',
      hospital_email: '',
      hospital_phone: '',
      hospital_website: '',
    },
  });

  const addressBusinessForm = useForm<AddressBusinessData>({
    resolver: yupResolver(addressBusinessSchema) as any,
    mode: 'onChange',
    defaultValues: {
      address_line_1: '',
      address_line_2: '',
      city: '',
      state: '',
      postal_code: '',
      country: '',
      license_number: '',
      tax_id: '',
    },
  });

  const administratorForm = useForm<AdministratorData>({
    resolver: yupResolver(administratorSchema) as any,
    mode: 'onChange',
    defaultValues: {
      admin_first_name: '',
      admin_last_name: '',
      admin_email: '',
      admin_phone: '',
      admin_password: '',
      admin_confirm_password: '',
    },
  });

  // Keep forms clean - no auto-population to prevent data bleeding
  // Each step should start with a fresh form

  // Get current form based on active step
  const getCurrentForm = () => {
    switch (activeStep) {
      case 0:
        return hospitalInfoForm;
      case 1:
        return addressBusinessForm;
      case 2:
        return administratorForm;
      default:
        return hospitalInfoForm;
    }
  };

  // Watch for form changes to update button state
  const currentForm = getCurrentForm();
  const watchedValues = currentForm.watch();

  const handleNext = async () => {
    const currentForm = getCurrentForm();
    
    // Trigger validation for all fields
    const isStepValid = await currentForm.trigger();
    const stepCompleted = isStepCompleted(activeStep);
    
    console.log('Navigation attempt:', {
      activeStep,
      isStepValid,
      stepCompleted,
      formErrors: currentForm.formState.errors,
      formValues: currentForm.getValues()
    });
    
    if (isStepValid && stepCompleted) {
      // Save current step data before moving to next step
      const currentData = currentForm.getValues();
      
      switch (activeStep) {
        case 0:
          setHospitalInfoData(currentData as HospitalInfoData);
          break;
        case 1:
          setAddressBusinessData(currentData as AddressBusinessData);
          break;
        case 2:
          setAdministratorData(currentData as AdministratorData);
          break;
      }
      
      // Clear the next form to ensure it starts clean
      const nextStep = activeStep + 1;
      switch (nextStep) {
        case 1:
          addressBusinessForm.reset();
          break;
        case 2:
          administratorForm.reset();
          break;
      }
      
      setActiveStep((prevActiveStep) => prevActiveStep + 1);
    } else {
      console.log('Navigation blocked:', {
        reason: !isStepValid ? 'Form validation failed' : 'Step not completed',
        errors: currentForm.formState.errors
      });
      
      // Scroll to first error field for better UX
      const firstErrorField = document.querySelector('.Mui-error input, .Mui-error textarea, .Mui-error .MuiSelect-select');
      if (firstErrorField) {
        firstErrorField.scrollIntoView({ behavior: 'smooth', block: 'center' });
        // Focus the field for better accessibility
        (firstErrorField as HTMLElement).focus();
      }
    }
  };

  const handleBack = () => {
    // Save current step data before going back
    const currentForm = getCurrentForm();
    const currentData = currentForm.getValues();
    
    switch (activeStep) {
      case 0:
        setHospitalInfoData(currentData as HospitalInfoData);
        break;
      case 1:
        setAddressBusinessData(currentData as AddressBusinessData);
        break;
      case 2:
        setAdministratorData(currentData as AdministratorData);
        break;
    }
    
    // Clear the previous form to ensure it starts clean
    const prevStep = activeStep - 1;
    switch (prevStep) {
      case 0:
        hospitalInfoForm.reset();
        break;
      case 1:
        addressBusinessForm.reset();
        break;
    }
    
    setActiveStep((prevActiveStep) => prevActiveStep - 1);
  };

  const getStepTitle = (step: number): string => {
    switch (step) {
      case 0:
        return 'Hospital Information';
      case 1:
        return 'Address & Business Information';
      case 2:
        return 'Administrator Account';
      default:
        return '';
    }
  };

  const getStepDescription = (step: number): string => {
    switch (step) {
      case 0:
        return 'Enter your hospital or clinic details';
      case 1:
        return 'Provide location and business information';
      case 2:
        return 'Create the administrator account for your hospital';
      default:
        return '';
    }
  };

  const isStepCompleted = (step: number): boolean => {
    switch (step) {
      case 0:
        // For the current step, check form data; for completed steps, check saved data
        if (step === activeStep) {
          const formData = hospitalInfoForm.getValues();
          const formState = hospitalInfoForm.formState;
          
          // Check if all required fields have values and no validation errors
          const hasRequiredFields = !!(formData.hospital_name?.trim() && 
                                      formData.hospital_type?.trim() && 
                                      formData.hospital_email?.trim() && 
                                      formData.hospital_phone?.trim());
          
          const hasNoErrors = !formState.errors.hospital_name && 
                             !formState.errors.hospital_type && 
                             !formState.errors.hospital_email && 
                             !formState.errors.hospital_phone;
          
          // Debug logging
          console.log('Step 0 validation:', {
            formData,
            hasRequiredFields,
            hasNoErrors,
            errors: formState.errors
          });
          
          return hasRequiredFields && hasNoErrors;
        } else {
          if (!hospitalInfoData) return false;
          return !!(hospitalInfoData.hospital_name && hospitalInfoData.hospital_type && 
                   hospitalInfoData.hospital_email && hospitalInfoData.hospital_phone);
        }
      case 1:
        // For the current step, check form data; for completed steps, check saved data
        if (step === activeStep) {
          const formData = addressBusinessForm.getValues();
          const formState = addressBusinessForm.formState;
          
          const hasRequiredFields = !!(formData.address_line_1?.trim() && 
                                      formData.city?.trim() && 
                                      formData.state?.trim() && 
                                      formData.postal_code?.trim() && 
                                      formData.country?.trim());
          
          const hasNoErrors = !formState.errors.address_line_1 && 
                             !formState.errors.city && 
                             !formState.errors.state && 
                             !formState.errors.postal_code && 
                             !formState.errors.country;
          
          return hasRequiredFields && hasNoErrors;
        } else {
          if (!addressBusinessData) return false;
          return !!(addressBusinessData.address_line_1 && addressBusinessData.city && 
                   addressBusinessData.state && addressBusinessData.postal_code && 
                   addressBusinessData.country);
        }
      case 2:
        // For the current step, check form data; for completed steps, check saved data
        if (step === activeStep) {
          const formData = administratorForm.getValues();
          const formState = administratorForm.formState;
          
          const hasRequiredFields = !!(formData.admin_first_name?.trim() && 
                                      formData.admin_last_name?.trim() && 
                                      formData.admin_email?.trim() && 
                                      formData.admin_password?.trim() && 
                                      formData.admin_confirm_password?.trim());
          
          const hasNoErrors = !formState.errors.admin_first_name && 
                             !formState.errors.admin_last_name && 
                             !formState.errors.admin_email && 
                             !formState.errors.admin_password && 
                             !formState.errors.admin_confirm_password;
          
          return hasRequiredFields && hasNoErrors;
        } else {
          if (!administratorData) return false;
          return !!(administratorData.admin_first_name && administratorData.admin_last_name && 
                   administratorData.admin_email && administratorData.admin_password && 
                   administratorData.admin_confirm_password);
        }
      default:
        return false;
    }
  };

  const handleCompleteRegistration = async () => {
    // Save current step data first
    const currentForm = getCurrentForm();
    const currentData = currentForm.getValues();
    setAdministratorData(currentData as AdministratorData);
    
    // Validate current step
    const isStepValid = await currentForm.trigger();
    if (!isStepValid) {
      return;
    }

    // Combine all data for submission
    if (!hospitalInfoData || !addressBusinessData) {
      console.error('Missing data from previous steps');
      return;
    }

    try {
      const { admin_confirm_password, ...adminDataWithoutConfirm } = currentData as AdministratorData;
      const completeData: CompleteRegistrationData = {
        ...hospitalInfoData,
        ...addressBusinessData,
        ...adminDataWithoutConfirm,
      };

      const finalData = {
        ...completeData,
        timezone: 'Africa/Nairobi' // Default timezone for Kenya/East Africa
      };
      
      await registerHospital(finalData).unwrap();
      
      setRegistrationSuccess(true);
      
      // Redirect to login page after 3 seconds
      setTimeout(() => {
        navigate('/login', { 
          state: { 
            message: 'Hospital registered successfully! Please log in with your administrator credentials.',
            email: completeData.admin_email 
          } 
        });
      }, 3000);
      
    } catch (err) {
      console.error('Registration failed:', err);
    }
  };

  const renderStepContent = (step: number) => {
    const stepContent = () => {
      switch (step) {
        case 0:
          return renderHospitalInformation();
        case 1:
          return renderAddressAndBusiness();
        case 2:
          return renderAdministratorAccount();
        default:
          return null;
      }
    };

    return (
      <Card 
        elevation={2} 
        sx={{ 
          mb: 3,
          border: isStepCompleted(step) ? '2px solid' : '1px solid',
          borderColor: isStepCompleted(step) ? 'success.main' : 'divider',
          transition: 'all 0.3s ease-in-out'
        }}
      >
        <CardContent sx={{ p: 4 }}>
          <Box sx={{ mb: 3 }}>
            <Typography variant="h5" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              {getStepTitle(step)}
              {isStepCompleted(step) && (
                <CheckCircleIcon color="success" sx={{ ml: 1 }} />
              )}
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              {getStepDescription(step)}
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
              <Typography variant="caption" color="text.secondary">
                Step {step + 1} of {steps.length}
              </Typography>
              <Box 
                sx={{ 
                  flex: 1, 
                  height: 4, 
                  bgcolor: 'grey.200', 
                  borderRadius: 2,
                  overflow: 'hidden'
                }}
              >
                <Box 
                  sx={{ 
                    height: '100%', 
                    bgcolor: isStepCompleted(step) ? 'success.main' : 'primary.main',
                    width: `${((step + 1) / steps.length) * 100}%`,
                    transition: 'all 0.3s ease-in-out'
                  }} 
                />
              </Box>
            </Box>
          </Box>
          {stepContent()}
        </CardContent>
      </Card>
    );
  };

  const renderHospitalInformation = () => (
    <form name="hospital-info-form" autoComplete="off" key={`hospital-form-${activeStep}`}>
      <Grid container spacing={3} data-form-section="hospital-info">
      
      <Grid size={12}>
        <Controller
          name="hospital_name"
          control={hospitalInfoForm.control}
          render={({ field }) => (
            <TextField
              {...field}
              fullWidth
              label="Hospital/Clinic Name"
              error={!!hospitalInfoForm.formState.errors.hospital_name}
              helperText={hospitalInfoForm.formState.errors.hospital_name?.message}
              autoComplete="organization"
              id="hospital_name_field"
              data-form="hospital-info"
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <BusinessIcon color="action" />
                  </InputAdornment>
                ),
              }}
            />
          )}
        />
      </Grid>
      
      <Grid size={{ xs: 12, sm: 6 }}>
        <Controller
          name="hospital_type"
          control={hospitalInfoForm.control}
          render={({ field }) => (
            <TextField
              {...field}
              select
              fullWidth
              label="Hospital Type"
              error={!!hospitalInfoForm.formState.errors.hospital_type}
              helperText={hospitalInfoForm.formState.errors.hospital_type?.message}
              autoComplete="off"
              id="hospital_type_field"
              data-form="hospital-info"
            >
              {hospitalTypes.map((option) => (
                <MenuItem key={option.value} value={option.value}>
                  {option.label}
                </MenuItem>
              ))}
            </TextField>
          )}
        />
      </Grid>
      
      <Grid size={{ xs: 12, sm: 6 }}>
        <Controller
          name="hospital_email"
          control={hospitalInfoForm.control}
          render={({ field }) => (
            <TextField
              {...field}
              fullWidth
              label="Hospital Email"
              type="email"
              error={!!hospitalInfoForm.formState.errors.hospital_email}
              helperText={hospitalInfoForm.formState.errors.hospital_email?.message}
              autoComplete="organization-email"
              id="hospital_email_field"
              data-form="hospital-info"
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
      </Grid>
      
      <Grid size={{ xs: 12, sm: 6 }}>
        <Controller
          name="hospital_phone"
          control={hospitalInfoForm.control}
          render={({ field }) => (
            <TextField
              {...field}
              fullWidth
              label="Hospital Phone"
              error={!!hospitalInfoForm.formState.errors.hospital_phone}
              helperText={hospitalInfoForm.formState.errors.hospital_phone?.message}
              autoComplete="organization-tel"
              id="hospital_phone_field"
              data-form="hospital-info"
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <PhoneIcon color="action" />
                  </InputAdornment>
                ),
              }}
            />
          )}
        />
      </Grid>
      
      <Grid size={{ xs: 12, sm: 6 }}>
        <Controller
          name="hospital_website"
          control={hospitalInfoForm.control}
          render={({ field }) => (
            <TextField
              {...field}
              fullWidth
              label="Website (Optional)"
              error={!!hospitalInfoForm.formState.errors.hospital_website}
              helperText={hospitalInfoForm.formState.errors.hospital_website?.message}
              placeholder="https://www.example.com"
              autoComplete="url"
              id="hospital_website_field"
              data-form="hospital-info"
            />
          )}
        />
      </Grid>
      </Grid>
    </form>
  );

  const renderAddressAndBusiness = () => (
    <form name="address-business-form" autoComplete="off" key={`address-form-${activeStep}`}>
      <Grid container spacing={3} data-form-section="address-business">
      
      <Grid size={12}>
        <Controller
          name="address_line_1"
          control={addressBusinessForm.control}
          render={({ field }) => (
            <TextField
              {...field}
              fullWidth
              label="Address Line 1"
              error={!!addressBusinessForm.formState.errors.address_line_1}
              helperText={addressBusinessForm.formState.errors.address_line_1?.message}
              autoComplete="address-line1"
              id="hospital_address_line_1_field"
              placeholder="Enter hospital/clinic address"
              data-form="address-business"
            />
          )}
        />
      </Grid>
      
      <Grid size={12}>
        <Controller
          name="address_line_2"
          control={addressBusinessForm.control}
          render={({ field }) => (
            <TextField
              {...field}
              fullWidth
              label="Address Line 2 (Optional)"
              error={!!addressBusinessForm.formState.errors.address_line_2}
              helperText={addressBusinessForm.formState.errors.address_line_2?.message}
              autoComplete="address-line2"
              id="hospital_address_line_2_field"
              placeholder="Suite, building, floor (optional)"
              data-form="address-business"
            />
          )}
        />
      </Grid>
      
      <Grid size={{ xs: 12, sm: 6 }}>
        <Controller
          name="city"
          control={addressBusinessForm.control}
          render={({ field }) => (
            <TextField
              {...field}
              fullWidth
              label="City"
              error={!!addressBusinessForm.formState.errors.city}
              helperText={addressBusinessForm.formState.errors.city?.message}
              autoComplete="address-level2"
              id="hospital_city_field"
              placeholder="Enter city"
              data-form="address-business"
            />
          )}
        />
      </Grid>
      
      <Grid size={{ xs: 12, sm: 3 }}>
        <Controller
          name="state"
          control={addressBusinessForm.control}
          render={({ field }) => (
            <TextField
              {...field}
              fullWidth
              label="State"
              error={!!addressBusinessForm.formState.errors.state}
              helperText={addressBusinessForm.formState.errors.state?.message}
              autoComplete="address-level1"
              id="hospital_state_field"
              placeholder="Enter state"
              data-form="address-business"
            />
          )}
        />
      </Grid>
      
      <Grid size={{ xs: 12, sm: 3 }}>
        <Controller
          name="postal_code"
          control={addressBusinessForm.control}
          render={({ field }) => (
            <TextField
              {...field}
              fullWidth
              label="Postal Code"
              error={!!addressBusinessForm.formState.errors.postal_code}
              helperText={addressBusinessForm.formState.errors.postal_code?.message}
              autoComplete="postal-code"
              id="hospital_postal_code_field"
              placeholder="Enter postal code"
              data-form="address-business"
            />
          )}
        />
      </Grid>
      
      <Grid size={{ xs: 12, sm: 6 }}>
        <Controller
          name="country"
          control={addressBusinessForm.control}
          render={({ field }) => (
            <TextField
              {...field}
              fullWidth
              label="Country"
              error={!!addressBusinessForm.formState.errors.country}
              helperText={addressBusinessForm.formState.errors.country?.message}
              autoComplete="country-name"
              id="hospital_country_field"
              placeholder="Enter country"
              data-form="address-business"
            />
          )}
        />
      </Grid>
      
      <Grid size={{ xs: 12, sm: 6 }}>
        <Controller
          name="license_number"
          control={addressBusinessForm.control}
          render={({ field }) => (
            <TextField
              {...field}
              fullWidth
              label="License Number (Optional)"
              error={!!addressBusinessForm.formState.errors.license_number}
              helperText={addressBusinessForm.formState.errors.license_number?.message}
              autoComplete="off"
              id="hospital_license_number_field"
              data-form="address-business"
            />
          )}
        />
      </Grid>
      
      <Grid size={{ xs: 12, sm: 6 }}>
        <Controller
          name="tax_id"
          control={addressBusinessForm.control}
          render={({ field }) => (
            <TextField
              {...field}
              fullWidth
              label="Tax ID (Optional)"
              error={!!addressBusinessForm.formState.errors.tax_id}
              helperText={addressBusinessForm.formState.errors.tax_id?.message}
              autoComplete="off"
              id="hospital_tax_id_field"
              data-form="address-business"
            />
          )}
        />
      </Grid>
      </Grid>
    </form>
  );

  const renderAdministratorAccount = () => (
    <form name="admin-account-form" autoComplete="off" key={`admin-form-${activeStep}`}>
      <Grid container spacing={3} data-form-section="admin-account">
      
      <Grid size={{ xs: 12, sm: 6 }}>
        <Controller
          name="admin_first_name"
          control={administratorForm.control}
          render={({ field }) => (
            <TextField
              {...field}
              fullWidth
              label="First Name"
              error={!!administratorForm.formState.errors.admin_first_name}
              helperText={administratorForm.formState.errors.admin_first_name?.message}
              autoComplete="given-name"
              id="admin_first_name_field"
              data-form="admin-account"
            />
          )}
        />
      </Grid>
      
      <Grid size={{ xs: 12, sm: 6 }}>
        <Controller
          name="admin_last_name"
          control={administratorForm.control}
          render={({ field }) => (
            <TextField
              {...field}
              fullWidth
              label="Last Name"
              error={!!administratorForm.formState.errors.admin_last_name}
              helperText={administratorForm.formState.errors.admin_last_name?.message}
              autoComplete="family-name"
              id="admin_last_name_field"
              data-form="admin-account"
            />
          )}
        />
      </Grid>
      
      <Grid size={{ xs: 12, sm: 6 }}>
        <Controller
          name="admin_email"
          control={administratorForm.control}
          render={({ field }) => (
            <TextField
              {...field}
              fullWidth
              label="Email Address"
              type="email"
              error={!!administratorForm.formState.errors.admin_email}
              helperText={administratorForm.formState.errors.admin_email?.message}
              autoComplete="email"
              id="admin_email_field"
              data-form="admin-account"
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
      </Grid>
      
      <Grid size={{ xs: 12, sm: 6 }}>
        <Controller
          name="admin_phone"
          control={administratorForm.control}
          render={({ field }) => (
            <TextField
              {...field}
              fullWidth
              label="Phone Number (Optional)"
              error={!!administratorForm.formState.errors.admin_phone}
              helperText={administratorForm.formState.errors.admin_phone?.message}
              autoComplete="tel"
              id="admin_phone_field"
              data-form="admin-account"
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <PhoneIcon color="action" />
                  </InputAdornment>
                ),
              }}
            />
          )}
        />
      </Grid>
      

      
      <Grid size={{ xs: 12, sm: 6 }}>
        <Controller
          name="admin_password"
          control={administratorForm.control}
          render={({ field }) => (
            <TextField
              {...field}
              fullWidth
              label="Password"
              type={showPassword ? 'text' : 'password'}
              error={!!administratorForm.formState.errors.admin_password}
              helperText={administratorForm.formState.errors.admin_password?.message}
              autoComplete="new-password"
              id="admin_password_field"
              data-form="admin-account"
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <LockIcon color="action" />
                  </InputAdornment>
                ),
                endAdornment: (
                  <InputAdornment position="end">
                    <IconButton
                      onClick={() => setShowPassword(!showPassword)}
                      edge="end"
                    >
                      {showPassword ? <VisibilityOff /> : <Visibility />}
                    </IconButton>
                  </InputAdornment>
                ),
              }}
            />
          )}
        />
      </Grid>
      
      <Grid size={{ xs: 12, sm: 6 }}>
        <Controller
          name="admin_confirm_password"
          control={administratorForm.control}
          render={({ field }) => (
            <TextField
              {...field}
              fullWidth
              label="Confirm Password"
              type={showConfirmPassword ? 'text' : 'password'}
              error={!!administratorForm.formState.errors.admin_confirm_password}
              helperText={administratorForm.formState.errors.admin_confirm_password?.message}
              autoComplete="new-password"
              id="admin_confirm_password_field"
              data-form="admin-account"
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <LockIcon color="action" />
                  </InputAdornment>
                ),
                endAdornment: (
                  <InputAdornment position="end">
                    <IconButton
                      onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                      edge="end"
                    >
                      {showConfirmPassword ? <VisibilityOff /> : <Visibility />}
                    </IconButton>
                  </InputAdornment>
                ),
              }}
            />
          )}
        />
      </Grid>
      </Grid>
    </form>
  );

  if (registrationSuccess) {
    return (
      <Container component="main" maxWidth="sm">
        <Box
          sx={{
            minHeight: '100vh',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'center',
            alignItems: 'center',
            py: 4,
          }}
        >
          <Card sx={{ width: '100%', textAlign: 'center', p: 4 }}>
            <CardContent>
              <CheckCircleIcon 
                sx={{ 
                  fontSize: 80, 
                  color: medicalColors.success.main, 
                  mb: 2 
                }} 
              />
              <Typography variant="h4" gutterBottom color="primary">
                Registration Successful!
              </Typography>
              <Typography variant="body1" color="text.secondary" paragraph>
                Your hospital has been registered successfully. You will be redirected to the login page shortly.
              </Typography>
              <CircularProgress sx={{ mt: 2 }} />
            </CardContent>
          </Card>
        </Box>
      </Container>
    );
  }

  return (
    <Container component="main" maxWidth="md">
      <Box
        sx={{
          minHeight: '100vh',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          py: 4,
        }}
      >
        <Paper
          elevation={8}
          sx={{
            p: 4,
            borderRadius: 3,
            background: 'linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%)',
            border: `1px solid ${medicalColors.primary[100]}`,
          }}
        >
          {/* Header */}
          <Box sx={{ mb: 4, textAlign: 'center' }}>
            <HospitalIcon 
              sx={{ 
                fontSize: 48, 
                color: medicalColors.primary.main, 
                mb: 2 
              }} 
            />
            <Typography variant="h4" gutterBottom color="primary">
              Hospital Registration
            </Typography>
            <Typography variant="body1" color="text.secondary">
              Join MediRemind to streamline your healthcare operations
            </Typography>
          </Box>

          {/* Enhanced Stepper */}
          <Stepper 
            activeStep={activeStep} 
            sx={{ 
              mb: 4,
              '& .MuiStepLabel-root': {
                cursor: 'default'
              }
            }}
          >
            {steps.map((label, index) => {
              const isCompleted = isStepCompleted(index);
              const isActive = index === activeStep;
              const canAccess = index === 0 || isStepCompleted(index - 1);
              
              return (
                <Step 
                  key={label} 
                  completed={isCompleted}
                  disabled={!canAccess}
                >
                  <StepLabel 
                    optional={
                      <Box>
                        <Typography variant="caption" color="text.secondary">
                          {getStepDescription(index)}
                        </Typography>
                        <Box sx={{ mt: 0.5, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                          {isCompleted && (
                            <Chip 
                              icon={<CheckCircleIcon />} 
                              label="Complete" 
                              size="small" 
                              color="success" 
                              variant="outlined"
                            />
                          )}
                          {isActive && !isCompleted && (
                            <Chip 
                              label="In Progress" 
                              size="small" 
                              color="primary" 
                              variant="outlined"
                            />
                          )}
                          {!canAccess && (
                            <Chip 
                              label="Locked" 
                              size="small" 
                              color="default" 
                              variant="outlined"
                            />
                          )}
                        </Box>
                      </Box>
                    }
                    sx={{
                      opacity: canAccess ? 1 : 0.5,
                      '& .MuiStepLabel-label': {
                        fontWeight: isActive ? 'bold' : 'normal'
                      }
                    }}
                  >
                    {getStepTitle(index)}
                  </StepLabel>
                </Step>
              );
            })}
          </Stepper>

          {/* Error Alert */}
          {error && (
            <Alert severity="error" sx={{ mb: 3 }}>
              {(error as any)?.data?.message || 'Registration failed. Please try again.'}
            </Alert>
          )}

          {/* Form Content */}
          <Box>
            {renderStepContent(activeStep)}

            {/* Enhanced Navigation Buttons */}
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mt: 4 }}>
              <Button
                onClick={activeStep === 0 ? () => navigate('/login') : handleBack}
                startIcon={<ArrowBackIcon />}
                variant="outlined"
                disabled={isLoading}
              >
                {activeStep === 0 ? 'Back to Login' : 'Back'}
              </Button>

              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                {/* Step completion indicator */}
                {activeStep < steps.length - 1 && (
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    {isStepCompleted(activeStep) ? (
                      <Chip 
                        icon={<CheckCircleIcon />} 
                        label="Step Complete" 
                        size="small" 
                        color="success" 
                        variant="outlined"
                      />
                    ) : (
                      <Chip 
                        label="Complete this step to continue" 
                        size="small" 
                        color="warning" 
                        variant="outlined"
                      />
                    )}
                  </Box>
                )}

                {activeStep === steps.length - 1 ? (
                  <Button
                    onClick={handleCompleteRegistration}
                    variant="contained"
                    disabled={isLoading || !isStepCompleted(activeStep)}
                    startIcon={isLoading ? <CircularProgress size={20} /> : <HospitalIcon />}
                    sx={{
                      background: `linear-gradient(45deg, ${medicalColors.primary.main} 30%, ${medicalColors.primary.light} 90%)`,
                      '&:hover': {
                        background: `linear-gradient(45deg, ${medicalColors.primary.dark} 30%, ${medicalColors.primary.main} 90%)`,
                      },
                    }}
                  >
                    {isLoading ? 'Registering...' : 'Complete Registration'}
                  </Button>
                ) : (
                  <Button
                    onClick={handleNext}
                    variant="contained"
                    disabled={!isStepCompleted(activeStep) || isLoading}
                    endIcon={<ArrowForwardIcon />}
                    sx={{
                      bgcolor: isStepCompleted(activeStep) ? 'primary.main' : 'grey.400',
                      '&:hover': {
                        bgcolor: isStepCompleted(activeStep) ? 'primary.dark' : 'grey.400',
                      }
                    }}
                  >
                    {isStepCompleted(activeStep) ? 'Continue' : 'Complete Step First'}
                  </Button>
                )}
              </Box>
            </Box>
          </Box>

          {/* Footer */}
          <Divider sx={{ my: 3 }} />
          <Typography variant="body2" color="text.secondary" align="center">
            Already have an account?{' '}
            <Button
              variant="text"
              onClick={() => navigate('/login')}
              sx={{ textTransform: 'none' }}
            >
              Sign in here
            </Button>
          </Typography>
        </Paper>
      </Box>
    </Container>
  );
};