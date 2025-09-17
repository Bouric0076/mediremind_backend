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
  Avatar,
  Accordion,
  AccordionSummary,
  AccordionDetails,
} from '@mui/material';
import {
  Timeline,
  TimelineItem,
  TimelineSeparator,
  TimelineConnector,
  TimelineContent,
  TimelineDot,
  TimelineOppositeContent,
} from '@mui/lab';
import Grid from '@mui/material/Grid';
import {
  Search as SearchIcon,
  Add as AddIcon,
  FilterList as FilterIcon,
  MedicalServices as MedicalIcon,
  Assignment as RecordIcon,
  Note as NoteIcon,
  Science as LabIcon,
  Medication as MedicationIcon,
  LocalHospital as HospitalIcon,
  Visibility as VisibilityIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Print as PrintIcon,
  Download as DownloadIcon,
  Person as PersonIcon,
  CalendarToday as CalendarIcon,
  Warning as WarningIcon,
  CheckCircle as CheckCircleIcon,
  Schedule as ScheduleIcon,
  AttachFile as AttachFileIcon,
  ExpandMore as ExpandMoreIcon,
  History as HistoryIcon,
  Bloodtype as BloodIcon,
  MonitorHeart as VitalsIcon,
  Psychology as MentalHealthIcon,
} from '@mui/icons-material';
import { setBreadcrumbs, setCurrentPage } from '../../store/slices/uiSlice';

interface MedicalRecord {
  id: string;
  patientId: string;
  patientName: string;
  patientAge: number;
  patientGender: string;
  recordType: 'consultation' | 'lab_result' | 'prescription' | 'procedure' | 'imaging' | 'vaccination';
  title: string;
  description: string;
  date: string;
  providerId: string;
  providerName: string;
  department: string;
  status: 'active' | 'completed' | 'pending' | 'cancelled';
  priority: 'low' | 'medium' | 'high' | 'urgent';
  diagnosis?: string[];
  medications?: string[];
  labResults?: LabResult[];
  vitals?: VitalSigns;
  attachments?: string[];
  notes?: string;
  followUpDate?: string;
  isConfidential: boolean;
  lastUpdated: string;
  createdBy: string;
}

interface LabResult {
  testName: string;
  value: string;
  unit: string;
  referenceRange: string;
  status: 'normal' | 'abnormal' | 'critical';
}

interface VitalSigns {
  bloodPressure?: string;
  heartRate?: number;
  temperature?: number;
  respiratoryRate?: number;
  oxygenSaturation?: number;
  weight?: number;
  height?: number;
  bmi?: number;
}

