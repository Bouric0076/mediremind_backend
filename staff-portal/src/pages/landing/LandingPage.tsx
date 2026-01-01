import React, { useEffect, useRef, useState } from 'react';
import {
  Box,
  Container,
  Typography,
  Button,
  Grid,
  Card,
  Stack,
  Avatar,

  IconButton,
  Drawer,
  List,
  ListItem,
  ListItemText,
  useTheme,
  useMediaQuery,
} from '@mui/material';
import {
  CalendarToday,
  LocationOn,
  Person,
  Schedule,
  Phone,
  Email,
  MedicalServices,
  PhoneAndroid,
  Chat,
  Sms,
  Notifications,
  Call,
  Menu as MenuIcon,
  Close as CloseIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { medicalColors, easings, durations } from '../../theme/colors';
import { animations } from '../../utils/animations';

// Import medical images
import healthcareProfessionalImg from '../../assets/images/healthcare-professional.jpg';

// Custom hook for scroll-triggered animations
const useScrollAnimation = (threshold = 0.1) => {
  const [isVisible, setIsVisible] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsVisible(true);
          // Disconnect after first trigger for performance
          observer.disconnect();
        }
      },
      { threshold }
    );

    if (ref.current) {
      observer.observe(ref.current);
    }

    return () => observer.disconnect();
  }, [threshold]);

  return [ref, isVisible] as const;
};

