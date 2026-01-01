import React, { useEffect, useState } from 'react';
import { useDispatch } from 'react-redux';
import {
  Box,
  Paper,
  Typography,
  Button,
  Chip,
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
  Avatar,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Alert,
  Badge,
  Stack,
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
  MedicalServices as MedicalIcon,
  Assignment as RecordIcon,
  Science as LabIcon,
  Medication as MedicationIcon,
  LocalHospital as HospitalIcon,
  Warning as WarningIcon,
  CheckCircle as CheckCircleIcon,
  AttachFile as AttachFileIcon,
  MonitorHeart as VitalsIcon,
  Vaccines as VaccineIcon,
  Emergency as EmergencyIcon,
  Print as PrintIcon,
  Download as DownloadIcon,
  Event as EventIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  ShowChart as ChartIcon,
  Healing as HealingIcon,
  CameraAlt as ImagingIcon,
  Favorite as FavoriteIcon,
} from '@mui/icons-material';
import { setBreadcrumbs, setCurrentPage } from '../../store/slices/uiSlice';

interface TimelineEvent {
  id: string;
  patientId: string;
  patientName: string;
  eventType: 'consultation' | 'lab_result' | 'prescription' | 'procedure' | 'imaging' | 'vaccination' | 'hospitalization' | 'emergency' | 'surgery' | 'diagnosis' | 'allergy' | 'vital_signs';
  category: 'medical' | 'surgical' | 'diagnostic' | 'therapeutic' | 'preventive' | 'emergency';
  title: string;
  description: string;
  date: string;
  endDate?: string; // For events with duration
  providerId: string;
  providerName: string;
  department: string;
  facility?: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  status: 'active' | 'resolved' | 'ongoing' | 'cancelled';
  outcome?: 'improved' | 'stable' | 'worsened' | 'resolved' | 'unknown';
  relatedEvents?: string[]; // IDs of related events
  diagnosis?: string[];
  medications?: string[];
  labValues?: LabValue[];
  vitalSigns?: VitalSigns[];
  images?: string[];
  documents?: string[];
  notes?: string;
  isSignificant: boolean; // Major medical events
  isChronic: boolean;
  tags: string[];
}

interface LabValue {
  name: string;
  value: string;
  unit: string;
  referenceRange: string;
  status: 'normal' | 'abnormal' | 'critical';
  trend?: 'up' | 'down' | 'stable';
}

interface VitalSigns {
  timestamp: string;
  bloodPressureSystolic?: number;
  bloodPressureDiastolic?: number;
  heartRate?: number;
  temperature?: number;
  respiratoryRate?: number;
  oxygenSaturation?: number;
  weight?: number;
  height?: number;
  bmi?: number;
  painLevel?: number;
}

interface Patient {
  id: string;
  name: string;
  dateOfBirth: string;
  age: number;
  gender: string;
  bloodType: string;
  allergies: string[];
  chronicConditions: string[];
  emergencyContact: string;
  primaryPhysician: string;
  insuranceInfo: string;
  medicalRecordNumber: string;
}

