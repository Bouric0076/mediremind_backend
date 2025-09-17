import React, { useEffect, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  IconButton,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Chip,
  Avatar,
  Menu,
  MenuItem,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  Fab,
  Tooltip,
  CircularProgress,
  Alert,
} from '@mui/material';
import Grid  from '@mui/material/Grid';
import {
  Search as SearchIcon,
  FilterList as FilterIcon,
  MoreVert as MoreVertIcon,
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Visibility as ViewIcon,
  Phone as PhoneIcon,
  Email as EmailIcon,
  Person as PersonIcon,
  Clear as ClearIcon,
} from '@mui/icons-material';
import type { RootState } from '../../store';
import { 
  setSearchQuery, 
  setFilters, 
  setPagination,
  clearFilters 
} from '../../store/slices/patientsSlice';
import { setBreadcrumbs, setCurrentPage } from '../../store/slices/uiSlice';
import { useGetPatientsQuery } from '../../store/api/apiSlice';

interface Patient {
  id: string;
  name: string;
  email: string;
  phone: string;
  date_of_birth: string;
  age: number;
  gender: string;
  status: 'active' | 'inactive' | 'archived';
  primary_care_physician: string;
  created_at: string;
  updated_at: string;
}

export const PatientsPage: React.FC = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  
  const { searchQuery, filters, pagination } = useSelector(
    (state: RootState) => state.patients
  );
  
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [selectedPatient, setSelectedPatient] = useState<Patient | null>(null);
  const [filterDialogOpen, setFilterDialogOpen] = useState(false);
  const [tempFilters, setTempFilters] = useState(filters);
  
  // Real API query
  const { data: patientsData, isLoading, error } = useGetPatientsQuery({
    page: pagination.page + 1, // Backend uses 1-based pagination
    limit: pagination.limit,
    search: searchQuery,
    ...filters,
  });

  useEffect(() => {
    dispatch(setCurrentPage('patients'));
    dispatch(setBreadcrumbs([
      { label: 'Patients', path: '/patients' }
    ]));
  }, [dispatch]);

  const handleSearchChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    dispatch(setSearchQuery(event.target.value));
  };

  const handlePageChange = (_event: unknown, newPage: number) => {
    dispatch(setPagination({ page: newPage }));
  };

  const handleRowsPerPageChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    dispatch(setPagination({ 
      page: 0, 
      limit: parseInt(event.target.value, 10) 
    }));
  };

  const handleMenuClick = (event: React.MouseEvent<HTMLElement>, patient: Patient) => {
    setAnchorEl(event.currentTarget);
    setSelectedPatient(patient);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
    setSelectedPatient(null);
  };

  const handleViewPatient = () => {
    if (selectedPatient) {
      navigate(`/app/patients/${selectedPatient.id}`);
    }
    handleMenuClose();
  };

  const handleEditPatient = () => {
    if (selectedPatient) {
      navigate(`/app/patients/${selectedPatient.id}/edit`);
    }
    handleMenuClose();
  };

  const handleDeletePatient = () => {
    // Implement delete logic
    console.log('Delete patient:', selectedPatient?.id);
    handleMenuClose();
  };

  const handleApplyFilters = () => {
    dispatch(setFilters(tempFilters));
    setFilterDialogOpen(false);
  };

  const handleClearFilters = () => {
    dispatch(clearFilters());
    setTempFilters({ status: '', gender: '', ageRange: undefined });
    setFilterDialogOpen(false);
  };

  const parseAgeRange = (value: string): { min: number; max: number } | undefined => {
    if (!value) return undefined;
    switch (value) {
      case '0-18': return { min: 0, max: 18 };
      case '19-35': return { min: 19, max: 35 };
      case '36-50': return { min: 36, max: 50 };
      case '51-65': return { min: 51, max: 65 };
      case '65+': return { min: 65, max: 150 };
      default: return undefined;
    }
  };

  const getAgeRangeValue = (ageRange: { min: number; max: number } | undefined): string => {
    if (!ageRange) return '';
    if (ageRange.min === 0 && ageRange.max === 18) return '0-18';
    if (ageRange.min === 19 && ageRange.max === 35) return '19-35';
    if (ageRange.min === 36 && ageRange.max === 50) return '36-50';
    if (ageRange.min === 51 && ageRange.max === 65) return '51-65';
    if (ageRange.min === 65 && ageRange.max === 150) return '65+';
    return '';
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'success';
      case 'inactive': return 'warning';
      case 'archived': return 'error';
      default: return 'default';
    }
  };

  const formatPhoneNumber = (phone: string) => {
    // Handle encrypted phone numbers - show placeholder if encrypted
    if (phone && phone.includes('gAAAAA')) {
      return '+1 (***) ***-****';
    }
    return phone || 'N/A';
  };

  const getInitials = (name: string) => {
    return name
      .split(' ')
      .map(part => part.charAt(0))
      .join('')
      .toUpperCase()
      .slice(0, 2);
  };

  // Show loading state
  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '400px' }}>
        <CircularProgress />
      </Box>
    );
  }

  // Show error state
  if (error) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">
          Failed to load patients. Please try again later.
        </Alert>
      </Box>
    );
  }

  const patients = patientsData?.patients || [];
  const totalPatients = patientsData?.total || 0;

  return (
    <Box>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1" fontWeight="bold">
          Patients
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => navigate('/app/patients/new')}
        >
          Add Patient
        </Button>
      </Box>

      {/* Search and Filters */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid size={{ xs: 12, md: 6 }}>
            <TextField
              fullWidth
              placeholder="Search patients by name, email, or phone..."
              value={searchQuery}
              onChange={handleSearchChange}
              InputProps={{
                startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />,
                endAdornment: searchQuery && (
                  <IconButton onClick={() => dispatch(setSearchQuery(''))} size="small">
                    <ClearIcon />
                  </IconButton>
                ),
              }}
            />
          </Grid>
          <Grid size={{ xs: 12, md: 6 }}>
            <Box sx={{ display: 'flex', gap: 1, justifyContent: 'flex-end' }}>
              <Button
                variant="outlined"
                startIcon={<FilterIcon />}
                onClick={() => setFilterDialogOpen(true)}
              >
                Filters
              </Button>
              {(filters.status || filters.gender || filters.ageRange) && (
                <Button
                  variant="text"
                  onClick={handleClearFilters}
                  startIcon={<ClearIcon />}
                >
                  Clear
                </Button>
              )}
            </Box>
          </Grid>
        </Grid>
      </Paper>

      {/* Patients Table */}
      <Paper>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Patient</TableCell>
                <TableCell>Contact</TableCell>
                <TableCell>Age</TableCell>
                <TableCell>Gender</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Last Visit</TableCell>
                <TableCell>Next Appointment</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {patients.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={8} align="center" sx={{ py: 4 }}>
                    <Typography variant="body1" color="text.secondary">
                      No patients found
                    </Typography>
                  </TableCell>
                </TableRow>
              ) : (
                patients.map((patient) => (
                  <TableRow key={patient.id} hover>
                    <TableCell>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                        <Avatar sx={{ bgcolor: 'primary.main' }}>
                          {getInitials(patient.name)}
                        </Avatar>
                        <Box>
                          <Typography variant="subtitle2" fontWeight="medium">
                            {patient.name}
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            ID: {patient.id.slice(0, 8)}...
                          </Typography>
                        </Box>
                      </Box>
                    </TableCell>
                    <TableCell>
                      <Box>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mb: 0.5 }}>
                          <EmailIcon sx={{ fontSize: 14, color: 'text.secondary' }} />
                          <Typography variant="body2">{patient.email}</Typography>
                        </Box>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                          <PhoneIcon sx={{ fontSize: 14, color: 'text.secondary' }} />
                          <Typography variant="body2">{formatPhoneNumber(patient.phone)}</Typography>
                        </Box>
                      </Box>
                    </TableCell>
                    <TableCell>{patient.age}</TableCell>
                    <TableCell sx={{ textTransform: 'capitalize' }}>{patient.gender.toLowerCase()}</TableCell>
                    <TableCell>
                      <Chip
                        label={patient.status}
                        size="small"
                        color={getStatusColor(patient.status) as any}
                        variant="outlined"
                      />
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" color="text.secondary">
                        No data
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" color="text.secondary">
                        No appointment
                      </Typography>
                    </TableCell>
                    <TableCell align="right">
                      <IconButton
                        onClick={(e) => handleMenuClick(e, patient)}
                        size="small"
                      >
                        <MoreVertIcon />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
        <TablePagination
          component="div"
          count={totalPatients}
          page={pagination.page}
          onPageChange={handlePageChange}
          rowsPerPage={pagination.limit}
          onRowsPerPageChange={handleRowsPerPageChange}
          rowsPerPageOptions={[10, 25, 50]}
        />
      </Paper>

      {/* Action Menu */}
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
      >
        <MenuItem onClick={handleViewPatient}>
          <ViewIcon sx={{ mr: 1 }} />
          View Details
        </MenuItem>
        <MenuItem onClick={handleEditPatient}>
          <EditIcon sx={{ mr: 1 }} />
          Edit Patient
        </MenuItem>
        <MenuItem onClick={handleDeletePatient} sx={{ color: 'error.main' }}>
          <DeleteIcon sx={{ mr: 1 }} />
          Delete Patient
        </MenuItem>
      </Menu>

      {/* Filter Dialog */}
      <Dialog open={filterDialogOpen} onClose={() => setFilterDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Filter Patients</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
              <Grid size={{ xs: 12, md: 6 }}>
              <FormControl fullWidth>
                <InputLabel>Status</InputLabel>
                <Select
                  value={tempFilters.status}
                  label="Status"
                  onChange={(e) => setTempFilters({ ...tempFilters, status: e.target.value })}
                >
                  <MenuItem value="">All</MenuItem>
                  <MenuItem value="active">Active</MenuItem>
                  <MenuItem value="inactive">Inactive</MenuItem>
                  <MenuItem value="archived">Archived</MenuItem>
                </Select>
              </FormControl>
            </Grid>
              <Grid size={{ xs: 12, md: 6 }}>
              <FormControl fullWidth>
                <InputLabel>Gender</InputLabel>
                <Select
                  value={tempFilters.gender}
                  label="Gender"
                  onChange={(e) => setTempFilters({ ...tempFilters, gender: e.target.value })}
                >
                  <MenuItem value="">All</MenuItem>
                  <MenuItem value="male">Male</MenuItem>
                  <MenuItem value="female">Female</MenuItem>
                  <MenuItem value="other">Other</MenuItem>
                </Select>
              </FormControl>
            </Grid>
              <Grid size={{ xs: 12 }}>
              <FormControl fullWidth>
                <InputLabel>Age Range</InputLabel>
                <Select
                  value={getAgeRangeValue(tempFilters.ageRange)}
                  label="Age Range"
                  onChange={(e) => setTempFilters({ ...tempFilters, ageRange: parseAgeRange(e.target.value as string) })}
                >
                  <MenuItem value="">All Ages</MenuItem>
                  <MenuItem value="0-18">0-18 years</MenuItem>
                  <MenuItem value="19-35">19-35 years</MenuItem>
                  <MenuItem value="36-50">36-50 years</MenuItem>
                  <MenuItem value="51-65">51-65 years</MenuItem>
                  <MenuItem value="65+">65+ years</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setFilterDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleClearFilters} color="secondary">Clear All</Button>
          <Button onClick={handleApplyFilters} variant="contained">Apply Filters</Button>
        </DialogActions>
      </Dialog>

      {/* Floating Action Button */}
      <Tooltip title="Add New Patient">
        <Fab
          color="primary"
          sx={{ position: 'fixed', bottom: 16, right: 16 }}
          onClick={() => navigate('/app/patients/new')}
        >
          <AddIcon />
        </Fab>
      </Tooltip>
    </Box>
  );
};