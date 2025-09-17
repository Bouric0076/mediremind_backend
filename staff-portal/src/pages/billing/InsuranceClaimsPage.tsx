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
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  IconButton,
  Tooltip,
  Tabs,
  Tab,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
  Alert,
  LinearProgress,
  Stepper,
  Step,
  StepLabel,
  StepContent,
} from '@mui/material';
import Grid from '@mui/material/Grid';
import {
  Search as SearchIcon,
  Add as AddIcon,
  FilterList as FilterIcon,
  LocalHospital as InsuranceIcon,
  Assignment as ClaimIcon,
  Send as SendIcon,
  Visibility as VisibilityIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Print as PrintIcon,
  Download as DownloadIcon,
  CheckCircle as CheckCircleIcon,
  Schedule as ScheduleIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
  Refresh as RefreshIcon,
  TrendingUp as TrendingUpIcon,
  AttachMoney as MoneyIcon,
  Description as DocumentIcon,
  Phone as PhoneIcon,
  Email as EmailIcon,
  History as HistoryIcon,
} from '@mui/icons-material';
import { setBreadcrumbs, setCurrentPage } from '../../store/slices/uiSlice';

interface InsuranceClaim {
  id: string;
  claimNumber: string;
  patientId: string;
  patientName: string;
  insuranceProvider: string;
  policyNumber: string;
  groupNumber?: string;
  serviceDate: string;
  submissionDate: string;
  claimAmount: number;
  approvedAmount?: number;
  paidAmount?: number;
  status: 'draft' | 'submitted' | 'pending' | 'approved' | 'denied' | 'paid' | 'appealed';
  denialReason?: string;
  procedureCodes: string[];
  diagnosisCodes: string[];
  providerId: string;
  providerName: string;
  facilityId: string;
  facilityName: string;
  notes?: string;
  attachments?: string[];
  lastUpdated: string;
  assignedTo?: string;
}

