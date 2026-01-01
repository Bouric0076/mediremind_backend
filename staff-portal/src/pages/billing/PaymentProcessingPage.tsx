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
  Alert,
} from '@mui/material';
import Grid from '@mui/material/Grid';
import {
  Search as SearchIcon,
  Add as AddIcon,
  Payment as PaymentIcon,
  CreditCard as CreditCardIcon,
  AccountBalance as BankIcon,
  Money as CashIcon,
  Receipt as ReceiptIcon,
  Visibility as VisibilityIcon,
  Print as PrintIcon,
  Download as DownloadIcon,
  CheckCircle as CheckCircleIcon,
  Schedule as ScheduleIcon,
  Error as ErrorIcon,
  Refresh as RefreshIcon,
  TrendingUp as TrendingUpIcon,
} from '@mui/icons-material';
import { setBreadcrumbs, setCurrentPage } from '../../store/slices/uiSlice';

interface Payment {
  id: string;
  paymentNumber: string;
  invoiceId: string;
  invoiceNumber: string;
  patientId: string;
  patientName: string;
  amount: number;
  paymentMethod: 'credit_card' | 'debit_card' | 'cash' | 'check' | 'bank_transfer' | 'insurance';
  paymentDate: string;
  status: 'completed' | 'pending' | 'failed' | 'refunded' | 'cancelled';
  transactionId?: string;
  referenceNumber?: string;
  notes?: string;
  processedBy: string;
  cardLast4?: string;
  checkNumber?: string;
  insuranceClaimId?: string;
}

