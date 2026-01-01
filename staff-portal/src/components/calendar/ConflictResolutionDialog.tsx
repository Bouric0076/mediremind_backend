import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  Box,
  Card,
  CardContent,
  Chip,
  Alert,
  RadioGroup,
  FormControlLabel,
  Radio,
  Divider,
  IconButton,
} from '@mui/material';
import {
  Warning as WarningIcon,
  Schedule as ScheduleIcon,
  Person as PersonIcon,
  Close as CloseIcon,
  CalendarToday as CalendarIcon,
} from '@mui/icons-material';
import { format, parseISO } from 'date-fns';
import type { SyncConflict } from '../../types/calendar';

interface ConflictResolutionDialogProps {
  open: boolean;
  conflicts: SyncConflict[];
  onClose: () => void;
  onResolve: (conflictId: string, resolution: 'keep_internal' | 'keep_external' | 'merge') => void;
  onResolveAll: (resolution: 'keep_internal' | 'keep_external' | 'merge') => void;
}

const ConflictResolutionDialog: React.FC<ConflictResolutionDialogProps> = ({
  open,
  conflicts,
  onClose,
  onResolve,
  onResolveAll,
}) => {
  const [selectedResolutions, setSelectedResolutions] = useState<Record<string, string>>({});
  const [globalResolution, setGlobalResolution] = useState<string>('');

  const handleResolutionChange = (conflictId: string, resolution: string) => {
    setSelectedResolutions(prev => ({
      ...prev,
      [conflictId]: resolution,
    }));
  };

  const handleResolveConflict = (conflict: SyncConflict) => {
    const resolution = selectedResolutions[conflict.id];
    if (resolution) {
      onResolve(conflict.id, resolution as 'keep_internal' | 'keep_external' | 'merge');
    }
  };

  const handleResolveAll = () => {
    if (globalResolution) {
      onResolveAll(globalResolution as 'keep_internal' | 'keep_external' | 'merge');
      onClose();
    }
  };

  const getConflictTypeColor = (type: string) => {
    switch (type) {
      case 'time_overlap':
        return 'error';
      case 'duplicate':
        return 'warning';
      case 'data_mismatch':
        return 'info';
      default:
        return 'default';
    }
  };

  const formatDateTime = (dateTime: string) => {
    try {
      const date = parseISO(dateTime);
      return format(date, 'MMM dd, yyyy h:mm a');
    } catch {
      return dateTime;
    }
  };

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="md"
      fullWidth
      PaperProps={{
        sx: {
          borderRadius: 3,
          maxHeight: '90vh',
        },
      }}
    >
      <DialogTitle
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          pb: 2,
          background: 'linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%)',
          color: 'white',
          mb: 2,
        }}
      >
        <Box display="flex" alignItems="center" gap={2}>
          <WarningIcon />
          <Typography variant="h6" fontWeight={600}>
            Calendar Sync Conflicts ({conflicts.length})
          </Typography>
        </Box>
        <IconButton onClick={onClose} sx={{ color: 'white' }}>
          <CloseIcon />
        </IconButton>
      </DialogTitle>

      <DialogContent sx={{ px: 3 }}>
        <Alert severity="warning" sx={{ mb: 3 }}>
          <Typography variant="body2">
            We found {conflicts.length} conflict{conflicts.length > 1 ? 's' : ''} between your internal appointments and external calendar events. 
            Please choose how to resolve each conflict.
          </Typography>
        </Alert>

        {/* Global Resolution Option */}
        {conflicts.length > 1 && (
          <Card sx={{ mb: 3, bgcolor: 'grey.50' }}>
            <CardContent>
              <Typography variant="subtitle1" fontWeight={600} gutterBottom>
                Resolve All Conflicts
              </Typography>
              <RadioGroup
                value={globalResolution}
                onChange={(e) => setGlobalResolution(e.target.value)}
                row
              >
                <FormControlLabel
                  value="keep_internal"
                  control={<Radio size="small" />}
                  label="Keep Internal"
                />
                <FormControlLabel
                  value="keep_external"
                  control={<Radio size="small" />}
                  label="Keep External"
                />
                <FormControlLabel
                  value="merge"
                  control={<Radio size="small" />}
                  label="Merge Both"
                />
              </RadioGroup>
              <Button
                variant="contained"
                size="small"
                onClick={handleResolveAll}
                disabled={!globalResolution}
                sx={{ mt: 1 }}
              >
                Apply to All
              </Button>
            </CardContent>
          </Card>
        )}

        <Divider sx={{ mb: 3 }} />

        {/* Individual Conflicts */}
        <Box sx={{ maxHeight: '400px', overflowY: 'auto' }}>
          {conflicts.map((conflict, index) => (
            <Card key={conflict.id} sx={{ mb: 2, border: '1px solid', borderColor: 'grey.200' }}>
              <CardContent>
                <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
                  <Box display="flex" alignItems="center" gap={2}>
                    <Typography variant="h6" fontWeight={600}>
                      Conflict #{index + 1}
                    </Typography>
                    <Chip
                      label={conflict.conflict_type.replace('_', ' ').toUpperCase()}
                      color={getConflictTypeColor(conflict.conflict_type) as any}
                      size="small"
                    />
                  </Box>
                </Box>

                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  {conflict.conflict_details?.description || 'No description available'}
                </Typography>

                {/* Internal Appointment */}
                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" fontWeight={600} color="primary.main" gutterBottom>
                    📅 Internal Appointment
                  </Typography>
                  <Card variant="outlined" sx={{ bgcolor: 'primary.50' }}>
                    <CardContent sx={{ py: 2 }}>
                      <Box display="flex" alignItems="center" gap={2} mb={1}>
                        <PersonIcon fontSize="small" />
                        <Typography variant="body2">
                          {conflict.conflict_details?.internal_appointment?.patientName} - {conflict.conflict_details?.internal_appointment?.appointmentType}
                        </Typography>
                      </Box>
                      <Box display="flex" alignItems="center" gap={2}>
                        <ScheduleIcon fontSize="small" />
                        <Typography variant="body2">
                          {formatDateTime(conflict.conflict_details?.internal_appointment?.date + 'T' + conflict.conflict_details?.internal_appointment?.time)}
                          {' '}({conflict.conflict_details?.internal_appointment?.duration} min)
                        </Typography>
                      </Box>
                    </CardContent>
                  </Card>
                </Box>

                {/* External Event */}
                <Box sx={{ mb: 3 }}>
                  <Typography variant="subtitle2" fontWeight={600} color="secondary.main" gutterBottom>
                    🔗 External Calendar Event
                  </Typography>
                  <Card variant="outlined" sx={{ bgcolor: 'secondary.50' }}>
                    <CardContent sx={{ py: 2 }}>
                      <Box display="flex" alignItems="center" gap={2} mb={1}>
                        <CalendarIcon fontSize="small" />
                        <Typography variant="body2">
                          {conflict.conflict_details?.external_event?.title}
                        </Typography>
                      </Box>
                      <Box display="flex" alignItems="center" gap={2}>
                        <ScheduleIcon fontSize="small" />
                        <Typography variant="body2">
                          {formatDateTime(conflict.conflict_details?.external_event?.start_time)} - {formatDateTime(conflict.conflict_details?.external_event?.end_time)}
                        </Typography>
                      </Box>
                      {conflict.conflict_details?.external_event?.calendar_name && (
                        <Typography variant="caption" color="text.secondary">
                          From: {conflict.conflict_details.external_event.calendar_name}
                        </Typography>
                      )}
                    </CardContent>
                  </Card>
                </Box>

                {/* Resolution Options */}
                <Box>
                  <Typography variant="subtitle2" fontWeight={600} gutterBottom>
                    Resolution
                  </Typography>
                  <RadioGroup
                    value={selectedResolutions[conflict.id] || ''}
                    onChange={(e) => handleResolutionChange(conflict.id, e.target.value)}
                  >
                    <FormControlLabel
                      value="keep_internal"
                      control={<Radio size="small" />}
                      label={
                        <Box>
                          <Typography variant="body2" fontWeight={500}>
                            Keep Internal Appointment
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            Remove the external event from display
                          </Typography>
                        </Box>
                      }
                    />
                    <FormControlLabel
                      value="keep_external"
                      control={<Radio size="small" />}
                      label={
                        <Box>
                          <Typography variant="body2" fontWeight={500}>
                            Keep External Event
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            Hide the internal appointment for this time slot
                          </Typography>
                        </Box>
                      }
                    />
                    <FormControlLabel
                      value="merge"
                      control={<Radio size="small" />}
                      label={
                        <Box>
                          <Typography variant="body2" fontWeight={500}>
                            Show Both (Merge)
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            Display both events with visual indicators
                          </Typography>
                        </Box>
                      }
                    />
                  </RadioGroup>

                  <Button
                    variant="outlined"
                    size="small"
                    onClick={() => handleResolveConflict(conflict)}
                    disabled={!selectedResolutions[conflict.id]}
                    sx={{ mt: 2 }}
                  >
                    Resolve This Conflict
                  </Button>
                </Box>
              </CardContent>
            </Card>
          ))}
        </Box>
      </DialogContent>

      <DialogActions sx={{ px: 3, py: 2 }}>
        <Button onClick={onClose} color="inherit">
          Cancel
        </Button>
        <Button
          variant="contained"
          onClick={() => {
            // Resolve all conflicts with individual selections
            Object.entries(selectedResolutions).forEach(([conflictId, resolution]) => {
              onResolve(conflictId, resolution as 'keep_internal' | 'keep_external' | 'merge');
            });
            onClose();
          }}
          disabled={Object.keys(selectedResolutions).length === 0}
        >
          Resolve Selected
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default ConflictResolutionDialog;