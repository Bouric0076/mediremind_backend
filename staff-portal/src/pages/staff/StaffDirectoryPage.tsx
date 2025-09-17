import React, { useEffect, useState } from 'react';
import { useDispatch } from 'react-redux';
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
  Card,
  CardContent,
  CardActions,
  Stack,
} from '@mui/material';
import Grid from '@mui/material/Grid';
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
  Badge as BadgeIcon,
  Schedule as ScheduleIcon,
  LocalHospital as HospitalIcon,
} from '@mui/icons-material';
import { setBreadcrumbs, setCurrentPage } from '../../store/slices/uiSlice';

interface StaffMember {
  id: string;
  firstName: string;
  lastName: string;
  email: string;
  phone: string;
  jobTitle: string;
  department: string;
  specialization: string;
  employmentStatus: 'full_time' | 'part_time' | 'contract' | 'per_diem' | 'locum_tenens' | 'inactive';
  hireDate: string;
  licenseNumber: string;
  licenseExpiration: string;
  avatar?: string;
  isActive: boolean;
}

const mockStaffData: StaffMember[] = [
  {
    id: '1',
    firstName: 'Dr. Sarah',
    lastName: 'Johnson',
    email: 'sarah.johnson@mediremind.com',
    phone: '(555) 123-4567',
    jobTitle: 'Cardiologist',
    department: 'Cardiology',
    specialization: 'Interventional Cardiology',
    employmentStatus: 'full_time',
    hireDate: '2020-03-15',
    licenseNumber: 'MD123456',
    licenseExpiration: '2025-12-31',
    isActive: true,
  },
  {
    id: '2',
    firstName: 'Dr. Michael',
    lastName: 'Chen',
    email: 'michael.chen@mediremind.com',
    phone: '(555) 234-5678',
    jobTitle: 'Neurologist',
    department: 'Neurology',
    specialization: 'Stroke Medicine',
    employmentStatus: 'full_time',
    hireDate: '2019-08-22',
    licenseNumber: 'MD789012',
    licenseExpiration: '2024-06-30',
    isActive: true,
  },
  {
    id: '3',
    firstName: 'Lisa',
    lastName: 'Rodriguez',
    email: 'lisa.rodriguez@mediremind.com',
    phone: '(555) 345-6789',
    jobTitle: 'Nurse Practitioner',
    department: 'Primary Care',
    specialization: 'Family Medicine',
    employmentStatus: 'part_time',
    hireDate: '2021-01-10',
    licenseNumber: 'NP345678',
    licenseExpiration: '2026-03-15',
    isActive: true,
  },
];