const LandingPage: React.FC = () => {
  const navigate = useNavigate();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  
  // Scroll animation hooks for different sections
  const [featuresRef, featuresVisible] = useScrollAnimation(0.2);
  const [smartNotificationRef, smartNotificationVisible] = useScrollAnimation(0.2);
  const [communicationRef, communicationVisible] = useScrollAnimation(0.2);

  const navigationItems = ['Features', 'Pricing', 'Support'];

  const handleMobileMenuToggle = () => {
    setMobileMenuOpen(!mobileMenuOpen);
  };

  return (
    <Box sx={{ 
      minHeight: '100vh', 
      background: 'linear-gradient(135deg, #f5f9fc 0%, #e8f4f8 100%)'
    }}>
      {/* Header */}
      <Box sx={{ 
        bgcolor: 'rgba(255, 255, 255, 0.95)', 
        py: 3, 
        backdropFilter: 'blur(20px)',
        borderBottom: `1px solid ${medicalColors.neutral[200]}`,
        position: 'sticky',
        top: 0,
        zIndex: 1000,
        boxShadow: medicalColors.shadows.medium,
        animation: `${animations.fadeInDown} ${durations.standard}ms ${easings.easeOut}`,
      }}>
        <Container maxWidth="lg">
          <Stack direction="row" alignItems="center" justifyContent="space-between">
            <Stack direction="row" alignItems="center" spacing={2}>
              <Schedule sx={{ 
                color: medicalColors.primary.main, 
                fontSize: 36,
                filter: `drop-shadow(0 2px 4px ${medicalColors.primary[300]})`,
                animation: `${animations.pulse} ${durations.complex}ms ${easings.easeInOut} infinite`,
              }} />
              <Typography 
                variant="h4" 
                sx={{ 
                  fontWeight: 800, 
                  fontSize: '1.8rem',
                  letterSpacing: '-0.02em',
                  background: medicalColors.gradients.medical,
                  backgroundClip: 'text',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                  animation: `${animations.fadeInLeft} ${durations.complex}ms ${easings.easeOut}`,
                }}
              >
                MediRemind
              </Typography>
            </Stack>
            {/* Desktop Navigation */}
            {!isMobile ? (
              <Stack direction="row" spacing={4} alignItems="center">
                {navigationItems.map((item, index) => (
                  <Typography 
                    key={item}
                    variant="body1" 
                    sx={{ 
                      color: medicalColors.medical.textSecondary, 
                      cursor: 'pointer',
                      fontWeight: 500,
                      transition: `all ${durations.standard}ms ${easings.easeOut}`,
                      animation: `${animations.fadeInDown} ${durations.complex}ms ${easings.easeOut}`,
                      animationDelay: `${(index + 1) * 100}ms`,
                      animationFillMode: 'both',
                      '&:hover': { 
                        color: medicalColors.primary.main,
                        transform: 'translateY(-2px)',
                        textShadow: `0 2px 8px ${medicalColors.primary[200]}`,
                      }
                    }}
                  >
                    {item}
                  </Typography>
                ))}
                <Button
                  variant="contained"
                  sx={{
                    background: medicalColors.gradients.medicalAccent,
                    color: 'white',
                    borderRadius: 3,
                    px: 4,
                    py: 1.5,
                    fontWeight: 600,
                    fontSize: '0.95rem',
                    textTransform: 'none',
                    boxShadow: medicalColors.shadows.primary,
                    transition: `all ${durations.standard}ms ${easings.easeOut}`,
                    animation: `${animations.fadeInRight} ${durations.complex}ms ${easings.easeOut}`,
                    animationDelay: '400ms',
                    animationFillMode: 'both',
                    position: 'relative',
                    overflow: 'hidden',
                    '&:hover': { 
                      background: medicalColors.gradients.primaryDark,
                      transform: 'translateY(-2px)',
                      boxShadow: medicalColors.shadows.hoverLarge,
                    },
                    '&::before': {
                      content: '""',
                      position: 'absolute',
                      top: 0,
                      left: '-100%',
                      width: '100%',
                      height: '100%',
                      background: 'linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent)',
                      transition: `left ${durations.complex}ms ${easings.easeOut}`,
                    },
                    '&:hover::before': {
                      left: '100%',
                    },
                  }}
                  onClick={() => navigate('/login')}
                >
                  Get Started
                </Button>
              </Stack>
            ) : (
              /* Mobile Navigation - Only Menu Icon */
              <IconButton
                onClick={handleMobileMenuToggle}
                sx={{
                  color: medicalColors.primary.main,
                  '&:hover': {
                    backgroundColor: 'rgba(2, 136, 209, 0.1)',
                  }
                }}
              >
                <MenuIcon />
              </IconButton>
            )}
          </Stack>
        </Container>
      </Box>

      {/* Mobile Navigation Drawer */}
      <Drawer
        anchor="right"
        open={mobileMenuOpen}
        onClose={handleMobileMenuToggle}
        sx={{
          '& .MuiDrawer-paper': {
            width: 280,
            bgcolor: 'rgba(255, 255, 255, 0.98)',
            backdropFilter: 'blur(20px)',
          },
        }}
      >
        <Box sx={{ p: 2 }}>
          <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 3 }}>
            <Typography variant="h6" sx={{ fontWeight: 600, color: medicalColors.primary.main }}>
              Menu
            </Typography>
            <IconButton onClick={handleMobileMenuToggle}>
              <CloseIcon />
            </IconButton>
          </Stack>
          <List>
            {navigationItems.map((item) => (
              <ListItem 
                key={item} 
                sx={{ 
                  borderRadius: 2, 
                  mb: 1,
                  '&:hover': {
                    bgcolor: 'rgba(2, 136, 209, 0.1)',
                  }
                }}
              >
                <ListItemText 
                  primary={item} 
                  sx={{
                    '& .MuiListItemText-primary': {
                      fontWeight: 500,
                      color: medicalColors.medical.textSecondary,
                    }
                  }}
                />
              </ListItem>
            ))}
            <ListItem sx={{ mt: 2 }}>
              <Button
                fullWidth
                variant="contained"
                sx={{
                  background: medicalColors.gradients.medicalAccent,
                  color: 'white',
                  borderRadius: 2,
                  py: 1.5,
                  fontWeight: 600,
                  textTransform: 'none',
                  fontSize: '1rem',
                  boxShadow: '0 4px 12px rgba(2, 136, 209, 0.3)',
                  '&:hover': {
                    boxShadow: '0 6px 16px rgba(2, 136, 209, 0.4)',
                    transform: 'translateY(-1px)',
                  },
                  transition: 'all 0.2s ease-in-out',
                }}
                onClick={() => {
                  navigate('/login');
                  setMobileMenuOpen(false);
                }}
              >
                Login
              </Button>
            </ListItem>
          </List>
        </Box>
      </Drawer>

      {/* Hero Section */}
      <Container maxWidth="lg" sx={{ py: { xs: 8, md: 12 } }}>
        <Grid container spacing={8} alignItems="center">
          <Grid size={{ xs: 12, md: 6 }}>
            <Box 
              sx={{ 
                mb: 3,
                animation: `${animations.fadeInUp} ${durations.complex}ms ${easings.easeOut}`,
                animationDelay: '200ms',
                animationFillMode: 'both',
              }}
            >
              <Typography
                variant="overline"
                sx={{
                  color: medicalColors.primary.main,
                  fontWeight: 700,
                  fontSize: '0.9rem',
                  letterSpacing: '0.1em',
                  textTransform: 'uppercase',
                  position: 'relative',
                  '&::after': {
                    content: '""',
                    position: 'absolute',
                    bottom: -4,
                    left: 0,
                    width: '60px',
                    height: '2px',
                    background: medicalColors.gradients.medicalAccent,
                    borderRadius: '1px',
                  }
                }}
              >
                Healthcare Innovation
              </Typography>
            </Box>
            <Typography
              variant="h1"
              sx={{
                fontWeight: 800,
                fontSize: { xs: '2.8rem', md: '4.2rem', lg: '4.8rem' },
                lineHeight: { xs: 1.1, md: 1.05 },
                mb: 4,
                letterSpacing: '-0.03em',
                background: medicalColors.gradients.medical,
                backgroundClip: 'text',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                animation: `${animations.fadeInUp} ${durations.complex}ms ${easings.easeOut}`,
                animationDelay: '400ms',
                animationFillMode: 'both',
              }}
            >
              Never Miss
              <br />
              <Box 
                component="span" 
                sx={{ 
                  background: medicalColors.gradients.medicalAccent,
                  backgroundClip: 'text',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                  position: 'relative',
                  '&::after': {
                    content: '""',
                    position: 'absolute',
                    bottom: 0,
                    left: 0,
                    width: '100%',
                    height: '4px',
                    background: medicalColors.gradients.medicalAccent,
                    borderRadius: '2px',
                    opacity: 0.3,
                  }
                }}
              >
                An Appointment
              </Box>
            </Typography>
            <Typography
              variant="h6"
              sx={{
                fontSize: { xs: '1.1rem', md: '1.25rem' },
                color: medicalColors.medical.textSecondary,
                mb: 6,
                lineHeight: 1.6,
                fontWeight: 400,
                maxWidth: '90%',
                animation: `${animations.fadeInUp} ${durations.complex}ms ${easings.easeOut}`,
                animationDelay: '600ms',
                animationFillMode: 'both',
              }}
            >
              MediRemind's intelligent appointment reminder system ensures patients never miss 
              their healthcare appointments through automated SMS, email, and push notifications.
            </Typography>
            <Box sx={{ display: 'flex', gap: 3, flexWrap: 'wrap', alignItems: 'center' }}>
              <Button
                variant="contained"
                size="large"
                onClick={() => navigate('/register')}
                sx={{
                  background: 'linear-gradient(135deg, #0288d1 0%, #0277bd 100%)',
                  boxShadow: '0 8px 32px rgba(2, 136, 209, 0.3)',
                  px: 6,
                  py: 2,
                  fontSize: '1.1rem',
                  fontWeight: 700,
                  borderRadius: 3,
                  textTransform: 'none',
                  minWidth: '180px',
                  position: 'relative',
                  overflow: 'hidden',
                  animation: `${animations.fadeInUp} ${durations.complex}ms ${easings.easeOut}`,
                  animationDelay: '800ms',
                  animationFillMode: 'both',
                  transition: `all ${durations.standard}ms ${easings.easeOut}`,
                  '&::before': {
                    content: '""',
                    position: 'absolute',
                    top: 0,
                    left: '-100%',
                    width: '100%',
                    height: '100%',
                    background: 'linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent)',
                    transition: `left ${durations.complex}ms ${easings.easeOut}`,
                  },
                  '&::after': {
                    content: '""',
                    position: 'absolute',
                    top: '50%',
                    left: '50%',
                    width: '0',
                    height: '0',
                    borderRadius: '50%',
                    background: 'rgba(255, 255, 255, 0.3)',
                    transform: 'translate(-50%, -50%)',
                    transition: `all ${durations.standard}ms ${easings.easeOut}`,
                  },
                  '&:hover': {
                    background: 'linear-gradient(135deg, #0277bd 0%, #01579b 100%)',
                    boxShadow: '0 12px 40px rgba(2, 136, 209, 0.4)',
                    transform: 'translateY(-3px) scale(1.02)',
                    '&::before': {
                      left: '100%',
                    },
                  },
                  '&:active': {
                    transform: 'translateY(-1px) scale(0.98)',
                    '&::after': {
                      width: '300px',
                      height: '300px',
                    }
                  }
                }}
              >
                Get Started Free
              </Button>
              <Button
                variant="outlined"
                size="large"
                onClick={() => navigate('/demo')}
                sx={{
                  borderColor: '#0288d1',
                  color: '#0288d1',
                  borderWidth: 2,
                  px: 6,
                  py: 2,
                  fontSize: '1.1rem',
                  fontWeight: 600,
                  borderRadius: 3,
                  textTransform: 'none',
                  minWidth: '160px',
                  position: 'relative',
                  overflow: 'hidden',
                  animation: `${animations.fadeInUp} ${durations.complex}ms ${easings.easeOut}`,
                  animationDelay: '900ms',
                  animationFillMode: 'both',
                  transition: `all ${durations.standard}ms ${easings.easeOut}`,
                  '&::before': {
                    content: '""',
                    position: 'absolute',
                    top: 0,
                    left: 0,
                    right: 0,
                    bottom: 0,
                    background: 'linear-gradient(135deg, #0288d1 0%, #0277bd 100%)',
                    opacity: 0,
                    transition: `opacity ${durations.standard}ms ${easings.easeOut}`,
                    zIndex: -1,
                  },
                  '&::after': {
                    content: '""',
                    position: 'absolute',
                    top: '50%',
                    left: '50%',
                    width: '0',
                    height: '0',
                    borderRadius: '50%',
                    background: 'rgba(2, 136, 209, 0.2)',
                    transform: 'translate(-50%, -50%)',
                    transition: `all ${durations.standard}ms ${easings.easeOut}`,
                  },
                  '&:hover': {
                    borderColor: '#0277bd',
                    color: 'white',
                    transform: 'translateY(-2px) scale(1.02)',
                    boxShadow: '0 8px 24px rgba(2, 136, 209, 0.3)',
                    '&::before': {
                      opacity: 1,
                    },
                  },
                  '&:active': {
                    transform: 'translateY(0px) scale(0.98)',
                    '&::after': {
                      width: '300px',
                      height: '300px',
                    }
                  }
                }}
              >
                Watch Demo
              </Button>
            </Box>
          </Grid>
          <Grid size={{ xs: 12, md: 6 }}>
            <Box
              sx={{
                position: 'relative',
                borderRadius: 6,
                overflow: 'hidden',
                minHeight: 280,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: '0 20px 60px rgba(2, 136, 209, 0.15)',
                animation: `${animations.fadeInRight} ${durations.complex}ms ${easings.easeOut}`,
                animationDelay: '800ms',
                animationFillMode: 'both',
                '&::before': {
                  content: '""',
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  right: 0,
                  bottom: 0,
                  background: 'linear-gradient(45deg, rgba(2, 136, 209, 0.1) 0%, rgba(1, 87, 155, 0.05) 100%)',
                  zIndex: 2
                }
              }}
            >
              {/* Healthcare Professional Image */}
              <Box
                component="img"
                src={healthcareProfessionalImg}
                alt="Healthcare Professional"
                sx={{
                  width: '100%',
                  height: '100%',
                  objectFit: 'cover',
                  borderRadius: 6,
                  transition: `transform ${durations.complex}ms ${easings.easeOut}`,
                  '&:hover': {
                    transform: 'scale(1.02)',
                  }
                }}
              />
              
              {/* Floating medical icons with enhanced animations */}
              <Box
                sx={{
                  position: 'absolute',
                  top: 20,
                  right: 20,
                  width: 80,
                  height: 80,
                  bgcolor: 'rgba(255, 255, 255, 0.95)',
                  borderRadius: '50%',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  boxShadow: '0 8px 32px rgba(2, 136, 209, 0.3)',
                  zIndex: 3,
                  animation: `${animations.pulse} 3s ${easings.easeInOut} infinite, ${animations.float} 6s ${easings.easeInOut} infinite`,
                  animationDelay: '1s, 1.5s',
                  transition: `all ${durations.standard}ms ${easings.easeOut}`,
                  cursor: 'pointer',
                  '&:hover': {
                    transform: 'scale(1.1) rotate(10deg)',
                    boxShadow: '0 12px 40px rgba(2, 136, 209, 0.4)',
                    bgcolor: 'rgba(255, 255, 255, 1)',
                  },
                  '&:hover .icon': {
                    transform: 'rotate(-10deg) scale(1.1)',
                    color: medicalColors.primary.dark,
                  }
                }}
              >
                <Schedule 
                  className="icon"
                  sx={{ 
                    fontSize: 40, 
                    color: medicalColors.primary.main,
                    transition: `all ${durations.standard}ms ${easings.easeOut}`,
                  }} 
                />
              </Box>
              
              <Box
                sx={{
                  position: 'absolute',
                  bottom: 20,
                  left: 20,
                  width: 70,
                  height: 70,
                  bgcolor: 'rgba(255, 255, 255, 0.95)',
                  borderRadius: '50%',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  boxShadow: '0 8px 32px rgba(2, 136, 209, 0.3)',
                  zIndex: 3,
                  animation: `${animations.pulse} 3s ${easings.easeInOut} infinite, ${animations.float} 5s ${easings.easeInOut} infinite`,
                  animationDelay: '1.5s, 2s',
                  transition: `all ${durations.standard}ms ${easings.easeOut}`,
                  cursor: 'pointer',
                  '&:hover': {
                    transform: 'scale(1.15) rotate(-10deg)',
                    boxShadow: '0 12px 40px rgba(2, 136, 209, 0.4)',
                    bgcolor: 'rgba(255, 255, 255, 1)',
                  },
                  '&:hover .icon': {
                    transform: 'rotate(10deg) scale(1.2)',
                    color: medicalColors.primary.dark,
                  }
                }}
              >
                <MedicalServices 
                  className="icon"
                  sx={{ 
                    fontSize: 35, 
                    color: medicalColors.primary.main,
                    transition: `all ${durations.standard}ms ${easings.easeOut}`,
                  }} 
                />
              </Box>
            </Box>
          </Grid>
        </Grid>
      </Container>

      {/* Features Section */}
      <Container maxWidth="lg" sx={{ py: { xs: 8, md: 12 } }} ref={featuresRef}>
        <Box sx={{ 
          textAlign: 'center', 
          mb: 8,
          opacity: featuresVisible ? 1 : 0,
          transform: featuresVisible ? 'translateY(0)' : 'translateY(50px)',
          transition: `all ${durations.complex}ms ${easings.easeOut}`,
        }}>
          <Typography
            variant="overline"
            sx={{
              color: '#0288d1',
              fontWeight: 700,
              fontSize: '0.9rem',
              letterSpacing: '0.1em',
              textTransform: 'uppercase',
              mb: 2,
              display: 'block'
            }}
          >
            Core Features
          </Typography>
          <Typography
            variant="h3"
            sx={{
              fontWeight: 800,
              fontSize: { xs: '2.2rem', md: '3rem' },
              color: '#1a365d',
              mb: 3,
              letterSpacing: '-0.02em'
            }}
          >
            Everything You Need for
            <Box component="span" sx={{ 
              color: '#0288d1',
              display: 'block'
            }}>
              Seamless Healthcare
            </Box>
          </Typography>
        </Box>
        
        <Grid container spacing={4}>
          {[
            {
              title: 'Smart Reminders',
              subtitle: 'Automated SMS & email notifications that reduce no-shows by up to 40%',
              icon: <Schedule />,
              gradient: 'linear-gradient(135deg, #0288d1 0%, #0277bd 100%)',
            },
            {
              title: 'Patient Management',
              subtitle: 'Comprehensive patient tracking with secure data management',
              icon: <Person />,
              gradient: 'linear-gradient(135deg, #0277bd 0%, #01579b 100%)',
            },
            {
              title: 'Appointment Scheduling',
              subtitle: 'Seamless booking system with real-time availability',
              icon: <CalendarToday />,
              gradient: 'linear-gradient(135deg, #01579b 0%, #0d47a1 100%)',
            },
            {
              title: 'Analytics Dashboard',
              subtitle: 'Real-time insights & reports to optimize your practice',
              icon: <MedicalServices />,
              gradient: 'linear-gradient(135deg, #0d47a1 0%, #1565c0 100%)',
            },
          ].map((service, index) => (
            <Grid size={{ xs: 12, sm: 6, md: 3 }} key={index}>
              <Card
                sx={{
                  p: 4,
                  textAlign: 'center',
                  height: '100%',
                  borderRadius: 4,
                  border: '1px solid rgba(2, 136, 209, 0.1)',
                  boxShadow: '0 4px 20px rgba(2, 136, 209, 0.08)',
                  transition: 'all 0.4s cubic-bezier(0.4, 0, 0.2, 1)',
                  position: 'relative',
                  overflow: 'hidden',
                  cursor: 'pointer',
                  animation: `${animations.fadeInUp} ${durations.complex}ms ${easings.easeOut}`,
                  animationDelay: `${index * 150}ms`,
                  animationFillMode: 'both',
                  '&::before': {
                    content: '""',
                    position: 'absolute',
                    top: 0,
                    left: 0,
                    right: 0,
                    height: '4px',
                    background: service.gradient,
                    transition: `height ${durations.standard}ms ${easings.easeOut}`,
                  },
                  '&::after': {
                    content: '""',
                    position: 'absolute',
                    top: 0,
                    left: '-100%',
                    width: '100%',
                    height: '100%',
                    background: 'linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent)',
                    transition: `left ${durations.complex}ms ${easings.easeOut}`,
                    zIndex: 1,
                  },
                  '&:hover': {
                    transform: 'translateY(-12px) scale(1.02)',
                    boxShadow: '0 25px 50px rgba(2, 136, 209, 0.2)',
                    borderColor: 'rgba(2, 136, 209, 0.3)',
                    '&::before': {
                      height: '8px',
                    },
                    '&::after': {
                      left: '100%',
                    },
                    '& .feature-icon': {
                      transform: 'scale(1.15) rotate(5deg)',
                      color: 'white',
                      boxShadow: '0 8px 25px rgba(2, 136, 209, 0.3)',
                      '&::before': {
                        opacity: 1,
                      },
                      '&::after': {
                        width: '120%',
                        height: '120%',
                      }
                    },
                    '& .feature-title': {
                      color: medicalColors.primary.main,
                      transform: 'translateY(-2px)',
                    },
                    '& .feature-subtitle': {
                      color: medicalColors.medical.textPrimary,
                    },
                    '& .feature-button': {
                      transform: 'translateX(8px)',
                      color: medicalColors.primary.main,
                      fontWeight: 700,
                    }
                  },
                }}
              >
                <Box
                  className="feature-icon"
                  sx={{
                    width: 80,
                    height: 80,
                    borderRadius: 3,
                    background: 'linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    mx: 'auto',
                    mb: 3,
                    color: '#0288d1',
                    transition: `all ${durations.standard}ms ${easings.easeOut}`,
                    position: 'relative',
                    zIndex: 2,
                    animation: `${animations.fadeInUp} ${durations.complex}ms ${easings.easeOut}`,
                    animationDelay: `${index * 150 + 600}ms`,
                    animationFillMode: 'both',
                    '&::before': {
                      content: '""',
                      position: 'absolute',
                      top: 0,
                      left: 0,
                      right: 0,
                      bottom: 0,
                      borderRadius: 3,
                      background: service.gradient,
                      opacity: 0,
                      transition: `opacity ${durations.standard}ms ${easings.easeOut}`,
                      zIndex: -1,
                    },
                    '&::after': {
                      content: '""',
                      position: 'absolute',
                      top: '50%',
                      left: '50%',
                      width: '0%',
                      height: '0%',
                      borderRadius: '50%',
                      background: 'rgba(255, 255, 255, 0.3)',
                      transform: 'translate(-50%, -50%)',
                      transition: `all ${durations.standard}ms ${easings.easeOut}`,
                      zIndex: 1,
                    }
                  }}
                >
                  {React.cloneElement(service.icon, { 
                    sx: { 
                      fontSize: 40,
                      transition: `all ${durations.standard}ms ${easings.easeOut}`,
                      position: 'relative',
                      zIndex: 2,
                    } 
                  })}
                </Box>
                <Typography 
                  variant="h6" 
                  gutterBottom 
                  className="feature-title"
                  sx={{ 
                    fontWeight: 700,
                    color: '#1a365d',
                    mb: 2,
                    fontSize: '1.1rem',
                    transition: `all ${durations.standard}ms ${easings.easeOut}`,
                    position: 'relative',
                    zIndex: 2,
                  }}
                >
                  {service.title}
                </Typography>
                <Typography 
                  variant="body2" 
                  className="feature-subtitle"
                  sx={{ 
                    color: '#546e7a',
                    lineHeight: 1.6,
                    mb: 3,
                    transition: `all ${durations.standard}ms ${easings.easeOut}`,
                    position: 'relative',
                    zIndex: 2,
                  }}
                >
                  {service.subtitle}
                </Typography>
                <Button
                  variant="text"
                  size="small"
                  className="feature-button"
                  sx={{
                    color: '#0288d1',
                    fontWeight: 600,
                    textTransform: 'none',
                    transition: `all ${durations.standard}ms ${easings.easeOut}`,
                    position: 'relative',
                    zIndex: 2,
                    '&:hover': { 
                      backgroundColor: 'rgba(2, 136, 209, 0.08)',
                    },
                  }}
                >
                  Learn More →
                </Button>
              </Card>
            </Grid>
          ))}
        </Grid>
      </Container>

      {/* Smart Notification Section */}
      <Box sx={{ 
        background: 'linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%)', 
        py: { xs: 8, md: 12 } 
      }} ref={smartNotificationRef}>
        <Container maxWidth="lg">
          <Box sx={{ 
            textAlign: 'center', 
            mb: 8,
            opacity: smartNotificationVisible ? 1 : 0,
            transform: smartNotificationVisible ? 'translateY(0)' : 'translateY(50px)',
            transition: `all ${durations.complex}ms ${easings.easeOut}`,
          }}>
            <Typography
              variant="overline"
              sx={{
                color: '#0288d1',
                fontWeight: 700,
                fontSize: '0.9rem',
                letterSpacing: '0.1em',
                textTransform: 'uppercase',
                mb: 2,
                display: 'block'
              }}
            >
              Smart Technology
            </Typography>
            <Typography 
              variant="h3" 
              sx={{ 
                fontWeight: 800,
                fontSize: { xs: '2.2rem', md: '3rem' },
                color: '#1a365d',
                mb: 3,
                letterSpacing: '-0.02em'
              }}
            >
              Intelligent Notification System
            </Typography>
          </Box>
          
          <Grid container spacing={8} alignItems="center">
            <Grid size={{ xs: 12, md: 6 }}>
              <Box
                sx={{
                  position: 'relative',
                  borderRadius: 6,
                  overflow: 'hidden',
                  background: 'linear-gradient(135deg, #0288d1 0%, #0277bd 100%)',
                  p: 6,
                  minHeight: 400,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  boxShadow: '0 20px 60px rgba(2, 136, 209, 0.25)',
                  '&::before': {
                    content: '""',
                    position: 'absolute',
                    top: 0,
                    left: 0,
                    right: 0,
                    bottom: 0,
                    background: 'radial-gradient(circle at 30% 30%, rgba(255,255,255,0.2) 0%, transparent 50%)',
                    zIndex: 1
                  }
                }}
              >
                <Box
                  sx={{
                    width: 160,
                    height: 160,
                    bgcolor: 'rgba(255,255,255,0.95)',
                    color: '#0288d1',
                    borderRadius: 5,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    boxShadow: '0 12px 40px rgba(0,0,0,0.15)',
                    position: 'relative',
                    zIndex: 2,
                    transition: 'transform 0.3s ease',
                    '&:hover': { transform: 'scale(1.05)' }
                  }}
                >
                  <Schedule sx={{ fontSize: 80 }} />
                </Box>
              </Box>
            </Grid>
            <Grid size={{ xs: 12, md: 6 }}>
              <Typography 
                variant="h4" 
                gutterBottom 
                sx={{ 
                  fontWeight: 700,
                  color: '#1a365d',
                  mb: 3,
                  fontSize: { xs: '1.8rem', md: '2.2rem' }
                }}
              >
                Automated Appointment Reminders
              </Typography>
              <Typography 
                variant="h6" 
                sx={{ 
                  mb: 4, 
                  color: '#546e7a', 
                  lineHeight: 1.6,
                  fontWeight: 400,
                  fontSize: '1.1rem'
                }}
              >
                Reduce no-shows by up to 80% with our intelligent reminder system. Send personalized 
                SMS, email, and push notifications to patients automatically. Customize timing, 
                frequency, and messaging to match your practice's needs.
              </Typography>
              
              <Box sx={{ mb: 4 }}>
                {[
                  'Automated SMS & Email reminders',
                  'Customizable timing & frequency',
                  'Multi-language support',
                  'Real-time delivery tracking'
                ].map((feature, index) => (
                  <Box key={index} sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <Box
                      sx={{
                        width: 24,
                        height: 24,
                        borderRadius: '50%',
                        background: 'linear-gradient(135deg, #0288d1 0%, #0277bd 100%)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        mr: 2,
                        flexShrink: 0
                      }}
                    >
                      <Typography sx={{ color: 'white', fontSize: '0.8rem', fontWeight: 'bold' }}>
                        ✓
                      </Typography>
                    </Box>
                    <Typography sx={{ color: '#546e7a', fontWeight: 500 }}>
                      {feature}
                    </Typography>
                  </Box>
                ))}
              </Box>
              
              <Button
                variant="contained"
                size="large"
                sx={{
                  background: 'linear-gradient(135deg, #0288d1 0%, #0277bd 100%)',
                  boxShadow: '0 8px 32px rgba(2, 136, 209, 0.3)',
                  '&:hover': {
                    background: 'linear-gradient(135deg, #0277bd 0%, #01579b 100%)',
                    boxShadow: '0 12px 40px rgba(2, 136, 209, 0.4)',
                    transform: 'translateY(-2px)',
                  },
                  px: 4,
                  py: 1.5,
                  fontSize: '1rem',
                  fontWeight: 600,
                  borderRadius: 3,
                  textTransform: 'none',
                  transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                }}
              >
                Learn More
              </Button>
            </Grid>
          </Grid>
        </Container>
      </Box>

      {/* Multi-Channel Communication Section */}
      <Container maxWidth="lg" sx={{ py: { xs: 8, md: 12 } }} ref={communicationRef}>
        <Box sx={{ 
          textAlign: 'center', 
          mb: 8,
          opacity: communicationVisible ? 1 : 0,
          transform: communicationVisible ? 'translateY(0)' : 'translateY(50px)',
          transition: `all ${durations.complex}ms ${easings.easeOut}`,
        }}>
          <Typography
            variant="overline"
            sx={{
              color: '#0288d1',
              fontWeight: 700,
              fontSize: '0.9rem',
              letterSpacing: '0.1em',
              textTransform: 'uppercase',
              mb: 2,
              display: 'block'
            }}
          >
            Communication Excellence
          </Typography>
          <Typography 
            variant="h3" 
            sx={{ 
              fontWeight: 800,
              fontSize: { xs: '2.2rem', md: '3rem' },
              color: '#1a365d',
              mb: 3,
              letterSpacing: '-0.02em'
            }}
          >
            Multi-Channel Communication
          </Typography>
        </Box>
        
        <Grid container spacing={4} justifyContent="center">
          <Grid size={{ xs: 12, md: 10 }}>
            <Card
              sx={{
                p: { xs: 4, md: 6 },
                borderRadius: 6,
                background: 'linear-gradient(135deg, #0288d1 0%, #0277bd 100%)',
                color: 'white',
                textAlign: 'center',
                boxShadow: '0 20px 60px rgba(2, 136, 209, 0.25)',
                position: 'relative',
                overflow: 'hidden',
                '&::before': {
                  content: '""',
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  right: 0,
                  bottom: 0,
                  background: 'radial-gradient(circle at 70% 20%, rgba(255,255,255,0.15) 0%, transparent 50%)',
                  zIndex: 1
                }
              }}
            >
              <Box sx={{ position: 'relative', zIndex: 2 }}>
                <Typography 
                  variant="h4" 
                  gutterBottom 
                  sx={{ 
                    fontWeight: 700,
                    mb: 3,
                    fontSize: { xs: '1.8rem', md: '2.2rem' }
                  }}
                >
                  Smart Communication Hub
                </Typography>
                <Typography 
                  variant="h6" 
                  sx={{ 
                    mb: 4, 
                    opacity: 0.95,
                    lineHeight: 1.6,
                    fontWeight: 400,
                    fontSize: '1.1rem',
                    maxWidth: '80%',
                    mx: 'auto'
                  }}
                >
                  Reach patients through their preferred channels - SMS, email, push notifications, 
                  and voice calls. Our AI-powered system optimizes delivery timing for maximum engagement.
                </Typography>
                
                <Grid container spacing={3} sx={{ mb: 4, justifyContent: 'center' }}>
                  {[
                    { icon: Sms, label: 'SMS Messages' },
                    { icon: Email, label: 'Email Alerts' },
                    { icon: Notifications, label: 'Push Notifications' },
                    { icon: Call, label: 'Voice Calls' }
                  ].map((channel, index) => {
                    const IconComponent = channel.icon;
                    return (
                      <Grid size={{ xs: 6, sm: 3 }} key={index}>
                        <Box
                          sx={{
                            p: 2,
                            borderRadius: 3,
                            background: 'rgba(255,255,255,0.15)',
                            backdropFilter: 'blur(10px)',
                            border: '1px solid rgba(255,255,255,0.2)',
                            transition: 'transform 0.2s ease',
                            '&:hover': { transform: 'translateY(-4px)' }
                          }}
                        >
                          <Box sx={{ mb: 1, display: 'flex', justifyContent: 'center' }}>
                            <IconComponent sx={{ fontSize: '2rem', color: '#90caf9' }} />
                          </Box>
                          <Typography sx={{ fontSize: '0.9rem', fontWeight: 500 }}>
                            {channel.label}
                          </Typography>
                        </Box>
                      </Grid>
                    );
                  })}
                </Grid>
                
                <Button
                  variant="contained"
                  size="large"
                  sx={{
                    bgcolor: 'white',
                    color: '#0288d1',
                    fontWeight: 700,
                    px: 6,
                    py: 2,
                    fontSize: '1.1rem',
                    borderRadius: 3,
                    textTransform: 'none',
                    boxShadow: '0 8px 32px rgba(255,255,255,0.3)',
                    '&:hover': { 
                      bgcolor: 'rgba(255,255,255,0.95)',
                      transform: 'translateY(-2px)',
                      boxShadow: '0 12px 40px rgba(255,255,255,0.4)'
                    },
                    transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                  }}
                >
                  Get Started Today
                </Button>
              </Box>
            </Card>
          </Grid>
        </Grid>
      </Container>

      {/* Appointment Schedules Section */}
      <Box sx={{ bgcolor: 'white', py: 8 }}>
        <Container maxWidth="lg">
          <Grid container spacing={6} alignItems="center">
            <Grid size={{ xs: 12, md: 6 }}>
              <Typography variant="h4" gutterBottom sx={{ fontWeight: 600 }}>
                Reminder
                <br />
                Management
              </Typography>
              <Typography variant="body1" sx={{ mb: 3, color: 'text.secondary', lineHeight: 1.6 }}>
                Set up customizable reminder sequences for different appointment types. 
                Track delivery status, patient responses, and optimize your communication strategy with detailed analytics.
              </Typography>
              <Button
                variant="contained"
                sx={{
                  bgcolor: '#00bcd4',
                  '&:hover': { bgcolor: '#00acc1' }
                }}
              >
                Manage Reminders
              </Button>
            </Grid>
            <Grid size={{ xs: 12, md: 6 }}>
              <Box
                sx={{
                  position: 'relative',
                  borderRadius: 4,
                  overflow: 'hidden',
                  background: 'linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%)',
                  p: 4,
                  minHeight: 300,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <CalendarToday sx={{ fontSize: 120, color: '#00bcd4' }} />
              </Box>
            </Grid>
          </Grid>
        </Container>
      </Box>

      {/* Doctors Section */}
      <Container maxWidth="lg" sx={{ py: 8 }}>
        <Typography variant="h4" align="center" gutterBottom sx={{ mb: 6, fontWeight: 600 }}>
          Staff Management
        </Typography>
        <Grid container spacing={4}>
          {[
            {
              name: 'Admin Dashboard',
              specialty: 'Centralized Control',
              experience: 'Real-time monitoring',
              avatar: 'AD',
            },
            {
              name: 'Team Collaboration',
              specialty: 'Staff Coordination',
              experience: 'Seamless workflow',
              avatar: 'TC',
            },
            {
              name: 'Performance Analytics',
              specialty: 'Data Insights',
              experience: 'Optimize efficiency',
              avatar: 'PA',
            },
          ].map((feature, index) => (
            <Grid size={{ xs: 12, sm: 6, md: 4 }} key={index}>
              <Card
                sx={{
                  p: 3,
                  textAlign: 'center',
                  borderRadius: 3,
                  transition: 'transform 0.2s',
                  '&:hover': {
                    transform: 'translateY(-4px)',
                    boxShadow: 4,
                  },
                }}
              >
                <Avatar
                  sx={{
                    width: 80,
                    height: 80,
                    mx: 'auto',
                    mb: 2,
                    bgcolor: '#00bcd4',
                    fontSize: '1.5rem',
                  }}
                >
                  {feature.avatar}
                </Avatar>
                <Typography variant="h6" gutterBottom sx={{ fontWeight: 600 }}>
                  {feature.name}
                </Typography>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  {feature.specialty}
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  {feature.experience}
                </Typography>
                <Button
                  variant="contained"
                  size="small"
                  sx={{
                    bgcolor: '#00bcd4',
                    '&:hover': { bgcolor: '#00acc1' }
                  }}
                >
                  Learn More
                </Button>
              </Card>
            </Grid>
          ))}
        </Grid>
      </Container>

      {/* Footer */}
      <Box sx={{ 
        background: 'linear-gradient(135deg, #0d1421 0%, #1a1a2e 50%, #16213e 100%)', 
        color: 'white', 
        py: { xs: 6, md: 8 },
        position: 'relative',
        '&::before': {
          content: '""',
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'radial-gradient(circle at 20% 80%, rgba(0, 150, 136, 0.1) 0%, transparent 50%), radial-gradient(circle at 80% 20%, rgba(33, 150, 243, 0.1) 0%, transparent 50%)',
          pointerEvents: 'none'
        }
      }}>
        <Container maxWidth="lg" sx={{ position: 'relative', zIndex: 1 }}>
          <Grid container spacing={6}>
            <Grid size={{ xs: 12, md: 4 }}>
              <Stack direction="row" alignItems="center" spacing={2} sx={{ mb: 4 }}>
                <Box
                  sx={{
                    width: 48,
                    height: 48,
                    borderRadius: 3,
                    background: 'linear-gradient(135deg, #00695c 0%, #004d40 100%)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    boxShadow: '0 8px 32px rgba(0, 105, 92, 0.4)',
                    border: '1px solid rgba(0, 150, 136, 0.2)'
                  }}
                >
                  <Schedule sx={{ color: 'white', fontSize: 28 }} />
                </Box>
                <Typography variant="h5" sx={{ fontWeight: 800, color: 'white' }}>
                  MediRemind
                </Typography>
              </Stack>
              <Typography 
                variant="body1" 
                sx={{ 
                  opacity: 0.85, 
                  mb: 4,
                  lineHeight: 1.7,
                  fontSize: '1rem',
                  color: '#b0bec5'
                }}
              >
                Intelligent appointment reminder system that reduces no-shows and improves patient engagement through smart automation across Kenya's healthcare network.
              </Typography>
              <Box sx={{ display: 'flex', gap: 2 }}>
                {[
                  { icon: PhoneAndroid, label: 'Mobile App' },
                  { icon: Chat, label: 'Live Chat' },
                  { icon: Email, label: 'Email Support' }
                ].map((item, index) => {
                  const IconComponent = item.icon;
                  return (
                    <Box
                      key={index}
                      sx={{
                        width: 44,
                        height: 44,
                        borderRadius: 3,
                        background: 'rgba(0, 150, 136, 0.1)',
                        border: '1px solid rgba(0, 150, 136, 0.2)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        cursor: 'pointer',
                        transition: 'all 0.3s ease',
                        '&:hover': {
                          background: 'rgba(0, 150, 136, 0.2)',
                          transform: 'translateY(-3px)',
                          boxShadow: '0 8px 25px rgba(0, 150, 136, 0.3)'
                        }
                      }}
                      title={item.label}
                    >
                      <IconComponent sx={{ fontSize: 22, color: '#4db6ac' }} />
                    </Box>
                  );
                })}
              </Box>
            </Grid>
            
            <Grid size={{ xs: 12, md: 4 }}>
              <Typography 
                variant="h6" 
                gutterBottom 
                sx={{ 
                  fontWeight: 700,
                  mb: 3,
                  color: 'white',
                  fontSize: '1.1rem'
                }}
              >
                Quick Links
              </Typography>
              <Stack spacing={2.5}>
                {['Features', 'Pricing', 'Support', 'Documentation', 'Privacy Policy', 'Terms of Service'].map((link, index) => (
                  <Typography 
                    key={index}
                    variant="body1" 
                    sx={{ 
                      opacity: 0.8, 
                      cursor: 'pointer',
                      fontWeight: 500,
                      color: '#b0bec5',
                      transition: 'all 0.3s ease',
                      '&:hover': { 
                        opacity: 1,
                        color: '#4db6ac',
                        transform: 'translateX(6px)'
                      }
                    }}
                  >
                    {link}
                  </Typography>
                ))}
              </Stack>
            </Grid>
            
            <Grid size={{ xs: 12, md: 4 }}>
              <Typography 
                variant="h6" 
                gutterBottom 
                sx={{ 
                  fontWeight: 700,
                  mb: 3,
                  color: 'white',
                  fontSize: '1.1rem'
                }}
              >
                Contact Info - Kenya
              </Typography>
              <Stack spacing={3}>
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <Box
                    sx={{
                      width: 36,
                      height: 36,
                      borderRadius: 3,
                      background: 'rgba(0, 150, 136, 0.15)',
                      border: '1px solid rgba(0, 150, 136, 0.3)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      mr: 3
                    }}
                  >
                    <Phone sx={{ fontSize: 20, color: '#4db6ac' }} />
                  </Box>
                  <Typography variant="body1" sx={{ opacity: 0.9, fontWeight: 500, color: '#b0bec5' }}>
                    +254 700 123 456
                  </Typography>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <Box
                    sx={{
                      width: 36,
                      height: 36,
                      borderRadius: 3,
                      background: 'rgba(0, 150, 136, 0.15)',
                      border: '1px solid rgba(0, 150, 136, 0.3)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      mr: 3
                    }}
                  >
                    <Email sx={{ fontSize: 20, color: '#4db6ac' }} />
                  </Box>
                  <Typography variant="body1" sx={{ opacity: 0.9, fontWeight: 500, color: '#b0bec5' }}>
                    support@mediremind.co.ke
                  </Typography>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'flex-start' }}>
                  <Box
                    sx={{
                      width: 36,
                      height: 36,
                      borderRadius: 3,
                      background: 'rgba(0, 150, 136, 0.15)',
                      border: '1px solid rgba(0, 150, 136, 0.3)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      mr: 3,
                      mt: 0.5
                    }}
                  >
                    <LocationOn sx={{ fontSize: 20, color: '#4db6ac' }} />
                  </Box>
                  <Box>
                    <Typography variant="body1" sx={{ opacity: 0.9, fontWeight: 500, color: '#b0bec5', lineHeight: 1.5 }}>
                      Westlands Business Park,<br />
                      Waiyaki Way, Nairobi, Kenya
                    </Typography>
                  </Box>
                </Box>
              </Stack>
            </Grid>
          </Grid>
          
          <Box sx={{ 
            borderTop: '1px solid rgba(255,255,255,0.1)', 
            mt: 8, 
            pt: 6, 
            textAlign: 'center' 
          }}>
            <Typography 
              variant="body1" 
              sx={{ 
                opacity: 0.7,
                fontWeight: 500,
                color: '#90a4ae',
                fontSize: '0.95rem'
              }}
            >
              © {new Date().getFullYear()} MediRemind Kenya. All rights reserved. Built with ❤️ for healthcare professionals across Kenya.
            </Typography>
          </Box>
        </Container>
      </Box>
    </Box>
  );
};

export default LandingPage;