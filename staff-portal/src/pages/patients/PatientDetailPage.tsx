import React from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  Chip,
  Avatar,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Button,
  IconButton,
} from '@mui/material';
import {
  Person,
  Phone,
  Email,
  LocationOn,
  CalendarToday,
  Edit,
  ArrowBack,
} from '@mui/icons-material';
import { useParams, useNavigate } from 'react-router-dom';
import { useGetPatientQuery } from '../../store/api/apiSlice';

export const PatientDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data: patient, isLoading, error } = useGetPatientQuery(id!);

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <Typography>Loading patient details...</Typography>
      </Box>
    );
  }

  if (error || !patient) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <Typography color="error">Patient not found</Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
        <IconButton onClick={() => navigate('/patients')} sx={{ mr: 2 }}>
          <ArrowBack />
        </IconButton>
        <Typography variant="h4" component="h1">
          Patient Details
        </Typography>
      </Box>

      <Grid container spacing={3}>
        {/* Patient Info Card */}
        <Grid size={{ xs: 12, md: 4 }}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Avatar
                  sx={{ width: 80, height: 80, mr: 2, bgcolor: 'primary.main' }}
                >
                  <Person sx={{ fontSize: 40 }} />
                </Avatar>
                <Box>
                  <Typography variant="h5">
                    {patient.firstName} {patient.lastName}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Patient ID: {patient.id}
                  </Typography>
                </Box>
              </Box>
              
              <Divider sx={{ my: 2 }} />
              
              <List dense>
                <ListItem>
                  <ListItemIcon>
                    <Phone />
                  </ListItemIcon>
                  <ListItemText
                    primary="Phone"
                    secondary={patient.phone || 'Not provided'}
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <Email />
                  </ListItemIcon>
                  <ListItemText
                    primary="Email"
                    secondary={patient.email || 'Not provided'}
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <LocationOn />
                  </ListItemIcon>
                  <ListItemText
                    primary="Address"
                    secondary={patient.address || 'Not provided'}
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <CalendarToday />
                  </ListItemIcon>
                  <ListItemText
                    primary="Date of Birth"
                    secondary={patient.dateOfBirth ? new Date(patient.dateOfBirth).toLocaleDateString() : 'Not provided'}
                  />
                </ListItem>
              </List>
              
              <Box sx={{ mt: 2 }}>
                <Button
                  variant="contained"
                  startIcon={<Edit />}
                  fullWidth
                  onClick={() => navigate(`/patients/${id}/edit`)}
                >
                  Edit Patient
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Medical Information */}
        <Grid size={{ xs: 12, md: 8 }}>
          <Grid container spacing={2}>
            {/* Medical History */}
            <Grid size={{ xs: 12 }}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Medical History
                  </Typography>
                  {patient.medicalHistory && patient.medicalHistory.length > 0 ? (
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                      {patient.medicalHistory.map((condition: string, index: number) => (
                        <Chip key={index} label={condition} variant="outlined" />
                      ))}
                    </Box>
                  ) : (
                    <Typography color="text.secondary">
                      No medical history recorded
                    </Typography>
                  )}
                </CardContent>
              </Card>
            </Grid>

            {/* Allergies */}
            <Grid size={{ xs: 12 }}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Allergies
                  </Typography>
                  {patient.allergies && patient.allergies.length > 0 ? (
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                      {patient.allergies.map((allergy: string, index: number) => (
                        <Chip key={index} label={allergy} color="warning" variant="outlined" />
                      ))}
                    </Box>
                  ) : (
                    <Typography color="text.secondary">
                      No known allergies
                    </Typography>
                  )}
                </CardContent>
              </Card>
            </Grid>

            {/* Recent Appointments */}
            <Grid size={{ xs: 12 }}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Recent Appointments
                  </Typography>
                  <Typography color="text.secondary">
                    Appointment history will be displayed here
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