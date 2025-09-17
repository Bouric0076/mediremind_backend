import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Tab,
  Tabs,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Checkbox,
  FormControlLabel,
  Grid,
  Avatar,
  Menu,
  ListItemIcon,
  ListItemText,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  MoreVert as MoreVertIcon,
  Person as PersonIcon,
  Security as SecurityIcon,
  AdminPanelSettings as AdminIcon,
  Group as GroupIcon,
  Lock as LockIcon,
  Visibility as ViewIcon,
} from '@mui/icons-material';


interface User {
  id: string;
  name: string;
  email: string;
  role: string;
  department: string;
  status: 'active' | 'inactive' | 'suspended';
  lastLogin: string;
  avatar?: string;
}

interface Role {
  id: string;
  name: string;
  description: string;
  permissions: string[];
  userCount: number;
  isSystem: boolean;
}

interface Permission {
  id: string;
  name: string;
  description: string;
  category: string;
}

// Mock data
const mockUsers: User[] = [
  {
    id: '1',
    name: 'Dr. Sarah Johnson',
    email: 'sarah.johnson@mediremind.com',
    role: 'Doctor',
    department: 'Cardiology',
    status: 'active',
    lastLogin: '2024-01-15 09:30:00',
  },
  {
    id: '2',
    name: 'Mike Chen',
    email: 'mike.chen@mediremind.com',
    role: 'Nurse',
    department: 'Emergency',
    status: 'active',
    lastLogin: '2024-01-15 08:45:00',
  },
  {
    id: '3',
    name: 'Admin User',
    email: 'admin@mediremind.com',
    role: 'Administrator',
    department: 'IT',
    status: 'active',
    lastLogin: '2024-01-15 10:15:00',
  },
];

const mockRoles: Role[] = [
  {
    id: '1',
    name: 'Administrator',
    description: 'Full system access and management capabilities',
    permissions: ['user_management', 'system_config', 'all_patients', 'reports'],
    userCount: 2,
    isSystem: true,
  },
  {
    id: '2',
    name: 'Doctor',
    description: 'Medical professionals with patient care access',
    permissions: ['patient_read', 'patient_write', 'prescriptions', 'medical_records'],
    userCount: 15,
    isSystem: false,
  },
  {
    id: '3',
    name: 'Nurse',
    description: 'Nursing staff with limited patient access',
    permissions: ['patient_read', 'vital_signs', 'basic_records'],
    userCount: 25,
    isSystem: false,
  },
];

const mockPermissions: Permission[] = [
  { id: '1', name: 'user_management', description: 'Manage users and roles', category: 'Administration' },
  { id: '2', name: 'system_config', description: 'Configure system settings', category: 'Administration' },
  { id: '3', name: 'patient_read', description: 'View patient information', category: 'Patient Care' },
  { id: '4', name: 'patient_write', description: 'Edit patient information', category: 'Patient Care' },
  { id: '5', name: 'prescriptions', description: 'Manage prescriptions', category: 'Medical' },
  { id: '6', name: 'medical_records', description: 'Access medical records', category: 'Medical' },
];

