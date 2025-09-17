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
  Menu,
  MenuList,
  ListItemIcon,
  ListItemText,
  Divider,
  Alert,
} from '@mui/material';
import Grid from '@mui/material/Grid';
import {
  Search as SearchIcon,
  Add as AddIcon,
  FilterList as FilterIcon,
  MoreVert as MoreVertIcon,
  Visibility as VisibilityIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Print as PrintIcon,
  Email as EmailIcon,
  Download as DownloadIcon,
  Payment as PaymentIcon,
  Receipt as ReceiptIcon,
  Warning as WarningIcon,
  CheckCircle as CheckCircleIcon,
  Schedule as ScheduleIcon,
  Cancel as CancelIcon,
  AttachMoney as MoneyIcon,
} from '@mui/icons-material';
import { setBreadcrumbs, setCurrentPage } from '../../store/slices/uiSlice';

interface Invoice {
  id: string;
  invoiceNumber: string;
  patientId: string;
  patientName: string;
  appointmentId?: string;
  appointmentDate?: string;
  issueDate: string;
  dueDate: string;
  status: 'draft' | 'sent' | 'paid' | 'overdue' | 'cancelled' | 'partial';
  totalAmount: number;
  paidAmount: number;
  balanceAmount: number;
  insuranceClaimId?: string;
  insuranceStatus?: 'pending' | 'approved' | 'denied' | 'partial';
  paymentMethod?: string;
  lastPaymentDate?: string;
  services: InvoiceService[];
  notes?: string;
}

interface InvoiceService {
  id: string;
  serviceCode: string;
  description: string;
  quantity: number;
  unitPrice: number;
  totalPrice: number;
}

const mockInvoices: Invoice[] = [
  {
    id: '1',
    invoiceNumber: 'INV-2024-001',
    patientId: '1',
    patientName: 'John Smith',
    appointmentId: 'APT-001',
    appointmentDate: '2024-01-15',
    issueDate: '2024-01-15',
    dueDate: '2024-02-15',
    status: 'paid',
    totalAmount: 250.00,
    paidAmount: 250.00,
    balanceAmount: 0.00,
    insuranceClaimId: 'CLM-001',
    insuranceStatus: 'approved',
    paymentMethod: 'Insurance + Credit Card',
    lastPaymentDate: '2024-01-20',
    services: [
      {
        id: '1',
        serviceCode: '99213',
        description: 'Office Visit - Established Patient',
        quantity: 1,
        unitPrice: 150.00,
        totalPrice: 150.00,
      },
      {
        id: '2',
        serviceCode: '93000',
        description: 'Electrocardiogram',
        quantity: 1,
        unitPrice: 100.00,
        totalPrice: 100.00,
      },
    ],
  },
  {
    id: '2',
    invoiceNumber: 'INV-2024-002',
    patientId: '2',
    patientName: 'Sarah Johnson',
    appointmentId: 'APT-002',
    appointmentDate: '2024-01-16',
    issueDate: '2024-01-16',
    dueDate: '2024-02-16',
    status: 'overdue',
    totalAmount: 450.00,
    paidAmount: 200.00,
    balanceAmount: 250.00,
    insuranceClaimId: 'CLM-002',
    insuranceStatus: 'partial',
    paymentMethod: 'Insurance',
    lastPaymentDate: '2024-01-25',
    services: [
      {
        id: '3',
        serviceCode: '99214',
        description: 'Office Visit - Comprehensive',
        quantity: 1,
        unitPrice: 200.00,
        totalPrice: 200.00,
      },
      {
        id: '4',
        serviceCode: '80053',
        description: 'Comprehensive Metabolic Panel',
        quantity: 1,
        unitPrice: 250.00,
        totalPrice: 250.00,
      },
    ],
  },
  {
    id: '3',
    invoiceNumber: 'INV-2024-003',
    patientId: '3',
    patientName: 'Michael Brown',
    appointmentDate: '2024-01-17',
    issueDate: '2024-01-17',
    dueDate: '2024-02-17',
    status: 'sent',
    totalAmount: 180.00,
    paidAmount: 0.00,
    balanceAmount: 180.00,
    insuranceStatus: 'pending',
    services: [
      {
        id: '5',
        serviceCode: '99212',
        description: 'Office Visit - Brief',
        quantity: 1,
        unitPrice: 120.00,
        totalPrice: 120.00,
      },
      {
        id: '6',
        serviceCode: '90471',
        description: 'Immunization Administration',
        quantity: 1,
        unitPrice: 60.00,
        totalPrice: 60.00,
      },
    ],
  },
  {
    id: '4',
    invoiceNumber: 'INV-2024-004',
    patientId: '4',
    patientName: 'Emily Davis',
    appointmentDate: '2024-01-18',
    issueDate: '2024-01-18',
    dueDate: '2024-02-18',
    status: 'partial',
    totalAmount: 320.00,
    paidAmount: 150.00,
    balanceAmount: 170.00,
    insuranceStatus: 'approved',
    paymentMethod: 'Insurance',
    lastPaymentDate: '2024-01-22',
    services: [
      {
        id: '7',
        serviceCode: '99215',
        description: 'Office Visit - Complex',
        quantity: 1,
        unitPrice: 320.00,
        totalPrice: 320.00,
      },
    ],
  },
  {
    id: '5',
    invoiceNumber: 'INV-2024-005',
    patientId: '5',
    patientName: 'Robert Wilson',
    issueDate: '2024-01-19',
    dueDate: '2024-02-19',
    status: 'draft',
    totalAmount: 275.00,
    paidAmount: 0.00,
    balanceAmount: 275.00,
    services: [
      {
        id: '8',
        serviceCode: '99213',
        description: 'Office Visit - Established Patient',
        quantity: 1,
        unitPrice: 150.00,
        totalPrice: 150.00,
      },
      {
        id: '9',
        serviceCode: '71020',
        description: 'Chest X-Ray',
        quantity: 1,
        unitPrice: 125.00,
        totalPrice: 125.00,
      },
    ],
  },
];

