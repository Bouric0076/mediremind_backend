import React, { useEffect, useState } from 'react';
import { useDispatch } from 'react-redux';
import { useNavigate, useParams } from 'react-router-dom';
import {
  Box,
  Paper,
  Typography,
  Button,
  Avatar,
  Chip,
  Tabs,
  Tab,
  Card,
  CardContent,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Alert,
} from '@mui/material';
import Grid from '@mui/material/Grid';
import {
  Edit as EditIcon,
  Email as EmailIcon,
  Phone as PhoneIcon,
  LocationOn as LocationIcon,
  Badge as BadgeIcon,
  Schedule as ScheduleIcon,
  School as SchoolIcon,
  LocalHospital as HospitalIcon,
  Warning as WarningIcon,
  CheckCircle as CheckCircleIcon,
  Assignment as AssignmentIcon,
  History as HistoryIcon,
  Person as PersonIcon,
  Security as SecurityIcon,
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
  employmentStatus: string;
  hireDate: string;
  licenseNumber: string;
  licenseExpiration: string;
  deaNumber?: string;
  deaExpiration?: string;
  npiNumber?: string;
  officeLocation: string;
  workPhone: string;
  education: string;
  yearsExperience: number;
  languagesSpoken: string[];
  boardCertifications: any[];
  emergencyContactName: string;
  emergencyContactPhone: string;
  emergencyContactRelationship: string;
  avatar?: string;
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
      id={`staff-tabpanel-${index}`}
      aria-labelledby={`staff-tab-${index}`}
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

const mockStaffMember: StaffMember = {
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
  deaNumber: 'BA1234567',
  deaExpiration: '2024-08-15',
  npiNumber: '1234567890',
  officeLocation: 'Building A, Floor 3, Room 301',
  workPhone: '(555) 123-4567 ext. 301',
  education: 'MD from Harvard Medical School, Residency at Johns Hopkins',
  yearsExperience: 12,
  languagesSpoken: ['English', 'Spanish', 'French'],
  boardCertifications: [
    { name: 'American Board of Internal Medicine - Cardiology', expiration: '2025-06-30' },
    { name: 'American Board of Internal Medicine - Interventional Cardiology', expiration: '2025-06-30' }
  ],
  emergencyContactName: 'John Johnson',
  emergencyContactPhone: '(555) 987-6543',
  emergencyContactRelationship: 'Spouse',
  isActive: true,
};

export const StaffProfilePage: React.FC = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const [staffMember] = useState<StaffMember>(mockStaffMember);
  const [tabValue, setTabValue] = useState(0);

  useEffect(() => {
    dispatch(setBreadcrumbs([
      { label: 'Dashboard', path: '/dashboard' },
      { label: 'Staff Directory', path: '/staff' },
      { label: `${staffMember.firstName} ${staffMember.lastName}`, path: `/staff/${id}` },
    ]));
    dispatch(setCurrentPage('Staff Profile'));
  }, [dispatch, id, staffMember.firstName, staffMember.lastName]);

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

  const isCredentialExpiringSoon = (expirationDate: string) => {
    const expDate = new Date(expirationDate);
    const today = new Date();
    const thirtyDaysFromNow = new Date(today.getTime() + (30 * 24 * 60 * 60 * 1000));
    return expDate <= thirtyDaysFromNow;
  };

  const isCredentialExpired = (expirationDate: string) => {
    const expDate = new Date(expirationDate);
    const today = new Date();
    return expDate < today;
  };

  const getCredentialStatus = (expirationDate: string) => {
    if (isCredentialExpired(expirationDate)) {
      return { color: 'error', label: 'Expired', icon: <WarningIcon /> };
    } else if (isCredentialExpiringSoon(expirationDate)) {
      return { color: 'warning', label: 'Expiring Soon', icon: <WarningIcon /> };
    } else {
      return { color: 'success', label: 'Valid', icon: <CheckCircleIcon /> };
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Grid container spacing={3} alignItems="center">
          <Grid>
            <Avatar
              src={staffMember.avatar}
              sx={{ width: 100, height: 100 }}
            >
              {staffMember.firstName[0]}{staffMember.lastName[0]}
            </Avatar>
          </Grid>
          <Grid size="grow">
            <Typography variant="h4" gutterBottom>
              {staffMember.firstName} {staffMember.lastName}
            </Typography>
            <Typography variant="h6" color="text.secondary" gutterBottom>
              {staffMember.jobTitle}
            </Typography>
            <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
              <Chip
                label={getStatusLabel(staffMember.employmentStatus)}
                color={getStatusColor(staffMember.employmentStatus) as any}
              />
              <Chip
                label={staffMember.department}
                variant="outlined"
              />
              <Chip
                label={`${staffMember.yearsExperience} years experience`}
                variant="outlined"
              />
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                <EmailIcon fontSize="small" color="action" />
                <Typography variant="body2">{staffMember.email}</Typography>
              </Box>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                <PhoneIcon fontSize="small" color="action" />
                <Typography variant="body2">{staffMember.phone}</Typography>
              </Box>
            </Box>
          </Grid>
          <Grid>
            <Button
              variant="contained"
              startIcon={<EditIcon />}
              onClick={() => navigate(`/staff/${id}/edit`)}
            >
              Edit Profile
            </Button>
          </Grid>
        </Grid>
      </Paper>

      {/* Credential Alerts */}
      {(isCredentialExpiringSoon(staffMember.licenseExpiration) || 
        (staffMember.deaExpiration && isCredentialExpiringSoon(staffMember.deaExpiration))) && (
        <Alert severity="warning" sx={{ mb: 3 }}>
          <Typography variant="subtitle2" gutterBottom>
            Credential Expiration Alert
          </Typography>
          {isCredentialExpiringSoon(staffMember.licenseExpiration) && (
            <Typography variant="body2">
              Medical License expires on {new Date(staffMember.licenseExpiration).toLocaleDateString()}
            </Typography>
          )}
          {staffMember.deaExpiration && isCredentialExpiringSoon(staffMember.deaExpiration) && (
            <Typography variant="body2">
              DEA Registration expires on {new Date(staffMember.deaExpiration).toLocaleDateString()}
            </Typography>
          )}
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
          <Tab label="Overview" icon={<PersonIcon />} />
          <Tab label="Credentials" icon={<BadgeIcon />} />
          <Tab label="Contact & Location" icon={<LocationIcon />} />
          <Tab label="Education & Experience" icon={<SchoolIcon />} />
          <Tab label="Schedule" icon={<ScheduleIcon />} />
          <Tab label="Performance" icon={<AssignmentIcon />} />
        </Tabs>

        {/* Overview Tab */}
        <TabPanel value={tabValue} index={0}>
          <Grid container spacing={3}>
            <Grid size={{ xs: 12, md: 6 }}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Professional Information
                  </Typography>
                  <List>
                    <ListItem>
                      <ListItemIcon><HospitalIcon /></ListItemIcon>
                      <ListItemText
                        primary="Department"
                        secondary={staffMember.department}
                      />
                    </ListItem>
                    <ListItem>
                      <ListItemIcon><BadgeIcon /></ListItemIcon>
                      <ListItemText
                        primary="Specialization"
                        secondary={staffMember.specialization}
                      />
                    </ListItem>
                    <ListItem>
                      <ListItemIcon><ScheduleIcon /></ListItemIcon>
                      <ListItemText
                        primary="Employment Status"
                        secondary={getStatusLabel(staffMember.employmentStatus)}
                      />
                    </ListItem>
                    <ListItem>
                      <ListItemIcon><HistoryIcon /></ListItemIcon>
                      <ListItemText
                        primary="Hire Date"
                        secondary={new Date(staffMember.hireDate).toLocaleDateString()}
                      />
                    </ListItem>
                  </List>
                </CardContent>
              </Card>
            </Grid>
            <Grid size={{ xs: 12, md: 6 }}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Quick Stats
                  </Typography>
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="body2" color="text.secondary">
                      Years of Experience
                    </Typography>
                    <Typography variant="h4" color="primary">
                      {staffMember.yearsExperience}
                    </Typography>
                  </Box>
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="body2" color="text.secondary">
                      Languages Spoken
                    </Typography>
                    <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap', mt: 1 }}>
                      {staffMember.languagesSpoken.map((lang) => (
                        <Chip key={lang} label={lang} size="small" variant="outlined" />
                      ))}
                    </Box>
                  </Box>
                  <Box>
                    <Typography variant="body2" color="text.secondary">
                      Board Certifications
                    </Typography>
                    <Typography variant="h6">
                      {staffMember.boardCertifications.length}
                    </Typography>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>

        {/* Credentials Tab */}
        <TabPanel value={tabValue} index={1}>
          <Grid container spacing={3}>
            <Grid size={{ xs: 12, md: 6 }}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Medical License
                  </Typography>
                  <List>
                    <ListItem>
                      <ListItemText
                        primary="License Number"
                        secondary={staffMember.licenseNumber}
                      />
                    </ListItem>
                    <ListItem>
                      <ListItemText
                        primary="Expiration Date"
                        secondary={new Date(staffMember.licenseExpiration).toLocaleDateString()}
                      />
                      <Chip
                        label={getCredentialStatus(staffMember.licenseExpiration).label}
                        color={getCredentialStatus(staffMember.licenseExpiration).color as any}
                        size="small"
                        icon={getCredentialStatus(staffMember.licenseExpiration).icon}
                      />
                    </ListItem>
                  </List>
                </CardContent>
              </Card>
            </Grid>
            {staffMember.deaNumber && (
              <Grid size={{ xs: 12, md: 6 }}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      DEA Registration
                    </Typography>
                    <List>
                      <ListItem>
                        <ListItemText
                          primary="DEA Number"
                          secondary={staffMember.deaNumber}
                        />
                      </ListItem>
                      {staffMember.deaExpiration && (
                        <ListItem>
                          <ListItemText
                            primary="Expiration Date"
                            secondary={new Date(staffMember.deaExpiration).toLocaleDateString()}
                          />
                          <Chip
                            label={getCredentialStatus(staffMember.deaExpiration).label}
                            color={getCredentialStatus(staffMember.deaExpiration).color as any}
                            size="small"
                            icon={getCredentialStatus(staffMember.deaExpiration).icon}
                          />
                        </ListItem>
                      )}
                    </List>
                  </CardContent>
                </Card>
              </Grid>
            )}
            {staffMember.npiNumber && (
              <Grid size={{ xs: 12, md: 6 }}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      NPI Number
                    </Typography>
                    <Typography variant="body1">
                      {staffMember.npiNumber}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            )}
            <Grid size={{ xs: 12 }}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Board Certifications
                  </Typography>
                  {staffMember.boardCertifications.length > 0 ? (
                    <List>
                      {staffMember.boardCertifications.map((cert, index) => (
                        <ListItem key={index}>
                          <ListItemText
                            primary={cert.name}
                            secondary={`Expires: ${new Date(cert.expiration).toLocaleDateString()}`}
                          />
                          <Chip
                            label={getCredentialStatus(cert.expiration).label}
                            color={getCredentialStatus(cert.expiration).color as any}
                            size="small"
                            icon={getCredentialStatus(cert.expiration).icon}
                          />
                        </ListItem>
                      ))}
                    </List>
                  ) : (
                    <Typography color="text.secondary">
                      No board certifications on file
                    </Typography>
                  )}
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>

        {/* Contact & Location Tab */}
        <TabPanel value={tabValue} index={2}>
          <Grid container spacing={3}>
            <Grid size={{ xs: 12, md: 6 }}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Work Contact
                  </Typography>
                  <List>
                    <ListItem>
                      <ListItemIcon><EmailIcon /></ListItemIcon>
                      <ListItemText
                        primary="Email"
                        secondary={staffMember.email}
                      />
                    </ListItem>
                    <ListItem>
                      <ListItemIcon><PhoneIcon /></ListItemIcon>
                      <ListItemText
                        primary="Work Phone"
                        secondary={staffMember.workPhone}
                      />
                    </ListItem>
                    <ListItem>
                      <ListItemIcon><LocationIcon /></ListItemIcon>
                      <ListItemText
                        primary="Office Location"
                        secondary={staffMember.officeLocation}
                      />
                    </ListItem>
                  </List>
                </CardContent>
              </Card>
            </Grid>
            <Grid size={{ xs: 12, md: 6 }}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Emergency Contact
                  </Typography>
                  <List>
                    <ListItem>
                      <ListItemIcon><PersonIcon /></ListItemIcon>
                      <ListItemText
                        primary="Name"
                        secondary={staffMember.emergencyContactName}
                      />
                    </ListItem>
                    <ListItem>
                      <ListItemIcon><PhoneIcon /></ListItemIcon>
                      <ListItemText
                        primary="Phone"
                        secondary={staffMember.emergencyContactPhone}
                      />
                    </ListItem>
                    <ListItem>
                      <ListItemIcon><SecurityIcon /></ListItemIcon>
                      <ListItemText
                        primary="Relationship"
                        secondary={staffMember.emergencyContactRelationship}
                      />
                    </ListItem>
                  </List>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>

        {/* Education & Experience Tab */}
        <TabPanel value={tabValue} index={3}>
          <Grid container spacing={3}>
            <Grid size={{ xs: 12 }}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Education Background
                  </Typography>
                  <Typography variant="body1">
                    {staffMember.education}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid size={{ xs: 12, md: 6 }}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Experience
                  </Typography>
                  <Typography variant="h3" color="primary" gutterBottom>
                    {staffMember.yearsExperience}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Years of Professional Experience
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid size={{ xs: 12, md: 6 }}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Languages
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                    {staffMember.languagesSpoken.map((lang) => (
                      <Chip key={lang} label={lang} variant="outlined" />
                    ))}
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>

        {/* Schedule Tab */}
        <TabPanel value={tabValue} index={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Work Schedule
              </Typography>
              <Typography color="text.secondary">
                Schedule management functionality will be implemented here.
              </Typography>
            </CardContent>
          </Card>
        </TabPanel>

        {/* Performance Tab */}
        <TabPanel value={tabValue} index={5}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Performance Metrics
              </Typography>
              <Typography color="text.secondary">
                Performance tracking and review functionality will be implemented here.
              </Typography>
            </CardContent>
          </Card>
        </TabPanel>
      </Paper>
    </Box>
  );
};