interface PaymentMethod {
  id: string;
  type: string;
  name: string;
  isActive: boolean;
  processingFee: number;
  description: string;
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
      id={`payment-tabpanel-${index}`}
      aria-labelledby={`payment-tab-${index}`}
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

const mockPayments: Payment[] = [
  {
    id: '1',
    paymentNumber: 'PAY-2024-001',
    invoiceId: '1',
    invoiceNumber: 'INV-2024-001',
    patientId: '1',
    patientName: 'John Smith',
    amount: 250.00,
    paymentMethod: 'credit_card',
    paymentDate: '2024-01-20',
    status: 'completed',
    transactionId: 'TXN-ABC123',
    processedBy: 'Sarah Johnson',
    cardLast4: '4532',
  },
  {
    id: '2',
    paymentNumber: 'PAY-2024-002',
    invoiceId: '2',
    invoiceNumber: 'INV-2024-002',
    patientId: '2',
    patientName: 'Sarah Johnson',
    amount: 200.00,
    paymentMethod: 'insurance',
    paymentDate: '2024-01-25',
    status: 'completed',
    processedBy: 'Michael Chen',
    insuranceClaimId: 'CLM-002',
  },
  {
    id: '3',
    paymentNumber: 'PAY-2024-003',
    invoiceId: '4',
    invoiceNumber: 'INV-2024-004',
    patientId: '4',
    patientName: 'Emily Davis',
    amount: 150.00,
    paymentMethod: 'bank_transfer',
    paymentDate: '2024-01-22',
    status: 'completed',
    referenceNumber: 'REF-XYZ789',
    processedBy: 'Emily Davis',
  },
  {
    id: '4',
    paymentNumber: 'PAY-2024-004',
    invoiceId: '3',
    invoiceNumber: 'INV-2024-003',
    patientId: '3',
    patientName: 'Michael Brown',
    amount: 180.00,
    paymentMethod: 'credit_card',
    paymentDate: '2024-01-28',
    status: 'pending',
    transactionId: 'TXN-DEF456',
    processedBy: 'Robert Wilson',
    cardLast4: '1234',
  },
  {
    id: '5',
    paymentNumber: 'PAY-2024-005',
    invoiceId: '5',
    invoiceNumber: 'INV-2024-005',
    patientId: '5',
    patientName: 'Robert Wilson',
    amount: 75.00,
    paymentMethod: 'cash',
    paymentDate: '2024-01-30',
    status: 'completed',
    processedBy: 'Sarah Johnson',
  },
];

const mockPaymentMethods: PaymentMethod[] = [
  {
    id: '1',
    type: 'credit_card',
    name: 'Credit Card',
    isActive: true,
    processingFee: 2.9,
    description: 'Visa, MasterCard, American Express',
  },
  {
    id: '2',
    type: 'debit_card',
    name: 'Debit Card',
    isActive: true,
    processingFee: 1.5,
    description: 'Bank debit cards',
  },
  {
    id: '3',
    type: 'bank_transfer',
    name: 'Bank Transfer',
    isActive: true,
    processingFee: 0.5,
    description: 'ACH and wire transfers',
  },
  {
    id: '4',
    type: 'cash',
    name: 'Cash',
    isActive: true,
    processingFee: 0,
    description: 'Cash payments',
  },
  {
    id: '5',
    type: 'check',
    name: 'Check',
    isActive: true,
    processingFee: 0,
    description: 'Personal and business checks',
  },
  {
    id: '6',
    type: 'insurance',
    name: 'Insurance',
    isActive: true,
    processingFee: 0,
    description: 'Insurance claim payments',
  },
];

export const PaymentProcessingPage: React.FC = () => {
  const dispatch = useDispatch();
  const [payments] = useState<Payment[]>(mockPayments);
  const [paymentMethods] = useState<PaymentMethod[]>(mockPaymentMethods);
  const [filteredPayments, setFilteredPayments] = useState<Payment[]>(mockPayments);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [methodFilter, setMethodFilter] = useState('all');
  const [dateFilter, setDateFilter] = useState('all');
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [tabValue, setTabValue] = useState(0);
  const [selectedPayment, setSelectedPayment] = useState<Payment | null>(null);
  const [viewDialogOpen, setViewDialogOpen] = useState(false);
  const [addPaymentDialogOpen, setAddPaymentDialogOpen] = useState(false);

  useEffect(() => {
    dispatch(setBreadcrumbs([
      { label: 'Dashboard', path: '/dashboard' },
      { label: 'Billing & Finance', path: '/billing' },
      { label: 'Payment Processing', path: '/billing/payments' },
    ]));
    dispatch(setCurrentPage('Payment Processing'));
  }, [dispatch]);

  useEffect(() => {
    let filtered = payments;

    if (searchTerm) {
      filtered = filtered.filter(
        (payment) =>
          payment.paymentNumber.toLowerCase().includes(searchTerm.toLowerCase()) ||
          payment.patientName.toLowerCase().includes(searchTerm.toLowerCase()) ||
          payment.invoiceNumber.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    if (statusFilter !== 'all') {
      filtered = filtered.filter((payment) => payment.status === statusFilter);
    }

    if (methodFilter !== 'all') {
      filtered = filtered.filter((payment) => payment.paymentMethod === methodFilter);
    }

    if (dateFilter !== 'all') {
      const today = new Date();
      const filterDate = new Date();
      
      switch (dateFilter) {
        case 'today':
          filterDate.setHours(0, 0, 0, 0);
          filtered = filtered.filter(payment => 
            new Date(payment.paymentDate) >= filterDate
          );
          break;
        case 'week':
          filterDate.setDate(today.getDate() - 7);
          filtered = filtered.filter(payment => 
            new Date(payment.paymentDate) >= filterDate
          );
          break;
        case 'month':
          filterDate.setMonth(today.getMonth() - 1);
          filtered = filtered.filter(payment => 
            new Date(payment.paymentDate) >= filterDate
          );
          break;
      }
    }

    setFilteredPayments(filtered);
    setPage(0);
  }, [payments, searchTerm, statusFilter, methodFilter, dateFilter]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'success';
      case 'pending': return 'warning';
      case 'failed': return 'error';
      case 'refunded': return 'info';
      case 'cancelled': return 'default';
      default: return 'default';
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'completed': return 'Completed';
      case 'pending': return 'Pending';
      case 'failed': return 'Failed';
      case 'refunded': return 'Refunded';
      case 'cancelled': return 'Cancelled';
      default: return status;
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed': return <CheckCircleIcon />;
      case 'pending': return <ScheduleIcon />;
      case 'failed': return <ErrorIcon />;
      case 'refunded': return <RefreshIcon />;
      case 'cancelled': return <ErrorIcon />;
      default: return <></>; // Return empty fragment instead of null
    }
  };

  const getPaymentMethodIcon = (method: string) => {
    switch (method) {
      case 'credit_card':
      case 'debit_card':
        return <CreditCardIcon />;
      case 'bank_transfer':
        return <BankIcon />;
      case 'cash':
        return <CashIcon />;
      case 'check':
        return <ReceiptIcon />;
      case 'insurance':
        return <PaymentIcon />;
      default:
        return <PaymentIcon />;
    }
  };

  const getPaymentMethodLabel = (method: string) => {
    switch (method) {
      case 'credit_card': return 'Credit Card';
      case 'debit_card': return 'Debit Card';
      case 'bank_transfer': return 'Bank Transfer';
      case 'cash': return 'Cash';
      case 'check': return 'Check';
      case 'insurance': return 'Insurance';
      default: return method;
    }
  };

  const getPaymentStats = () => {
    const total = payments.length;
    const completed = payments.filter(p => p.status === 'completed').length;
    const pending = payments.filter(p => p.status === 'pending').length;
    const failed = payments.filter(p => p.status === 'failed').length;
    const totalAmount = payments
      .filter(p => p.status === 'completed')
      .reduce((sum, payment) => sum + payment.amount, 0);
    const pendingAmount = payments
      .filter(p => p.status === 'pending')
      .reduce((sum, payment) => sum + payment.amount, 0);

    return { total, completed, pending, failed, totalAmount, pendingAmount };
  };

  const handleViewPayment = (payment: Payment) => {
    setSelectedPayment(payment);
    setViewDialogOpen(true);
  };

  const stats = getPaymentStats();

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">
          Payment Processing
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
            onClick={() => setAddPaymentDialogOpen(true)}
          >
            Record Payment
          </Button>
        </Box>
      </Box>

      {/* Stats Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid size={{ xs: 12, sm: 6, md: 2 }}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Total Payments
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
                Completed
              </Typography>
              <Typography variant="h4" color="success.main">
                {stats.completed}
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
                Failed
              </Typography>
              <Typography variant="h4" color="error.main">
                {stats.failed}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 2 }}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Total Processed
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
                Pending Amount
              </Typography>
              <Typography variant="h4" color="warning.main">
                ${stats.pendingAmount.toLocaleString()}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Alerts */}
      {stats.failed > 0 && (
        <Alert severity="error" sx={{ mb: 3 }}>
          <Typography variant="subtitle2">
            {stats.failed} payment(s) have failed and require attention.
          </Typography>
        </Alert>
      )}
      {stats.pending > 0 && (
        <Alert severity="warning" sx={{ mb: 3 }}>
          <Typography variant="subtitle2">
            {stats.pending} payment(s) are pending processing.
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
          <Tab label="All Payments" icon={<PaymentIcon />} />
          <Tab label="Payment Methods" icon={<CreditCardIcon />} />
          <Tab label="Processing Queue" icon={<ScheduleIcon />} />
          <Tab label="Reports" icon={<TrendingUpIcon />} />
        </Tabs>

        {/* All Payments Tab */}
        <TabPanel value={tabValue} index={0}>
          {/* Filters */}
          <Box sx={{ display: 'flex', gap: 2, mb: 3, flexWrap: 'wrap' }}>
            <TextField
              placeholder="Search payments..."
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
                <MenuItem value="completed">Completed</MenuItem>
                <MenuItem value="pending">Pending</MenuItem>
                <MenuItem value="failed">Failed</MenuItem>
                <MenuItem value="refunded">Refunded</MenuItem>
                <MenuItem value="cancelled">Cancelled</MenuItem>
              </Select>
            </FormControl>
            <FormControl sx={{ minWidth: 150 }}>
              <InputLabel>Method</InputLabel>
              <Select
                value={methodFilter}
                label="Method"
                onChange={(e) => setMethodFilter(e.target.value)}
              >
                <MenuItem value="all">All Methods</MenuItem>
                <MenuItem value="credit_card">Credit Card</MenuItem>
                <MenuItem value="debit_card">Debit Card</MenuItem>
                <MenuItem value="bank_transfer">Bank Transfer</MenuItem>
                <MenuItem value="cash">Cash</MenuItem>
                <MenuItem value="check">Check</MenuItem>
                <MenuItem value="insurance">Insurance</MenuItem>
              </Select>
            </FormControl>
            <FormControl sx={{ minWidth: 150 }}>
              <InputLabel>Date Range</InputLabel>
              <Select
                value={dateFilter}
                label="Date Range"
                onChange={(e) => setDateFilter(e.target.value)}
              >
                <MenuItem value="all">All Time</MenuItem>
                <MenuItem value="today">Today</MenuItem>
                <MenuItem value="week">Last 7 Days</MenuItem>
                <MenuItem value="month">Last 30 Days</MenuItem>
              </Select>
            </FormControl>
          </Box>

          {/* Payments Table */}
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Payment #</TableCell>
                  <TableCell>Invoice #</TableCell>
                  <TableCell>Patient</TableCell>
                  <TableCell>Amount</TableCell>
                  <TableCell>Method</TableCell>
                  <TableCell>Date</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Processed By</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {filteredPayments
                  .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
                  .map((payment) => (
                    <TableRow key={payment.id} hover>
                      <TableCell>
                        <Typography variant="body2" fontWeight="medium">
                          {payment.paymentNumber}
                        </Typography>
                      </TableCell>
                      <TableCell>{payment.invoiceNumber}</TableCell>
                      <TableCell>{payment.patientName}</TableCell>
                      <TableCell>
                        <Typography fontWeight="medium">
                          ${payment.amount.toFixed(2)}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          {getPaymentMethodIcon(payment.paymentMethod)}
                          {getPaymentMethodLabel(payment.paymentMethod)}
                          {payment.cardLast4 && (
                            <Typography variant="caption" color="text.secondary">
                              ****{payment.cardLast4}
                            </Typography>
                          )}
                        </Box>
                      </TableCell>
                      <TableCell>
                        {new Date(payment.paymentDate).toLocaleDateString()}
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={getStatusLabel(payment.status)}
                          color={getStatusColor(payment.status) as any}
                          size="small"
                          icon={getStatusIcon(payment.status)}
                        />
                      </TableCell>
                      <TableCell>{payment.processedBy}</TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', gap: 0.5 }}>
                          <Tooltip title="View Details">
                            <IconButton
                              size="small"
                              onClick={() => handleViewPayment(payment)}
                            >
                              <VisibilityIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                          <Tooltip title="Print Receipt">
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
            count={filteredPayments.length}
            rowsPerPage={rowsPerPage}
            page={page}
            onPageChange={(_, newPage) => setPage(newPage)}
            onRowsPerPageChange={(e) => {
              setRowsPerPage(parseInt(e.target.value, 10));
              setPage(0);
            }}
          />
        </TabPanel>

        {/* Payment Methods Tab */}
        <TabPanel value={tabValue} index={1}>
          <Grid container spacing={3}>
            {paymentMethods.map((method) => (
              <Grid size={{ xs: 12, sm: 6, md: 4 }} key={method.id}>
                <Card>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                      {getPaymentMethodIcon(method.type)}
                      <Typography variant="h6">
                        {method.name}
                      </Typography>
                      <Chip
                        label={method.isActive ? 'Active' : 'Inactive'}
                        color={method.isActive ? 'success' : 'default'}
                        size="small"
                      />
                    </Box>
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      {method.description}
                    </Typography>
                    <Typography variant="body2">
                      Processing Fee: {method.processingFee}%
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </TabPanel>

        {/* Processing Queue Tab */}
        <TabPanel value={tabValue} index={2}>
          <List>
            {payments.filter(p => p.status === 'pending').map((payment) => (
              <ListItem key={payment.id}>
                <ListItemIcon>
                  <ScheduleIcon color="warning" />
                </ListItemIcon>
                <ListItemText
                  primary={`${payment.paymentNumber} - ${payment.patientName}`}
                  secondary={`$${payment.amount.toFixed(2)} via ${getPaymentMethodLabel(payment.paymentMethod)}`}
                />
                <Button size="small" variant="outlined">
                  Process Now
                </Button>
              </ListItem>
            ))}
          </List>
        </TabPanel>

        {/* Reports Tab */}
        <TabPanel value={tabValue} index={3}>
          <Typography color="text.secondary">
            Payment reports and analytics functionality will be implemented here.
          </Typography>
        </TabPanel>
      </Paper>

      {/* Payment Details Dialog */}
      <Dialog
        open={viewDialogOpen}
        onClose={() => setViewDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          Payment Details - {selectedPayment?.paymentNumber}
        </DialogTitle>
        <DialogContent>
          {selectedPayment && (
            <Box sx={{ mt: 2 }}>
              <Grid container spacing={3}>
                <Grid size={{ xs: 12, md: 6 }}>
                  <Typography variant="h6" gutterBottom>
                    Payment Information
                  </Typography>
                  <Typography><strong>Amount:</strong> ${selectedPayment.amount.toFixed(2)}</Typography>
                  <Typography><strong>Method:</strong> {getPaymentMethodLabel(selectedPayment.paymentMethod)}</Typography>
                  <Typography><strong>Date:</strong> {new Date(selectedPayment.paymentDate).toLocaleDateString()}</Typography>
                  <Typography><strong>Status:</strong> 
                    <Chip
                      label={getStatusLabel(selectedPayment.status)}
                      color={getStatusColor(selectedPayment.status) as any}
                      size="small"
                      sx={{ ml: 1 }}
                    />
                  </Typography>
                  <Typography><strong>Processed By:</strong> {selectedPayment.processedBy}</Typography>
                </Grid>
                <Grid size={{ xs: 12, md: 6 }}>
                  <Typography variant="h6" gutterBottom>
                    Transaction Details
                  </Typography>
                  <Typography><strong>Invoice:</strong> {selectedPayment.invoiceNumber}</Typography>
                  <Typography><strong>Patient:</strong> {selectedPayment.patientName}</Typography>
                  {selectedPayment.transactionId && (
                    <Typography><strong>Transaction ID:</strong> {selectedPayment.transactionId}</Typography>
                  )}
                  {selectedPayment.referenceNumber && (
                    <Typography><strong>Reference:</strong> {selectedPayment.referenceNumber}</Typography>
                  )}
                  {selectedPayment.cardLast4 && (
                    <Typography><strong>Card:</strong> ****{selectedPayment.cardLast4}</Typography>
                  )}
                </Grid>
                {selectedPayment.notes && (
                  <Grid size={{ xs: 12 }}>
                    <Typography variant="h6" gutterBottom>
                      Notes
                    </Typography>
                    <Typography>{selectedPayment.notes}</Typography>
                  </Grid>
                )}
              </Grid>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setViewDialogOpen(false)}>Close</Button>
          <Button variant="contained" startIcon={<PrintIcon />}>
            Print Receipt
          </Button>
        </DialogActions>
      </Dialog>

      {/* Add Payment Dialog */}
      <Dialog
        open={addPaymentDialogOpen}
        onClose={() => setAddPaymentDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Record New Payment</DialogTitle>
        <DialogContent>
          <Typography color="text.secondary">
            Payment recording form will be implemented here.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAddPaymentDialogOpen(false)}>Cancel</Button>
          <Button variant="contained">Record Payment</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};