export const InvoiceManagementPage: React.FC = () => {
  const dispatch = useDispatch();
  const [invoices, setInvoices] = useState<Invoice[]>(mockInvoices);
  const [filteredInvoices, setFilteredInvoices] = useState<Invoice[]>(mockInvoices);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [dateFilter, setDateFilter] = useState('all');
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [selectedInvoice, setSelectedInvoice] = useState<Invoice | null>(null);
  const [viewDialogOpen, setViewDialogOpen] = useState(false);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [menuInvoiceId, setMenuInvoiceId] = useState<string | null>(null);

  useEffect(() => {
    dispatch(setBreadcrumbs([
      { label: 'Dashboard', path: '/dashboard' },
      { label: 'Billing & Finance', path: '/billing' },
      { label: 'Invoice Management', path: '/billing/invoices' },
    ]));
    dispatch(setCurrentPage('Invoice Management'));
  }, [dispatch]);

  useEffect(() => {
    let filtered = invoices;

    if (searchTerm) {
      filtered = filtered.filter(
        (invoice) =>
          invoice.invoiceNumber.toLowerCase().includes(searchTerm.toLowerCase()) ||
          invoice.patientName.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    if (statusFilter !== 'all') {
      filtered = filtered.filter((invoice) => invoice.status === statusFilter);
    }

    if (dateFilter !== 'all') {
      const today = new Date();
      const filterDate = new Date();
      
      switch (dateFilter) {
        case 'today':
          filterDate.setHours(0, 0, 0, 0);
          filtered = filtered.filter(invoice => 
            new Date(invoice.issueDate) >= filterDate
          );
          break;
        case 'week':
          filterDate.setDate(today.getDate() - 7);
          filtered = filtered.filter(invoice => 
            new Date(invoice.issueDate) >= filterDate
          );
          break;
        case 'month':
          filterDate.setMonth(today.getMonth() - 1);
          filtered = filtered.filter(invoice => 
            new Date(invoice.issueDate) >= filterDate
          );
          break;
      }
    }

    setFilteredInvoices(filtered);
    setPage(0);
  }, [invoices, searchTerm, statusFilter, dateFilter]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'paid': return 'success';
      case 'sent': return 'info';
      case 'partial': return 'warning';
      case 'overdue': return 'error';
      case 'cancelled': return 'default';
      case 'draft': return 'default';
      default: return 'default';
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'paid': return 'Paid';
      case 'sent': return 'Sent';
      case 'partial': return 'Partially Paid';
      case 'overdue': return 'Overdue';
      case 'cancelled': return 'Cancelled';
      case 'draft': return 'Draft';
      default: return status;
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'paid': return <CheckCircleIcon />;
      case 'sent': return <EmailIcon />;
      case 'partial': return <PaymentIcon />;
      case 'overdue': return <WarningIcon />;
      case 'cancelled': return <CancelIcon />;
      case 'draft': return <ScheduleIcon />;
      default: return null;
    }
  };

  const getInvoiceStats = () => {
    const total = invoices.length;
    const paid = invoices.filter(i => i.status === 'paid').length;
    const overdue = invoices.filter(i => i.status === 'overdue').length;
    const pending = invoices.filter(i => i.status === 'sent').length;
    const totalRevenue = invoices.reduce((sum, inv) => sum + inv.paidAmount, 0);
    const outstandingAmount = invoices.reduce((sum, inv) => sum + inv.balanceAmount, 0);

    return { total, paid, overdue, pending, totalRevenue, outstandingAmount };
  };

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>, invoiceId: string) => {
    setAnchorEl(event.currentTarget);
    setMenuInvoiceId(invoiceId);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
    setMenuInvoiceId(null);
  };

  const handleViewInvoice = (invoice: Invoice) => {
    setSelectedInvoice(invoice);
    setViewDialogOpen(true);
    handleMenuClose();
  };

  const stats = getInvoiceStats();

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">
          Invoice Management
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
          >
            Create Invoice
          </Button>
        </Box>
      </Box>

      {/* Stats Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid size={{ xs: 12, sm: 6, md: 2 }}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Total Invoices
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
                Paid
              </Typography>
              <Typography variant="h4" color="success.main">
                {stats.paid}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 2 }}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Overdue
              </Typography>
              <Typography variant="h4" color="error.main">
                {stats.overdue}
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
              <Typography variant="h4" color="info.main">
                {stats.pending}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 2 }}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Total Revenue
              </Typography>
              <Typography variant="h4" color="primary">
                ${stats.totalRevenue.toLocaleString()}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 2 }}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Outstanding
              </Typography>
              <Typography variant="h4" color="warning.main">
                ${stats.outstandingAmount.toLocaleString()}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Alerts */}
      {stats.overdue > 0 && (
        <Alert severity="warning" sx={{ mb: 3 }}>
          <Typography variant="subtitle2">
            You have {stats.overdue} overdue invoice(s) requiring immediate attention.
          </Typography>
        </Alert>
      )}

      {/* Filters */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
          <TextField
            placeholder="Search invoices..."
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
              <MenuItem value="sent">Sent</MenuItem>
              <MenuItem value="paid">Paid</MenuItem>
              <MenuItem value="partial">Partially Paid</MenuItem>
              <MenuItem value="overdue">Overdue</MenuItem>
              <MenuItem value="cancelled">Cancelled</MenuItem>
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
      </Paper>

      {/* Invoices Table */}
      <Paper>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Invoice #</TableCell>
                <TableCell>Patient</TableCell>
                <TableCell>Issue Date</TableCell>
                <TableCell>Due Date</TableCell>
                <TableCell>Total Amount</TableCell>
                <TableCell>Paid Amount</TableCell>
                <TableCell>Balance</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {filteredInvoices
                .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
                .map((invoice) => (
                  <TableRow key={invoice.id} hover>
                    <TableCell>
                      <Typography variant="body2" fontWeight="medium">
                        {invoice.invoiceNumber}
                      </Typography>
                    </TableCell>
                    <TableCell>{invoice.patientName}</TableCell>
                    <TableCell>
                      {new Date(invoice.issueDate).toLocaleDateString()}
                    </TableCell>
                    <TableCell>
                      {new Date(invoice.dueDate).toLocaleDateString()}
                    </TableCell>
                    <TableCell>${invoice.totalAmount.toFixed(2)}</TableCell>
                    <TableCell>${invoice.paidAmount.toFixed(2)}</TableCell>
                    <TableCell>
                      <Typography
                        color={invoice.balanceAmount > 0 ? 'error.main' : 'success.main'}
                        fontWeight="medium"
                      >
                        ${invoice.balanceAmount.toFixed(2)}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={getStatusLabel(invoice.status)}
                        color={getStatusColor(invoice.status) as any}
                        size="small"
                        icon={getStatusIcon(invoice.status)}
                      />
                    </TableCell>
                    <TableCell>
                      <IconButton
                        size="small"
                        onClick={(e) => handleMenuOpen(e, invoice.id)}
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
          rowsPerPageOptions={[5, 10, 25]}
          component="div"
          count={filteredInvoices.length}
          rowsPerPage={rowsPerPage}
          page={page}
          onPageChange={(_, newPage) => setPage(newPage)}
          onRowsPerPageChange={(e) => {
            setRowsPerPage(parseInt(e.target.value, 10));
            setPage(0);
          }}
        />
      </Paper>

      {/* Action Menu */}
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
      >
        <MenuList>
          <MenuItem onClick={() => {
            const invoice = invoices.find(i => i.id === menuInvoiceId);
            if (invoice) handleViewInvoice(invoice);
          }}>
            <ListItemIcon><VisibilityIcon /></ListItemIcon>
            <ListItemText>View Details</ListItemText>
          </MenuItem>
          <MenuItem onClick={handleMenuClose}>
            <ListItemIcon><EditIcon /></ListItemIcon>
            <ListItemText>Edit Invoice</ListItemText>
          </MenuItem>
          <MenuItem onClick={handleMenuClose}>
            <ListItemIcon><PrintIcon /></ListItemIcon>
            <ListItemText>Print</ListItemText>
          </MenuItem>
          <MenuItem onClick={handleMenuClose}>
            <ListItemIcon><EmailIcon /></ListItemIcon>
            <ListItemText>Send Email</ListItemText>
          </MenuItem>
          <MenuItem onClick={handleMenuClose}>
            <ListItemIcon><PaymentIcon /></ListItemIcon>
            <ListItemText>Record Payment</ListItemText>
          </MenuItem>
          <Divider />
          <MenuItem onClick={handleMenuClose}>
            <ListItemIcon><DeleteIcon /></ListItemIcon>
            <ListItemText>Delete</ListItemText>
          </MenuItem>
        </MenuList>
      </Menu>

      {/* Invoice Details Dialog */}
      <Dialog
        open={viewDialogOpen}
        onClose={() => setViewDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          Invoice Details - {selectedInvoice?.invoiceNumber}
        </DialogTitle>
        <DialogContent>
          {selectedInvoice && (
            <Box sx={{ mt: 2 }}>
              <Grid container spacing={3}>
                <Grid item xs={12} md={6}>
                  <Typography variant="h6" gutterBottom>
                    Patient Information
                  </Typography>
                  <Typography><strong>Name:</strong> {selectedInvoice.patientName}</Typography>
                  <Typography><strong>Patient ID:</strong> {selectedInvoice.patientId}</Typography>
                  {selectedInvoice.appointmentDate && (
                    <Typography><strong>Appointment Date:</strong> {new Date(selectedInvoice.appointmentDate).toLocaleDateString()}</Typography>
                  )}
                </Grid>
                <Grid item xs={12} md={6}>
                  <Typography variant="h6" gutterBottom>
                    Invoice Information
                  </Typography>
                  <Typography><strong>Issue Date:</strong> {new Date(selectedInvoice.issueDate).toLocaleDateString()}</Typography>
                  <Typography><strong>Due Date:</strong> {new Date(selectedInvoice.dueDate).toLocaleDateString()}</Typography>
                  <Typography><strong>Status:</strong> 
                    <Chip
                      label={getStatusLabel(selectedInvoice.status)}
                      color={getStatusColor(selectedInvoice.status) as any}
                      size="small"
                      sx={{ ml: 1 }}
                    />
                  </Typography>
                </Grid>
                <Grid item xs={12}>
                  <Typography variant="h6" gutterBottom>
                    Services
                  </Typography>
                  <TableContainer>
                    <Table size="small">
                      <TableHead>
                        <TableRow>
                          <TableCell>Service Code</TableCell>
                          <TableCell>Description</TableCell>
                          <TableCell>Quantity</TableCell>
                          <TableCell>Unit Price</TableCell>
                          <TableCell>Total</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {selectedInvoice.services.map((service) => (
                          <TableRow key={service.id}>
                            <TableCell>{service.serviceCode}</TableCell>
                            <TableCell>{service.description}</TableCell>
                            <TableCell>{service.quantity}</TableCell>
                            <TableCell>${service.unitPrice.toFixed(2)}</TableCell>
                            <TableCell>${service.totalPrice.toFixed(2)}</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                </Grid>
                <Grid item xs={12}>
                  <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 2 }}>
                    <Box sx={{ minWidth: 200 }}>
                      <Typography><strong>Total Amount:</strong> ${selectedInvoice.totalAmount.toFixed(2)}</Typography>
                      <Typography><strong>Paid Amount:</strong> ${selectedInvoice.paidAmount.toFixed(2)}</Typography>
                      <Typography color={selectedInvoice.balanceAmount > 0 ? 'error.main' : 'success.main'}>
                        <strong>Balance:</strong> ${selectedInvoice.balanceAmount.toFixed(2)}
                      </Typography>
                    </Box>
                  </Box>
                </Grid>
              </Grid>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setViewDialogOpen(false)}>Close</Button>
          <Button variant="contained" startIcon={<PrintIcon />}>
            Print
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};