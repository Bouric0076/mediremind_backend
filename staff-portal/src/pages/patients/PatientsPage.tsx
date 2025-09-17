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
  firstName: string;
  lastName: string;
  email: string;
  phone: string;
  dateOfBirth: string;
  gender: 'male' | 'female' | 'other';
  status: 'active' | 'inactive' | 'archived';
  lastVisit: string;
  nextAppointment?: string;
  avatar?: string;
}

const mockPatients: Patient[] = [
  {
    id: '1',
    firstName: 'John',
    lastName: 'Doe',
    email: 'john.doe@email.com',
    phone: '+1 (555) 123-4567',
    dateOfBirth: '1985-03-15',
    gender: 'male',
    status: 'active',
    lastVisit: '2024-01-15',
    nextAppointment: '2024-02-01',
  },
  {
    id: '2',
    firstName: 'Jane',
    lastName: 'Smith',
    email: 'jane.smith@email.com',
    phone: '+1 (555) 987-6543',
    dateOfBirth: '1990-07-22',
    gender: 'female',
    status: 'active',
    lastVisit: '2024-01-10',
  },
  {
    id: '3',
    firstName: 'Mike',
    lastName: 'Johnson',
    email: 'mike.johnson@email.com',
    phone: '+1 (555) 456-7890',
    dateOfBirth: '1978-11-08',
    gender: 'male',
    status: 'inactive',
    lastVisit: '2023-12-20',
  },
];

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
  const [searchTerm] = useState('');
  const [currentPage] = useState(0);
  const [pageSize] = useState(10);
  
  // Mock query - replace with actual API call
  // const { data: patientsData, isLoading } = useGetPatientsQuery({
  //   page: pagination.page,
  //   limit: pagination.limit,
  //   search: searchQuery,
  //   ...filters,
  // });

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
      navigate(`/patients/${selectedPatient.id}`);
    }
    handleMenuClose();
  };

  const handleEditPatient = () => {
    if (selectedPatient) {
      navigate(`/patients/${selectedPatient.id}/edit`);
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

  const calculateAge = (dateOfBirth: string) => {
    const today = new Date();
    const birthDate = new Date(dateOfBirth);
    let age = today.getFullYear() - birthDate.getFullYear();
    const monthDiff = today.getMonth() - birthDate.getMonth();
    if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birthDate.getDate())) {
      age--;
    }
    return age;
  };

  const filteredPatients = mockPatients.filter(patient => {
    const matchesSearch = !searchQuery || 
      `${patient.firstName} ${patient.lastName}`.toLowerCase().includes(searchQuery.toLowerCase()) ||
      patient.email.toLowerCase().includes(searchQuery.toLowerCase()) ||
      patient.phone.includes(searchQuery);
    
    const matchesStatus = !filters.status || patient.status === filters.status;
    const matchesGender = !filters.gender || patient.gender === filters.gender;
    
    return matchesSearch && matchesStatus && matchesGender;
  });

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
              value={searchTerm}
              onChange={handleSearchChange}
              InputProps={{
                startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />,
                endAdornment: searchTerm && (
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
              {filteredPatients.map((patient) => (
                <TableRow key={patient.id} hover>
                  <TableCell>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                      <Avatar sx={{ bgcolor: 'primary.main' }}>
                        {patient.avatar ? (
                          <img src={patient.avatar} alt={`${patient.firstName} ${patient.lastName}`} />
                        ) : (
                          <PersonIcon />
                        )}
                      </Avatar>
                      <Box>
                        <Typography variant="subtitle2" fontWeight="medium">
                          {patient.firstName} {patient.lastName}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          ID: {patient.id}
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
                        <Typography variant="body2">{patient.phone}</Typography>
                      </Box>
                    </Box>
                  </TableCell>
                  <TableCell>{calculateAge(patient.dateOfBirth)}</TableCell>
                  <TableCell sx={{ textTransform: 'capitalize' }}>{patient.gender}</TableCell>
                  <TableCell>
                    <Chip
                      label={patient.status}
                      size="small"
                      color={getStatusColor(patient.status) as any}
                      variant="outlined"
                    />
                  </TableCell>
                  <TableCell>{new Date(patient.lastVisit).toLocaleDateString()}</TableCell>
                  <TableCell>
                    {patient.nextAppointment ? (
                      new Date(patient.nextAppointment).toLocaleDateString()
                    ) : (
                      <Typography variant="body2" color="text.secondary">
                        No appointment
                      </Typography>
                    )}
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
              ))}
            </TableBody>
          </Table>
        </TableContainer>
        <TablePagination
          component="div"
          count={filteredPatients.length}
          page={currentPage}
          onPageChange={handlePageChange}
          rowsPerPage={pageSize}
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