const UserRoleManagementPage: React.FC = () => {
  const [currentTab, setCurrentTab] = useState(0);
  const [users] = useState<User[]>(mockUsers);
  const [roles] = useState<Role[]>(mockRoles);
  const [permissions] = useState<Permission[]>(mockPermissions);
  
  // Dialog states
  const [userDialogOpen, setUserDialogOpen] = useState(false);
  const [roleDialogOpen, setRoleDialogOpen] = useState(false);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [selectedRole, setSelectedRole] = useState<Role | null>(null);
  
  // Menu states
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [menuUserId, setMenuUserId] = useState<string | null>(null);

  const handleTabChange = (_: React.SyntheticEvent, newValue: number) => {
    setCurrentTab(newValue);
  };

  const handleUserMenuClick = (event: React.MouseEvent<HTMLElement>, userId: string) => {
    setAnchorEl(event.currentTarget);
    setMenuUserId(userId);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
    setMenuUserId(null);
  };

  const handleEditUser = (user: User) => {
    setSelectedUser(user);
    setUserDialogOpen(true);
    handleMenuClose();
  };

  const handleEditRole = (role: Role) => {
    setSelectedRole(role);
    setRoleDialogOpen(true);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'success';
      case 'inactive': return 'default';
      case 'suspended': return 'error';
      default: return 'default';
    }
  };

  const renderUsersTab = () => (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h6">User Management</Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => {
            setSelectedUser(null);
            setUserDialogOpen(true);
          }}
        >
          Add User
        </Button>
      </Box>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>User</TableCell>
              <TableCell>Role</TableCell>
              <TableCell>Department</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Last Login</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {users.map((user) => (
              <TableRow key={user.id}>
                <TableCell>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                    <Avatar src={user.avatar}>
                      <PersonIcon />
                    </Avatar>
                    <Box>
                      <Typography variant="subtitle2">{user.name}</Typography>
                      <Typography variant="body2" color="text.secondary">
                        {user.email}
                      </Typography>
                    </Box>
                  </Box>
                </TableCell>
                <TableCell>
                  <Chip label={user.role} size="small" />
                </TableCell>
                <TableCell>{user.department}</TableCell>
                <TableCell>
                  <Chip
                    label={user.status}
                    size="small"
                    color={getStatusColor(user.status) as any}
                  />
                </TableCell>
                <TableCell>{new Date(user.lastLogin).toLocaleString()}</TableCell>
                <TableCell align="right">
                  <IconButton
                    onClick={(e) => handleUserMenuClick(e, user.id)}
                  >
                    <MoreVertIcon />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
      >
        <MenuItem onClick={() => {
          const user = users.find(u => u.id === menuUserId);
          if (user) handleEditUser(user);
        }}>
          <ListItemIcon><EditIcon /></ListItemIcon>
          <ListItemText>Edit User</ListItemText>
        </MenuItem>
        <MenuItem onClick={handleMenuClose}>
          <ListItemIcon><ViewIcon /></ListItemIcon>
          <ListItemText>View Details</ListItemText>
        </MenuItem>
        <MenuItem onClick={handleMenuClose}>
          <ListItemIcon><LockIcon /></ListItemIcon>
          <ListItemText>Reset Password</ListItemText>
        </MenuItem>
        <MenuItem onClick={handleMenuClose}>
          <ListItemIcon><DeleteIcon /></ListItemIcon>
          <ListItemText>Deactivate</ListItemText>
        </MenuItem>
      </Menu>
    </Box>
  );

  const renderRolesTab = () => (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h6">Role Management</Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => {
            setSelectedRole(null);
            setRoleDialogOpen(true);
          }}
        >
          Add Role
        </Button>
      </Box>

      <Grid container spacing={3}>
        {roles.map((role) => (
          <Grid size={{ xs: 12, md: 6, lg: 4 }} key={role.id}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                  <Avatar sx={{ bgcolor: 'primary.main' }}>
                    {role.isSystem ? <AdminIcon /> : <GroupIcon />}
                  </Avatar>
                  <Box sx={{ flexGrow: 1 }}>
                    <Typography variant="h6">{role.name}</Typography>
                    <Typography variant="body2" color="text.secondary">
                      {role.userCount} users
                    </Typography>
                  </Box>
                  <IconButton onClick={() => handleEditRole(role)}>
                    <EditIcon />
                  </IconButton>
                </Box>
                <Typography variant="body2" sx={{ mb: 2 }}>
                  {role.description}
                </Typography>
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                  {role.permissions.slice(0, 3).map((permission) => (
                    <Chip key={permission} label={permission} size="small" variant="outlined" />
                  ))}
                  {role.permissions.length > 3 && (
                    <Chip label={`+${role.permissions.length - 3} more`} size="small" variant="outlined" />
                  )}
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Box>
  );

  const renderPermissionsTab = () => {
    const permissionsByCategory = permissions.reduce((acc, permission) => {
      if (!acc[permission.category]) {
        acc[permission.category] = [];
      }
      acc[permission.category].push(permission);
      return acc;
    }, {} as Record<string, Permission[]>);

    return (
      <Box>
        <Typography variant="h6" sx={{ mb: 3 }}>Permission Management</Typography>
        
        {Object.entries(permissionsByCategory).map(([category, categoryPermissions]) => (
          <Card key={category} sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
                <SecurityIcon />
                {category}
              </Typography>
              <Grid container spacing={2}>
                {categoryPermissions.map((permission) => (
                  <Grid size={{ xs: 12, sm: 6, md: 4 }} key={permission.id}>
                    <Box sx={{ p: 2, border: 1, borderColor: 'divider', borderRadius: 1 }}>
                      <Typography variant="subtitle2">{permission.name}</Typography>
                      <Typography variant="body2" color="text.secondary">
                        {permission.description}
                      </Typography>
                    </Box>
                  </Grid>
                ))}
              </Grid>
            </CardContent>
          </Card>
        ))}
      </Box>
    );
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" sx={{ mb: 3 }}>User & Role Management</Typography>
      
      <Card>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={currentTab} onChange={handleTabChange}>
            <Tab label="Users" />
            <Tab label="Roles" />
            <Tab label="Permissions" />
          </Tabs>
        </Box>
        <CardContent>
          {currentTab === 0 && renderUsersTab()}
          {currentTab === 1 && renderRolesTab()}
          {currentTab === 2 && renderPermissionsTab()}
        </CardContent>
      </Card>

      {/* User Dialog */}
      <Dialog open={userDialogOpen} onClose={() => setUserDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>{selectedUser ? 'Edit User' : 'Add New User'}</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField
                fullWidth
                label="Full Name"
                defaultValue={selectedUser?.name || ''}
              />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField
                fullWidth
                label="Email"
                type="email"
                defaultValue={selectedUser?.email || ''}
              />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <FormControl fullWidth>
                <InputLabel>Role</InputLabel>
                <Select defaultValue={selectedUser?.role || ''}>
                  {roles.map((role) => (
                    <MenuItem key={role.id} value={role.name}>{role.name}</MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField
                fullWidth
                label="Department"
                defaultValue={selectedUser?.department || ''}
              />
            </Grid>
            <Grid size={{ xs: 12 }}>
              <FormControl fullWidth>
                <InputLabel>Status</InputLabel>
                <Select defaultValue={selectedUser?.status || 'active'}>
                  <MenuItem value="active">Active</MenuItem>
                  <MenuItem value="inactive">Inactive</MenuItem>
                  <MenuItem value="suspended">Suspended</MenuItem>
                </Select>
              </FormControl>
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setUserDialogOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={() => setUserDialogOpen(false)}>Save</Button>
        </DialogActions>
      </Dialog>

      {/* Role Dialog */}
      <Dialog open={roleDialogOpen} onClose={() => setRoleDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>{selectedRole ? 'Edit Role' : 'Add New Role'}</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid size={{ xs: 12 }}>
              <TextField
                fullWidth
                label="Role Name"
                defaultValue={selectedRole?.name || ''}
              />
            </Grid>
            <Grid size={{ xs: 12 }}>
              <TextField
                fullWidth
                label="Description"
                multiline
                rows={3}
                defaultValue={selectedRole?.description || ''}
              />
            </Grid>
            <Grid size={{ xs: 12 }}>
              <Typography variant="subtitle1" sx={{ mb: 2 }}>Permissions</Typography>
              {Object.entries(permissions.reduce((acc, permission) => {
                if (!acc[permission.category]) {
                  acc[permission.category] = [];
                }
                acc[permission.category].push(permission);
                return acc;
              }, {} as Record<string, Permission[]>)).map(([category, categoryPermissions]) => (
                <Box key={category} sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" sx={{ mb: 1 }}>{category}</Typography>
                  {categoryPermissions.map((permission) => (
                    <FormControlLabel
                      key={permission.id}
                      control={
                        <Checkbox
                          defaultChecked={selectedRole?.permissions.includes(permission.name)}
                        />
                      }
                      label={`${permission.name} - ${permission.description}`}
                      sx={{ display: 'block', ml: 2 }}
                    />
                  ))}
                </Box>
              ))}
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setRoleDialogOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={() => setRoleDialogOpen(false)}>Save</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default UserRoleManagementPage;