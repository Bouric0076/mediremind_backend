import { createTheme } from '@mui/material/styles';
import type { ThemeOptions } from '@mui/material/styles';

// Color palette as specified in the roadmap
const colors = {
  primary: {
    50: '#e3f2fd',
    100: '#bbdefb',
    500: '#2196f3', // Main brand color
    700: '#1976d2',
    900: '#0d47a1',
  },
  secondary: {
    50: '#f3e5f5',
    500: '#9c27b0',
    700: '#7b1fa2',
  },
  success: {
    main: '#4caf50',
  },
  warning: {
    main: '#ff9800',
  },
  error: {
    main: '#f44336',
  },
  info: {
    main: '#2196f3',
  },
  grey: {
    50: '#fafafa',
    100: '#f5f5f5',
    300: '#e0e0e0',
    500: '#9e9e9e',
    700: '#616161',
    900: '#212121',
  },
};

// Typography configuration
const typography = {
  fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
  h1: {
    fontSize: '2.25rem', // 36px
    fontWeight: 700,
    lineHeight: 1.2,
  },
  h2: {
    fontSize: '1.875rem', // 30px
    fontWeight: 600,
    lineHeight: 1.3,
  },
  h3: {
    fontSize: '1.5rem', // 24px
    fontWeight: 600,
    lineHeight: 1.4,
  },
  h4: {
    fontSize: '1.25rem', // 20px
    fontWeight: 600,
    lineHeight: 1.4,
  },
  h5: {
    fontSize: '1.125rem', // 18px
    fontWeight: 500,
    lineHeight: 1.4,
  },
  h6: {
    fontSize: '1rem', // 16px
    fontWeight: 500,
    lineHeight: 1.4,
  },
  body1: {
    fontSize: '1rem', // 16px
    fontWeight: 400,
    lineHeight: 1.5,
  },
  body2: {
    fontSize: '0.875rem', // 14px
    fontWeight: 400,
    lineHeight: 1.5,
  },
  caption: {
    fontSize: '0.75rem', // 12px
    fontWeight: 400,
    lineHeight: 1.4,
  },
};

// Spacing system (4px base unit)
const spacing = (factor: number) => `${0.25 * factor}rem`;

// Component overrides
const components = {
  MuiButton: {
    styleOverrides: {
      root: {
        borderRadius: '0.5rem',
        textTransform: 'none' as const,
        fontWeight: 500,
        padding: '0.75rem 1.5rem',
        transition: 'all 0.2s ease',
        '&:hover': {
          transform: 'translateY(-1px)',
        },
      },
      contained: {
        boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
        '&:hover': {
          boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
        },
      },
    },
  },
  MuiCard: {
    styleOverrides: {
      root: {
        borderRadius: '0.75rem',
        boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
        transition: 'box-shadow 0.2s ease',
        '&:hover': {
          boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
        },
      },
    },
  },
  MuiTextField: {
    styleOverrides: {
      root: {
        '& .MuiOutlinedInput-root': {
          borderRadius: '0.5rem',
          transition: 'all 0.15s ease',
          '&:hover': {
            '& .MuiOutlinedInput-notchedOutline': {
              borderColor: colors.primary[500],
            },
          },
          '&.Mui-focused': {
            '& .MuiOutlinedInput-notchedOutline': {
              borderColor: colors.primary[500],
              borderWidth: '2px',
            },
          },
        },
      },
    },
  },
};

// Light theme configuration
const lightTheme: ThemeOptions = {
  palette: {
    mode: 'light',
    primary: {
      main: colors.primary[500],
      light: colors.primary[100],
      dark: colors.primary[700],
    },
    secondary: {
      main: colors.secondary[500],
      light: colors.secondary[50],
      dark: colors.secondary[700],
    },
    success: colors.success,
    warning: colors.warning,
    error: colors.error,
    info: colors.info,
    grey: colors.grey,
    background: {
      default: colors.grey[50],
      paper: '#ffffff',
    },
    text: {
      primary: colors.grey[900],
      secondary: colors.grey[700],
    },
  },
  typography,
  spacing,
  components,
  shape: {
    borderRadius: 8,
  },
};

// Dark theme configuration
const darkThemeConfig: ThemeOptions = {
  palette: {
    mode: 'dark',
    primary: {
      main: colors.primary[500],
      light: colors.primary[100],
      dark: colors.primary[700],
    },
    secondary: {
      main: colors.secondary[500],
      light: colors.secondary[50],
      dark: colors.secondary[700],
    },
    success: colors.success,
    warning: colors.warning,
    error: colors.error,
    info: colors.info,
    background: {
      default: '#121212',
      paper: '#1e1e1e',
    },
    text: {
      primary: '#ffffff',
      secondary: colors.grey[300],
    },
  },
  typography,
  spacing,
  components,
  shape: {
    borderRadius: 8,
  },
};

export const theme = createTheme(lightTheme);
export const darkTheme = createTheme(darkThemeConfig);
export default theme;