import React, { useEffect, useState } from 'react';
import { useDispatch } from 'react-redux';
import {
  Box,
  Paper,
  Typography,
  Button,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  TextField,
  InputAdornment,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Card,
  CardContent,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Tabs,
  Tab,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Avatar,
  IconButton,
  Tooltip,
} from '@mui/material';
import Grid from '@mui/material/Grid';
import {
  Search as SearchIcon,
  Add as AddIcon,
  Warning as WarningIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Refresh as RefreshIcon,
  Download as DownloadIcon,
  Visibility as VisibilityIcon,
  Edit as EditIcon,
  Badge as BadgeIcon,
  School as SchoolIcon,
  LocalHospital as HospitalIcon,
  Assignment as AssignmentIcon,
} from '@mui/icons-material';
import { setBreadcrumbs, setCurrentPage } from '../../store/slices/uiSlice';

interface Credential {
  id: string;
  staffId: string;
  staffName: string;
  staffAvatar?: string;
  credentialType: string;
  credentialNumber: string;
  issuingAuthority: string;
  issueDate: string;
  expirationDate: string;
  status: 'valid' | 'expiring_soon' | 'expired' | 'pending_renewal';
  documentUrl?: string;
  notes?: string;
  renewalReminders: boolean;
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`credential-tabpanel-${index}`}
      aria-labelledby={`credential-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

const mockCredentials: Credential[] = [
  {
    id: '1',
    staffId: '1',
    staffName: 'Dr. Sarah Johnson',
    credentialType: 'Medical License',
    credentialNumber: 'MD123456',
    issuingAuthority: 'State Medical Board',
    issueDate: '2020-01-15',
    expirationDate: '2025-01-15',
    status: 'valid',
    renewalReminders: true,
  },
  {
    id: '2',
    staffId: '1',
    staffName: 'Dr. Sarah Johnson',
    credentialType: 'DEA Registration',
    credentialNumber: 'BA1234567',
    issuingAuthority: 'DEA',
    issueDate: '2021-08-15',
    expirationDate: '2024-08-15',
    status: 'expiring_soon',
    renewalReminders: true,
  },
  {
    id: '3',
    staffId: '2',
    staffName: 'Dr. Michael Chen',
    credentialType: 'Board Certification',
    credentialNumber: 'BC789012',
    issuingAuthority: 'American Board of Internal Medicine',
    issueDate: '2019-06-30',
    expirationDate: '2024-06-30',
    status: 'expiring_soon',
    renewalReminders: true,
  },
  {
    id: '4',
    staffId: '3',
    staffName: 'Nurse Emily Davis',
    credentialType: 'Nursing License',
    credentialNumber: 'RN345678',
    issuingAuthority: 'State Board of Nursing',
    issueDate: '2018-03-20',
    expirationDate: '2023-03-20',
    status: 'expired',
    renewalReminders: true,
  },
  {
    id: '5',
    staffId: '4',
    staffName: 'Dr. Robert Wilson',
    credentialType: 'Medical License',
    credentialNumber: 'MD567890',
    issuingAuthority: 'State Medical Board',
    issueDate: '2022-01-10',
    expirationDate: '2027-01-10',
    status: 'valid',
    renewalReminders: true,
  },
];

export const CredentialManagementPage: React.FC = () => {
  const dispatch = useDispatch();
  const [credentials] = useState<Credential[]>(mockCredentials);
  const [filteredCredentials, setFilteredCredentials] = useState<Credential[]>(mockCredentials);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [typeFilter, setTypeFilter] = useState('all');
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [tabValue, setTabValue] = useState(0);
  const [addDialogOpen, setAddDialogOpen] = useState(false);
  // const [selectedCredential, setSelectedCredential] = useState<Credential | null>(null);

  useEffect(() => {
    dispatch(setBreadcrumbs([
      { label: 'Dashboard', path: '/dashboard' },
      { label: 'Staff Management', path: '/staff' },
      { label: 'Credential Management', path: '/staff/credentials' },
    ]));
    dispatch(setCurrentPage('Credential Management'));
  }, [dispatch]);

  useEffect(() => {
    let filtered = credentials;

    if (searchTerm) {
      filtered = filtered.filter(
        (credential) =>
          credential.staffName.toLowerCase().includes(searchTerm.toLowerCase()) ||
          credential.credentialType.toLowerCase().includes(searchTerm.toLowerCase()) ||
          credential.credentialNumber.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    if (statusFilter !== 'all') {
      filtered = filtered.filter((credential) => credential.status === statusFilter);
    }

    if (typeFilter !== 'all') {
      filtered = filtered.filter((credential) => credential.credentialType === typeFilter);
    }

    setFilteredCredentials(filtered);
    setPage(0);
  }, [credentials, searchTerm, statusFilter, typeFilter]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'valid': return 'success';
      case 'expiring_soon': return 'warning';
      case 'expired': return 'error';
      case 'pending_renewal': return 'info';
      default: return 'default';
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'valid': return 'Valid';
      case 'expiring_soon': return 'Expiring Soon';
      case 'expired': return 'Expired';
      case 'pending_renewal': return 'Pending Renewal';
      default: return status;
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'valid': return <CheckCircleIcon />;
      case 'expiring_soon': return <WarningIcon />;
      case 'expired': return <ErrorIcon />;
      case 'pending_renewal': return <RefreshIcon />;
      default: return null;
    }
  };

  const getCredentialTypeIcon = (type: string) => {
    switch (type.toLowerCase()) {
      case 'medical license': return <HospitalIcon />;
      case 'nursing license': return <HospitalIcon />;
      case 'board certification': return <SchoolIcon />;
      case 'dea registration': return <BadgeIcon />;
      default: return <AssignmentIcon />;
    }
  };

  const isExpiringSoon = (expirationDate: string) => {
    const expDate = new Date(expirationDate);
    const today = new Date();
    const thirtyDaysFromNow = new Date(today.getTime() + (30 * 24 * 60 * 60 * 1000));
    return expDate <= thirtyDaysFromNow && expDate >= today;
  };

  const isExpired = (expirationDate: string) => {
    const expDate = new Date(expirationDate);
    const today = new Date();
    return expDate < today;
  };

  const getExpiringCredentials = () => {
    return credentials.filter(cred => isExpiringSoon(cred.expirationDate));
  };

  const getExpiredCredentials = () => {
    return credentials.filter(cred => isExpired(cred.expirationDate));
  };

  const getCredentialStats = () => {
    const total = credentials.length;
    const valid = credentials.filter(c => c.status === 'valid').length;
    const expiring = getExpiringCredentials().length;
    const expired = getExpiredCredentials().length;
    const pending = credentials.filter(c => c.status === 'pending_renewal').length;

    return { total, valid, expiring, expired, pending };
  };

  const stats = getCredentialStats();

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">
          Credential Management
        </Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            variant="outlined"
            startIcon={<DownloadIcon />}
          >
            Export
          </Button>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setAddDialogOpen(true)}
          >
            Add Credential
          </Button>
        </Box>
      </Box>

      {/* Stats Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid size={{ xs: 12, sm: 6, md: 2.4 }}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Total Credentials
              </Typography>
              <Typography variant="h4">
                {stats.total}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 2.4 }}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Valid
              </Typography>
              <Typography variant="h4" color="success.main">
                {stats.valid}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 2.4 }}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Expiring Soon
              </Typography>
              <Typography variant="h4" color="warning.main">
                {stats.expiring}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 2.4 }}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Expired
              </Typography>
              <Typography variant="h4" color="error.main">
                {stats.expired}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 2.4 }}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Pending Renewal
              </Typography>
              <Typography variant="h4" color="info.main">
                {stats.pending}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Alerts */}
      {(stats.expired > 0 || stats.expiring > 0) && (
        <Box sx={{ mb: 3 }}>
          {stats.expired > 0 && (
            <Alert severity="error" sx={{ mb: 1 }}>
              <Typography variant="subtitle2">
                {stats.expired} credential(s) have expired and require immediate attention.
              </Typography>
            </Alert>
          )}
          {stats.expiring > 0 && (
            <Alert severity="warning">
              <Typography variant="subtitle2">
                {stats.expiring} credential(s) are expiring within 30 days.
              </Typography>
            </Alert>
          )}
        </Box>
      )}

      {/* Tabs */}
      <Paper>
        <Tabs
          value={tabValue}
          onChange={(_, newValue) => setTabValue(newValue)}
          variant="scrollable"
          scrollButtons="auto"
        >
          <Tab label="All Credentials" />
          <Tab label={`Expiring Soon (${stats.expiring})`} />
          <Tab label={`Expired (${stats.expired})`} />
          <Tab label="Renewal Tracking" />
        </Tabs>

        {/* All Credentials Tab */}
        <TabPanel value={tabValue} index={0}>
          {/* Filters */}
          <Box sx={{ display: 'flex', gap: 2, mb: 3, flexWrap: 'wrap' }}>
            <TextField
              placeholder="Search credentials..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon />
                  </InputAdornment>
                ),
              }}
              sx={{ minWidth: 300 }}
            />
            <FormControl sx={{ minWidth: 150 }}>
              <InputLabel>Status</InputLabel>
              <Select
                value={statusFilter}
                label="Status"
                onChange={(e) => setStatusFilter(e.target.value)}
              >
                <MenuItem value="all">All Status</MenuItem>
                <MenuItem value="valid">Valid</MenuItem>
                <MenuItem value="expiring_soon">Expiring Soon</MenuItem>
                <MenuItem value="expired">Expired</MenuItem>
                <MenuItem value="pending_renewal">Pending Renewal</MenuItem>
              </Select>
            </FormControl>
            <FormControl sx={{ minWidth: 200 }}>
              <InputLabel>Type</InputLabel>
              <Select
                value={typeFilter}
                label="Type"
                onChange={(e) => setTypeFilter(e.target.value)}
              >
                <MenuItem value="all">All Types</MenuItem>
                <MenuItem value="Medical License">Medical License</MenuItem>
                <MenuItem value="Nursing License">Nursing License</MenuItem>
                <MenuItem value="DEA Registration">DEA Registration</MenuItem>
                <MenuItem value="Board Certification">Board Certification</MenuItem>
              </Select>
            </FormControl>
          </Box>

          {/* Credentials Table */}
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Staff Member</TableCell>
                  <TableCell>Credential Type</TableCell>
                  <TableCell>Number</TableCell>
                  <TableCell>Issuing Authority</TableCell>
                  <TableCell>Expiration Date</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {filteredCredentials
                  .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
                  .map((credential) => (
                    <TableRow key={credential.id} hover>
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Avatar sx={{ width: 32, height: 32 }}>
                            {credential.staffName.split(' ').map(n => n[0]).join('')}
                          </Avatar>
                          <Typography variant="body2">
                            {credential.staffName}
                          </Typography>
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          {getCredentialTypeIcon(credential.credentialType)}
                          {credential.credentialType}
                        </Box>
                      </TableCell>
                      <TableCell>{credential.credentialNumber}</TableCell>
                      <TableCell>{credential.issuingAuthority}</TableCell>
                      <TableCell>
                        {new Date(credential.expirationDate).toLocaleDateString()}
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={getStatusLabel(credential.status)}
                          color={getStatusColor(credential.status) as any}
                          size="small"
                          icon={getStatusIcon(credential.status) || undefined}
                        />
                      </TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', gap: 0.5 }}>
                          <Tooltip title="View Details">
                            <IconButton size="small">
                              <VisibilityIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                          <Tooltip title="Edit">
                            <IconButton size="small">
                              <EditIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                          <Tooltip title="Download Document">
                            <IconButton size="small">
                              <DownloadIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                        </Box>
                      </TableCell>
                    </TableRow>
                  ))}
              </TableBody>
            </Table>
          </TableContainer>

          <TablePagination
            rowsPerPageOptions={[5, 10, 25]}
            component="div"
            count={filteredCredentials.length}
            rowsPerPage={rowsPerPage}
            page={page}
            onPageChange={(_, newPage) => setPage(newPage)}
            onRowsPerPageChange={(e) => {
              setRowsPerPage(parseInt(e.target.value, 10));
              setPage(0);
            }}
          />
        </TabPanel>

        {/* Expiring Soon Tab */}
        <TabPanel value={tabValue} index={1}>
          <List>
            {getExpiringCredentials().map((credential) => (
              <ListItem key={credential.id}>
                <ListItemIcon>
                  <WarningIcon color="warning" />
                </ListItemIcon>
                <ListItemText
                  primary={`${credential.staffName} - ${credential.credentialType}`}
                  secondary={`Expires on ${new Date(credential.expirationDate).toLocaleDateString()}`}
                />
                <Button size="small" variant="outlined">
                  Send Reminder
                </Button>
              </ListItem>
            ))}
          </List>
        </TabPanel>

        {/* Expired Tab */}
        <TabPanel value={tabValue} index={2}>
          <List>
            {getExpiredCredentials().map((credential) => (
              <ListItem key={credential.id}>
                <ListItemIcon>
                  <ErrorIcon color="error" />
                </ListItemIcon>
                <ListItemText
                  primary={`${credential.staffName} - ${credential.credentialType}`}
                  secondary={`Expired on ${new Date(credential.expirationDate).toLocaleDateString()}`}
                />
                <Button size="small" variant="contained" color="error">
                  Urgent Action Required
                </Button>
              </ListItem>
            ))}
          </List>
        </TabPanel>

        {/* Renewal Tracking Tab */}
        <TabPanel value={tabValue} index={3}>
          <Typography color="text.secondary">
            Renewal tracking and automated reminder functionality will be implemented here.
          </Typography>
        </TabPanel>
      </Paper>

      {/* Add Credential Dialog */}
      <Dialog open={addDialogOpen} onClose={() => setAddDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Add New Credential</DialogTitle>
        <DialogContent>
          <Typography color="text.secondary">
            Add credential form will be implemented here.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAddDialogOpen(false)}>Cancel</Button>
          <Button variant="contained">Add Credential</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};