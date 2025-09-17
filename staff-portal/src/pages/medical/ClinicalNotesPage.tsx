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
  TextareaAutosize,
  FormControlLabel,
  Checkbox,
  RadioGroup,
  Radio,
  Autocomplete,
  Stack,
} from '@mui/material';
import Grid from '@mui/material/Grid';
import {
  Search as SearchIcon,
  Add as AddIcon,
  FilterList as FilterIcon,
  Note as NoteIcon,
  Assignment as AssignmentIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Save as SaveIcon,
  Cancel as CancelIcon,
  Visibility as VisibilityIcon,
  Person as PersonIcon,
  CalendarToday as CalendarIcon,
  AccessTime as TimeIcon,
  MedicalServices as MedicalIcon,
  Psychology as PsychologyIcon,
  LocalHospital as HospitalIcon,
  Healing as HealingIcon,
  ExpandMore as ExpandMoreIcon,
  Print as PrintIcon,
  Share as ShareIcon,
  Lock as LockIcon,
  LockOpen as LockOpenIcon,
  Star as StarIcon,
  StarBorder as StarBorderIcon,
  Flag as FlagIcon,
  AttachFile as AttachFileIcon,
  VoiceChat as VoiceChatIcon,
  Mic as MicIcon,
  Stop as StopIcon,
  PlayArrow as PlayIcon,
} from '@mui/icons-material';
import { setBreadcrumbs, setCurrentPage } from '../../store/slices/uiSlice';

interface ClinicalNote {
  id: string;
  patientId: string;
  patientName: string;
  patientAge: number;
  patientGender: string;
  appointmentId?: string;
  noteType: 'progress' | 'assessment' | 'plan' | 'soap' | 'consultation' | 'discharge' | 'admission' | 'procedure';
  title: string;
  content: string;
  chiefComplaint?: string;
  historyOfPresentIllness?: string;
  physicalExamination?: string;
  assessment?: string;
  plan?: string;
  subjective?: string;
  objective?: string;
  providerId: string;
  providerName: string;
  department: string;
  specialty: string;
  date: string;
  lastModified: string;
  status: 'draft' | 'completed' | 'signed' | 'amended' | 'deleted';
  priority: 'routine' | 'urgent' | 'stat';
  isConfidential: boolean;
  isStarred: boolean;
  isFlagged: boolean;
  tags: string[];
  attachments: string[];
  voiceNotes: string[];
  templateUsed?: string;
  signedBy?: string;
  signedDate?: string;
  amendments?: Amendment[];
  sharedWith: string[];
  accessLevel: 'public' | 'restricted' | 'confidential';
}

interface Amendment {
  id: string;
  date: string;
  amendedBy: string;
  reason: string;
  changes: string;
}

interface NoteTemplate {
  id: string;
  name: string;
  type: string;
  specialty: string;
  content: string;
  fields: TemplateField[];
}