const mockTimelineEvents: TimelineEvent[] = [
  {
    id: '1',
    patientId: '1',
    patientName: 'John Smith',
    eventType: 'diagnosis',
    category: 'medical',
    title: 'Hypertension Diagnosis',
    description: 'Initial diagnosis of essential hypertension following elevated blood pressure readings',
    date: '2020-03-15',
    providerId: '1',
    providerName: 'Dr. Sarah Johnson',
    department: 'Internal Medicine',
    facility: 'MediRemind Medical Center',
    severity: 'medium',
    status: 'ongoing',
    outcome: 'stable',
    diagnosis: ['I10 - Essential hypertension'],
    medications: ['Lisinopril 10mg daily'],
    vitalSigns: [{
      timestamp: '2020-03-15',
      bloodPressureSystolic: 150,
      bloodPressureDiastolic: 95,
      heartRate: 78,
    }],
    isSignificant: true,
    isChronic: true,
    tags: ['hypertension', 'chronic-disease', 'cardiovascular'],
  },
  {
    id: '2',
    patientId: '1',
    patientName: 'John Smith',
    eventType: 'lab_result',
    category: 'diagnostic',
    title: 'Comprehensive Metabolic Panel',
    description: 'Routine lab work showing normal kidney function and electrolytes',
    date: '2023-12-15',
    providerId: '1',
    providerName: 'Dr. Sarah Johnson',
    department: 'Laboratory',
    severity: 'low',
    status: 'resolved',
    outcome: 'improved',
    labValues: [
      { name: 'Creatinine', value: '1.0', unit: 'mg/dL', referenceRange: '0.7-1.3', status: 'normal', trend: 'stable' },
      { name: 'BUN', value: '15', unit: 'mg/dL', referenceRange: '7-20', status: 'normal', trend: 'stable' },
      { name: 'Glucose', value: '95', unit: 'mg/dL', referenceRange: '70-100', status: 'normal', trend: 'down' },
      { name: 'Sodium', value: '140', unit: 'mEq/L', referenceRange: '136-145', status: 'normal', trend: 'stable' },
    ],
    isSignificant: false,
    isChronic: false,
    tags: ['lab-results', 'routine', 'metabolic-panel'],
  },
  {
    id: '3',
    patientId: '1',
    patientName: 'John Smith',
    eventType: 'vaccination',
    category: 'preventive',
    title: 'COVID-19 Vaccination (Booster)',
    description: 'COVID-19 booster vaccination administered',
    date: '2023-10-20',
    providerId: '2',
    providerName: 'Nurse Jennifer Wilson',
    department: 'Preventive Care',
    severity: 'low',
    status: 'resolved',
    outcome: 'improved',
    notes: 'No adverse reactions observed. Patient tolerated well.',
    isSignificant: false,
    isChronic: false,
    tags: ['vaccination', 'covid-19', 'preventive-care'],
  },
  {
    id: '4',
    patientId: '1',
    patientName: 'John Smith',
    eventType: 'procedure',
    category: 'diagnostic',
    title: 'Echocardiogram',
    description: 'Cardiac ultrasound to assess heart function and structure',
    date: '2023-08-10',
    providerId: '3',
    providerName: 'Dr. Michael Chen',
    department: 'Cardiology',
    severity: 'medium',
    status: 'resolved',
    outcome: 'stable',
    notes: 'Normal left ventricular function. No significant valvular disease.',
    images: ['echo-report.pdf', 'echo-images.jpg'],
    isSignificant: true,
    isChronic: false,
    tags: ['cardiology', 'echocardiogram', 'heart-function'],
  },
  {
    id: '5',
    patientId: '1',
    patientName: 'John Smith',
    eventType: 'emergency',
    category: 'emergency',
    title: 'Emergency Department Visit - Chest Pain',
    description: 'Presented to ED with acute chest pain, ruled out myocardial infarction',
    date: '2022-11-28',
    endDate: '2022-11-29',
    providerId: '4',
    providerName: 'Dr. Emergency Physician',
    department: 'Emergency Medicine',
    facility: 'MediRemind Emergency Department',
    severity: 'high',
    status: 'resolved',
    outcome: 'resolved',
    diagnosis: ['R06.02 - Shortness of breath'],
    labValues: [
      { name: 'Troponin I', value: '0.02', unit: 'ng/mL', referenceRange: '<0.04', status: 'normal' },
      { name: 'CK-MB', value: '2.1', unit: 'ng/mL', referenceRange: '<6.3', status: 'normal' },
    ],
    notes: 'EKG normal. Chest X-ray clear. Discharged home with follow-up.',
    isSignificant: true,
    isChronic: false,
    tags: ['emergency', 'chest-pain', 'cardiac-workup'],
  },
  {
    id: '6',
    patientId: '1',
    patientName: 'John Smith',
    eventType: 'consultation',
    category: 'medical',
    title: 'Annual Physical Examination',
    description: 'Comprehensive annual physical examination with health maintenance',
    date: '2024-01-20',
    providerId: '1',
    providerName: 'Dr. Sarah Johnson',
    department: 'Internal Medicine',
    severity: 'low',
    status: 'resolved',
    outcome: 'stable',
    vitalSigns: [{
      timestamp: '2024-01-20',
      bloodPressureSystolic: 128,
      bloodPressureDiastolic: 82,
      heartRate: 72,
      temperature: 98.6,
      weight: 180,
      height: 70,
      bmi: 25.8,
    }],
    notes: 'Overall good health. Continue current medications and lifestyle.',
    isSignificant: false,
    isChronic: false,
    tags: ['annual-physical', 'preventive-care', 'health-maintenance'],
  },
];

const mockPatients: Patient[] = [
  {
    id: '1',
    name: 'John Smith',
    dateOfBirth: '1979-05-15',
    age: 45,
    gender: 'Male',
    bloodType: 'O+',
    allergies: ['Penicillin', 'Shellfish'],
    chronicConditions: ['Hypertension'],
    emergencyContact: 'Jane Smith (Wife) - (555) 123-4567',
    primaryPhysician: 'Dr. Sarah Johnson',
    insuranceInfo: 'Blue Cross Blue Shield - Policy #12345',
    medicalRecordNumber: 'MRN-001234',
  },
];

