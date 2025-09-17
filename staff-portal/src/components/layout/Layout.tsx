import React, { useEffect } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import {
  Box,
  Drawer,
  AppBar,
  Toolbar,
  useTheme,
  useMediaQuery,
} from '@mui/material';
import type { RootState } from '../../store';
import { setSidebarMobile, setOnlineStatus } from '../../store/slices/uiSlice';
import { Header } from './Header';
import { Sidebar } from './Sidebar';
import { Breadcrumbs } from './Breadcrumbs';

interface LayoutProps {
  children: React.ReactNode;
}

const DRAWER_WIDTH = 280;
const DRAWER_WIDTH_COLLAPSED = 64;

export const Layout: React.FC<LayoutProps> = ({ children }) => {
  const theme = useTheme();
  const dispatch = useDispatch();
  const isMobile = useMediaQuery(theme.breakpoints.down('lg'));
  
  const { sidebarCollapsed, sidebarMobile } = useSelector(
    (state: RootState) => state.ui
  );

  // Handle mobile sidebar state
  useEffect(() => {
    dispatch(setSidebarMobile(isMobile));
  }, [isMobile, dispatch]);

  // Handle online/offline status
  useEffect(() => {
    const handleConnectionChange = (event: CustomEvent) => {
      dispatch(setOnlineStatus(event.detail.isOnline));
    };

    window.addEventListener('connection-change', handleConnectionChange as EventListener);
    
    return () => {
      window.removeEventListener('connection-change', handleConnectionChange as EventListener);
    };
  }, [dispatch]);

  const drawerWidth = isMobile
    ? DRAWER_WIDTH
    : sidebarCollapsed
    ? DRAWER_WIDTH_COLLAPSED
    : DRAWER_WIDTH;

  const sidebarContent = <Sidebar />;

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh' }}>
      {/* App Bar */}
      <AppBar
        position="fixed"
        sx={{
          zIndex: theme.zIndex.drawer + 1,
          transition: theme.transitions.create(['width', 'margin'], {
            easing: theme.transitions.easing.sharp,
            duration: theme.transitions.duration.leavingScreen,
          }),
        }}
      >
        <Header />
      </AppBar>

      {/* Sidebar */}
      {isMobile ? (
        // Mobile drawer
        <Drawer
          variant="temporary"
          open={sidebarMobile}
          onClose={() => dispatch(setSidebarMobile(false))}
          ModalProps={{
            keepMounted: true, // Better open performance on mobile
          }}
          sx={{
            '& .MuiDrawer-paper': {
              width: DRAWER_WIDTH,
              boxSizing: 'border-box',
            },
          }}
        >
          {sidebarContent}
        </Drawer>
      ) : (
        // Desktop drawer
        <Drawer
          variant="permanent"
          sx={{
            width: drawerWidth,
            flexShrink: 0,
            '& .MuiDrawer-paper': {
              width: drawerWidth,
              boxSizing: 'border-box',
              transition: theme.transitions.create('width', {
                easing: theme.transitions.easing.sharp,
                duration: theme.transitions.duration.enteringScreen,
              }),
              overflowX: 'hidden',
            },
          }}
        >
          {sidebarContent}
        </Drawer>
      )}

      {/* Main content */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          display: 'flex',
          flexDirection: 'column',
          transition: theme.transitions.create('margin', {
            easing: theme.transitions.easing.sharp,
            duration: theme.transitions.duration.leavingScreen,
          }),
        }}
      >
        {/* Toolbar spacer */}
        <Toolbar />
        
        {/* Breadcrumbs */}
        <Box sx={{ px: 3, py: 2, borderBottom: 1, borderColor: 'divider' }}>
          <Breadcrumbs />
        </Box>
        
        {/* Page content */}
        <Box
          sx={{
            flexGrow: 1,
            p: 3,
            backgroundColor: theme.palette.background.default,
            minHeight: 'calc(100vh - 64px)', // Account for app bar height
          }}
        >
          {children}
        </Box>
      </Box>
    </Box>
  );
};