interface Patient {
  id: string;
  name: string;
  age: number;
  gender: string;
  bloodType: string;
  allergies: string[];
  chronicConditions: string[];
  emergencyContact: string;
  lastVisit: string;
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
      id={`records-tabpanel-${index}`}
      aria-labelledby={`records-tab-${index}`}
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

const mockMedicalRecords: MedicalRecord[] = [
  {
    id: '1',
    patientId: '1',
    patientName: 'John Smith',
    patientAge: 45,
    patientGender: 'Male',
    recordType: 'consultation',
    title: 'Annual Physical Examination',
    description: 'Routine annual physical examination with comprehensive health assessment',
    date: '2024-01-20',
    providerId: '1',
    providerName: 'Dr. Sarah Johnson',
    department: 'Internal Medicine',
    status: 'completed',
    priority: 'medium',
    diagnosis: ['Z00.00 - Encounter for general adult medical examination without abnormal findings'],
    vitals: {
      bloodPressure: '120/80',
      heartRate: 72,
      temperature: 98.6,
      respiratoryRate: 16,
      oxygenSaturation: 98,
      weight: 180,
      height: 70,
      bmi: 25.8,
    },
    notes: 'Patient in good health. Continue current exercise routine and diet.',
    followUpDate: '2025-01-20',
    isConfidential: false,
    lastUpdated: '2024-01-20',
    createdBy: 'Dr. Sarah Johnson',
  },
  {
    id: '2',
    patientId: '2',
    patientName: 'Sarah Johnson',
    patientAge: 32,
    patientGender: 'Female',
    recordType: 'lab_result',
    title: 'Complete Blood Count (CBC)',
    description: 'Routine blood work for annual physical',
    date: '2024-01-18',
    providerId: '2',
    providerName: 'Dr. Michael Chen',
    department: 'Laboratory',
    status: 'completed',
    priority: 'medium',
    labResults: [
      { testName: 'Hemoglobin', value: '13.5', unit: 'g/dL', referenceRange: '12.0-15.5', status: 'normal' },
      { testName: 'White Blood Cells', value: '7.2', unit: 'K/uL', referenceRange: '4.5-11.0', status: 'normal' },
      { testName: 'Platelets', value: '250', unit: 'K/uL', referenceRange: '150-450', status: 'normal' },
    ],
    isConfidential: false,
    lastUpdated: '2024-01-18',
    createdBy: 'Lab Technician',
  },
  {
    id: '3',
    patientId: '3',
    patientName: 'Michael Brown',
    patientAge: 58,
    patientGender: 'Male',
    recordType: 'prescription',
    title: 'Diabetes Management Prescription',
    description: 'Prescription for diabetes medication adjustment',
    date: '2024-01-22',
    providerId: '1',
    providerName: 'Dr. Sarah Johnson',
    department: 'Endocrinology',
    status: 'active',
    priority: 'high',
    diagnosis: ['E11.9 - Type 2 diabetes mellitus without complications'],
    medications: ['Metformin 500mg twice daily', 'Glipizide 5mg once daily'],
    notes: 'Patient responding well to current medication regimen. Monitor blood glucose levels.',
    followUpDate: '2024-04-22',
    isConfidential: false,
    lastUpdated: '2024-01-22',
    createdBy: 'Dr. Sarah Johnson',
  },
  {
    id: '4',
    patientId: '4',
    patientName: 'Emily Davis',
    patientAge: 28,
    patientGender: 'Female',
    recordType: 'procedure',
    title: 'Minor Surgical Procedure',
    description: 'Removal of benign skin lesion',
    date: '2024-01-25',
    providerId: '3',
    providerName: 'Dr. Emily Davis',
    department: 'Dermatology',
    status: 'completed',
    priority: 'medium',
    diagnosis: ['D23.9 - Other benign neoplasm of skin, unspecified'],
    notes: 'Procedure completed successfully. Wound healing well. No complications.',
    followUpDate: '2024-02-08',
    isConfidential: false,
    lastUpdated: '2024-01-25',
    createdBy: 'Dr. Emily Davis',
  },
  {
    id: '5',
    patientId: '5',
    patientName: 'Robert Wilson',
    patientAge: 65,
    patientGender: 'Male',
    recordType: 'imaging',
    title: 'Chest X-Ray',
    description: 'Routine chest X-ray for annual physical',
    date: '2024-01-28',
    providerId: '4',
    providerName: 'Dr. Robert Wilson',
    department: 'Radiology',
    status: 'completed',
    priority: 'low',
    diagnosis: ['Z87.891 - Personal history of nicotine dependence'],
    notes: 'Clear chest X-ray. No acute findings. Continue smoking cessation program.',
    isConfidential: false,
    lastUpdated: '2024-01-28',
    createdBy: 'Radiologist',
  },
];

const mockPatients: Patient[] = [
  {
    id: '1',
    name: 'John Smith',
    age: 45,
    gender: 'Male',
    bloodType: 'O+',
    allergies: ['Penicillin', 'Shellfish'],
    chronicConditions: ['Hypertension'],
    emergencyContact: 'Jane Smith (Wife) - (555) 123-4567',
    lastVisit: '2024-01-20',
  },
  {
    id: '2',
    name: 'Sarah Johnson',
    age: 32,
    gender: 'Female',
    bloodType: 'A+',
    allergies: [],
    chronicConditions: [],
    emergencyContact: 'Mike Johnson (Husband) - (555) 234-5678',
    lastVisit: '2024-01-18',
  },
  {
    id: '3',
    name: 'Michael Brown',
    age: 58,
    gender: 'Male',
    bloodType: 'B+',
    allergies: ['Sulfa drugs'],
    chronicConditions: ['Type 2 Diabetes', 'High Cholesterol'],
    emergencyContact: 'Lisa Brown (Wife) - (555) 345-6789',
    lastVisit: '2024-01-22',
  },
  {
    id: '4',
    name: 'Emily Davis',
    age: 28,
    gender: 'Female',
    bloodType: 'AB+',
    allergies: ['Latex'],
    chronicConditions: [],
    emergencyContact: 'Tom Davis (Husband) - (555) 456-7890',
    lastVisit: '2024-01-25',
  },
  {
    id: '5',
    name: 'Robert Wilson',
    age: 65,
    gender: 'Male',
    bloodType: 'O-',
    allergies: ['Aspirin'],
    chronicConditions: ['COPD', 'Former Smoker'],
    emergencyContact: 'Mary Wilson (Wife) - (555) 567-8901',
    lastVisit: '2024-01-28',
  },
];

export const MedicalRecordsPage: React.FC = () => {
  const dispatch = useDispatch();
  const [records, setRecords] = useState<MedicalRecord[]>(mockMedicalRecords);
  const [patients, setPatients] = useState<Patient[]>(mockPatients);
  const [filteredRecords, setFilteredRecords] = useState<MedicalRecord[]>(mockMedicalRecords);
  const [searchTerm, setSearchTerm] = useState('');
  const [typeFilter, setTypeFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all');
  const [priorityFilter, setPriorityFilter] = useState('all');
  const [departmentFilter, setDepartmentFilter] = useState('all');
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [tabValue, setTabValue] = useState(0);
  const [selectedRecord, setSelectedRecord] = useState<MedicalRecord | null>(null);
  const [selectedPatient, setSelectedPatient] = useState<Patient | null>(null);
  const [viewDialogOpen, setViewDialogOpen] = useState(false);
  const [patientDialogOpen, setPatientDialogOpen] = useState(false);
  const [addRecordDialogOpen, setAddRecordDialogOpen] = useState(false);

  useEffect(() => {
    dispatch(setBreadcrumbs([
      { label: 'Dashboard', path: '/dashboard' },
      { label: 'Medical Records', path: '/medical/records' },
    ]));
    dispatch(setCurrentPage('Medical Records'));
  }, [dispatch]);

  useEffect(() => {
    let filtered = records;

    if (searchTerm) {
      filtered = filtered.filter(
        (record) =>
          record.patientName.toLowerCase().includes(searchTerm.toLowerCase()) ||
          record.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
          record.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
          record.providerName.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    if (typeFilter !== 'all') {
      filtered = filtered.filter((record) => record.recordType === typeFilter);
    }

    if (statusFilter !== 'all') {
      filtered = filtered.filter((record) => record.status === statusFilter);
    }

    if (priorityFilter !== 'all') {
      filtered = filtered.filter((record) => record.priority === priorityFilter);
    }

    if (departmentFilter !== 'all') {
      filtered = filtered.filter((record) => record.department === departmentFilter);
    }

    setFilteredRecords(filtered);
    setPage(0);
  }, [records, searchTerm, typeFilter, statusFilter, priorityFilter, departmentFilter]);

  const getRecordTypeIcon = (type: string) => {
    switch (type) {
      case 'consultation': return <MedicalIcon />;
      case 'lab_result': return <LabIcon />;
      case 'prescription': return <MedicationIcon />;
      case 'procedure': return <HospitalIcon />;
      case 'imaging': return <RecordIcon />;
      case 'vaccination': return <MedicalIcon />;
      default: return <RecordIcon />;
    }
  };

  const getRecordTypeLabel = (type: string) => {
    switch (type) {
      case 'consultation': return 'Consultation';
      case 'lab_result': return 'Lab Result';
      case 'prescription': return 'Prescription';
      case 'procedure': return 'Procedure';
      case 'imaging': return 'Imaging';
      case 'vaccination': return 'Vaccination';
      default: return type;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'success';
      case 'active': return 'primary';
      case 'pending': return 'warning';
      case 'cancelled': return 'error';
      default: return 'default';
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'urgent': return 'error';
      case 'high': return 'warning';
      case 'medium': return 'info';
      case 'low': return 'success';
      default: return 'default';
    }
  };

  const getLabResultColor = (status: string) => {
    switch (status) {
      case 'normal': return 'success';
      case 'abnormal': return 'warning';
      case 'critical': return 'error';
      default: return 'default';
    }
  };

  const getRecordStats = () => {
    const total = records.length;
    const consultations = records.filter(r => r.recordType === 'consultation').length;
    const labResults = records.filter(r => r.recordType === 'lab_result').length;
    const prescriptions = records.filter(r => r.recordType === 'prescription').length;
    const procedures = records.filter(r => r.recordType === 'procedure').length;
    const pending = records.filter(r => r.status === 'pending').length;
    const urgent = records.filter(r => r.priority === 'urgent').length;

    return { total, consultations, labResults, prescriptions, procedures, pending, urgent };
  };

  const handleViewRecord = (record: MedicalRecord) => {
    setSelectedRecord(record);
    setViewDialogOpen(true);
  };

  const handleViewPatient = (patientId: string) => {
    const patient = patients.find(p => p.id === patientId);
    if (patient) {
      setSelectedPatient(patient);
      setPatientDialogOpen(true);
    }
  };

  const stats = getRecordStats();
  const departments = [...new Set(records.map(r => r.department))];

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">
          Medical Records Management
        </Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            variant="outlined"
            startIcon={<DownloadIcon />}
          >
            Export Records
          </Button>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setAddRecordDialogOpen(true)}
          >
            New Record
          </Button>
        </Box>
      </Box>

      {/* Stats Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid size={{ xs: 12, sm: 6, md: 2 }}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Total Records
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
                Consultations
              </Typography>
              <Typography variant="h4" color="primary">
                {stats.consultations}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 2 }}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Lab Results
              </Typography>
              <Typography variant="h4" color="info.main">
                {stats.labResults}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 2 }}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Prescriptions
              </Typography>
              <Typography variant="h4" color="success.main">
                {stats.prescriptions}
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
                Urgent
              </Typography>
              <Typography variant="h4" color="error.main">
                {stats.urgent}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Alerts */}
      {stats.urgent > 0 && (
        <Alert severity="error" sx={{ mb: 3 }}>
          <Typography variant="subtitle2">
            {stats.urgent} record(s) marked as urgent require immediate attention.
          </Typography>
        </Alert>
      )}
      {stats.pending > 0 && (
        <Alert severity="warning" sx={{ mb: 3 }}>
          <Typography variant="subtitle2">
            {stats.pending} record(s) are pending completion.
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
          <Tab label="All Records" icon={<RecordIcon />} />
          <Tab label="Patient Overview" icon={<PersonIcon />} />
          <Tab label="Lab Results" icon={<LabIcon />} />
          <Tab label="Timeline" icon={<HistoryIcon />} />
        </Tabs>

        {/* All Records Tab */}
        <TabPanel value={tabValue} index={0}>
          {/* Filters */}
          <Box sx={{ display: 'flex', gap: 2, mb: 3, flexWrap: 'wrap' }}>
            <TextField
              placeholder="Search records..."
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
              <InputLabel>Record Type</InputLabel>
              <Select
                value={typeFilter}
                label="Record Type"
                onChange={(e) => setTypeFilter(e.target.value)}
              >
                <MenuItem value="all">All Types</MenuItem>
                <MenuItem value="consultation">Consultation</MenuItem>
                <MenuItem value="lab_result">Lab Result</MenuItem>
                <MenuItem value="prescription">Prescription</MenuItem>
                <MenuItem value="procedure">Procedure</MenuItem>
                <MenuItem value="imaging">Imaging</MenuItem>
                <MenuItem value="vaccination">Vaccination</MenuItem>
              </Select>
            </FormControl>
            <FormControl sx={{ minWidth: 150 }}>
              <InputLabel>Status</InputLabel>
              <Select
                value={statusFilter}
                label="Status"
                onChange={(e) => setStatusFilter(e.target.value)}
              >
                <MenuItem value="all">All Status</MenuItem>
                <MenuItem value="active">Active</MenuItem>
                <MenuItem value="completed">Completed</MenuItem>
                <MenuItem value="pending">Pending</MenuItem>
                <MenuItem value="cancelled">Cancelled</MenuItem>
              </Select>
            </FormControl>
            <FormControl sx={{ minWidth: 150 }}>
              <InputLabel>Priority</InputLabel>
              <Select
                value={priorityFilter}
                label="Priority"
                onChange={(e) => setPriorityFilter(e.target.value)}
              >
                <MenuItem value="all">All Priority</MenuItem>
                <MenuItem value="urgent">Urgent</MenuItem>
                <MenuItem value="high">High</MenuItem>
                <MenuItem value="medium">Medium</MenuItem>
                <MenuItem value="low">Low</MenuItem>
              </Select>
            </FormControl>
            <FormControl sx={{ minWidth: 150 }}>
              <InputLabel>Department</InputLabel>
              <Select
                value={departmentFilter}
                label="Department"
                onChange={(e) => setDepartmentFilter(e.target.value)}
              >
                <MenuItem value="all">All Departments</MenuItem>
                {departments.map((dept) => (
                  <MenuItem key={dept} value={dept}>
                    {dept}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Box>

          {/* Records Table */}
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Patient</TableCell>
                  <TableCell>Record Type</TableCell>
                  <TableCell>Title</TableCell>
                  <TableCell>Provider</TableCell>
                  <TableCell>Department</TableCell>
                  <TableCell>Date</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Priority</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {filteredRecords
                  .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
                  .map((record) => (
                    <TableRow key={record.id} hover>
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Avatar sx={{ width: 32, height: 32 }}>
                            {record.patientName.charAt(0)}
                          </Avatar>
                          <Box>
                            <Typography variant="body2" fontWeight="medium">
                              {record.patientName}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              {record.patientAge}y, {record.patientGender}
                            </Typography>
                          </Box>
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          {getRecordTypeIcon(record.recordType)}
                          {getRecordTypeLabel(record.recordType)}
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" fontWeight="medium">
                          {record.title}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {record.description.substring(0, 50)}...
                        </Typography>
                      </TableCell>
                      <TableCell>{record.providerName}</TableCell>
                      <TableCell>{record.department}</TableCell>
                      <TableCell>
                        {new Date(record.date).toLocaleDateString()}
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={record.status}
                          color={getStatusColor(record.status) as any}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={record.priority}
                          color={getPriorityColor(record.priority) as any}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', gap: 0.5 }}>
                          <Tooltip title="View Record">
                            <IconButton
                              size="small"
                              onClick={() => handleViewRecord(record)}
                            >
                              <VisibilityIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                          <Tooltip title="View Patient">
                            <IconButton
                              size="small"
                              onClick={() => handleViewPatient(record.patientId)}
                            >
                              <PersonIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                          <Tooltip title="Edit Record">
                            <IconButton size="small">
                              <EditIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                          <Tooltip title="Print Record">
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
            count={filteredRecords.length}
            rowsPerPage={rowsPerPage}
            page={page}
            onPageChange={(_, newPage) => setPage(newPage)}
            onRowsPerPageChange={(e) => {
              setRowsPerPage(parseInt(e.target.value, 10));
              setPage(0);
            }}
          />
        </TabPanel>

        {/* Patient Overview Tab */}
        <TabPanel value={tabValue} index={1}>
          <Grid container spacing={3}>
            {patients.map((patient) => (
              <Grid size={{ xs: 12, md: 6, lg: 4 }} key={patient.id}>
                <Card>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                      <Avatar sx={{ width: 48, height: 48 }}>
                        {patient.name.charAt(0)}
                      </Avatar>
                      <Box>
                        <Typography variant="h6">
                          {patient.name}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          {patient.age} years old, {patient.gender}
                        </Typography>
                      </Box>
                    </Box>
                    <Typography variant="body2" gutterBottom>
                      <strong>Blood Type:</strong> {patient.bloodType}
                    </Typography>
                    <Typography variant="body2" gutterBottom>
                      <strong>Last Visit:</strong> {new Date(patient.lastVisit).toLocaleDateString()}
                    </Typography>
                    {patient.allergies.length > 0 && (
                      <Box sx={{ mt: 1 }}>
                        <Typography variant="body2" color="error" gutterBottom>
                          <strong>Allergies:</strong>
                        </Typography>
                        {patient.allergies.map((allergy, index) => (
                          <Chip
                            key={index}
                            label={allergy}
                            size="small"
                            color="error"
                            sx={{ mr: 0.5, mb: 0.5 }}
                          />
                        ))}
                      </Box>
                    )}
                    {patient.chronicConditions.length > 0 && (
                      <Box sx={{ mt: 1 }}>
                        <Typography variant="body2" color="warning.main" gutterBottom>
                          <strong>Chronic Conditions:</strong>
                        </Typography>
                        {patient.chronicConditions.map((condition, index) => (
                          <Chip
                            key={index}
                            label={condition}
                            size="small"
                            color="warning"
                            sx={{ mr: 0.5, mb: 0.5 }}
                          />
                        ))}
                      </Box>
                    )}
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </TabPanel>

        {/* Lab Results Tab */}
        <TabPanel value={tabValue} index={2}>
          <List>
            {records.filter(r => r.recordType === 'lab_result').map((record) => (
              <ListItem key={record.id}>
                <ListItemIcon>
                  <LabIcon color="info" />
                </ListItemIcon>
                <ListItemText
                  primary={`${record.title} - ${record.patientName}`}
                  secondary={`${record.providerName} | ${new Date(record.date).toLocaleDateString()}`}
                />
                <Button
                  size="small"
                  variant="outlined"
                  onClick={() => handleViewRecord(record)}
                >
                  View Results
                </Button>
              </ListItem>
            ))}
          </List>
        </TabPanel>

        {/* Timeline Tab */}
        <TabPanel value={tabValue} index={3}>
          <Timeline>
            {records
              .sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime())
              .slice(0, 10)
              .map((record) => (
                <TimelineItem key={record.id}>
                  <TimelineOppositeContent color="text.secondary">
                    {new Date(record.date).toLocaleDateString()}
                  </TimelineOppositeContent>
                  <TimelineSeparator>
                    <TimelineDot color={getStatusColor(record.status) as any}>
                      {getRecordTypeIcon(record.recordType)}
                    </TimelineDot>
                    <TimelineConnector />
                  </TimelineSeparator>
                  <TimelineContent>
                    <Typography variant="h6" component="span">
                      {record.title}
                    </Typography>
                    <Typography color="text.secondary">
                      {record.patientName} - {record.providerName}
                    </Typography>
                    <Typography variant="body2">
                      {record.description}
                    </Typography>
                  </TimelineContent>
                </TimelineItem>
              ))}
          </Timeline>
        </TabPanel>
      </Paper>

      {/* Record Details Dialog */}
      <Dialog
        open={viewDialogOpen}
        onClose={() => setViewDialogOpen(false)}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle>
          Medical Record Details - {selectedRecord?.title}
        </DialogTitle>
        <DialogContent>
          {selectedRecord && (
            <Box sx={{ mt: 2 }}>
              <Grid container spacing={3}>
                <Grid size={{ xs: 12, md: 6 }}>
                  <Typography variant="h6" gutterBottom>
                    Patient Information
                  </Typography>
                  <Typography><strong>Name:</strong> {selectedRecord.patientName}</Typography>
                  <Typography><strong>Age:</strong> {selectedRecord.patientAge}</Typography>
                  <Typography><strong>Gender:</strong> {selectedRecord.patientGender}</Typography>
                  <Typography><strong>Record Type:</strong> {getRecordTypeLabel(selectedRecord.recordType)}</Typography>
                  <Typography><strong>Date:</strong> {new Date(selectedRecord.date).toLocaleDateString()}</Typography>
                </Grid>
                <Grid size={{ xs: 12, md: 6 }}>
                  <Typography variant="h6" gutterBottom>
                    Provider Information
                  </Typography>
                  <Typography><strong>Provider:</strong> {selectedRecord.providerName}</Typography>
                  <Typography><strong>Department:</strong> {selectedRecord.department}</Typography>
                  <Typography><strong>Status:</strong> 
                    <Chip
                      label={selectedRecord.status}
                      color={getStatusColor(selectedRecord.status) as any}
                      size="small"
                      sx={{ ml: 1 }}
                    />
                  </Typography>
                  <Typography><strong>Priority:</strong> 
                    <Chip
                      label={selectedRecord.priority}
                      color={getPriorityColor(selectedRecord.priority) as any}
                      size="small"
                      sx={{ ml: 1 }}
                    />
                  </Typography>
                </Grid>
                <Grid size={{ xs: 12 }}>
                  <Typography variant="h6" gutterBottom>
                    Description
                  </Typography>
                  <Typography>{selectedRecord.description}</Typography>
                </Grid>
                {selectedRecord.diagnosis && selectedRecord.diagnosis.length > 0 && (
                  <Grid size={{ xs: 12 }}>
                    <Typography variant="h6" gutterBottom>
                      Diagnosis
                    </Typography>
                    {selectedRecord.diagnosis.map((diag, index) => (
                      <Typography key={index}>• {diag}</Typography>
                    ))}
                  </Grid>
                )}
                {selectedRecord.medications && selectedRecord.medications.length > 0 && (
                  <Grid size={{ xs: 12 }}>
                    <Typography variant="h6" gutterBottom>
                      Medications
                    </Typography>
                    {selectedRecord.medications.map((med, index) => (
                      <Typography key={index}>• {med}</Typography>
                    ))}
                  </Grid>
                )}
                {selectedRecord.vitals && (
                  <Grid size={{ xs: 12 }}>
                    <Typography variant="h6" gutterBottom>
                      Vital Signs
                    </Typography>
                    <Grid container spacing={2}>
                      {selectedRecord.vitals.bloodPressure && (
                        <Grid size={{ xs: 6, sm: 4 }}>
                          <Typography><strong>Blood Pressure:</strong> {selectedRecord.vitals.bloodPressure}</Typography>
                        </Grid>
                      )}
                      {selectedRecord.vitals.heartRate && (
                        <Grid size={{ xs: 6, sm: 4 }}>
                          <Typography><strong>Heart Rate:</strong> {selectedRecord.vitals.heartRate} bpm</Typography>
                        </Grid>
                      )}
                      {selectedRecord.vitals.temperature && (
                        <Grid size={{ xs: 6, sm: 4 }}>
                          <Typography><strong>Temperature:</strong> {selectedRecord.vitals.temperature}°F</Typography>
                        </Grid>
                      )}
                      {selectedRecord.vitals.weight && (
                        <Grid size={{ xs: 6, sm: 4 }}>
                          <Typography><strong>Weight:</strong> {selectedRecord.vitals.weight} lbs</Typography>
                        </Grid>
                      )}
                      {selectedRecord.vitals.height && (
                        <Grid size={{ xs: 6, sm: 4 }}>
                          <Typography><strong>Height:</strong> {selectedRecord.vitals.height} in</Typography>
                        </Grid>
                      )}
                      {selectedRecord.vitals.bmi && (
                        <Grid size={{ xs: 6, sm: 4 }}>
                          <Typography><strong>BMI:</strong> {selectedRecord.vitals.bmi}</Typography>
                        </Grid>
                      )}
                    </Grid>
                  </Grid>
                )}
                {selectedRecord.labResults && selectedRecord.labResults.length > 0 && (
                  <Grid size={{ xs: 12 }}>
                    <Typography variant="h6" gutterBottom>
                      Lab Results
                    </Typography>
                    <TableContainer component={Paper} variant="outlined">
                      <Table size="small">
                        <TableHead>
                          <TableRow>
                            <TableCell>Test</TableCell>
                            <TableCell>Value</TableCell>
                            <TableCell>Unit</TableCell>
                            <TableCell>Reference Range</TableCell>
                            <TableCell>Status</TableCell>
                          </TableRow>
                        </TableHead>
                        <TableBody>
                          {selectedRecord.labResults.map((result, index) => (
                            <TableRow key={index}>
                              <TableCell>{result.testName}</TableCell>
                              <TableCell>{result.value}</TableCell>
                              <TableCell>{result.unit}</TableCell>
                              <TableCell>{result.referenceRange}</TableCell>
                              <TableCell>
                                <Chip
                                  label={result.status}
                                  color={getLabResultColor(result.status) as any}
                                  size="small"
                                />
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </TableContainer>
                  </Grid>
                )}
                {selectedRecord.notes && (
                  <Grid size={{ xs: 12 }}>
                    <Typography variant="h6" gutterBottom>
                      Notes
                    </Typography>
                    <Typography>{selectedRecord.notes}</Typography>
                  </Grid>
                )}
                {selectedRecord.followUpDate && (
                  <Grid size={{ xs: 12 }}>
                    <Typography variant="h6" gutterBottom>
                      Follow-up
                    </Typography>
                    <Typography><strong>Follow-up Date:</strong> {new Date(selectedRecord.followUpDate).toLocaleDateString()}</Typography>
                  </Grid>
                )}
              </Grid>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setViewDialogOpen(false)}>Close</Button>
          <Button variant="outlined" startIcon={<EditIcon />}>
            Edit Record
          </Button>
          <Button variant="contained" startIcon={<PrintIcon />}>
            Print Record
          </Button>
        </DialogActions>
      </Dialog>

      {/* Patient Details Dialog */}
      <Dialog
        open={patientDialogOpen}
        onClose={() => setPatientDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          Patient Details - {selectedPatient?.name}
        </DialogTitle>
        <DialogContent>
          {selectedPatient && (
            <Box sx={{ mt: 2 }}>
              <Grid container spacing={3}>
                <Grid size={{ xs: 12, md: 6 }}>
                  <Typography variant="h6" gutterBottom>
                    Basic Information
                  </Typography>
                  <Typography><strong>Age:</strong> {selectedPatient.age}</Typography>
                  <Typography><strong>Gender:</strong> {selectedPatient.gender}</Typography>
                  <Typography><strong>Blood Type:</strong> {selectedPatient.bloodType}</Typography>
                  <Typography><strong>Last Visit:</strong> {new Date(selectedPatient.lastVisit).toLocaleDateString()}</Typography>
                </Grid>
                <Grid size={{ xs: 12, md: 6 }}>
                  <Typography variant="h6" gutterBottom>
                    Emergency Contact
                  </Typography>
                  <Typography>{selectedPatient.emergencyContact}</Typography>
                </Grid>
                {selectedPatient.allergies.length > 0 && (
                  <Grid size={{ xs: 12 }}>
                    <Typography variant="h6" gutterBottom color="error">
                      Allergies
                    </Typography>
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                      {selectedPatient.allergies.map((allergy, index) => (
                        <Chip
                          key={index}
                          label={allergy}
                          color="error"
                          icon={<WarningIcon />}
                        />
                      ))}
                    </Box>
                  </Grid>
                )}
                {selectedPatient.chronicConditions.length > 0 && (
                  <Grid size={{ xs: 12 }}>
                    <Typography variant="h6" gutterBottom color="warning.main">
                      Chronic Conditions
                    </Typography>
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                      {selectedPatient.chronicConditions.map((condition, index) => (
                        <Chip
                          key={index}
                          label={condition}
                          color="warning"
                        />
                      ))}
                    </Box>
                  </Grid>
                )}
              </Grid>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setPatientDialogOpen(false)}>Close</Button>
          <Button variant="contained" startIcon={<EditIcon />}>
            Edit Patient
          </Button>
        </DialogActions>
      </Dialog>

      {/* Add Record Dialog */}
      <Dialog
        open={addRecordDialogOpen}
        onClose={() => setAddRecordDialogOpen(false)}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle>Create New Medical Record</DialogTitle>
        <DialogContent>
          <Typography color="text.secondary">
            New medical record creation form will be implemented here.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAddRecordDialogOpen(false)}>Cancel</Button>
          <Button variant="contained">Create Record</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};