export const MedicalHistoryTimelinePage: React.FC = () => {
  const dispatch = useDispatch();
  const [events] = useState<TimelineEvent[]>(mockTimelineEvents);
  const [filteredEvents, setFilteredEvents] = useState<TimelineEvent[]>(mockTimelineEvents);
  const [selectedPatient] = useState<Patient | null>(mockPatients[0]);
  const [searchTerm, setSearchTerm] = useState('');
  const [eventTypeFilter, setEventTypeFilter] = useState('all');
  const [categoryFilter, setCategoryFilter] = useState('all');
  const [severityFilter, setSeverityFilter] = useState('all');
  const [statusFilter] = useState('all');
  const [dateRangeFilter, setDateRangeFilter] = useState('all');
  const [showSignificantOnly, setShowSignificantOnly] = useState(false);
  const [showChronicOnly, setShowChronicOnly] = useState(false);
  const [selectedEvent, setSelectedEvent] = useState<TimelineEvent | null>(null);
  const [viewDialogOpen, setViewDialogOpen] = useState(false);
  const [timelineView, setTimelineView] = useState<'detailed' | 'compact'>('detailed');

  useEffect(() => {
    dispatch(setBreadcrumbs([
      { label: 'Dashboard', path: '/dashboard' },
      { label: 'Medical Records', path: '/medical' },
      { label: 'Medical History Timeline', path: '/medical/timeline' },
    ]));
    dispatch(setCurrentPage('Medical History Timeline'));
  }, [dispatch]);

  useEffect(() => {
    let filtered = events;

    // Filter by selected patient
    if (selectedPatient) {
      filtered = filtered.filter(event => event.patientId === selectedPatient.id);
    }

    if (searchTerm) {
      filtered = filtered.filter(
        (event) =>
          event.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
          event.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
          event.providerName.toLowerCase().includes(searchTerm.toLowerCase()) ||
          event.department.toLowerCase().includes(searchTerm.toLowerCase()) ||
          event.tags.some(tag => tag.toLowerCase().includes(searchTerm.toLowerCase()))
      );
    }

    if (eventTypeFilter !== 'all') {
      filtered = filtered.filter((event) => event.eventType === eventTypeFilter);
    }

    if (categoryFilter !== 'all') {
      filtered = filtered.filter((event) => event.category === categoryFilter);
    }

    if (severityFilter !== 'all') {
      filtered = filtered.filter((event) => event.severity === severityFilter);
    }

    if (statusFilter !== 'all') {
      filtered = filtered.filter((event) => event.status === statusFilter);
    }

    if (showSignificantOnly) {
      filtered = filtered.filter((event) => event.isSignificant);
    }

    if (showChronicOnly) {
      filtered = filtered.filter((event) => event.isChronic);
    }

    // Date range filtering
    if (dateRangeFilter !== 'all') {
      const now = new Date();
      let cutoffDate = new Date();
      
      switch (dateRangeFilter) {
        case '1month':
          cutoffDate.setMonth(now.getMonth() - 1);
          break;
        case '3months':
          cutoffDate.setMonth(now.getMonth() - 3);
          break;
        case '6months':
          cutoffDate.setMonth(now.getMonth() - 6);
          break;
        case '1year':
          cutoffDate.setFullYear(now.getFullYear() - 1);
          break;
        case '2years':
          cutoffDate.setFullYear(now.getFullYear() - 2);
          break;
      }
      
      filtered = filtered.filter(event => new Date(event.date) >= cutoffDate);
    }

    // Sort by date (most recent first)
    filtered.sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());

    setFilteredEvents(filtered);
  }, [events, selectedPatient, searchTerm, eventTypeFilter, categoryFilter, severityFilter, statusFilter, dateRangeFilter, showSignificantOnly, showChronicOnly]);

  const getEventTypeIcon = (type: string) => {
    switch (type) {
      case 'consultation': return <MedicalIcon />;
      case 'lab_result': return <LabIcon />;
      case 'prescription': return <MedicationIcon />;
      case 'procedure': return <HospitalIcon />;
      case 'imaging': return <ImagingIcon />;
      case 'vaccination': return <VaccineIcon />;
      case 'hospitalization': return <HospitalIcon />;
      case 'emergency': return <EmergencyIcon />;
      case 'surgery': return <HealingIcon />;
      case 'diagnosis': return <RecordIcon />;
      case 'allergy': return <WarningIcon />;
      case 'vital_signs': return <VitalsIcon />;
      default: return <EventIcon />;
    }
  };

  const getEventTypeLabel = (type: string) => {
    switch (type) {
      case 'consultation': return 'Consultation';
      case 'lab_result': return 'Lab Result';
      case 'prescription': return 'Prescription';
      case 'procedure': return 'Procedure';
      case 'imaging': return 'Imaging';
      case 'vaccination': return 'Vaccination';
      case 'hospitalization': return 'Hospitalization';
      case 'emergency': return 'Emergency';
      case 'surgery': return 'Surgery';
      case 'diagnosis': return 'Diagnosis';
      case 'allergy': return 'Allergy';
      case 'vital_signs': return 'Vital Signs';
      default: return type;
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'error';
      case 'high': return 'warning';
      case 'medium': return 'info';
      case 'low': return 'success';
      default: return 'default';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'resolved': return 'success';
      case 'active': return 'primary';
      case 'ongoing': return 'info';
      case 'cancelled': return 'error';
      default: return 'default';
    }
  };

  const getOutcomeIcon = (outcome?: string) => {
    switch (outcome) {
      case 'improved': return <TrendingUpIcon color="success" />;
      case 'worsened': return <TrendingDownIcon color="error" />;
      case 'stable': return <ChartIcon color="info" />;
      case 'resolved': return <CheckCircleIcon color="success" />;
      default: return null;
    }
  };

  const getLabValueTrendIcon = (trend?: string) => {
    switch (trend) {
      case 'up': return <TrendingUpIcon fontSize="small" />;
      case 'down': return <TrendingDownIcon fontSize="small" />;
      case 'stable': return <ChartIcon fontSize="small" />;
      default: return <ChartIcon fontSize="small" />; // Default to chart icon instead of null
    }
  };

  const handleViewEvent = (event: TimelineEvent) => {
    setSelectedEvent(event);
    setViewDialogOpen(true);
  };

  const getTimelineStats = () => {
    const total = filteredEvents.length;
    const significant = filteredEvents.filter(e => e.isSignificant).length;
    const chronic = filteredEvents.filter(e => e.isChronic).length;
    const emergency = filteredEvents.filter(e => e.category === 'emergency').length;
    const recent = filteredEvents.filter(e => {
      const eventDate = new Date(e.date);
      const thirtyDaysAgo = new Date();
      thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
      return eventDate >= thirtyDaysAgo;
    }).length;

    return { total, significant, chronic, emergency, recent };
  };

  const stats = getTimelineStats();

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">
          Medical History Timeline
        </Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            variant="outlined"
            startIcon={<PrintIcon />}
          >
            Print Timeline
          </Button>
          <Button
            variant="outlined"
            startIcon={<DownloadIcon />}
          >
            Export Timeline
          </Button>
        </Box>
      </Box>

      {/* Patient Info Card */}
      {selectedPatient && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Grid container spacing={3}>
              <Grid size={{ xs: 12, md: 3 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  <Avatar sx={{ width: 64, height: 64, fontSize: '1.5rem' }}>
                    {selectedPatient.name.charAt(0)}
                  </Avatar>
                  <Box>
                    <Typography variant="h6">
                      {selectedPatient.name}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      MRN: {selectedPatient.medicalRecordNumber}
                    </Typography>
                  </Box>
                </Box>
              </Grid>
              <Grid size={{ xs: 12, md: 3 }}>
                <Typography variant="body2" gutterBottom>
                  <strong>Age:</strong> {selectedPatient.age} years
                </Typography>
                <Typography variant="body2" gutterBottom>
                  <strong>Gender:</strong> {selectedPatient.gender}
                </Typography>
                <Typography variant="body2" gutterBottom>
                  <strong>Blood Type:</strong> {selectedPatient.bloodType}
                </Typography>
              </Grid>
              <Grid size={{ xs: 12, md: 3 }}>
                <Typography variant="body2" gutterBottom>
                  <strong>Primary Physician:</strong> {selectedPatient.primaryPhysician}
                </Typography>
                <Typography variant="body2" gutterBottom>
                  <strong>DOB:</strong> {new Date(selectedPatient.dateOfBirth).toLocaleDateString()}
                </Typography>
              </Grid>
              <Grid size={{ xs: 12, md: 3 }}>
                {selectedPatient.allergies.length > 0 && (
                  <Box>
                    <Typography variant="body2" color="error" gutterBottom>
                      <strong>Allergies:</strong>
                    </Typography>
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                      {selectedPatient.allergies.map((allergy, index) => (
                        <Chip
                          key={index}
                          label={allergy}
                          size="small"
                          color="error"
                          icon={<WarningIcon />}
                        />
                      ))}
                    </Box>
                  </Box>
                )}
                {selectedPatient.chronicConditions.length > 0 && (
                  <Box sx={{ mt: 1 }}>
                    <Typography variant="body2" color="warning.main" gutterBottom>
                      <strong>Chronic Conditions:</strong>
                    </Typography>
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                      {selectedPatient.chronicConditions.map((condition, index) => (
                        <Chip
                          key={index}
                          label={condition}
                          size="small"
                          color="warning"
                        />
                      ))}
                    </Box>
                  </Box>
                )}
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      )}

      {/* Stats Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid size={{ xs: 12, sm: 6, md: 2.4 }}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Total Events
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
                Significant Events
              </Typography>
              <Typography variant="h4" color="primary">
                {stats.significant}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 2.4 }}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Chronic Conditions
              </Typography>
              <Typography variant="h4" color="warning.main">
                {stats.chronic}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 2.4 }}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Emergency Events
              </Typography>
              <Typography variant="h4" color="error.main">
                {stats.emergency}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 2.4 }}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Recent (30 days)
              </Typography>
              <Typography variant="h4" color="info.main">
                {stats.recent}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Filters */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Timeline Filters
        </Typography>
        <Grid container spacing={2}>
          <Grid size={{ xs: 12, md: 3 }}>
            <TextField
              fullWidth
              placeholder="Search timeline..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon />
                  </InputAdornment>
                ),
              }}
            />
          </Grid>
          <Grid size={{ xs: 12, md: 2 }}>
            <FormControl fullWidth>
              <InputLabel>Event Type</InputLabel>
              <Select
                value={eventTypeFilter}
                label="Event Type"
                onChange={(e) => setEventTypeFilter(e.target.value)}
              >
                <MenuItem value="all">All Types</MenuItem>
                <MenuItem value="consultation">Consultation</MenuItem>
                <MenuItem value="lab_result">Lab Result</MenuItem>
                <MenuItem value="prescription">Prescription</MenuItem>
                <MenuItem value="procedure">Procedure</MenuItem>
                <MenuItem value="imaging">Imaging</MenuItem>
                <MenuItem value="vaccination">Vaccination</MenuItem>
                <MenuItem value="emergency">Emergency</MenuItem>
                <MenuItem value="surgery">Surgery</MenuItem>
                <MenuItem value="diagnosis">Diagnosis</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid size={{ xs: 12, md: 2 }}>
            <FormControl fullWidth>
              <InputLabel>Category</InputLabel>
              <Select
                value={categoryFilter}
                label="Category"
                onChange={(e) => setCategoryFilter(e.target.value)}
              >
                <MenuItem value="all">All Categories</MenuItem>
                <MenuItem value="medical">Medical</MenuItem>
                <MenuItem value="surgical">Surgical</MenuItem>
                <MenuItem value="diagnostic">Diagnostic</MenuItem>
                <MenuItem value="therapeutic">Therapeutic</MenuItem>
                <MenuItem value="preventive">Preventive</MenuItem>
                <MenuItem value="emergency">Emergency</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid size={{ xs: 12, md: 2 }}>
            <FormControl fullWidth>
              <InputLabel>Severity</InputLabel>
              <Select
                value={severityFilter}
                label="Severity"
                onChange={(e) => setSeverityFilter(e.target.value)}
              >
                <MenuItem value="all">All Severity</MenuItem>
                <MenuItem value="critical">Critical</MenuItem>
                <MenuItem value="high">High</MenuItem>
                <MenuItem value="medium">Medium</MenuItem>
                <MenuItem value="low">Low</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid size={{ xs: 12, md: 2 }}>
            <FormControl fullWidth>
              <InputLabel>Time Range</InputLabel>
              <Select
                value={dateRangeFilter}
                label="Time Range"
                onChange={(e) => setDateRangeFilter(e.target.value)}
              >
                <MenuItem value="all">All Time</MenuItem>
                <MenuItem value="1month">Last Month</MenuItem>
                <MenuItem value="3months">Last 3 Months</MenuItem>
                <MenuItem value="6months">Last 6 Months</MenuItem>
                <MenuItem value="1year">Last Year</MenuItem>
                <MenuItem value="2years">Last 2 Years</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid size={{ xs: 12, md: 1 }}>
             <Stack spacing={1}>
               <Button
                 variant={showSignificantOnly ? 'contained' : 'outlined'}
                 size="small"
                 onClick={() => setShowSignificantOnly(!showSignificantOnly)}
               >
                 Significant
               </Button>
               <Button
                 variant={showChronicOnly ? 'contained' : 'outlined'}
                 size="small"
                 onClick={() => setShowChronicOnly(!showChronicOnly)}
               >
                 Chronic
               </Button>
             </Stack>
           </Grid>
        </Grid>
      </Paper>

      {/* Timeline */}
      <Paper sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
          <Typography variant="h6">
            Medical Timeline ({filteredEvents.length} events)
          </Typography>
          <FormControl size="small">
            <InputLabel>View</InputLabel>
            <Select
              value={timelineView}
              label="View"
              onChange={(e) => setTimelineView(e.target.value as 'detailed' | 'compact')}
            >
              <MenuItem value="detailed">Detailed View</MenuItem>
              <MenuItem value="compact">Compact View</MenuItem>
            </Select>
          </FormControl>
        </Box>

        {filteredEvents.length === 0 ? (
          <Alert severity="info">
            No events found matching the current filters.
          </Alert>
        ) : (
          <Timeline>
            {filteredEvents.map((event, index) => (
              <TimelineItem key={event.id}>
                <TimelineOppositeContent color="text.secondary" sx={{ flex: 0.2 }}>
                  <Typography variant="body2">
                    {new Date(event.date).toLocaleDateString()}
                  </Typography>
                  {event.endDate && (
                    <Typography variant="caption">
                      to {new Date(event.endDate).toLocaleDateString()}
                    </Typography>
                  )}
                </TimelineOppositeContent>
                <TimelineSeparator>
                  <TimelineDot color={getSeverityColor(event.severity) as any}>
                    {event.isSignificant ? (
                      <Badge badgeContent="!" color="error">
                        {getEventTypeIcon(event.eventType)}
                      </Badge>
                    ) : (
                      getEventTypeIcon(event.eventType)
                    )}
                  </TimelineDot>
                  {index < filteredEvents.length - 1 && <TimelineConnector />}
                </TimelineSeparator>
                <TimelineContent sx={{ flex: 0.8 }}>
                  <Card 
                    sx={{ 
                      mb: 2, 
                      cursor: 'pointer',
                      '&:hover': { boxShadow: 3 }
                    }}
                    onClick={() => handleViewEvent(event)}
                  >
                    <CardContent>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
                        <Box sx={{ flex: 1 }}>
                          <Typography variant="h6" gutterBottom>
                            {event.title}
                          </Typography>
                          <Typography variant="body2" color="text.secondary" gutterBottom>
                            {event.description}
                          </Typography>
                        </Box>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          {getOutcomeIcon(event.outcome)}
                          <Chip
                            label={event.status}
                            color={getStatusColor(event.status) as any}
                            size="small"
                          />
                        </Box>
                      </Box>
                      
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                        <Typography variant="body2">
                          <strong>{event.providerName}</strong> - {event.department}
                        </Typography>
                        <Box sx={{ display: 'flex', gap: 0.5 }}>
                          <Chip
                            label={getEventTypeLabel(event.eventType)}
                            size="small"
                            variant="outlined"
                          />
                          <Chip
                            label={event.category}
                            size="small"
                            variant="outlined"
                          />
                          {event.isSignificant && (
                            <Chip
                              label="Significant"
                              size="small"
                              color="primary"
                            />
                          )}
                          {event.isChronic && (
                            <Chip
                              label="Chronic"
                              size="small"
                              color="warning"
                            />
                          )}
                        </Box>
                      </Box>

                      {timelineView === 'detailed' && (
                        <>
                          {/* Lab Values Preview */}
                          {event.labValues && event.labValues.length > 0 && (
                            <Box sx={{ mt: 2 }}>
                              <Typography variant="subtitle2" gutterBottom>
                                Lab Values:
                              </Typography>
                              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                                {event.labValues.slice(0, 3).map((lab, idx) => (
                                  <Chip
                                    key={idx}
                                    label={`${lab.name}: ${lab.value} ${lab.unit}`}
                                    size="small"
                                    color={lab.status === 'normal' ? 'success' : lab.status === 'critical' ? 'error' : 'warning'}
                                    icon={getLabValueTrendIcon(lab.trend)}
                                  />
                                ))}
                                {event.labValues.length > 3 && (
                                  <Chip
                                    label={`+${event.labValues.length - 3} more`}
                                    size="small"
                                    variant="outlined"
                                  />
                                )}
                              </Box>
                            </Box>
                          )}

                          {/* Vital Signs Preview */}
                          {event.vitalSigns && event.vitalSigns.length > 0 && (
                            <Box sx={{ mt: 2 }}>
                              <Typography variant="subtitle2" gutterBottom>
                                Vital Signs:
                              </Typography>
                              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                                {event.vitalSigns[0].bloodPressureSystolic && (
                                  <Chip
                                    label={`BP: ${event.vitalSigns[0].bloodPressureSystolic}/${event.vitalSigns[0].bloodPressureDiastolic}`}
                                    size="small"
                                    icon={<VitalsIcon />}
                                  />
                                )}
                                {event.vitalSigns[0].heartRate && (
                                  <Chip
                                    label={`HR: ${event.vitalSigns[0].heartRate} bpm`}
                                    size="small"
                                    icon={<FavoriteIcon />}
                                  />
                                )}
                                {event.vitalSigns[0].temperature && (
                                  <Chip
                                    label={`Temp: ${event.vitalSigns[0].temperature}°F`}
                                    size="small"
                                  />
                                )}
                              </Box>
                            </Box>
                          )}

                          {/* Tags */}
                          {event.tags.length > 0 && (
                            <Box sx={{ mt: 2 }}>
                              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                                {event.tags.slice(0, 4).map((tag, idx) => (
                                  <Chip
                                    key={idx}
                                    label={tag}
                                    size="small"
                                    variant="outlined"
                                  />
                                ))}
                                {event.tags.length > 4 && (
                                  <Chip
                                    label={`+${event.tags.length - 4}`}
                                    size="small"
                                    variant="outlined"
                                  />
                                )}
                              </Box>
                            </Box>
                          )}
                        </>
                      )}
                    </CardContent>
                  </Card>
                </TimelineContent>
              </TimelineItem>
            ))}
          </Timeline>
        )}
      </Paper>

      {/* Event Details Dialog */}
      <Dialog
        open={viewDialogOpen}
        onClose={() => setViewDialogOpen(false)}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle>
          {selectedEvent?.title}
        </DialogTitle>
        <DialogContent>
          {selectedEvent && (
            <Box sx={{ mt: 2 }}>
              <Grid container spacing={3}>
                <Grid size={{ xs: 12, md: 6 }}>
                  <Typography variant="h6" gutterBottom>
                    Event Information
                  </Typography>
                  <Typography><strong>Type:</strong> {getEventTypeLabel(selectedEvent.eventType)}</Typography>
                  <Typography><strong>Category:</strong> {selectedEvent.category}</Typography>
                  <Typography><strong>Date:</strong> {new Date(selectedEvent.date).toLocaleDateString()}</Typography>
                  {selectedEvent.endDate && (
                    <Typography><strong>End Date:</strong> {new Date(selectedEvent.endDate).toLocaleDateString()}</Typography>
                  )}
                  <Typography><strong>Provider:</strong> {selectedEvent.providerName}</Typography>
                  <Typography><strong>Department:</strong> {selectedEvent.department}</Typography>
                  {selectedEvent.facility && (
                    <Typography><strong>Facility:</strong> {selectedEvent.facility}</Typography>
                  )}
                </Grid>
                <Grid size={{ xs: 12, md: 6 }}>
                  <Typography variant="h6" gutterBottom>
                    Status & Severity
                  </Typography>
                  <Typography><strong>Status:</strong> 
                    <Chip
                      label={selectedEvent.status}
                      color={getStatusColor(selectedEvent.status) as any}
                      size="small"
                      sx={{ ml: 1 }}
                    />
                  </Typography>
                  <Typography><strong>Severity:</strong> 
                    <Chip
                      label={selectedEvent.severity}
                      color={getSeverityColor(selectedEvent.severity) as any}
                      size="small"
                      sx={{ ml: 1 }}
                    />
                  </Typography>
                  {selectedEvent.outcome && (
                    <Typography><strong>Outcome:</strong> 
                      <Box sx={{ display: 'inline-flex', alignItems: 'center', ml: 1 }}>
                        {getOutcomeIcon(selectedEvent.outcome)}
                        <Typography sx={{ ml: 0.5 }}>{selectedEvent.outcome}</Typography>
                      </Box>
                    </Typography>
                  )}
                  <Typography><strong>Significant:</strong> {selectedEvent.isSignificant ? 'Yes' : 'No'}</Typography>
                  <Typography><strong>Chronic:</strong> {selectedEvent.isChronic ? 'Yes' : 'No'}</Typography>
                </Grid>
                <Grid size={{ xs: 12 }}>
                  <Typography variant="h6" gutterBottom>
                    Description
                  </Typography>
                  <Typography>{selectedEvent.description}</Typography>
                </Grid>
                {selectedEvent.diagnosis && selectedEvent.diagnosis.length > 0 && (
                  <Grid size={{ xs: 12 }}>
                    <Typography variant="h6" gutterBottom>
                      Diagnosis
                    </Typography>
                    {selectedEvent.diagnosis.map((diag, index) => (
                      <Typography key={index}>• {diag}</Typography>
                    ))}
                  </Grid>
                )}
                {selectedEvent.medications && selectedEvent.medications.length > 0 && (
                  <Grid size={{ xs: 12 }}>
                    <Typography variant="h6" gutterBottom>
                      Medications
                    </Typography>
                    {selectedEvent.medications.map((med, index) => (
                      <Typography key={index}>• {med}</Typography>
                    ))}
                  </Grid>
                )}
                {selectedEvent.labValues && selectedEvent.labValues.length > 0 && (
                  <Grid size={{ xs: 12 }}>
                    <Typography variant="h6" gutterBottom>
                      Lab Values
                    </Typography>
                    <Grid container spacing={2}>
                      {selectedEvent.labValues.map((lab, index) => (
                        <Grid size={{ xs: 12, sm: 6, md: 4 }} key={index}>
                          <Card variant="outlined">
                            <CardContent>
                              <Typography variant="subtitle2">{lab.name}</Typography>
                              <Typography variant="h6">
                                {lab.value} {lab.unit}
                                {getLabValueTrendIcon(lab.trend)}
                              </Typography>
                              <Typography variant="caption" color="text.secondary">
                                Reference: {lab.referenceRange}
                              </Typography>
                              <Chip
                                label={lab.status}
                                size="small"
                                color={lab.status === 'normal' ? 'success' : lab.status === 'critical' ? 'error' : 'warning'}
                                sx={{ mt: 1 }}
                              />
                            </CardContent>
                          </Card>
                        </Grid>
                      ))}
                    </Grid>
                  </Grid>
                )}
                {selectedEvent.vitalSigns && selectedEvent.vitalSigns.length > 0 && (
                  <Grid size={{ xs: 12 }}>
                    <Typography variant="h6" gutterBottom>
                      Vital Signs
                    </Typography>
                    {selectedEvent.vitalSigns.map((vitals, index) => (
                      <Card key={index} variant="outlined" sx={{ mb: 2 }}>
                        <CardContent>
                          <Typography variant="subtitle2" gutterBottom>
                            {new Date(vitals.timestamp).toLocaleString()}
                          </Typography>
                          <Grid container spacing={2}>
                            {vitals.bloodPressureSystolic && (
                              <Grid size={{ xs: 6, sm: 4, md: 3 }}>
                                <Typography><strong>Blood Pressure:</strong> {vitals.bloodPressureSystolic}/{vitals.bloodPressureDiastolic}</Typography>
                              </Grid>
                            )}
                            {vitals.heartRate && (
                              <Grid size={{ xs: 6, sm: 4, md: 3 }}>
                                <Typography><strong>Heart Rate:</strong> {vitals.heartRate} bpm</Typography>
                              </Grid>
                            )}
                            {vitals.temperature && (
                              <Grid size={{ xs: 6, sm: 4, md: 3 }}>
                                <Typography><strong>Temperature:</strong> {vitals.temperature}°F</Typography>
                              </Grid>
                            )}
                            {vitals.respiratoryRate && (
                              <Grid size={{ xs: 6, sm: 4, md: 3 }}>
                                <Typography><strong>Respiratory Rate:</strong> {vitals.respiratoryRate}/min</Typography>
                              </Grid>
                            )}
                            {vitals.oxygenSaturation && (
                              <Grid size={{ xs: 6, sm: 4, md: 3 }}>
                                <Typography><strong>O2 Saturation:</strong> {vitals.oxygenSaturation}%</Typography>
                              </Grid>
                            )}
                            {vitals.weight && (
                              <Grid size={{ xs: 6, sm: 4, md: 3 }}>
                                <Typography><strong>Weight:</strong> {vitals.weight} lbs</Typography>
                              </Grid>
                            )}
                            {vitals.height && (
                              <Grid size={{ xs: 6, sm: 4, md: 3 }}>
                                <Typography><strong>Height:</strong> {vitals.height} in</Typography>
                              </Grid>
                            )}
                            {vitals.bmi && (
                              <Grid size={{ xs: 6, sm: 4, md: 3 }}>
                                <Typography><strong>BMI:</strong> {vitals.bmi}</Typography>
                              </Grid>
                            )}
                          </Grid>
                        </CardContent>
                      </Card>
                    ))}
                  </Grid>
                )}
                {selectedEvent.notes && (
                  <Grid size={{ xs: 12 }}>
                    <Typography variant="h6" gutterBottom>
                      Notes
                    </Typography>
                    <Typography>{selectedEvent.notes}</Typography>
                  </Grid>
                )}
                {selectedEvent.tags.length > 0 && (
                  <Grid size={{ xs: 12 }}>
                    <Typography variant="h6" gutterBottom>
                      Tags
                    </Typography>
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                      {selectedEvent.tags.map((tag, index) => (
                        <Chip key={index} label={tag} size="small" />
                      ))}
                    </Box>
                  </Grid>
                )}
                {(selectedEvent.images?.length || selectedEvent.documents?.length) && (
                  <Grid size={{ xs: 12 }}>
                    <Typography variant="h6" gutterBottom>
                      Attachments
                    </Typography>
                    <List>
                      {selectedEvent.images?.map((image, index) => (
                        <ListItem key={index}>
                          <ListItemIcon>
                            <ImagingIcon />
                          </ListItemIcon>
                          <ListItemText primary={image} secondary="Image" />
                        </ListItem>
                      ))}
                      {selectedEvent.documents?.map((doc, index) => (
                        <ListItem key={index}>
                          <ListItemIcon>
                            <AttachFileIcon />
                          </ListItemIcon>
                          <ListItemText primary={doc} secondary="Document" />
                        </ListItem>
                      ))}
                    </List>
                  </Grid>
                )}
              </Grid>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setViewDialogOpen(false)}>Close</Button>
          <Button variant="outlined" startIcon={<PrintIcon />}>
            Print Event
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};