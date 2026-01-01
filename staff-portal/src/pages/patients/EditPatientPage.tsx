import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
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
  InputAdornment,

} from '@mui/material';
import {
  ArrowBack as ArrowBackIcon,
  Save as SaveIcon,
  Person as PersonIcon,
  Phone as PhoneIcon,

  LocalHospital as LocalHospitalIcon,
  Business as BusinessIcon,
} from '@mui/icons-material';
import { setBreadcrumbs, setCurrentPage } from '../../store/slices/uiSlice';
import type { RootState } from '../../store';
import { useGetPatientQuery, useUpdatePatientMutation } from '../../store/api/apiSlice';

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
    country: 'Kenya',
  },
  emergencyContacts: [
    { name: '', relationship: '', phone: '', email: '', priority: 1 },
    { name: '', relationship: '', phone: '', email: '', priority: 2 },
    { name: '', relationship: '', phone: '', email: '', priority: 3 },
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
};

export const EditPatientPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const { isAuthenticated } = useSelector((state: RootState) => state.auth);
  
  const [formData, setFormData] = useState<PatientFormData>(initialFormData);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  // Fetch patient data
  const { data: patientData, isLoading: isPatientLoading, error: patientError } = useGetPatientQuery(id!, {
    skip: !id,
  });

  // Update patient mutation
  const [updatePatient] = useUpdatePatientMutation();

  useEffect(() => {
    dispatch(setCurrentPage('patients'));
    dispatch(setBreadcrumbs([
      { label: 'Patients', path: '/app/patients' },
      { label: 'Edit Patient', path: `/app/patients/${id}/edit` }
    ]));
  }, [dispatch, id]);

  // Populate form with patient data
  useEffect(() => {
    if (patientData) {
      const patient = patientData.patient || patientData;
      setFormData({
        firstName: patient.first_name || '',
        lastName: patient.last_name || '',
        email: patient.email || '',
        phone: patient.phone || '',
        dateOfBirth: patient.date_of_birth || '',
        gender: patient.gender ? patient.gender.toLowerCase() : '',
        address: {
          street: patient.address?.street || '',
          city: patient.address?.city || '',
          state: patient.address?.state || '',
          zipCode: patient.address?.zip_code || '',
          country: patient.address?.country || 'Kenya',
        },
        emergencyContacts: patient.emergency_contacts && patient.emergency_contacts.length > 0 
          ? patient.emergency_contacts.map((contact: any) => ({
              name: contact.name || '',
              relationship: contact.relationship || '',
              phone: contact.phone || '',
              email: contact.email || '',
              priority: contact.priority || 1,
            }))
          : [
              { name: '', relationship: '', phone: '', email: '', priority: 1 },
              { name: '', relationship: '', phone: '', email: '', priority: 2 },
              { name: '', relationship: '', phone: '', email: '', priority: 3 },
            ],
        medicalInfo: {
          bloodType: patient.blood_type || '',
          allergies: patient.allergies || '',
          medications: patient.medications || '',
          medicalHistory: patient.medical_history || '',
        },
        insurance: {
          provider: patient.insurance?.provider || '',
          policyNumber: patient.insurance?.policy_number || '',
          groupNumber: patient.insurance?.group_number || '',
        },
      });
    }
  }, [patientData]);

  const handleInputChange = (field: string, value: string, contactIndex?: number) => {
    if (field.includes('.')) {
      const [parent, child] = field.split('.');
      
      // Handle emergency contacts array
      if (parent === 'emergencyContacts' && contactIndex !== undefined) {
        setFormData(prev => {
          const updatedContacts = [...prev.emergencyContacts];
          updatedContacts[contactIndex] = {
            ...updatedContacts[contactIndex],
            [child]: value,
          };
          return {
            ...prev,
            emergencyContacts: updatedContacts,
          };
        });
        return;
      }
      
      // Handle nested objects (address, medicalInfo, insurance)
      setFormData(prev => ({
        ...prev,
        [parent]: {
          ...(prev[parent as keyof PatientFormData] as Record<string, unknown>),
          [child]: value,
        },
      }));
    } else {
      setFormData(prev => ({
        ...prev,
        [field]: value,
      }));
    }
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

    // Primary emergency contact validation
    const primaryContact = formData.emergencyContacts[0];
    if (!primaryContact.name.trim()) {
      setError('Primary emergency contact name is required');
      return false;
    }
    if (!primaryContact.relationship.trim()) {
      setError('Primary emergency contact relationship is required');
      return false;
    }
    if (!primaryContact.phone.trim()) {
      setError('Primary emergency contact phone is required');
      return false;
    }

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
        first_name: formData.firstName,
        last_name: formData.lastName,
        email: formData.email,
        phone: formData.phone,
        date_of_birth: formData.dateOfBirth,
        gender: formData.gender,
        address: {
          street: formData.address.street,
          city: formData.address.city,
          state: formData.address.state,
          zip_code: formData.address.zipCode,
          country: formData.address.country,
        },
        emergency_contacts: formData.emergencyContacts.map(contact => ({
          name: contact.name,
          relationship: contact.relationship,
          phone: contact.phone,
          email: contact.email,
          priority: contact.priority,
        })).filter(contact => contact.name.trim() || contact.phone.trim()),
        blood_type: formData.medicalInfo.bloodType,
        allergies: formData.medicalInfo.allergies,
        medications: formData.medicalInfo.medications,
        medical_history: formData.medicalInfo.medicalHistory,
        insurance: {
          provider: formData.insurance.provider,
          policy_number: formData.insurance.policyNumber,
          group_number: formData.insurance.groupNumber,
        },
      };

      await updatePatient({ id: id!, updates: submissionData }).unwrap();

      setSuccess(true);
      
      setTimeout(() => {
        navigate(`/app/patients/${id}`);
      }, 2000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred while updating patient');
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = () => {
    navigate(`/app/patients/${id}`);
  };

  if (isPatientLoading) {
    return (
      <Box sx={{ p: 3, display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '60vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  if (patientError) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">
          Failed to load patient data. Please try again.
        </Alert>
        <Button onClick={() => navigate('/app/patients')} sx={{ mt: 2 }}>
          Back to Patients
        </Button>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
        <IconButton onClick={handleCancel} sx={{ mr: 2 }}>
          <ArrowBackIcon />
        </IconButton>
        <Typography variant="h4" component="h1">
          Edit Patient
        </Typography>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {success && (
        <Alert severity="success" sx={{ mb: 3 }}>
          Patient updated successfully! Redirecting...
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
                      InputProps={{
                        startAdornment: <InputAdornment position="start">+</InputAdornment>,
                      }}
                    />
                  </Grid>
                  <Grid size={{ xs: 12, sm: 6 }}>
                    <TextField
                      fullWidth
                      label="Date of Birth"
                      type="date"
                      value={formData.dateOfBirth}
                      onChange={(e) => handleInputChange('dateOfBirth', e.target.value)}
                      required
                      InputLabelProps={{
                        shrink: true,
                      }}
                    />
                  </Grid>
                  <Grid size={{ xs: 12, sm: 6 }}>
                    <FormControl fullWidth required>
                      <InputLabel>Gender</InputLabel>
                      <Select
                        value={formData.gender}
                        onChange={(e) => handleInputChange('gender', e.target.value)}
                        label="Gender"
                      >
                        <MenuItem value="">Select Gender</MenuItem>
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
                  <BusinessIcon sx={{ mr: 1, color: 'primary.main' }} />
                  <Typography variant="h6">Address Information</Typography>
                </Box>
                <Grid container spacing={2}>
                  <Grid size={{ xs: 12, sm: 6 }}>
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
                  <Grid size={{ xs: 12, sm: 6 }}>
                    <TextField
                      fullWidth
                      label="State/Province"
                      value={formData.address.state}
                      onChange={(e) => handleInputChange('address.state', e.target.value)}
                    />
                  </Grid>
                  <Grid size={{ xs: 12, sm: 6 }}>
                    <TextField
                      fullWidth
                      label="ZIP/Postal Code"
                      value={formData.address.zipCode}
                      onChange={(e) => handleInputChange('address.zipCode', e.target.value)}
                    />
                  </Grid>
                  <Grid size={{ xs: 12, sm: 6 }}>
                    <TextField
                      fullWidth
                      label="Country"
                      value={formData.address.country}
                      onChange={(e) => handleInputChange('address.country', e.target.value)}
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
                          onChange={(e) => handleInputChange('emergencyContacts.name', e.target.value, index)}
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
                          onChange={(e) => handleInputChange('emergencyContacts.relationship', e.target.value, index)}
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
                          onChange={(e) => handleInputChange('emergencyContacts.phone', e.target.value, index)}
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
                          onChange={(e) => handleInputChange('emergencyContacts.email', e.target.value, index)}
                          placeholder="Optional - for notifications"
                        />
                      </Grid>
                    </Grid>
                  </Box>
                ))}
              </CardContent>
            </Card>
          </Grid>

          {/* Medical Information */}
          <Grid size={12}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <LocalHospitalIcon sx={{ mr: 1, color: 'primary.main' }} />
                  <Typography variant="h6">Medical Information</Typography>
                </Box>
                <Grid container spacing={2}>
                  <Grid size={{ xs: 12, sm: 6 }}>
                    <TextField
                      fullWidth
                      label="Blood Type"
                      value={formData.medicalInfo.bloodType}
                      onChange={(e) => handleInputChange('medicalInfo.bloodType', e.target.value)}
                    />
                  </Grid>
                  <Grid size={{ xs: 12, sm: 6 }}>
                    <TextField
                      fullWidth
                      label="Allergies"
                      value={formData.medicalInfo.allergies}
                      onChange={(e) => handleInputChange('medicalInfo.allergies', e.target.value)}
                    />
                  </Grid>
                  <Grid size={{ xs: 12, sm: 6 }}>
                    <TextField
                      fullWidth
                      label="Current Medications"
                      value={formData.medicalInfo.medications}
                      onChange={(e) => handleInputChange('medicalInfo.medications', e.target.value)}
                    />
                  </Grid>
                  <Grid size={{ xs: 12, sm: 6 }}>
                    <TextField
                      fullWidth
                      label="Medical History"
                      value={formData.medicalInfo.medicalHistory}
                      onChange={(e) => handleInputChange('medicalInfo.medicalHistory', e.target.value)}
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
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <BusinessIcon sx={{ mr: 1, color: 'primary.main' }} />
                  <Typography variant="h6">Insurance Information</Typography>
                </Box>
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
                {loading ? 'Saving...' : 'Save Changes'}
              </Button>
            </Box>
          </Grid>
        </Grid>
      </form>
    </Box>
  );
};