interface TemplateField {
  name: string;
  type: 'text' | 'textarea' | 'select' | 'checkbox' | 'radio';
  label: string;
  required: boolean;
  options?: string[];
  defaultValue?: string;
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
      id={`notes-tabpanel-${index}`}
      aria-labelledby={`notes-tab-${index}`}
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

const mockClinicalNotes: ClinicalNote[] = [
  {
    id: '1',
    patientId: '1',
    patientName: 'John Smith',
    patientAge: 45,
    patientGender: 'Male',
    appointmentId: 'apt-001',
    noteType: 'soap',
    title: 'Annual Physical Examination - SOAP Note',
    content: 'Complete SOAP note for annual physical examination',
    chiefComplaint: 'Annual physical examination, no specific complaints',
    subjective: 'Patient reports feeling well overall. No new symptoms or concerns. Continues regular exercise routine and healthy diet. No changes in medications.',
    objective: 'Vital signs stable. Physical examination unremarkable. All systems reviewed and normal.',
    assessment: 'Healthy 45-year-old male with no acute concerns. Continue current health maintenance.',
    plan: 'Continue current lifestyle. Return in 1 year for next annual physical. Routine lab work ordered.',
    providerId: '1',
    providerName: 'Dr. Sarah Johnson',
    department: 'Internal Medicine',
    specialty: 'Internal Medicine',
    date: '2024-01-20',
    lastModified: '2024-01-20',
    status: 'signed',
    priority: 'routine',
    isConfidential: false,
    isStarred: false,
    isFlagged: false,
    tags: ['annual-physical', 'preventive-care'],
    attachments: [],
    voiceNotes: [],
    signedBy: 'Dr. Sarah Johnson',
    signedDate: '2024-01-20',
    amendments: [],
    sharedWith: [],
    accessLevel: 'public',
  },
  {
    id: '2',
    patientId: '2',
    patientName: 'Sarah Johnson',
    patientAge: 32,
    patientGender: 'Female',
    noteType: 'progress',
    title: 'Follow-up Visit - Hypertension Management',
    content: 'Progress note for hypertension follow-up visit',
    chiefComplaint: 'Follow-up for hypertension management',
    historyOfPresentIllness: 'Patient returns for routine follow-up of hypertension. Reports good compliance with medications. Home BP readings averaging 130/85.',
    physicalExamination: 'BP 128/82, HR 68, regular. Cardiovascular exam normal. No peripheral edema.',
    assessment: 'Hypertension, well-controlled on current regimen',
    plan: 'Continue current antihypertensive therapy. Return in 3 months. Continue home BP monitoring.',
    providerId: '1',
    providerName: 'Dr. Sarah Johnson',
    department: 'Internal Medicine',
    specialty: 'Cardiology',
    date: '2024-01-22',
    lastModified: '2024-01-22',
    status: 'completed',
    priority: 'routine',
    isConfidential: false,
    isStarred: true,
    isFlagged: false,
    tags: ['hypertension', 'follow-up', 'chronic-care'],
    attachments: ['bp-log.pdf'],
    voiceNotes: [],
    amendments: [],
    sharedWith: ['cardiology-team'],
    accessLevel: 'public',
  },
  {
    id: '3',
    patientId: '3',
    patientName: 'Michael Brown',
    patientAge: 58,
    patientGender: 'Male',
    noteType: 'consultation',
    title: 'Endocrinology Consultation - Diabetes Management',
    content: 'Consultation note for diabetes management and medication adjustment',
    chiefComplaint: 'Diabetes management consultation',
    historyOfPresentIllness: 'Patient with Type 2 DM for 10 years. Recent HbA1c 8.2%. Reports difficulty with glucose control despite medication compliance.',
    physicalExamination: 'Well-appearing male. BMI 28. Diabetic foot exam normal. No signs of neuropathy.',
    assessment: 'Type 2 diabetes mellitus, suboptimal control. Consider medication adjustment.',
    plan: 'Increase metformin dose. Add GLP-1 agonist. Diabetes education referral. Follow-up in 6 weeks.',
    providerId: '3',
    providerName: 'Dr. Emily Davis',
    department: 'Endocrinology',
    specialty: 'Endocrinology',
    date: '2024-01-25',
    lastModified: '2024-01-25',
    status: 'signed',
    priority: 'urgent',
    isConfidential: false,
    isStarred: false,
    isFlagged: true,
    tags: ['diabetes', 'consultation', 'medication-adjustment'],
    attachments: ['hba1c-results.pdf', 'glucose-log.xlsx'],
    voiceNotes: ['consultation-summary.mp3'],
    signedBy: 'Dr. Emily Davis',
    signedDate: '2024-01-25',
    amendments: [],
    sharedWith: ['primary-care', 'diabetes-educator'],
    accessLevel: 'public',
  },
  {
    id: '4',
    patientId: '4',
    patientName: 'Emily Davis',
    patientAge: 28,
    patientGender: 'Female',
    noteType: 'procedure',
    title: 'Minor Surgical Procedure - Skin Lesion Removal',
    content: 'Procedure note for benign skin lesion removal',
    chiefComplaint: 'Skin lesion removal',
    historyOfPresentIllness: 'Patient presents with 1cm pigmented lesion on left shoulder, present for 6 months with recent changes.',
    physicalExamination: 'Well-demarcated 1cm pigmented lesion on left posterior shoulder. No surrounding inflammation.',
    assessment: 'Benign appearing pigmented lesion, excision recommended for histologic evaluation.',
    plan: 'Excisional biopsy performed. Specimen sent to pathology. Wound care instructions provided. Follow-up in 2 weeks.',
    providerId: '4',
    providerName: 'Dr. Robert Wilson',
    department: 'Dermatology',
    specialty: 'Dermatology',
    date: '2024-01-28',
    lastModified: '2024-01-28',
    status: 'completed',
    priority: 'routine',
    isConfidential: false,
    isStarred: false,
    isFlagged: false,
    tags: ['procedure', 'biopsy', 'dermatology'],
    attachments: ['procedure-photos.jpg', 'pathology-request.pdf'],
    voiceNotes: [],
    amendments: [],
    sharedWith: ['pathology'],
    accessLevel: 'public',
  },
  {
    id: '5',
    patientId: '5',
    patientName: 'Robert Wilson',
    patientAge: 65,
    patientGender: 'Male',
    noteType: 'assessment',
    title: 'Psychiatric Assessment - Depression Screening',
    content: 'Mental health assessment and depression screening',
    chiefComplaint: 'Depression screening and mental health evaluation',
    historyOfPresentIllness: 'Patient reports feeling down and loss of interest in activities for past 2 months. Sleep disturbances and decreased appetite.',
    physicalExamination: 'Mental status exam: Alert and oriented. Mood depressed, affect congruent. No suicidal ideation.',
    assessment: 'Major depressive disorder, moderate severity. PHQ-9 score: 14.',
    plan: 'Initiate SSRI therapy. Counseling referral. Safety assessment completed. Follow-up in 2 weeks.',
    providerId: '5',
    providerName: 'Dr. Lisa Chen',
    department: 'Psychiatry',
    specialty: 'Psychiatry',
    date: '2024-01-30',
    lastModified: '2024-01-30',
    status: 'draft',
    priority: 'urgent',
    isConfidential: true,
    isStarred: true,
    isFlagged: true,
    tags: ['mental-health', 'depression', 'assessment'],
    attachments: ['phq9-score.pdf'],
    voiceNotes: [],
    amendments: [],
    sharedWith: ['mental-health-team'],
    accessLevel: 'confidential',
  },
];

const mockNoteTemplates: NoteTemplate[] = [
  {
    id: '1',
    name: 'SOAP Note Template',
    type: 'soap',
    specialty: 'General',
    content: 'Standard SOAP note template',
    fields: [
      { name: 'subjective', type: 'textarea', label: 'Subjective', required: true },
      { name: 'objective', type: 'textarea', label: 'Objective', required: true },
      { name: 'assessment', type: 'textarea', label: 'Assessment', required: true },
      { name: 'plan', type: 'textarea', label: 'Plan', required: true },
    ],
  },
  {
    id: '2',
    name: 'Progress Note Template',
    type: 'progress',
    specialty: 'General',
    content: 'Standard progress note template',
    fields: [
      { name: 'chiefComplaint', type: 'text', label: 'Chief Complaint', required: true },
      { name: 'historyOfPresentIllness', type: 'textarea', label: 'History of Present Illness', required: true },
      { name: 'physicalExamination', type: 'textarea', label: 'Physical Examination', required: true },
      { name: 'assessment', type: 'textarea', label: 'Assessment', required: true },
      { name: 'plan', type: 'textarea', label: 'Plan', required: true },
    ],
  },
  {
    id: '3',
    name: 'Consultation Note Template',
    type: 'consultation',
    specialty: 'Specialty',
    content: 'Consultation note template',
    fields: [
      { name: 'reasonForConsultation', type: 'text', label: 'Reason for Consultation', required: true },
      { name: 'historyOfPresentIllness', type: 'textarea', label: 'History of Present Illness', required: true },
      { name: 'physicalExamination', type: 'textarea', label: 'Physical Examination', required: true },
      { name: 'impression', type: 'textarea', label: 'Impression', required: true },
      { name: 'recommendations', type: 'textarea', label: 'Recommendations', required: true },
    ],
  },
];

export const ClinicalNotesPage: React.FC = () => {
  const dispatch = useDispatch();
  const [notes, setNotes] = useState<ClinicalNote[]>(mockClinicalNotes);
  const [templates, setTemplates] = useState<NoteTemplate[]>(mockNoteTemplates);
  const [filteredNotes, setFilteredNotes] = useState<ClinicalNote[]>(mockClinicalNotes);
  const [searchTerm, setSearchTerm] = useState('');
  const [typeFilter, setTypeFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all');
  const [priorityFilter, setPriorityFilter] = useState('all');
  const [providerFilter, setProviderFilter] = useState('all');
  const [departmentFilter, setDepartmentFilter] = useState('all');
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [tabValue, setTabValue] = useState(0);
  const [selectedNote, setSelectedNote] = useState<ClinicalNote | null>(null);
  const [viewDialogOpen, setViewDialogOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState<NoteTemplate | null>(null);
  const [isRecording, setIsRecording] = useState(false);
  const [editingNote, setEditingNote] = useState<Partial<ClinicalNote>>({});

  useEffect(() => {
    dispatch(setBreadcrumbs([
      { label: 'Dashboard', path: '/dashboard' },
      { label: 'Medical Records', path: '/medical' },
      { label: 'Clinical Notes', path: '/medical/notes' },
    ]));
    dispatch(setCurrentPage('Clinical Notes'));
  }, [dispatch]);

  useEffect(() => {
    let filtered = notes;

    if (searchTerm) {
      filtered = filtered.filter(
        (note) =>
          note.patientName.toLowerCase().includes(searchTerm.toLowerCase()) ||
          note.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
          note.content.toLowerCase().includes(searchTerm.toLowerCase()) ||
          note.providerName.toLowerCase().includes(searchTerm.toLowerCase()) ||
          note.tags.some(tag => tag.toLowerCase().includes(searchTerm.toLowerCase()))
      );
    }

    if (typeFilter !== 'all') {
      filtered = filtered.filter((note) => note.noteType === typeFilter);
    }

    if (statusFilter !== 'all') {
      filtered = filtered.filter((note) => note.status === statusFilter);
    }

    if (priorityFilter !== 'all') {
      filtered = filtered.filter((note) => note.priority === priorityFilter);
    }

    if (providerFilter !== 'all') {
      filtered = filtered.filter((note) => note.providerId === providerFilter);
    }

    if (departmentFilter !== 'all') {
      filtered = filtered.filter((note) => note.department === departmentFilter);
    }

    setFilteredNotes(filtered);
    setPage(0);
  }, [notes, searchTerm, typeFilter, statusFilter, priorityFilter, providerFilter, departmentFilter]);

  const getNoteTypeIcon = (type: string) => {
    switch (type) {
      case 'soap': return <NoteIcon />;
      case 'progress': return <AssignmentIcon />;
      case 'consultation': return <MedicalIcon />;
      case 'assessment': return <PsychologyIcon />;
      case 'procedure': return <HospitalIcon />;
      case 'discharge': return <HealingIcon />;
      case 'admission': return <HospitalIcon />;
      default: return <NoteIcon />;
    }
  };

  const getNoteTypeLabel = (type: string) => {
    switch (type) {
      case 'soap': return 'SOAP Note';
      case 'progress': return 'Progress Note';
      case 'consultation': return 'Consultation';
      case 'assessment': return 'Assessment';
      case 'procedure': return 'Procedure Note';
      case 'discharge': return 'Discharge Note';
      case 'admission': return 'Admission Note';
      case 'plan': return 'Treatment Plan';
      default: return type;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'signed': return 'success';
      case 'completed': return 'primary';
      case 'draft': return 'warning';
      case 'amended': return 'info';
      case 'deleted': return 'error';
      default: return 'default';
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'stat': return 'error';
      case 'urgent': return 'warning';
      case 'routine': return 'success';
      default: return 'default';
    }
  };

  const getAccessLevelColor = (level: string) => {
    switch (level) {
      case 'confidential': return 'error';
      case 'restricted': return 'warning';
      case 'public': return 'success';
      default: return 'default';
    }
  };

  const getNoteStats = () => {
    const total = notes.length;
    const drafts = notes.filter(n => n.status === 'draft').length;
    const signed = notes.filter(n => n.status === 'signed').length;
    const urgent = notes.filter(n => n.priority === 'urgent' || n.priority === 'stat').length;
    const starred = notes.filter(n => n.isStarred).length;
    const flagged = notes.filter(n => n.isFlagged).length;
    const confidential = notes.filter(n => n.isConfidential).length;

    return { total, drafts, signed, urgent, starred, flagged, confidential };
  };

  const handleViewNote = (note: ClinicalNote) => {
    setSelectedNote(note);
    setViewDialogOpen(true);
  };

  const handleEditNote = (note: ClinicalNote) => {
    setSelectedNote(note);
    setEditingNote({ ...note });
    setEditDialogOpen(true);
  };

  const handleCreateNote = (template?: NoteTemplate) => {
    setSelectedTemplate(template || null);
    setEditingNote({
      noteType: template?.type as any || 'progress',
      title: '',
      content: '',
      status: 'draft',
      priority: 'routine',
      isConfidential: false,
      isStarred: false,
      isFlagged: false,
      tags: [],
      attachments: [],
      voiceNotes: [],
      sharedWith: [],
      accessLevel: 'public',
    });
    setCreateDialogOpen(true);
  };

  const handleToggleStar = (noteId: string) => {
    setNotes(prev => prev.map(note => 
      note.id === noteId ? { ...note, isStarred: !note.isStarred } : note
    ));
  };

  const handleToggleFlag = (noteId: string) => {
    setNotes(prev => prev.map(note => 
      note.id === noteId ? { ...note, isFlagged: !note.isFlagged } : note
    ));
  };

  const handleStartRecording = () => {
    setIsRecording(true);
    // Voice recording logic would be implemented here
  };

  const handleStopRecording = () => {
    setIsRecording(false);
    // Stop recording and process audio
  };

  const stats = getNoteStats();
  const providers = [...new Set(notes.map(n => n.providerName))];
  const departments = [...new Set(notes.map(n => n.department))];

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">
          Clinical Notes Management
        </Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            variant="outlined"
            startIcon={<VoiceChatIcon />}
            onClick={isRecording ? handleStopRecording : handleStartRecording}
            color={isRecording ? 'error' : 'primary'}
          >
            {isRecording ? 'Stop Recording' : 'Voice Note'}
          </Button>
          <Button
            variant="outlined"
            startIcon={<PrintIcon />}
          >
            Print Notes
          </Button>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => handleCreateNote()}
          >
            New Note
          </Button>
        </Box>
      </Box>

      {/* Stats Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid size={{ xs: 12, sm: 6, md: 2 }}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Total Notes
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
                Drafts
              </Typography>
              <Typography variant="h4" color="warning.main">
                {stats.drafts}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 2 }}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Signed
              </Typography>
              <Typography variant="h4" color="success.main">
                {stats.signed}
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
        <Grid size={{ xs: 12, sm: 6, md: 2 }}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Starred
              </Typography>
              <Typography variant="h4" color="primary.main">
                {stats.starred}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 2 }}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Confidential
              </Typography>
              <Typography variant="h4" color="error.main">
                {stats.confidential}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Alerts */}
      {stats.drafts > 0 && (
        <Alert severity="warning" sx={{ mb: 3 }}>
          <Typography variant="subtitle2">
            You have {stats.drafts} draft note(s) that need to be completed and signed.
          </Typography>
        </Alert>
      )}
      {stats.urgent > 0 && (
        <Alert severity="error" sx={{ mb: 3 }}>
          <Typography variant="subtitle2">
            {stats.urgent} note(s) marked as urgent require immediate attention.
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
          <Tab label="All Notes" icon={<NoteIcon />} />
          <Tab label="My Drafts" icon={<EditIcon />} />
          <Tab label="Starred" icon={<StarIcon />} />
          <Tab label="Templates" icon={<AssignmentIcon />} />
        </Tabs>

        {/* All Notes Tab */}
        <TabPanel value={tabValue} index={0}>
          {/* Filters */}
          <Box sx={{ display: 'flex', gap: 2, mb: 3, flexWrap: 'wrap' }}>
            <TextField
              placeholder="Search notes..."
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
              <InputLabel>Note Type</InputLabel>
              <Select
                value={typeFilter}
                label="Note Type"
                onChange={(e) => setTypeFilter(e.target.value)}
              >
                <MenuItem value="all">All Types</MenuItem>
                <MenuItem value="soap">SOAP Note</MenuItem>
                <MenuItem value="progress">Progress Note</MenuItem>
                <MenuItem value="consultation">Consultation</MenuItem>
                <MenuItem value="assessment">Assessment</MenuItem>
                <MenuItem value="procedure">Procedure Note</MenuItem>
                <MenuItem value="discharge">Discharge Note</MenuItem>
                <MenuItem value="admission">Admission Note</MenuItem>
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
                <MenuItem value="draft">Draft</MenuItem>
                <MenuItem value="completed">Completed</MenuItem>
                <MenuItem value="signed">Signed</MenuItem>
                <MenuItem value="amended">Amended</MenuItem>
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
                <MenuItem value="stat">STAT</MenuItem>
                <MenuItem value="urgent">Urgent</MenuItem>
                <MenuItem value="routine">Routine</MenuItem>
              </Select>
            </FormControl>
            <FormControl sx={{ minWidth: 150 }}>
              <InputLabel>Provider</InputLabel>
              <Select
                value={providerFilter}
                label="Provider"
                onChange={(e) => setProviderFilter(e.target.value)}
              >
                <MenuItem value="all">All Providers</MenuItem>
                {providers.map((provider) => (
                  <MenuItem key={provider} value={provider}>
                    {provider}
                  </MenuItem>
                ))}
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

          {/* Notes Table */}
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Patient</TableCell>
                  <TableCell>Note Type</TableCell>
                  <TableCell>Title</TableCell>
                  <TableCell>Provider</TableCell>
                  <TableCell>Date</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Priority</TableCell>
                  <TableCell>Access</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {filteredNotes
                  .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
                  .map((note) => (
                    <TableRow key={note.id} hover>
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Avatar sx={{ width: 32, height: 32 }}>
                            {note.patientName.charAt(0)}
                          </Avatar>
                          <Box>
                            <Typography variant="body2" fontWeight="medium">
                              {note.patientName}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              {note.patientAge}y, {note.patientGender}
                            </Typography>
                          </Box>
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          {getNoteTypeIcon(note.noteType)}
                          {getNoteTypeLabel(note.noteType)}
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Box>
                            <Typography variant="body2" fontWeight="medium">
                              {note.title}
                            </Typography>
                            <Box sx={{ display: 'flex', gap: 0.5, mt: 0.5 }}>
                              {note.tags.slice(0, 2).map((tag, index) => (
                                <Chip
                                  key={index}
                                  label={tag}
                                  size="small"
                                  variant="outlined"
                                />
                              ))}
                              {note.tags.length > 2 && (
                                <Chip
                                  label={`+${note.tags.length - 2}`}
                                  size="small"
                                  variant="outlined"
                                />
                              )}
                            </Box>
                          </Box>
                          {note.isStarred && <StarIcon color="primary" fontSize="small" />}
                          {note.isFlagged && <FlagIcon color="error" fontSize="small" />}
                          {note.isConfidential && <LockIcon color="error" fontSize="small" />}
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {note.providerName}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {note.department}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        {new Date(note.date).toLocaleDateString()}
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={note.status}
                          color={getStatusColor(note.status) as any}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={note.priority}
                          color={getPriorityColor(note.priority) as any}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={note.accessLevel}
                          color={getAccessLevelColor(note.accessLevel) as any}
                          size="small"
                          icon={note.accessLevel === 'confidential' ? <LockIcon /> : <LockOpenIcon />}
                        />
                      </TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', gap: 0.5 }}>
                          <Tooltip title="View Note">
                            <IconButton
                              size="small"
                              onClick={() => handleViewNote(note)}
                            >
                              <VisibilityIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                          <Tooltip title="Edit Note">
                            <IconButton
                              size="small"
                              onClick={() => handleEditNote(note)}
                            >
                              <EditIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                          <Tooltip title={note.isStarred ? 'Unstar' : 'Star'}>
                            <IconButton
                              size="small"
                              onClick={() => handleToggleStar(note.id)}
                            >
                              {note.isStarred ? (
                                <StarIcon fontSize="small" color="primary" />
                              ) : (
                                <StarBorderIcon fontSize="small" />
                              )}
                            </IconButton>
                          </Tooltip>
                          <Tooltip title={note.isFlagged ? 'Unflag' : 'Flag'}>
                            <IconButton
                              size="small"
                              onClick={() => handleToggleFlag(note.id)}
                            >
                              <FlagIcon
                                fontSize="small"
                                color={note.isFlagged ? 'error' : 'inherit'}
                              />
                            </IconButton>
                          </Tooltip>
                          <Tooltip title="Print Note">
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
            count={filteredNotes.length}
            rowsPerPage={rowsPerPage}
            page={page}
            onPageChange={(_, newPage) => setPage(newPage)}
            onRowsPerPageChange={(e) => {
              setRowsPerPage(parseInt(e.target.value, 10));
              setPage(0);
            }}
          />
        </TabPanel>

        {/* My Drafts Tab */}
        <TabPanel value={tabValue} index={1}>
          <List>
            {notes.filter(n => n.status === 'draft').map((note) => (
              <ListItem key={note.id}>
                <ListItemIcon>
                  <EditIcon color="warning" />
                </ListItemIcon>
                <ListItemText
                  primary={`${note.title} - ${note.patientName}`}
                  secondary={`Last modified: ${new Date(note.lastModified).toLocaleDateString()}`}
                />
                <Button
                  size="small"
                  variant="contained"
                  onClick={() => handleEditNote(note)}
                >
                  Continue Editing
                </Button>
              </ListItem>
            ))}
          </List>
        </TabPanel>

        {/* Starred Tab */}
        <TabPanel value={tabValue} index={2}>
          <List>
            {notes.filter(n => n.isStarred).map((note) => (
              <ListItem key={note.id}>
                <ListItemIcon>
                  <StarIcon color="primary" />
                </ListItemIcon>
                <ListItemText
                  primary={`${note.title} - ${note.patientName}`}
                  secondary={`${note.providerName} | ${new Date(note.date).toLocaleDateString()}`}
                />
                <Button
                  size="small"
                  variant="outlined"
                  onClick={() => handleViewNote(note)}
                >
                  View Note
                </Button>
              </ListItem>
            ))}
          </List>
        </TabPanel>

        {/* Templates Tab */}
        <TabPanel value={tabValue} index={3}>
          <Grid container spacing={3}>
            {templates.map((template) => (
              <Grid size={{ xs: 12, md: 6, lg: 4 }} key={template.id}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      {template.name}
                    </Typography>
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      Type: {template.type} | Specialty: {template.specialty}
                    </Typography>
                    <Typography variant="body2" gutterBottom>
                      {template.content}
                    </Typography>
                    <Box sx={{ mt: 2 }}>
                      <Button
                        variant="contained"
                        size="small"
                        onClick={() => handleCreateNote(template)}
                      >
                        Use Template
                      </Button>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </TabPanel>
      </Paper>

      {/* View Note Dialog */}
      <Dialog
        open={viewDialogOpen}
        onClose={() => setViewDialogOpen(false)}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle>
          {selectedNote?.title} - {selectedNote?.patientName}
        </DialogTitle>
        <DialogContent>
          {selectedNote && (
            <Box sx={{ mt: 2 }}>
              <Grid container spacing={3}>
                <Grid size={{ xs: 12, md: 6 }}>
                  <Typography variant="h6" gutterBottom>
                    Note Information
                  </Typography>
                  <Typography><strong>Type:</strong> {getNoteTypeLabel(selectedNote.noteType)}</Typography>
                  <Typography><strong>Date:</strong> {new Date(selectedNote.date).toLocaleDateString()}</Typography>
                  <Typography><strong>Provider:</strong> {selectedNote.providerName}</Typography>
                  <Typography><strong>Department:</strong> {selectedNote.department}</Typography>
                  <Typography><strong>Status:</strong> 
                    <Chip
                      label={selectedNote.status}
                      color={getStatusColor(selectedNote.status) as any}
                      size="small"
                      sx={{ ml: 1 }}
                    />
                  </Typography>
                </Grid>
                <Grid size={{ xs: 12, md: 6 }}>
                  <Typography variant="h6" gutterBottom>
                    Patient Information
                  </Typography>
                  <Typography><strong>Name:</strong> {selectedNote.patientName}</Typography>
                  <Typography><strong>Age:</strong> {selectedNote.patientAge}</Typography>
                  <Typography><strong>Gender:</strong> {selectedNote.patientGender}</Typography>
                  {selectedNote.appointmentId && (
                    <Typography><strong>Appointment ID:</strong> {selectedNote.appointmentId}</Typography>
                  )}
                </Grid>
                {selectedNote.chiefComplaint && (
                  <Grid size={{ xs: 12 }}>
                    <Typography variant="h6" gutterBottom>
                      Chief Complaint
                    </Typography>
                    <Typography>{selectedNote.chiefComplaint}</Typography>
                  </Grid>
                )}
                {selectedNote.subjective && (
                  <Grid size={{ xs: 12 }}>
                    <Typography variant="h6" gutterBottom>
                      Subjective
                    </Typography>
                    <Typography>{selectedNote.subjective}</Typography>
                  </Grid>
                )}
                {selectedNote.objective && (
                  <Grid size={{ xs: 12 }}>
                    <Typography variant="h6" gutterBottom>
                      Objective
                    </Typography>
                    <Typography>{selectedNote.objective}</Typography>
                  </Grid>
                )}
                {selectedNote.assessment && (
                  <Grid size={{ xs: 12 }}>
                    <Typography variant="h6" gutterBottom>
                      Assessment
                    </Typography>
                    <Typography>{selectedNote.assessment}</Typography>
                  </Grid>
                )}
                {selectedNote.plan && (
                  <Grid size={{ xs: 12 }}>
                    <Typography variant="h6" gutterBottom>
                      Plan
                    </Typography>
                    <Typography>{selectedNote.plan}</Typography>
                  </Grid>
                )}
                {selectedNote.tags.length > 0 && (
                  <Grid size={{ xs: 12 }}>
                    <Typography variant="h6" gutterBottom>
                      Tags
                    </Typography>
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                      {selectedNote.tags.map((tag, index) => (
                        <Chip key={index} label={tag} size="small" />
                      ))}
                    </Box>
                  </Grid>
                )}
                {selectedNote.attachments.length > 0 && (
                  <Grid size={{ xs: 12 }}>
                    <Typography variant="h6" gutterBottom>
                      Attachments
                    </Typography>
                    <List>
                      {selectedNote.attachments.map((attachment, index) => (
                        <ListItem key={index}>
                          <ListItemIcon>
                            <AttachFileIcon />
                          </ListItemIcon>
                          <ListItemText primary={attachment} />
                        </ListItem>
                      ))}
                    </List>
                  </Grid>
                )}
                {selectedNote.signedBy && (
                  <Grid size={{ xs: 12 }}>
                    <Typography variant="h6" gutterBottom>
                      Signature
                    </Typography>
                    <Typography><strong>Signed by:</strong> {selectedNote.signedBy}</Typography>
                    <Typography><strong>Signed on:</strong> {new Date(selectedNote.signedDate!).toLocaleDateString()}</Typography>
                  </Grid>
                )}
              </Grid>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setViewDialogOpen(false)}>Close</Button>
          <Button variant="outlined" startIcon={<EditIcon />}>
            Edit Note
          </Button>
          <Button variant="outlined" startIcon={<ShareIcon />}>
            Share Note
          </Button>
          <Button variant="contained" startIcon={<PrintIcon />}>
            Print Note
          </Button>
        </DialogActions>
      </Dialog>

      {/* Create/Edit Note Dialog */}
      <Dialog
        open={createDialogOpen || editDialogOpen}
        onClose={() => {
          setCreateDialogOpen(false);
          setEditDialogOpen(false);
          setEditingNote({});
        }}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle>
          {createDialogOpen ? 'Create New Clinical Note' : 'Edit Clinical Note'}
        </DialogTitle>
        <DialogContent>
          <Typography color="text.secondary" sx={{ mb: 2 }}>
            {createDialogOpen ? 'Create a new clinical note using the form below or select a template.' : 'Edit the clinical note details below.'}
          </Typography>
          
          {/* Note creation/editing form would be implemented here */}
          <Box sx={{ mt: 2 }}>
            <Grid container spacing={3}>
              <Grid size={{ xs: 12, md: 6 }}>
                <FormControl fullWidth>
                  <InputLabel>Note Type</InputLabel>
                  <Select
                    value={editingNote.noteType || ''}
                    label="Note Type"
                    onChange={(e) => setEditingNote(prev => ({ ...prev, noteType: e.target.value as any }))}
                  >
                    <MenuItem value="soap">SOAP Note</MenuItem>
                    <MenuItem value="progress">Progress Note</MenuItem>
                    <MenuItem value="consultation">Consultation</MenuItem>
                    <MenuItem value="assessment">Assessment</MenuItem>
                    <MenuItem value="procedure">Procedure Note</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid size={{ xs: 12, md: 6 }}>
                <TextField
                  fullWidth
                  label="Title"
                  value={editingNote.title || ''}
                  onChange={(e) => setEditingNote(prev => ({ ...prev, title: e.target.value }))}
                />
              </Grid>
              <Grid size={{ xs: 12 }}>
                <TextField
                  fullWidth
                  multiline
                  rows={4}
                  label="Content"
                  value={editingNote.content || ''}
                  onChange={(e) => setEditingNote(prev => ({ ...prev, content: e.target.value }))}
                />
              </Grid>
            </Grid>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => {
            setCreateDialogOpen(false);
            setEditDialogOpen(false);
            setEditingNote({});
          }}>
            Cancel
          </Button>
          <Button variant="outlined" startIcon={<SaveIcon />}>
            Save as Draft
          </Button>
          <Button variant="contained" startIcon={<SaveIcon />}>
            Save & Sign
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};