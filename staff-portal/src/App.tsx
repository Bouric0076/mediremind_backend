import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Provider } from 'react-redux';
import { PersistGate } from 'redux-persist/integration/react';
import { ThemeProvider, CssBaseline, CircularProgress, Box } from '@mui/material';
import { store, persistor } from './store';
import { theme } from './theme';
import { AuthGuard } from './components/auth/AuthGuard';
import { SessionMonitor } from './components/auth/SessionMonitor';
import { Layout } from './components/layout/Layout';
import { LoginPage } from './pages/auth/LoginPage';
import { HospitalRegistrationPage } from './pages/auth/HospitalRegistrationPage';
import LandingPage from './pages/landing/LandingPage';
import { DashboardPage } from './pages/dashboard/DashboardPage';
import { PatientsPage } from './pages/patients/PatientsPage';
import { AddPatientPage } from './pages/patients/AddPatientPage';
import { PatientDetailPage } from './pages/patients/PatientDetailPage';
import { AppointmentsPage } from './pages/appointments/AppointmentsPage';
import { NotificationsPage } from './pages/notifications/NotificationsPage';
import { PrescriptionsPage } from './pages/prescriptions/PrescriptionsPage';
import { ReportsPage } from './pages/reports/ReportsPage';
import { SettingsPage } from './pages/settings/SettingsPage';

// Calendar Integration Pages
import CalendarIntegrationPage from './pages/calendar/CalendarIntegrationPage';

// Staff Management Pages
import { StaffDirectoryPage } from './pages/staff/StaffDirectoryPage';
import { StaffProfilePage } from './pages/staff/StaffProfilePage';
import { CredentialManagementPage } from './pages/staff/CredentialManagementPage';

// Billing & Financial Management Pages
import { InvoiceManagementPage } from './pages/billing/InvoiceManagementPage';
import { PaymentProcessingPage } from './pages/billing/PaymentProcessingPage';
import { InsuranceClaimsPage } from './pages/billing/InsuranceClaimsPage';

// Medical Records Management Pages
import { MedicalRecordsPage } from './pages/medical/MedicalRecordsPage';
import { ClinicalNotesPage } from './pages/medical/ClinicalNotesPage';
import { MedicalHistoryTimelinePage } from './pages/medical/MedicalHistoryTimelinePage';
// Analytics
import AdvancedAnalyticsDashboard from './pages/analytics/AdvancedAnalyticsDashboard';

// System Administration Pages
import UserRoleManagementPage from './pages/admin/UserRoleManagementPage';
import SystemConfigurationPage from './pages/admin/SystemConfigurationPage';
import { ErrorBoundary } from './components/common/ErrorBoundary';
import { ToastContainer } from './components/common/ToastContainer';

// Loading component for PersistGate
const LoadingComponent = () => (
  <Box
    display="flex"
    justifyContent="center"
    alignItems="center"
    minHeight="100vh"
  >
    <CircularProgress />
  </Box>
);

function App() {
  return (
    <Provider store={store}>
      <PersistGate loading={<LoadingComponent />} persistor={persistor}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <ErrorBoundary>
          <Router>
            <Routes>
              {/* Public routes */}
              <Route path="/" element={<LandingPage />} />
              <Route path="/login" element={<LoginPage />} />
              <Route path="/register" element={<HospitalRegistrationPage />} />
              
              {/* Protected routes */}
              <Route
                path="/app/*"
                element={
                  <AuthGuard>
                    <Layout>
                      <Routes>
                        <Route path="/" element={<Navigate to="/app/dashboard" replace />} />
                        <Route path="/dashboard" element={<DashboardPage />} />
                        <Route path="/patients" element={<PatientsPage />} />
                        <Route path="/patients/new" element={<AddPatientPage />} />
                        <Route path="/patients/:id" element={<PatientDetailPage />} />
                        <Route path="/appointments" element={<AppointmentsPage />} />
                        <Route path="/appointments/:id" element={<AppointmentsPage />} />
                        <Route path="/notifications" element={<NotificationsPage />} />
                        <Route path="/prescriptions" element={<PrescriptionsPage />} />
                        <Route path="/reports" element={<ReportsPage />} />
                        <Route path="/settings" element={<SettingsPage />} />
                        
                        {/* Calendar Integration Routes */}
                        <Route path="/calendar" element={<CalendarIntegrationPage />} />
                        <Route path="/calendar/integration" element={<CalendarIntegrationPage />} />
                        
                        {/* Staff Management Routes */}
                        <Route path="/staff" element={<StaffDirectoryPage />} />
                        <Route path="/staff/directory" element={<StaffDirectoryPage />} />
                        <Route path="/staff/profile/:id" element={<StaffProfilePage />} />
                        <Route path="/staff/credentials" element={<CredentialManagementPage />} />
                        
                        {/* Billing & Financial Management Routes */}
                        <Route path="/billing" element={<InvoiceManagementPage />} />
                        <Route path="/billing/invoices" element={<InvoiceManagementPage />} />
                        <Route path="/billing/payments" element={<PaymentProcessingPage />} />
                        <Route path="/billing/insurance" element={<InsuranceClaimsPage />} />
                        
                        {/* Medical Records Management Routes */}
                        <Route path="/medical" element={<MedicalRecordsPage />} />
                        <Route path="/medical/records" element={<MedicalRecordsPage />} />
              <Route path="/medical/notes" element={<ClinicalNotesPage />} />
              <Route path="/medical/timeline" element={<MedicalHistoryTimelinePage />} />
              {/* Analytics */}
              <Route path="/analytics/dashboard" element={<AdvancedAnalyticsDashboard />} />
              
              {/* System Administration Routes */}
              <Route path="/admin/users" element={<UserRoleManagementPage />} />
              <Route path="/admin/config" element={<SystemConfigurationPage />} />
                        
                        <Route path="*" element={<Navigate to="/app/dashboard" replace />} />
                      </Routes>
                    </Layout>
                  </AuthGuard>
                }
              />
            </Routes>
          </Router>
          <SessionMonitor />
          <ToastContainer />
        </ErrorBoundary>
      </ThemeProvider>
      </PersistGate>
    </Provider>
  );
}

export default App;