interface InsuranceProvider {
  id: string;
  name: string;
  type: 'primary' | 'secondary' | 'tertiary';
  contactPhone: string;
  contactEmail: string;
  claimsAddress: string;
  electronicSubmission: boolean;
  averageProcessingDays: number;
  isActive: boolean;
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
      id={`claims-tabpanel-${index}`}
      aria-labelledby={`claims-tab-${index}`}
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

const mockClaims: InsuranceClaim[] = [
  {
    id: '1',
    claimNumber: 'CLM-2024-001',
    patientId: '1',
    patientName: 'John Smith',
    insuranceProvider: 'Blue Cross Blue Shield',
    policyNumber: 'BCBS123456789',
    groupNumber: 'GRP001',
    serviceDate: '2024-01-15',
    submissionDate: '2024-01-16',
    claimAmount: 450.00,
    approvedAmount: 400.00,
    paidAmount: 400.00,
    status: 'paid',
    procedureCodes: ['99213', '90834'],
    diagnosisCodes: ['F32.9', 'Z71.1'],
    providerId: '1',
    providerName: 'Dr. Sarah Johnson',
    facilityId: '1',
    facilityName: 'MediRemind Clinic',
    lastUpdated: '2024-01-25',
    assignedTo: 'Sarah Johnson',
  },
  {
    id: '2',
    claimNumber: 'CLM-2024-002',
    patientId: '2',
    patientName: 'Sarah Johnson',
    insuranceProvider: 'Aetna',
    policyNumber: 'AET987654321',
    serviceDate: '2024-01-18',
    submissionDate: '2024-01-19',
    claimAmount: 320.00,
    status: 'pending',
    procedureCodes: ['99214'],
    diagnosisCodes: ['M79.3'],
    providerId: '2',
    providerName: 'Dr. Michael Chen',
    facilityId: '1',
    facilityName: 'MediRemind Clinic',
    lastUpdated: '2024-01-19',
    assignedTo: 'Michael Chen',
  },
  {
    id: '3',
    claimNumber: 'CLM-2024-003',
    patientId: '3',
    patientName: 'Michael Brown',
    insuranceProvider: 'United Healthcare',
    policyNumber: 'UHC456789123',
    serviceDate: '2024-01-20',
    submissionDate: '2024-01-21',
    claimAmount: 280.00,
    status: 'denied',
    denialReason: 'Prior authorization required',
    procedureCodes: ['99215'],
    diagnosisCodes: ['E11.9'],
    providerId: '1',
    providerName: 'Dr. Sarah Johnson',
    facilityId: '1',
    facilityName: 'MediRemind Clinic',
    lastUpdated: '2024-01-28',
    assignedTo: 'Emily Davis',
  },
  {
    id: '4',
    claimNumber: 'CLM-2024-004',
    patientId: '4',
    patientName: 'Emily Davis',
    insuranceProvider: 'Cigna',
    policyNumber: 'CIG789123456',
    serviceDate: '2024-01-22',
    submissionDate: '2024-01-23',
    claimAmount: 380.00,
    approvedAmount: 350.00,
    status: 'approved',
    procedureCodes: ['99213', '96116'],
    diagnosisCodes: ['F41.1'],
    providerId: '3',
    providerName: 'Dr. Emily Davis',
    facilityId: '1',
    facilityName: 'MediRemind Clinic',
    lastUpdated: '2024-01-30',
    assignedTo: 'Robert Wilson',
  },
  {
    id: '5',
    claimNumber: 'CLM-2024-005',
    patientId: '5',
    patientName: 'Robert Wilson',
    insuranceProvider: 'Humana',
    policyNumber: 'HUM123789456',
    serviceDate: '2024-01-25',
    submissionDate: '',
    claimAmount: 200.00,
    status: 'draft',
    procedureCodes: ['99212'],
    diagnosisCodes: ['Z00.00'],
    providerId: '2',
    providerName: 'Dr. Michael Chen',
    facilityId: '1',
    facilityName: 'MediRemind Clinic',
    lastUpdated: '2024-01-25',
    assignedTo: 'Sarah Johnson',
  },
];

const mockInsuranceProviders: InsuranceProvider[] = [
  {
    id: '1',
    name: 'Blue Cross Blue Shield',
    type: 'primary',
    contactPhone: '1-800-BCBS-123',
    contactEmail: 'claims@bcbs.com',
    claimsAddress: '123 Insurance Ave, Chicago, IL 60601',
    electronicSubmission: true,
    averageProcessingDays: 14,
    isActive: true,
  },
  {
    id: '2',
    name: 'Aetna',
    type: 'primary',
    contactPhone: '1-800-AETNA-01',
    contactEmail: 'claims@aetna.com',
    claimsAddress: '456 Health Blvd, Hartford, CT 06156',
    electronicSubmission: true,
    averageProcessingDays: 10,
    isActive: true,
  },
  {
    id: '3',
    name: 'United Healthcare',
    type: 'primary',
    contactPhone: '1-800-UHC-CARE',
    contactEmail: 'claims@uhc.com',
    claimsAddress: '789 Medical St, Minneapolis, MN 55343',
    electronicSubmission: true,
    averageProcessingDays: 12,
    isActive: true,
  },
  {
    id: '4',
    name: 'Cigna',
    type: 'primary',
    contactPhone: '1-800-CIGNA-24',
    contactEmail: 'claims@cigna.com',
    claimsAddress: '321 Care Way, Bloomfield, CT 06002',
    electronicSubmission: true,
    averageProcessingDays: 15,
    isActive: true,
  },
  {
    id: '5',
    name: 'Humana',
    type: 'primary',
    contactPhone: '1-800-HUMANA1',
    contactEmail: 'claims@humana.com',
    claimsAddress: '654 Wellness Dr, Louisville, KY 40202',
    electronicSubmission: true,
    averageProcessingDays: 11,
    isActive: true,
  },
];

export const InsuranceClaimsPage: React.FC = () => {
  const dispatch = useDispatch();
  const [claims, setClaims] = useState<InsuranceClaim[]>(mockClaims);
  const [providers, setProviders] = useState<InsuranceProvider[]>(mockInsuranceProviders);
  const [filteredClaims, setFilteredClaims] = useState<InsuranceClaim[]>(mockClaims);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [providerFilter, setProviderFilter] = useState('all');
  const [dateFilter, setDateFilter] = useState('all');
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [tabValue, setTabValue] = useState(0);
  const [selectedClaim, setSelectedClaim] = useState<InsuranceClaim | null>(null);
  const [viewDialogOpen, setViewDialogOpen] = useState(false);
  const [addClaimDialogOpen, setAddClaimDialogOpen] = useState(false);

  useEffect(() => {
    dispatch(setBreadcrumbs([
      { label: 'Dashboard', path: '/dashboard' },
      { label: 'Billing & Finance', path: '/billing' },
      { label: 'Insurance Claims', path: '/billing/claims' },
    ]));
    dispatch(setCurrentPage('Insurance Claims'));
  }, [dispatch]);

  useEffect(() => {
    let filtered = claims;

    if (searchTerm) {
      filtered = filtered.filter(
        (claim) =>
          claim.claimNumber.toLowerCase().includes(searchTerm.toLowerCase()) ||
          claim.patientName.toLowerCase().includes(searchTerm.toLowerCase()) ||
          claim.insuranceProvider.toLowerCase().includes(searchTerm.toLowerCase()) ||
          claim.policyNumber.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    if (statusFilter !== 'all') {
      filtered = filtered.filter((claim) => claim.status === statusFilter);
    }

    if (providerFilter !== 'all') {
      filtered = filtered.filter((claim) => claim.insuranceProvider === providerFilter);
    }

    if (dateFilter !== 'all') {
      const today = new Date();
      const filterDate = new Date();
      
      switch (dateFilter) {
        case 'today':
          filterDate.setHours(0, 0, 0, 0);
          filtered = filtered.filter(claim => 
            new Date(claim.serviceDate) >= filterDate
          );
          break;
        case 'week':
          filterDate.setDate(today.getDate() - 7);
          filtered = filtered.filter(claim => 
            new Date(claim.serviceDate) >= filterDate
          );
          break;
        case 'month':
          filterDate.setMonth(today.getMonth() - 1);
          filtered = filtered.filter(claim => 
            new Date(claim.serviceDate) >= filterDate
          );
          break;
      }
    }

    setFilteredClaims(filtered);
    setPage(0);
  }, [claims, searchTerm, statusFilter, providerFilter, dateFilter]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'paid': return 'success';
      case 'approved': return 'info';
      case 'pending': return 'warning';
      case 'submitted': return 'primary';
      case 'denied': return 'error';
      case 'appealed': return 'secondary';
      case 'draft': return 'default';
      default: return 'default';
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'draft': return 'Draft';
      case 'submitted': return 'Submitted';
      case 'pending': return 'Pending';
      case 'approved': return 'Approved';
      case 'denied': return 'Denied';
      case 'paid': return 'Paid';
      case 'appealed': return 'Appealed';
      default: return status;
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'paid': return <CheckCircleIcon />;
      case 'approved': return <CheckCircleIcon />;
      case 'pending': return <ScheduleIcon />;
      case 'submitted': return <SendIcon />;
      case 'denied': return <ErrorIcon />;
      case 'appealed': return <RefreshIcon />;
      case 'draft': return <EditIcon />;
      default: return null;
    }
  };

  const getClaimStats = () => {
    const total = claims.length;
    const submitted = claims.filter(c => c.status === 'submitted').length;
    const pending = claims.filter(c => c.status === 'pending').length;
    const approved = claims.filter(c => c.status === 'approved').length;
    const denied = claims.filter(c => c.status === 'denied').length;
    const paid = claims.filter(c => c.status === 'paid').length;
    const totalAmount = claims.reduce((sum, claim) => sum + claim.claimAmount, 0);
    const paidAmount = claims
      .filter(c => c.status === 'paid')
      .reduce((sum, claim) => sum + (claim.paidAmount || 0), 0);
    const pendingAmount = claims
      .filter(c => ['submitted', 'pending', 'approved'].includes(c.status))
      .reduce((sum, claim) => sum + claim.claimAmount, 0);

    return { total, submitted, pending, approved, denied, paid, totalAmount, paidAmount, pendingAmount };
  };

  const handleViewClaim = (claim: InsuranceClaim) => {
    setSelectedClaim(claim);
    setViewDialogOpen(true);
  };

  const getClaimProgress = (claim: InsuranceClaim) => {
    const steps = ['Draft', 'Submitted', 'Pending', 'Approved/Denied', 'Paid'];
    const statusMap = {
      'draft': 0,
      'submitted': 1,
      'pending': 2,
      'approved': 3,
      'denied': 3,
      'appealed': 3,
      'paid': 4,
    };
    return statusMap[claim.status] || 0;
  };

  const stats = getClaimStats();

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">
          Insurance Claims Management
        </Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            variant="outlined"
            startIcon={<DownloadIcon />}
          >
            Export Claims
          </Button>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setAddClaimDialogOpen(true)}
          >
            New Claim
          </Button>
        </Box>
      </Box>

      {/* Stats Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid size={{ xs: 12, sm: 6, md: 2 }}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Total Claims
              </Typography>
              <Typography variant="h4">
                {stats.total}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 2 }}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Pending
              </Typography>
              <Typography variant="h4" color="warning.main">
                {stats.pending}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 2 }}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Approved
              </Typography>
              <Typography variant="h4" color="info.main">
                {stats.approved}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 2 }}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Denied
              </Typography>
              <Typography variant="h4" color="error.main">
                {stats.denied}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 2 }}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Total Amount
              </Typography>
              <Typography variant="h4" color="primary">
                ${stats.totalAmount.toLocaleString()}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 2 }}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Paid Amount
              </Typography>
              <Typography variant="h4" color="success.main">
                ${stats.paidAmount.toLocaleString()}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Alerts */}
      {stats.denied > 0 && (
        <Alert severity="error" sx={{ mb: 3 }}>
          <Typography variant="subtitle2">
            {stats.denied} claim(s) have been denied and may require appeal or correction.
          </Typography>
        </Alert>
      )}
      {stats.pending > 0 && (
        <Alert severity="warning" sx={{ mb: 3 }}>
          <Typography variant="subtitle2">
            {stats.pending} claim(s) are pending review with insurance providers.
          </Typography>
        </Alert>
      )}

      {/* Tabs */}
      <Paper>
        <Tabs
          value={tabValue}
          onChange={(_, newValue) => setTabValue(newValue)}
          variant="scrollable"
          scrollButtons="auto"
        >
          <Tab label="All Claims" icon={<ClaimIcon />} />
          <Tab label="Insurance Providers" icon={<InsuranceIcon />} />
          <Tab label="Denied Claims" icon={<ErrorIcon />} />
          <Tab label="Reports" icon={<TrendingUpIcon />} />
        </Tabs>

        {/* All Claims Tab */}
        <TabPanel value={tabValue} index={0}>
          {/* Filters */}
          <Box sx={{ display: 'flex', gap: 2, mb: 3, flexWrap: 'wrap' }}>
            <TextField
              placeholder="Search claims..."
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
                <MenuItem value="draft">Draft</MenuItem>
                <MenuItem value="submitted">Submitted</MenuItem>
                <MenuItem value="pending">Pending</MenuItem>
                <MenuItem value="approved">Approved</MenuItem>
                <MenuItem value="denied">Denied</MenuItem>
                <MenuItem value="paid">Paid</MenuItem>
                <MenuItem value="appealed">Appealed</MenuItem>
              </Select>
            </FormControl>
            <FormControl sx={{ minWidth: 200 }}>
              <InputLabel>Insurance Provider</InputLabel>
              <Select
                value={providerFilter}
                label="Insurance Provider"
                onChange={(e) => setProviderFilter(e.target.value)}
              >
                <MenuItem value="all">All Providers</MenuItem>
                {providers.map((provider) => (
                  <MenuItem key={provider.id} value={provider.name}>
                    {provider.name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <FormControl sx={{ minWidth: 150 }}>
              <InputLabel>Service Date</InputLabel>
              <Select
                value={dateFilter}
                label="Service Date"
                onChange={(e) => setDateFilter(e.target.value)}
              >
                <MenuItem value="all">All Time</MenuItem>
                <MenuItem value="today">Today</MenuItem>
                <MenuItem value="week">Last 7 Days</MenuItem>
                <MenuItem value="month">Last 30 Days</MenuItem>
              </Select>
            </FormControl>
          </Box>

          {/* Claims Table */}
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Claim #</TableCell>
                  <TableCell>Patient</TableCell>
                  <TableCell>Insurance Provider</TableCell>
                  <TableCell>Service Date</TableCell>
                  <TableCell>Claim Amount</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Assigned To</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {filteredClaims
                  .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
                  .map((claim) => (
                    <TableRow key={claim.id} hover>
                      <TableCell>
                        <Typography variant="body2" fontWeight="medium">
                          {claim.claimNumber}
                        </Typography>
                      </TableCell>
                      <TableCell>{claim.patientName}</TableCell>
                      <TableCell>{claim.insuranceProvider}</TableCell>
                      <TableCell>
                        {new Date(claim.serviceDate).toLocaleDateString()}
                      </TableCell>
                      <TableCell>
                        <Typography fontWeight="medium">
                          ${claim.claimAmount.toFixed(2)}
                        </Typography>
                        {claim.approvedAmount && (
                          <Typography variant="caption" color="text.secondary" display="block">
                            Approved: ${claim.approvedAmount.toFixed(2)}
                          </Typography>
                        )}
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={getStatusLabel(claim.status)}
                          color={getStatusColor(claim.status) as any}
                          size="small"
                          icon={getStatusIcon(claim.status)}
                        />
                        {claim.denialReason && (
                          <Typography variant="caption" color="error" display="block">
                            {claim.denialReason}
                          </Typography>
                        )}
                      </TableCell>
                      <TableCell>{claim.assignedTo}</TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', gap: 0.5 }}>
                          <Tooltip title="View Details">
                            <IconButton
                              size="small"
                              onClick={() => handleViewClaim(claim)}
                            >
                              <VisibilityIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                          <Tooltip title="Edit Claim">
                            <IconButton size="small">
                              <EditIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                          <Tooltip title="Print Claim">
                            <IconButton size="small">
                              <PrintIcon fontSize="small" />
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
            count={filteredClaims.length}
            rowsPerPage={rowsPerPage}
            page={page}
            onPageChange={(_, newPage) => setPage(newPage)}
            onRowsPerPageChange={(e) => {
              setRowsPerPage(parseInt(e.target.value, 10));
              setPage(0);
            }}
          />
        </TabPanel>

        {/* Insurance Providers Tab */}
        <TabPanel value={tabValue} index={1}>
          <Grid container spacing={3}>
            {providers.map((provider) => (
              <Grid size={{ xs: 12, md: 6 }} key={provider.id}>
                <Card>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                      <InsuranceIcon color="primary" />
                      <Typography variant="h6">
                        {provider.name}
                      </Typography>
                      <Chip
                        label={provider.isActive ? 'Active' : 'Inactive'}
                        color={provider.isActive ? 'success' : 'default'}
                        size="small"
                      />
                    </Box>
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      Type: {provider.type.charAt(0).toUpperCase() + provider.type.slice(1)}
                    </Typography>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                      <PhoneIcon fontSize="small" />
                      <Typography variant="body2">{provider.contactPhone}</Typography>
                    </Box>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                      <EmailIcon fontSize="small" />
                      <Typography variant="body2">{provider.contactEmail}</Typography>
                    </Box>
                    <Typography variant="body2" color="text.secondary">
                      Avg Processing: {provider.averageProcessingDays} days
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Electronic Submission: {provider.electronicSubmission ? 'Yes' : 'No'}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </TabPanel>

        {/* Denied Claims Tab */}
        <TabPanel value={tabValue} index={2}>
          <List>
            {claims.filter(c => c.status === 'denied').map((claim) => (
              <ListItem key={claim.id}>
                <ListItemIcon>
                  <ErrorIcon color="error" />
                </ListItemIcon>
                <ListItemText
                  primary={`${claim.claimNumber} - ${claim.patientName}`}
                  secondary={`${claim.insuranceProvider} | $${claim.claimAmount.toFixed(2)} | Reason: ${claim.denialReason}`}
                />
                <Button size="small" variant="outlined" color="primary">
                  Appeal
                </Button>
              </ListItem>
            ))}
          </List>
        </TabPanel>

        {/* Reports Tab */}
        <TabPanel value={tabValue} index={3}>
          <Typography color="text.secondary">
            Claims reports and analytics functionality will be implemented here.
          </Typography>
        </TabPanel>
      </Paper>

      {/* Claim Details Dialog */}
      <Dialog
        open={viewDialogOpen}
        onClose={() => setViewDialogOpen(false)}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle>
          Claim Details - {selectedClaim?.claimNumber}
        </DialogTitle>
        <DialogContent>
          {selectedClaim && (
            <Box sx={{ mt: 2 }}>
              <Grid container spacing={3}>
                <Grid size={{ xs: 12, md: 6 }}>
                  <Typography variant="h6" gutterBottom>
                    Claim Information
                  </Typography>
                  <Typography><strong>Patient:</strong> {selectedClaim.patientName}</Typography>
                  <Typography><strong>Service Date:</strong> {new Date(selectedClaim.serviceDate).toLocaleDateString()}</Typography>
                  <Typography><strong>Submission Date:</strong> {selectedClaim.submissionDate ? new Date(selectedClaim.submissionDate).toLocaleDateString() : 'Not submitted'}</Typography>
                  <Typography><strong>Provider:</strong> {selectedClaim.providerName}</Typography>
                  <Typography><strong>Facility:</strong> {selectedClaim.facilityName}</Typography>
                  <Typography><strong>Assigned To:</strong> {selectedClaim.assignedTo}</Typography>
                </Grid>
                <Grid size={{ xs: 12, md: 6 }}>
                  <Typography variant="h6" gutterBottom>
                    Insurance Information
                  </Typography>
                  <Typography><strong>Provider:</strong> {selectedClaim.insuranceProvider}</Typography>
                  <Typography><strong>Policy Number:</strong> {selectedClaim.policyNumber}</Typography>
                  {selectedClaim.groupNumber && (
                    <Typography><strong>Group Number:</strong> {selectedClaim.groupNumber}</Typography>
                  )}
                  <Typography><strong>Claim Amount:</strong> ${selectedClaim.claimAmount.toFixed(2)}</Typography>
                  {selectedClaim.approvedAmount && (
                    <Typography><strong>Approved Amount:</strong> ${selectedClaim.approvedAmount.toFixed(2)}</Typography>
                  )}
                  {selectedClaim.paidAmount && (
                    <Typography><strong>Paid Amount:</strong> ${selectedClaim.paidAmount.toFixed(2)}</Typography>
                  )}
                </Grid>
                <Grid size={{ xs: 12, md: 6 }}>
                  <Typography variant="h6" gutterBottom>
                    Medical Codes
                  </Typography>
                  <Typography><strong>Procedure Codes:</strong> {selectedClaim.procedureCodes.join(', ')}</Typography>
                  <Typography><strong>Diagnosis Codes:</strong> {selectedClaim.diagnosisCodes.join(', ')}</Typography>
                </Grid>
                <Grid size={{ xs: 12, md: 6 }}>
                  <Typography variant="h6" gutterBottom>
                    Status & Progress
                  </Typography>
                  <Chip
                    label={getStatusLabel(selectedClaim.status)}
                    color={getStatusColor(selectedClaim.status) as any}
                    icon={getStatusIcon(selectedClaim.status)}
                    sx={{ mb: 2 }}
                  />
                  {selectedClaim.denialReason && (
                    <Typography color="error"><strong>Denial Reason:</strong> {selectedClaim.denialReason}</Typography>
                  )}
                  <Typography><strong>Last Updated:</strong> {new Date(selectedClaim.lastUpdated).toLocaleDateString()}</Typography>
                </Grid>
                {selectedClaim.notes && (
                  <Grid size={{ xs: 12 }}>
                    <Typography variant="h6" gutterBottom>
                      Notes
                    </Typography>
                    <Typography>{selectedClaim.notes}</Typography>
                  </Grid>
                )}
              </Grid>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setViewDialogOpen(false)}>Close</Button>
          <Button variant="outlined" startIcon={<EditIcon />}>
            Edit Claim
          </Button>
          <Button variant="contained" startIcon={<PrintIcon />}>
            Print Claim
          </Button>
        </DialogActions>
      </Dialog>

      {/* Add Claim Dialog */}
      <Dialog
        open={addClaimDialogOpen}
        onClose={() => setAddClaimDialogOpen(false)}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle>Create New Insurance Claim</DialogTitle>
        <DialogContent>
          <Typography color="text.secondary">
            New claim creation form will be implemented here.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAddClaimDialogOpen(false)}>Cancel</Button>
          <Button variant="contained">Create Claim</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};