export const StaffDirectoryPage: React.FC = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const [staffMembers, setStaffMembers] = useState<StaffMember[]>(mockStaffData);
  const [filteredStaff, setFilteredStaff] = useState<StaffMember[]>(mockStaffData);
  const [searchQuery, setSearchQuery] = useState('');
  const [departmentFilter, setDepartmentFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [selectedStaff, setSelectedStaff] = useState<StaffMember | null>(null);
  const [viewMode, setViewMode] = useState<'table' | 'cards'>('table');

  useEffect(() => {
    dispatch(setBreadcrumbs([
      { label: 'Dashboard', path: '/dashboard' },
      { label: 'Staff Directory', path: '/staff' },
    ]));
    dispatch(setCurrentPage('Staff Directory'));
  }, [dispatch]);

  useEffect(() => {
    let filtered = staffMembers;

    if (searchQuery) {
      filtered = filtered.filter(staff =>
        `${staff.firstName} ${staff.lastName}`.toLowerCase().includes(searchQuery.toLowerCase()) ||
        staff.email.toLowerCase().includes(searchQuery.toLowerCase()) ||
        staff.jobTitle.toLowerCase().includes(searchQuery.toLowerCase()) ||
        staff.department.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }

    if (departmentFilter) {
      filtered = filtered.filter(staff => staff.department === departmentFilter);
    }

    if (statusFilter) {
      filtered = filtered.filter(staff => staff.employmentStatus === statusFilter);
    }

    setFilteredStaff(filtered);
    setPage(0);
  }, [searchQuery, departmentFilter, statusFilter, staffMembers]);

  const handleMenuClick = (event: React.MouseEvent<HTMLElement>, staff: StaffMember) => {
    setAnchorEl(event.currentTarget);
    setSelectedStaff(staff);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
    setSelectedStaff(null);
  };

  const handleViewProfile = () => {
    if (selectedStaff) {
      navigate(`/staff/${selectedStaff.id}`);
    }
    handleMenuClose();
  };

  const handleEditProfile = () => {
    if (selectedStaff) {
      navigate(`/staff/${selectedStaff.id}/edit`);
    }
    handleMenuClose();
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'full_time': return 'success';
      case 'part_time': return 'info';
      case 'contract': return 'warning';
      case 'inactive': return 'error';
      default: return 'default';
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'full_time': return 'Full Time';
      case 'part_time': return 'Part Time';
      case 'contract': return 'Contract';
      case 'per_diem': return 'Per Diem';
      case 'locum_tenens': return 'Locum Tenens';
      case 'inactive': return 'Inactive';
      default: return status;
    }
  };

  const isLicenseExpiringSoon = (expirationDate: string) => {
    const expDate = new Date(expirationDate);
    const today = new Date();
    const thirtyDaysFromNow = new Date(today.getTime() + (30 * 24 * 60 * 60 * 1000));
    return expDate <= thirtyDaysFromNow;
  };

  const departments = [...new Set(staffMembers.map(staff => staff.department))];
  const statuses = [...new Set(staffMembers.map(staff => staff.employmentStatus))];

  const renderTableView = () => (
    <TableContainer component={Paper}>
      <Table>
        <TableHead>
          <TableRow>
            <TableCell>Staff Member</TableCell>
            <TableCell>Job Title</TableCell>
            <TableCell>Department</TableCell>
            <TableCell>Status</TableCell>
            <TableCell>License</TableCell>
            <TableCell>Contact</TableCell>
            <TableCell align="right">Actions</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {filteredStaff
            .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
            .map((staff) => (
              <TableRow key={staff.id} hover>
                <TableCell>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                    <Avatar src={staff.avatar}>
                      {staff.firstName[0]}{staff.lastName[0]}
                    </Avatar>
                    <Box>
                      <Typography variant="subtitle2">
                        {staff.firstName} {staff.lastName}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {staff.specialization}
                      </Typography>
                    </Box>
                  </Box>
                </TableCell>
                <TableCell>{staff.jobTitle}</TableCell>
                <TableCell>{staff.department}</TableCell>
                <TableCell>
                  <Chip
                    label={getStatusLabel(staff.employmentStatus)}
                    color={getStatusColor(staff.employmentStatus) as any}
                    size="small"
                  />
                </TableCell>
                <TableCell>
                  <Box>
                    <Typography variant="body2">{staff.licenseNumber}</Typography>
                    <Typography 
                      variant="caption" 
                      color={isLicenseExpiringSoon(staff.licenseExpiration) ? 'error' : 'text.secondary'}
                    >
                      Expires: {new Date(staff.licenseExpiration).toLocaleDateString()}
                    </Typography>
                  </Box>
                </TableCell>
                <TableCell>
                  <Box>
                    <Typography variant="body2">{staff.email}</Typography>
                    <Typography variant="body2" color="text.secondary">{staff.phone}</Typography>
                  </Box>
                </TableCell>
                <TableCell align="right">
                  <IconButton
                    onClick={(e) => handleMenuClick(e, staff)}
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
  );

  const renderCardView = () => (
    <Grid container spacing={3}>
      {filteredStaff
        .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
        .map((staff) => (
          <Grid size={{ xs: 12, sm: 6, md: 4 }} key={staff.id}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                  <Avatar src={staff.avatar} sx={{ width: 56, height: 56 }}>
                    {staff.firstName[0]}{staff.lastName[0]}
                  </Avatar>
                  <Box sx={{ flex: 1 }}>
                    <Typography variant="h6">
                      {staff.firstName} {staff.lastName}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {staff.jobTitle}
                    </Typography>
                  </Box>
                  <IconButton
                    onClick={(e) => handleMenuClick(e, staff)}
                    size="small"
                  >
                    <MoreVertIcon />
                  </IconButton>
                </Box>
                
                <Stack spacing={1}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <HospitalIcon fontSize="small" color="action" />
                    <Typography variant="body2">{staff.department}</Typography>
                  </Box>
                  
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <BadgeIcon fontSize="small" color="action" />
                    <Typography variant="body2">{staff.specialization}</Typography>
                  </Box>
                  
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <EmailIcon fontSize="small" color="action" />
                    <Typography variant="body2" sx={{ fontSize: '0.75rem' }}>
                      {staff.email}
                    </Typography>
                  </Box>
                  
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <PhoneIcon fontSize="small" color="action" />
                    <Typography variant="body2">{staff.phone}</Typography>
                  </Box>
                  
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mt: 1 }}>
                    <Chip
                      label={getStatusLabel(staff.employmentStatus)}
                      color={getStatusColor(staff.employmentStatus) as any}
                      size="small"
                    />
                    {isLicenseExpiringSoon(staff.licenseExpiration) && (
                      <Chip
                        label="License Expiring"
                        color="error"
                        size="small"
                        variant="outlined"
                      />
                    )}
                  </Box>
                </Stack>
              </CardContent>
            </Card>
          </Grid>
        ))}
    </Grid>
  );

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          Staff Directory
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => navigate('/staff/new')}
        >
          Add Staff Member
        </Button>
      </Box>

      {/* Filters */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid size={{ xs: 12, md: 4 }}>
            <TextField
              fullWidth
              placeholder="Search staff members..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              InputProps={{
                startAdornment: <SearchIcon sx={{ mr: 1, color: 'action.active' }} />,
                endAdornment: searchQuery && (
                  <IconButton onClick={() => setSearchQuery('')} size="small">
                    <ClearIcon />
                  </IconButton>
                ),
              }}
            />
          </Grid>
          <Grid size={{ xs: 12, md: 3 }}>
            <FormControl fullWidth>
              <InputLabel>Department</InputLabel>
              <Select
                value={departmentFilter}
                label="Department"
                onChange={(e) => setDepartmentFilter(e.target.value)}
              >
                <MenuItem value="">All Departments</MenuItem>
                {departments.map((dept) => (
                  <MenuItem key={dept} value={dept}>{dept}</MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          <Grid size={{ xs: 12, md: 3 }}>
            <FormControl fullWidth>
              <InputLabel>Status</InputLabel>
              <Select
                value={statusFilter}
                label="Status"
                onChange={(e) => setStatusFilter(e.target.value)}
              >
                <MenuItem value="">All Statuses</MenuItem>
                {statuses.map((status) => (
                  <MenuItem key={status} value={status}>
                    {getStatusLabel(status)}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          <Grid size={{ xs: 12, md: 2 }}>
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Button
                variant={viewMode === 'table' ? 'contained' : 'outlined'}
                onClick={() => setViewMode('table')}
                size="small"
              >
                Table
              </Button>
              <Button
                variant={viewMode === 'cards' ? 'contained' : 'outlined'}
                onClick={() => setViewMode('cards')}
                size="small"
              >
                Cards
              </Button>
            </Box>
          </Grid>
        </Grid>
      </Paper>

      {/* Content */}
      {viewMode === 'table' ? renderTableView() : renderCardView()}

      {/* Pagination */}
      <TablePagination
        component="div"
        count={filteredStaff.length}
        page={page}
        onPageChange={(_, newPage) => setPage(newPage)}
        rowsPerPage={rowsPerPage}
        onRowsPerPageChange={(e) => {
          setRowsPerPage(parseInt(e.target.value, 10));
          setPage(0);
        }}
      />

      {/* Action Menu */}
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
      >
        <MenuItem onClick={handleViewProfile}>
          <ViewIcon sx={{ mr: 1 }} />
          View Profile
        </MenuItem>
        <MenuItem onClick={handleEditProfile}>
          <EditIcon sx={{ mr: 1 }} />
          Edit Profile
        </MenuItem>
        <MenuItem onClick={() => {
          // Handle schedule management
          handleMenuClose();
        }}>
          <ScheduleIcon sx={{ mr: 1 }} />
          Manage Schedule
        </MenuItem>
      </Menu>

      {/* Floating Action Button */}
      <Fab
        color="primary"
        aria-label="add staff"
        sx={{ position: 'fixed', bottom: 16, right: 16 }}
        onClick={() => navigate('/staff/new')}
      >
        <AddIcon />
      </Fab>
    </Box>
  );
};