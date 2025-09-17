import React, { useState } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  IconButton,
  TextField,
  InputAdornment,
  Grid,
} from '@mui/material';
import {
  Add,
  Search,
  Edit,
  Delete,
  Visibility,
  LocalPharmacy,
} from '@mui/icons-material';
import { useGetPrescriptionsQuery } from '../../store/api/apiSlice';

export const PrescriptionsPage: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const { data: prescriptions = [], isLoading } = useGetPrescriptionsQuery({});

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'active':
        return 'success';
      case 'completed':
        return 'default';
      case 'cancelled':
        return 'error';
      default:
        return 'default';
    }
  };

  const filteredPrescriptions = prescriptions.filter((prescription: any) =>
    prescription.patientName?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    prescription.medication?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    prescription.prescriptionId?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <Typography>Loading prescriptions...</Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          Prescriptions
        </Typography>
        <Button
          variant="contained"
          startIcon={<Add />}
          onClick={() => console.log('Add prescription')}
        >
          New Prescription
        </Button>
      </Box>

      {/* Stats Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <LocalPharmacy sx={{ fontSize: 40, color: 'primary.main', mr: 2 }} />
                <Box>
                  <Typography variant="h4">{prescriptions.length}</Typography>
                  <Typography variant="body2" color="text.secondary">
                    Total Prescriptions
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <LocalPharmacy sx={{ fontSize: 40, color: 'success.main', mr: 2 }} />
                <Box>
                  <Typography variant="h4">
                    {prescriptions.filter((p: any) => p.status === 'active').length}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Active
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <LocalPharmacy sx={{ fontSize: 40, color: 'warning.main', mr: 2 }} />
                <Box>
                  <Typography variant="h4">
                    {prescriptions.filter((p: any) => p.status === 'pending').length}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Pending
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <LocalPharmacy sx={{ fontSize: 40, color: 'info.main', mr: 2 }} />
                <Box>
                  <Typography variant="h4">
                    {prescriptions.filter((p: any) => p.status === 'completed').length}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Completed
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Search */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <TextField
            fullWidth
            placeholder="Search prescriptions by patient name, medication, or prescription ID..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <Search />
                </InputAdornment>
              ),
            }}
          />
        </CardContent>
      </Card>

      {/* Prescriptions Table */}
      <Card>
        <CardContent>
          <TableContainer component={Paper} elevation={0}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Prescription ID</TableCell>
                  <TableCell>Patient</TableCell>
                  <TableCell>Medication</TableCell>
                  <TableCell>Dosage</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Date Prescribed</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {filteredPrescriptions.length > 0 ? (
                  filteredPrescriptions.map((prescription: any) => (
                    <TableRow key={prescription.id}>
                      <TableCell>{prescription.prescriptionId || prescription.id}</TableCell>
                      <TableCell>{prescription.patientName || 'N/A'}</TableCell>
                      <TableCell>{prescription.medication || 'N/A'}</TableCell>
                      <TableCell>{prescription.dosage || 'N/A'}</TableCell>
                      <TableCell>
                        <Chip
                          label={prescription.status || 'Unknown'}
                          color={getStatusColor(prescription.status || 'unknown') as any}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        {prescription.datePrescribed
                          ? new Date(prescription.datePrescribed).toLocaleDateString()
                          : 'N/A'}
                      </TableCell>
                      <TableCell>
                        <IconButton
                          size="small"
                          onClick={() => console.log('View prescription', prescription.id)}
                        >
                          <Visibility />
                        </IconButton>
                        <IconButton
                          size="small"
                          onClick={() => console.log('Edit prescription', prescription.id)}
                        >
                          <Edit />
                        </IconButton>
                        <IconButton
                          size="small"
                          color="error"
                          onClick={() => console.log('Delete prescription', prescription.id)}
                        >
                          <Delete />
                        </IconButton>
                      </TableCell>
                    </TableRow>
                  ))
                ) : (
                  <TableRow>
                    <TableCell colSpan={7} align="center">
                      <Typography variant="body2" color="text.secondary">
                        {searchTerm ? 'No prescriptions found matching your search.' : 'No prescriptions available.'}
                      </Typography>
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>
    </Box>
  );
};

export default PrescriptionsPage;