import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Typography,
  Box,
  Chip,
  Alert,
  CircularProgress,
  Autocomplete,
  FormHelperText,
  Card,
  CardContent,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  DatePicker,
  TimePicker,
  LocalizationProvider,
} from '@mui/x-date-pickers';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import {
  Person as PersonIcon,
  Schedule as ScheduleIcon,
  LocationOn as LocationIcon,
  Notes as NotesIcon,
  Check as CheckIcon,
  Warning as WarningIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import { format, addMinutes, isAfter, isBefore, parseISO } from 'date-fns';

interface Patient {
  id: string;
  name: string;
  email: string;
  phone: string;
  dateOfBirth: string;
}

interface Provider {
  id: string;
  name: string;
  specialization: string;
  email: string;
  availability: string[];
}

interface AppointmentType {
  id: string;
  name: string;
  duration: number;
  description: string;
  color: string;
}

interface TimeSlot {
  time: string;
  available: boolean;
  reason?: string;
}

interface AppointmentFormData {
  patientId: string;
  providerId: string;
  appointmentTypeId: string;
  date: Date | null;
  time: Date | null;
  duration: number;
  location: string;
  notes: string;
  priority: 'low' | 'medium' | 'high';
  reminderPreferences: {
    email: boolean;
    sms: boolean;
    push: boolean;
  };
}

interface AppointmentSchedulerProps {
  open: boolean;
  onClose: () => void;
  onSubmit: (appointmentData: AppointmentFormData) => Promise<void>;
  editingAppointment?: any;
  patients: Patient[];
  providers: Provider[];
  appointmentTypes: AppointmentType[];
}

const defaultFormData: AppointmentFormData = {
  patientId: '',
  providerId: '',
  appointmentTypeId: '',
  date: null,
  time: null,
  duration: 30,
  location: 'Main Hospital',
  notes: '',
  priority: 'medium',
  reminderPreferences: {
    email: true,
    sms: true,
    push: true,
  },
};

export const AppointmentScheduler: React.FC<AppointmentSchedulerProps> = ({
  open,
  onClose,
  onSubmit,
  editingAppointment,
  patients,
  providers,
  appointmentTypes,
}) => {
  const [formData, setFormData] = useState<AppointmentFormData>(defaultFormData);
  const [availableSlots, setAvailableSlots] = useState<TimeSlot[]>([]);
  const [loading, setLoading] = useState(false);
  const [checkingAvailability, setCheckingAvailability] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [submitError, setSubmitError] = useState<string>('');

  // Reset form when dialog opens/closes
  useEffect(() => {
    if (open) {
      if (editingAppointment) {
        setFormData({
          patientId: editingAppointment.patientId || '',
          providerId: editingAppointment.providerId || '',
          appointmentTypeId: editingAppointment.appointmentTypeId || '',
          date: editingAppointment.date ? parseISO(editingAppointment.date) : null,
          time: editingAppointment.time ? parseISO(`2000-01-01T${editingAppointment.time}`) : null,
          duration: editingAppointment.duration || 30,
          location: editingAppointment.location || 'Main Hospital',
          notes: editingAppointment.notes || '',
          priority: editingAppointment.priority || 'medium',
          reminderPreferences: editingAppointment.reminderPreferences || {
            email: true,
            sms: true,
            push: true,
          },
        });
      } else {
        setFormData(defaultFormData);
      }
      setErrors({});
      setSubmitError('');
    }
  }, [open, editingAppointment]);

  // Check availability when provider, date, or duration changes
  useEffect(() => {
    if (formData.providerId && formData.date && formData.duration) {
      checkProviderAvailability();
    }
  }, [formData.providerId, formData.date, formData.duration]);

  const checkProviderAvailability = async () => {
    if (!formData.providerId || !formData.date) return;

    setCheckingAvailability(true);
    try {
      const dateStr = format(formData.date, 'yyyy-MM-dd');
      const response = await fetch(
        `/api/appointments/check-availability/?provider_id=${formData.providerId}&date=${dateStr}&duration=${formData.duration}`,
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
          },
        }
      );

      if (response.ok) {
        const data = await response.json();
        setAvailableSlots(data.available_slots || []);
      } else {
        console.error('Failed to check availability');
        setAvailableSlots([]);
      }
    } catch (error) {
      console.error('Error checking availability:', error);
      setAvailableSlots([]);
    } finally {
      setCheckingAvailability(false);
    }
  };

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.patientId) {
      newErrors.patientId = 'Patient is required';
    }

    if (!formData.providerId) {
      newErrors.providerId = 'Provider is required';
    }

    if (!formData.appointmentTypeId) {
      newErrors.appointmentTypeId = 'Appointment type is required';
    }

    if (!formData.date) {
      newErrors.date = 'Date is required';
    } else if (isBefore(formData.date, new Date())) {
      newErrors.date = 'Date cannot be in the past';
    }

    if (!formData.time) {
      newErrors.time = 'Time is required';
    }

    if (!formData.location.trim()) {
      newErrors.location = 'Location is required';
    }

    if (formData.duration < 15 || formData.duration > 240) {
      newErrors.duration = 'Duration must be between 15 and 240 minutes';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async () => {
    if (!validateForm()) return;

    setLoading(true);
    setSubmitError('');

    try {
      await onSubmit(formData);
      onClose();
    } catch (error: any) {
      setSubmitError(error.message || 'Failed to schedule appointment');
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (field: keyof AppointmentFormData, value: any) => {
    setFormData(prev => ({
      ...prev,
      [field]: value,
    }));

    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({
        ...prev,
        [field]: '',
      }));
    }
  };

  const handleReminderPreferenceChange = (type: keyof AppointmentFormData['reminderPreferences'], value: boolean) => {
    setFormData(prev => ({
      ...prev,
      reminderPreferences: {
        ...prev.reminderPreferences,
        [type]: value,
      },
    }));
  };

  const getSelectedPatient = () => patients.find(p => p.id === formData.patientId);
  const getSelectedProvider = () => providers.find(p => p.id === formData.providerId);
  const getSelectedAppointmentType = () => appointmentTypes.find(t => t.id === formData.appointmentTypeId);

  const isTimeSlotAvailable = (timeString: string): boolean => {
    const slot = availableSlots.find(s => s.time === timeString);
    return slot ? slot.available : false;
  };

  const getTimeSlotReason = (timeString: string): string | undefined => {
    const slot = availableSlots.find(s => s.time === timeString);
    return slot?.reason;
  };

  return (
    <LocalizationProvider dateAdapter={AdapterDateFns}>
      <Dialog
        open={open}
        onClose={onClose}
        maxWidth="md"
        fullWidth
        PaperProps={{
          sx: { minHeight: '80vh' }
        }}
      >
        <DialogTitle>
          <Box display="flex" alignItems="center" gap={1}>
            <ScheduleIcon color="primary" />
            <Typography variant="h6">
              {editingAppointment ? 'Edit Appointment' : 'Schedule New Appointment'}
            </Typography>
          </Box>
        </DialogTitle>

        <DialogContent dividers>
          <Grid container spacing={3}>
            {/* Patient Selection */}
            <Grid size={{ xs: 12, md: 6 }}>
              <Autocomplete
                options={patients}
                getOptionLabel={(option) => `${option.name} (${option.email})`}
                value={getSelectedPatient() || null}
                onChange={(_, value) => handleInputChange('patientId', value?.id || '')}
                renderInput={(params) => (
                  <TextField
                    {...params}
                    label="Patient"
                    error={!!errors.patientId}
                    helperText={errors.patientId}
                    InputProps={{
                      ...params.InputProps,
                      startAdornment: <PersonIcon color="action" sx={{ mr: 1 }} />,
                    }}
                  />
                )}
                renderOption={(props, option) => (
                  <Box component="li" {...props}>
                    <Box>
                      <Typography variant="body1">{option.name}</Typography>
                      <Typography variant="body2" color="text.secondary">
                        {option.email} • {option.phone}
                      </Typography>
                    </Box>
                  </Box>
                )}
              />
            </Grid>

            {/* Provider Selection */}
            <Grid size={{ xs: 12, md: 6 }}>
              <Autocomplete
                options={providers}
                getOptionLabel={(option) => `Dr. ${option.name} (${option.specialization})`}
                value={getSelectedProvider() || null}
                onChange={(_, value) => handleInputChange('providerId', value?.id || '')}
                renderInput={(params) => (
                  <TextField
                    {...params}
                    label="Provider"
                    error={!!errors.providerId}
                    helperText={errors.providerId}
                  />
                )}
                renderOption={(props, option) => (
                  <Box component="li" {...props}>
                    <Box>
                      <Typography variant="body1">Dr. {option.name}</Typography>
                      <Typography variant="body2" color="text.secondary">
                        {option.specialization}
                      </Typography>
                    </Box>
                  </Box>
                )}
              />
            </Grid>

            {/* Appointment Type */}
            <Grid size={{ xs: 12, md: 6 }}>
              <FormControl fullWidth error={!!errors.appointmentTypeId}>
                <InputLabel>Appointment Type</InputLabel>
                <Select
                  value={formData.appointmentTypeId}
                  onChange={(e) => {
                    const selectedType = appointmentTypes.find(t => t.id === e.target.value);
                    handleInputChange('appointmentTypeId', e.target.value);
                    if (selectedType) {
                      handleInputChange('duration', selectedType.duration);
                    }
                  }}
                  label="Appointment Type"
                >
                  {appointmentTypes.map((type) => (
                    <MenuItem key={type.id} value={type.id}>
                      <Box display="flex" alignItems="center" gap={1}>
                        <Chip
                          size="small"
                          label={type.name}
                          sx={{ backgroundColor: type.color, color: 'white' }}
                        />
                        <Typography variant="body2" color="text.secondary">
                          ({type.duration} min)
                        </Typography>
                      </Box>
                    </MenuItem>
                  ))}
                </Select>
                {errors.appointmentTypeId && (
                  <FormHelperText>{errors.appointmentTypeId}</FormHelperText>
                )}
              </FormControl>
            </Grid>

            {/* Priority */}
            <Grid size={{ xs: 12, md: 6 }}>
              <FormControl fullWidth>
                <InputLabel>Priority</InputLabel>
                <Select
                  value={formData.priority}
                  onChange={(e) => handleInputChange('priority', e.target.value)}
                  label="Priority"
                >
                  <MenuItem value="low">
                    <Chip label="Low" color="default" size="small" />
                  </MenuItem>
                  <MenuItem value="medium">
                    <Chip label="Medium" color="warning" size="small" />
                  </MenuItem>
                  <MenuItem value="high">
                    <Chip label="High" color="error" size="small" />
                  </MenuItem>
                </Select>
              </FormControl>
            </Grid>

            {/* Date Selection */}
            <Grid size={{ xs: 12, md: 6 }}>
              <DatePicker
                label="Appointment Date"
                value={formData.date}
                onChange={(date) => handleInputChange('date', date)}
                minDate={new Date()}
                slotProps={{
                  textField: {
                    fullWidth: true,
                    error: !!errors.date,
                    helperText: errors.date,
                  },
                }}
              />
            </Grid>

            {/* Duration */}
            <Grid size={{ xs: 12, md: 6 }}>
              <TextField
                fullWidth
                label="Duration (minutes)"
                type="number"
                value={formData.duration}
                onChange={(e) => handleInputChange('duration', parseInt(e.target.value) || 30)}
                error={!!errors.duration}
                helperText={errors.duration}
                inputProps={{ min: 15, max: 240, step: 15 }}
              />
            </Grid>

            {/* Available Time Slots */}
            {formData.providerId && formData.date && (
              <Grid size={{ xs: 12 }}>
                <Card variant="outlined">
                  <CardContent>
                    <Box display="flex" alignItems="center" gap={1} mb={2}>
                      <ScheduleIcon color="primary" />
                      <Typography variant="h6">Available Time Slots</Typography>
                      {checkingAvailability && <CircularProgress size={20} />}
                      <IconButton
                        size="small"
                        onClick={checkProviderAvailability}
                        disabled={checkingAvailability}
                      >
                        <RefreshIcon />
                      </IconButton>
                    </Box>

                    {availableSlots.length > 0 ? (
                      <Grid container spacing={1}>
                        {availableSlots.map((slot) => (
                          <Grid item key={slot.time}>
                            <Tooltip
                              title={slot.available ? 'Available' : slot.reason || 'Not available'}
                              arrow
                            >
                              <Chip
                                label={slot.time}
                                onClick={() => {
                                  if (slot.available) {
                                    const timeDate = new Date(`2000-01-01T${slot.time}`);
                                    handleInputChange('time', timeDate);
                                  }
                                }}
                                color={slot.available ? 'primary' : 'default'}
                                variant={
                                  formData.time && format(formData.time, 'HH:mm') === slot.time
                                    ? 'filled'
                                    : 'outlined'
                                }
                                disabled={!slot.available}
                                icon={slot.available ? <CheckIcon /> : <WarningIcon />}
                                sx={{
                                  cursor: slot.available ? 'pointer' : 'not-allowed',
                                  opacity: slot.available ? 1 : 0.5,
                                }}
                              />
                            </Tooltip>
                          </Grid>
                        ))}
                      </Grid>
                    ) : (
                      <Typography color="text.secondary">
                        {checkingAvailability ? 'Checking availability...' : 'No available slots found'}
                      </Typography>
                    )}

                    {errors.time && (
                      <Typography color="error" variant="body2" sx={{ mt: 1 }}>
                        {errors.time}
                      </Typography>
                    )}
                  </CardContent>
                </Card>
              </Grid>
            )}

            {/* Location */}
            <Grid size={{ xs: 12, md: 6 }}>
              <TextField
                fullWidth
                label="Location"
                value={formData.location}
                onChange={(e) => handleInputChange('location', e.target.value)}
                error={!!errors.location}
                helperText={errors.location}
                InputProps={{
                  startAdornment: <LocationIcon color="action" sx={{ mr: 1 }} />,
                }}
              />
            </Grid>

            {/* Notes */}
            <Grid size={{ xs: 12, md: 6 }}>
              <TextField
                fullWidth
                label="Notes"
                multiline
                rows={3}
                value={formData.notes}
                onChange={(e) => handleInputChange('notes', e.target.value)}
                InputProps={{
                  startAdornment: <NotesIcon color="action" sx={{ mr: 1, alignSelf: 'flex-start', mt: 1 }} />,
                }}
              />
            </Grid>

            {/* Reminder Preferences */}
            <Grid size={{ xs: 12 }}>
              <Card variant="outlined">
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Reminder Preferences
                  </Typography>
                  <Grid container spacing={2}>
                    <Grid size={{ xs: 12, sm: 4 }}>
                      <Box display="flex" alignItems="center" gap={1}>
                        <input
                          type="checkbox"
                          checked={formData.reminderPreferences.email}
                          onChange={(e) => handleReminderPreferenceChange('email', e.target.checked)}
                        />
                        <Typography>Email Reminders</Typography>
                      </Box>
                    </Grid>
                    <Grid size={{ xs: 12, sm: 4 }}>
                      <Box display="flex" alignItems="center" gap={1}>
                        <input
                          type="checkbox"
                          checked={formData.reminderPreferences.sms}
                          onChange={(e) => handleReminderPreferenceChange('sms', e.target.checked)}
                        />
                        <Typography>SMS Reminders</Typography>
                      </Box>
                    </Grid>
                    <Grid size={{ xs: 12, sm: 4 }}>
                      <Box display="flex" alignItems="center" gap={1}>
                        <input
                          type="checkbox"
                          checked={formData.reminderPreferences.push}
                          onChange={(e) => handleReminderPreferenceChange('push', e.target.checked)}
                        />
                        <Typography>Push Notifications</Typography>
                      </Box>
                    </Grid>
                  </Grid>
                </CardContent>
              </Card>
            </Grid>

            {/* Appointment Summary */}
            {formData.patientId && formData.providerId && formData.date && formData.time && (
              <Grid size={{ xs: 12 }}>
                <Card variant="outlined" sx={{ backgroundColor: 'primary.50' }}>
                  <CardContent>
                    <Typography variant="h6" gutterBottom color="primary">
                      Appointment Summary
                    </Typography>
                    <List dense>
                      <ListItem>
                        <ListItemIcon>
                          <PersonIcon />
                        </ListItemIcon>
                        <ListItemText
                          primary="Patient"
                          secondary={getSelectedPatient()?.name}
                        />
                      </ListItem>
                      <ListItem>
                        <ListItemIcon>
                          <PersonIcon />
                        </ListItemIcon>
                        <ListItemText
                          primary="Provider"
                          secondary={`Dr. ${getSelectedProvider()?.name}`}
                        />
                      </ListItem>
                      <ListItem>
                        <ListItemIcon>
                          <ScheduleIcon />
                        </ListItemIcon>
                        <ListItemText
                          primary="Date & Time"
                          secondary={`${format(formData.date, 'EEEE, MMMM d, yyyy')} at ${format(formData.time, 'h:mm a')}`}
                        />
                      </ListItem>
                      <ListItem>
                        <ListItemIcon>
                          <LocationIcon />
                        </ListItemIcon>
                        <ListItemText
                          primary="Location"
                          secondary={formData.location}
                        />
                      </ListItem>
                    </List>
                  </CardContent>
                </Card>
              </Grid>
            )}

            {/* Error Display */}
            {submitError && (
              <Grid size={{ xs: 12 }}>
                <Alert severity="error">{submitError}</Alert>
              </Grid>
            )}
          </Grid>
        </DialogContent>

        <DialogActions sx={{ p: 3 }}>
          <Button onClick={onClose} disabled={loading}>
            Cancel
          </Button>
          <Button
            onClick={handleSubmit}
            variant="contained"
            disabled={loading || checkingAvailability}
            startIcon={loading ? <CircularProgress size={20} /> : null}
          >
            {loading ? 'Scheduling...' : editingAppointment ? 'Update Appointment' : 'Schedule Appointment'}
          </Button>
        </DialogActions>
      </Dialog>
    </LocalizationProvider>
  );
};

export default AppointmentScheduler;