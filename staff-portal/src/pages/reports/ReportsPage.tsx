import React, { useState } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
} from '@mui/material';
import Grid from '@mui/material/Grid'; // ✅ Use Grid2 from MUI v7

import {
  Assessment,
  PictureAsPdf,
  GetApp,
  TrendingUp,
  People,
  LocalHospital,
  AttachMoney,
} from '@mui/icons-material';

export const ReportsPage: React.FC = () => {
  const [reportType, setReportType] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');

  const reportTypes = [
    { value: 'patient-summary', label: 'Patient Summary Report' },
    { value: 'appointment-analytics', label: 'Appointment Analytics' },
    { value: 'financial-report', label: 'Financial Report' },
    { value: 'medication-report', label: 'Medication Report' },
    { value: 'staff-performance', label: 'Staff Performance Report' },
  ];

  const recentReports = [
    {
      id: 1,
      name: 'Monthly Patient Summary - December 2024',
      type: 'Patient Summary',
      generatedDate: '2024-12-15',
      size: '2.3 MB',
    },
    {
      id: 2,
      name: 'Appointment Analytics - Q4 2024',
      type: 'Analytics',
      generatedDate: '2024-12-10',
      size: '1.8 MB',
    },
    {
      id: 3,
      name: 'Financial Report - November 2024',
      type: 'Financial',
      generatedDate: '2024-12-01',
      size: '3.1 MB',
    },
  ];

  const handleGenerateReport = () => {
    console.log('Generating report:', {
      type: reportType,
      startDate,
      endDate,
    });
  };

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Typography variant="h4" component="h1" gutterBottom>
        Reports & Analytics
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
        Generate comprehensive reports and view analytics for your medical practice.
      </Typography>

      <Grid container spacing={3}>
        {/* Report Generation */}
        <Grid size={{ xs: 12, md: 8 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Generate New Report
              </Typography>

              <Grid container spacing={3}>
                <Grid size={{ xs: 12 }}>
                  <FormControl fullWidth>
                    <InputLabel>Report Type</InputLabel>
                    <Select
                      value={reportType}
                      label="Report Type"
                      onChange={(e) => setReportType(e.target.value)}
                    >
                      {reportTypes.map((type) => (
                        <MenuItem key={type.value} value={type.value}>
                          {type.label}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid>

                <Grid size={{ xs: 12, sm: 6 }}>
                  <TextField
                    fullWidth
                    label="Start Date"
                    type="date"
                    value={startDate}
                    onChange={(e) => setStartDate(e.target.value)}
                    InputLabelProps={{ shrink: true }}
                  />
                </Grid>

                <Grid size={{ xs: 12, sm: 6 }}>
                  <TextField
                    fullWidth
                    label="End Date"
                    type="date"
                    value={endDate}
                    onChange={(e) => setEndDate(e.target.value)}
                    InputLabelProps={{ shrink: true }}
                  />
                </Grid>

                <Grid size={{ xs: 12 }}>
                  <Button
                    variant="contained"
                    startIcon={<Assessment />}
                    onClick={handleGenerateReport}
                    disabled={!reportType}
                    size="large"
                  >
                    Generate Report
                  </Button>
                </Grid>
              </Grid>
            </CardContent>
          </Card>

          {/* Quick Stats */}
          <Grid container spacing={2} sx={{ mt: 2 }}>
            <Grid size={{ xs: 12, sm: 6, md: 3 }}>
              <Card>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <People sx={{ fontSize: 40, color: 'primary.main', mr: 2 }} />
                    <Box>
                      <Typography variant="h4">1,234</Typography>
                      <Typography variant="body2" color="text.secondary">
                        Total Patients
                      </Typography>
                    </Box>
                  </Box>
                </CardContent>
              </Card>
            </Grid>

            <Grid size={{ xs: 12, sm: 6, md: 3 }}>
              <Card>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <LocalHospital sx={{ fontSize: 40, color: 'success.main', mr: 2 }} />
                    <Box>
                      <Typography variant="h4">856</Typography>
                      <Typography variant="body2" color="text.secondary">
                        Appointments
                      </Typography>
                    </Box>
                  </Box>
                </CardContent>
              </Card>
            </Grid>

            <Grid size={{ xs: 12, sm: 6, md: 3 }}>
              <Card>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <AttachMoney sx={{ fontSize: 40, color: 'warning.main', mr: 2 }} />
                    <Box>
                      <Typography variant="h4">$45.2K</Typography>
                      <Typography variant="body2" color="text.secondary">
                        Revenue
                      </Typography>
                    </Box>
                  </Box>
                </CardContent>
              </Card>
            </Grid>

            <Grid size={{ xs: 12, sm: 6, md: 3 }}>
              <Card>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <TrendingUp sx={{ fontSize: 40, color: 'info.main', mr: 2 }} />
                    <Box>
                      <Typography variant="h4">12%</Typography>
                      <Typography variant="body2" color="text.secondary">
                        Growth Rate
                      </Typography>
                    </Box>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </Grid>

        {/* Recent Reports */}
        <Grid size={{ xs: 12, md: 4 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Recent Reports
              </Typography>

              <List>
                {recentReports.map((report, index) => (
                  <React.Fragment key={report.id}>
                    <ListItem
                      sx={{
                        px: 0,
                        '&:hover': {
                          backgroundColor: 'action.hover',
                          borderRadius: 1,
                        },
                      }}
                    >
                      <ListItemIcon>
                        <PictureAsPdf color="error" />
                      </ListItemIcon>
                      <ListItemText
                        primary={report.name}
                        secondary={
                          <Box>
                            <Typography variant="caption" display="block">
                              {report.type} • {report.size}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              Generated: {new Date(report.generatedDate).toLocaleDateString()}
                            </Typography>
                          </Box>
                        }
                        slotProps={{
                secondary: { component: 'div' }
              }}
                      />
                      <Button
                        size="small"
                        startIcon={<GetApp />}
                        onClick={() => console.log('Download report', report.id)}
                      >
                        Download
                      </Button>
                    </ListItem>
                    {index < recentReports.length - 1 && <Divider />}
                  </React.Fragment>
                ))}
              </List>

              <Button
                variant="outlined"
                fullWidth
                sx={{ mt: 2 }}
                onClick={() => console.log('View all reports')}
              >
                View All Reports
              </Button>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default ReportsPage;