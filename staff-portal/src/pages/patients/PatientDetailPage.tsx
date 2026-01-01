import React from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Avatar,
  Button,
  Chip,
  Divider,
  IconButton,
  CircularProgress,
  Alert,
  Grid
} from '@mui/material';
import {
  Phone,
  Email,
  LocationOn,
  CalendarToday,
  Edit,
  ArrowBack,
  LocalHospital,
  AccountBalance,
  Badge
} from '@mui/icons-material';
import { useParams, useNavigate } from 'react-router-dom';
import { useGetPatientQuery } from '../../store/api/apiSlice';

import { decryptField, isEncrypted } from '../../utils/decryptionService';

export const PatientDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data: patientResponse, isLoading, error } = useGetPatientQuery(id!);
  
  // Extract patient data from the response structure
  const patient = patientResponse?.patient || patientResponse;

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (error || !patient) {
    return (
      <Box p={3}>
        <Alert severity="error">
          Failed to load patient details. Please try again.
        </Alert>
      </Box>
    );
  }

  const formatDate = (dateString: string) => {
    if (!dateString) return 'Not provided';
    try {
      return new Date(dateString).toLocaleDateString();
    } catch {
      return 'Invalid date';
    }
  };

  const formatPhone = (phone: string) => {
    if (!phone) return 'Not provided';
    
    // Try to decrypt if it appears to be encrypted
    const decryptedPhone = isEncrypted(phone) ? decryptField(phone) : phone;
    
    // Use Kenyan phone formatting
    const cleaned = decryptedPhone.replace(/\D/g, '');
    
    // Handle Kenyan phone numbers
    if (cleaned.length === 12 && cleaned.startsWith('254') && cleaned[3] === '7') {
      // 254712345678 -> +254 712 345 678
      return `+254 ${cleaned.slice(3, 6)} ${cleaned.slice(6, 9)} ${cleaned.slice(9)}`;
    } else if (cleaned.length === 10 && cleaned.startsWith('07')) {
      // 0712345678 -> +254 712 345 678
      return `+254 ${cleaned.slice(1, 4)} ${cleaned.slice(4, 7)} ${cleaned.slice(7)}`;
    } else if (cleaned.length === 9 && cleaned.startsWith('7')) {
      // 712345678 -> +254 712 345 678
      return `+254 ${cleaned.slice(0, 3)} ${cleaned.slice(3, 6)} ${cleaned.slice(6)}`;
    } else if (cleaned.length === 11 && cleaned.startsWith('126')) {
      // Handle US format like "12608815999" -> +254 088 159 99
      return `+254 ${cleaned.slice(3, 6)} ${cleaned.slice(6, 9)} ${cleaned.slice(9)}`;
    }
    
    // Fallback to original format if not recognized
    return decryptedPhone;
  };

  const formatEncryptedField = (field: string, fallback: string = 'Not provided') => {
    if (!field) return fallback;
    
    // Try to decrypt if it appears to be encrypted
    return isEncrypted(field) ? decryptField(field) : field;
  };

  const getInitials = (name: string) => {
    if (!name) return 'P';
    return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);
  };

  const getStatusColor = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'active': return 'success';
      case 'inactive': return 'error';
      case 'pending': return 'warning';
      default: return 'default';
    }
  };

  return (
    <Box p={3}>
      {/* Header */}
      <Box display="flex" alignItems="center" mb={3}>
        <IconButton onClick={() => navigate('/app/patients')} sx={{ mr: 2 }}>
          <ArrowBack />
        </IconButton>
        <Typography variant="h4" component="h1">
          Patient Details
        </Typography>
      </Box>

      <Grid container spacing={3}>
        {/* Patient Information */}
        <Grid size={{ xs: 12, md: 8 }}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" mb={3}>
                <Avatar
                  sx={{ 
                    width: 80, 
                    height: 80, 
                    mr: 3,
                    bgcolor: 'primary.main',
                    fontSize: '1.5rem'
                  }}
                >
                  {getInitials(patient.fullName || '')}
                </Avatar>
                <Box flex={1}>
                  <Typography variant="h4" component="h1" sx={{ fontWeight: 600 }}>
                    {patient?.fullName || 'Unknown Patient'}
                  </Typography>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    Patient ID: {patient.id}
                  </Typography>
                  <Chip 
                    label={patient.status || 'Unknown'} 
                    color={getStatusColor(patient.status)}
                    size="small"
                  />
                </Box>
                <Button
                  variant="outlined"
                  startIcon={<Edit />}
                  onClick={() => navigate(`/app/patients/${id}/edit`)}
                >
                  Edit
                </Button>
              </Box>

              <Divider sx={{ mb: 3 }} />

              <Grid container spacing={3}>
                <Grid size={{ xs: 12, sm: 6 }}>
                  <Box display="flex" alignItems="center" mb={2}>
                    <Phone sx={{ mr: 2, color: 'text.secondary' }} />
                    <Box>
                      <Typography variant="subtitle2" color="text.secondary">
                        Phone
                      </Typography>
                      <Typography variant="body1">
                        {formatPhone(patient?.phone)}
                      </Typography>
                    </Box>
                  </Box>
                </Grid>

                <Grid size={{ xs: 12, sm: 6 }}>
                  <Box display="flex" alignItems="center" mb={2}>
                    <Email sx={{ mr: 2, color: 'text.secondary' }} />
                    <Box>
                      <Typography variant="subtitle2" color="text.secondary">
                        Email
                      </Typography>
                      <Typography variant="body1">
                        {patient?.email || 'Not provided'}
                      </Typography>
                    </Box>
                  </Box>
                </Grid>

                <Grid size={{ xs: 12, sm: 6 }}>
                  <Box display="flex" alignItems="center" mb={2}>
                    <LocationOn sx={{ mr: 2, color: 'text.secondary' }} />
                    <Box>
                      <Typography variant="subtitle2" color="text.secondary">
                        Address
                      </Typography>
                      <Typography variant="body1">
                        {patient?.address ? (
                          <>
                            {formatEncryptedField(patient.address.street)}<br />
                            {formatEncryptedField(patient.address.city)}, {formatEncryptedField(patient.address.state)} {formatEncryptedField(patient.address.zipCode)}
                            {patient.address.country && (
                              <>
                                <br />{formatEncryptedField(patient.address.country)}
                              </>
                            )}
                          </>
                        ) : (
                          'Not provided'
                        )}
                      </Typography>
                    </Box>
                  </Box>
                </Grid>

                <Grid size={{ xs: 12, sm: 6 }}>
                  <Box display="flex" alignItems="center" mb={2}>
                    <CalendarToday sx={{ mr: 2, color: 'text.secondary' }} />
                    <Box>
                      <Typography variant="subtitle2" color="text.secondary">
                        Date of Birth
                      </Typography>
                      <Typography variant="body1">
                        {formatDate(patient.dateOfBirth)}
                      </Typography>
                    </Box>
                  </Box>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* Medical Information */}
        <Grid size={{ xs: 12, md: 4 }}>
          <Grid container spacing={2}>
            <Grid size={{ xs: 12 }}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Medical Information
                  </Typography>
                  <Box display="flex" alignItems="center" mb={2}>
                    <LocalHospital sx={{ mr: 2, color: 'text.secondary' }} />
                    <Box>
                      <Typography variant="subtitle2" color="text.secondary">
                        Blood Type
                      </Typography>
                      <Typography variant="body1">
                      {patient?.medicalInfo?.bloodType || 'Not specified'}
                    </Typography>
                    </Box>
                  </Box>
                </CardContent>
              </Card>
            </Grid>

            <Grid size={{ xs: 12 }}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Allergies
                  </Typography>
                  <Typography variant="body1">
                    {formatEncryptedField(patient?.medicalInfo?.allergies, 'No known allergies')}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>

            <Grid size={{ xs: 12 }}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Insurance Information
                  </Typography>
                  <Box display="flex" alignItems="center" mb={2}>
                    <AccountBalance sx={{ mr: 2, color: 'text.secondary' }} />
                    <Box>
                      <Typography variant="subtitle2" color="text.secondary">
                        Provider
                      </Typography>
                      <Typography variant="body1">
                        {formatEncryptedField(patient?.insurance?.provider, 'Not provided')}
                      </Typography>
                    </Box>
                  </Box>
                  <Box display="flex" alignItems="center">
                    <Badge sx={{ mr: 2, color: 'text.secondary' }} />
                    <Box>
                      <Typography variant="subtitle2" color="text.secondary">
                        Policy Number
                      </Typography>
                      <Typography variant="body1">
                        {formatEncryptedField(patient?.insurance?.policyNumber, 'Not provided')}
                      </Typography>
                    </Box>
                  </Box>
                </CardContent>
              </Card>
            </Grid>

            <Grid size={{ xs: 12 }}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Recent Appointments
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    No recent appointments
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </Grid>
      </Grid>
    </Box>
  );
};

export default PatientDetailPage;