// Sophisticated Medical-Grade Color Palette
export const medicalColors = {
  // Primary Medical Blues - Professional and trustworthy
  primary: {
    50: '#e3f2fd',
    100: '#bbdefb',
    200: '#90caf9',
    300: '#64b5f6',
    400: '#42a5f5',
    500: '#2196f3',
    600: '#1e88e5',
    700: '#1976d2',
    800: '#1565c0',
    900: '#0d47a1',
    main: '#1976d2',
    light: '#42a5f5',
    dark: '#1565c0',
  },

  // Medical Teal - Calming and professional
  secondary: {
    50: '#e0f2f1',
    100: '#b2dfdb',
    200: '#80cbc4',
    300: '#4db6ac',
    400: '#26a69a',
    500: '#009688',
    600: '#00897b',
    700: '#00796b',
    800: '#00695c',
    900: '#004d40',
    main: '#00897b',
    light: '#4db6ac',
    dark: '#00695c',
  },

  // Success Green - Health and wellness
  success: {
    50: '#e8f5e8',
    100: '#c8e6c9',
    200: '#a5d6a7',
    300: '#81c784',
    400: '#66bb6a',
    500: '#4caf50',
    600: '#43a047',
    700: '#388e3c',
    800: '#2e7d32',
    900: '#1b5e20',
    main: '#4caf50',
    light: '#81c784',
    dark: '#388e3c',
  },

  // Warning Orange - Attention and alerts
  warning: {
    50: '#fff3e0',
    100: '#ffe0b2',
    200: '#ffcc80',
    300: '#ffb74d',
    400: '#ffa726',
    500: '#ff9800',
    600: '#fb8c00',
    700: '#f57c00',
    800: '#ef6c00',
    900: '#e65100',
    main: '#ff9800',
    light: '#ffb74d',
    dark: '#f57c00',
  },

  // Error Red - Critical alerts
  error: {
    50: '#ffebee',
    100: '#ffcdd2',
    200: '#ef9a9a',
    300: '#e57373',
    400: '#ef5350',
    500: '#f44336',
    600: '#e53935',
    700: '#d32f2f',
    800: '#c62828',
    900: '#b71c1c',
    main: '#d32f2f',
    light: '#ef5350',
    dark: '#c62828',
  },

  // Neutral Grays - Professional text and backgrounds
  neutral: {
    50: '#fafafa',
    100: '#f5f5f5',
    200: '#eeeeee',
    300: '#e0e0e0',
    400: '#bdbdbd',
    500: '#9e9e9e',
    600: '#757575',
    700: '#616161',
    800: '#424242',
    900: '#212121',
    white: '#ffffff',
    black: '#000000',
  },

  // Medical Specific Colors
  medical: {
    // Deep medical blue for headers and important text
    deepBlue: '#1a365d',
    mediumBlue: '#2d5aa0',
    
    // Professional text colors
    textPrimary: '#1a365d',
    textSecondary: '#546e7a',
    textMuted: '#78909c',
    
    // Background variations
    backgroundPrimary: '#ffffff',
    backgroundSecondary: '#f8fafc',
    backgroundTertiary: '#f1f5f9',
    
    // Accent colors for highlights
    accent: '#0288d1',
    accentLight: '#03a9f4',
    accentDark: '#0277bd',
  },

  // Gradient Definitions
  gradients: {
    primary: 'linear-gradient(135deg, #1976d2 0%, #1565c0 100%)',
    primaryLight: 'linear-gradient(135deg, #42a5f5 0%, #1976d2 100%)',
    primaryDark: 'linear-gradient(135deg, #1565c0 0%, #0d47a1 100%)',
    
    secondary: 'linear-gradient(135deg, #00897b 0%, #00695c 100%)',
    secondaryLight: 'linear-gradient(135deg, #4db6ac 0%, #00897b 100%)',
    
    success: 'linear-gradient(135deg, #4caf50 0%, #388e3c 100%)',
    warning: 'linear-gradient(135deg, #ff9800 0%, #f57c00 100%)',
    error: 'linear-gradient(135deg, #f44336 0%, #d32f2f 100%)',
    
    // Medical specific gradients
    medical: 'linear-gradient(135deg, #1a365d 0%, #2d5aa0 100%)',
    medicalAccent: 'linear-gradient(135deg, #0288d1 0%, #0277bd 100%)',
    
    // Background gradients
    backgroundHero: 'linear-gradient(135deg, #e3f2fd 0%, #bbdefb 50%, #90caf9 100%)',
    backgroundSection: 'linear-gradient(180deg, #f8fafc 0%, #ffffff 100%)',
    backgroundCard: 'linear-gradient(145deg, #ffffff 0%, #f8fafc 100%)',
    
    // Glass morphism effects
    glass: 'linear-gradient(145deg, rgba(255, 255, 255, 0.25) 0%, rgba(255, 255, 255, 0.1) 100%)',
    glassBlue: 'linear-gradient(145deg, rgba(25, 118, 210, 0.1) 0%, rgba(21, 101, 192, 0.05) 100%)',
  },

  // Shadow Definitions
  shadows: {
    small: '0 2px 8px rgba(25, 118, 210, 0.1)',
    medium: '0 4px 16px rgba(25, 118, 210, 0.15)',
    large: '0 8px 32px rgba(25, 118, 210, 0.2)',
    xlarge: '0 12px 48px rgba(25, 118, 210, 0.25)',
    
    // Colored shadows
    primary: '0 8px 32px rgba(25, 118, 210, 0.3)',
    secondary: '0 8px 32px rgba(0, 137, 123, 0.3)',
    success: '0 8px 32px rgba(76, 175, 80, 0.3)',
    warning: '0 8px 32px rgba(255, 152, 0, 0.3)',
    error: '0 8px 32px rgba(244, 67, 54, 0.3)',
    
    // Hover shadows
    hoverSmall: '0 4px 12px rgba(25, 118, 210, 0.2)',
    hoverMedium: '0 8px 24px rgba(25, 118, 210, 0.25)',
    hoverLarge: '0 12px 40px rgba(25, 118, 210, 0.3)',
  },
};

// Animation Easing Functions
export const easings = {
  easeInOut: 'cubic-bezier(0.4, 0, 0.2, 1)',
  easeOut: 'cubic-bezier(0.0, 0, 0.2, 1)',
  easeIn: 'cubic-bezier(0.4, 0, 1, 1)',
  sharp: 'cubic-bezier(0.4, 0, 0.6, 1)',
  smooth: 'cubic-bezier(0.25, 0.46, 0.45, 0.94)',
  bounce: 'cubic-bezier(0.68, -0.55, 0.265, 1.55)',
};

// Animation Durations
export const durations = {
  shortest: 150,
  shorter: 200,
  short: 250,
  standard: 300,
  complex: 375,
  enteringScreen: 225,
  leavingScreen: 195,
};