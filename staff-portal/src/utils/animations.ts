import React from 'react';
import { keyframes } from '@mui/system';
import { easings, durations } from '../theme/colors';

// Keyframe Animations
export const animations = {
  // Fade animations
  fadeIn: keyframes`
    from {
      opacity: 0;
    }
    to {
      opacity: 1;
    }
  `,

  fadeInUp: keyframes`
    from {
      opacity: 0;
      transform: translateY(30px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  `,

  fadeInDown: keyframes`
    from {
      opacity: 0;
      transform: translateY(-30px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  `,

  fadeInLeft: keyframes`
    from {
      opacity: 0;
      transform: translateX(-30px);
    }
    to {
      opacity: 1;
      transform: translateX(0);
    }
  `,

  fadeInRight: keyframes`
    from {
      opacity: 0;
      transform: translateX(30px);
    }
    to {
      opacity: 1;
      transform: translateX(0);
    }
  `,

  // Scale animations
  scaleIn: keyframes`
    from {
      opacity: 0;
      transform: scale(0.8);
    }
    to {
      opacity: 1;
      transform: scale(1);
    }
  `,

  scaleInBounce: keyframes`
    0% {
      opacity: 0;
      transform: scale(0.3);
    }
    50% {
      transform: scale(1.05);
    }
    70% {
      transform: scale(0.9);
    }
    100% {
      opacity: 1;
      transform: scale(1);
    }
  `,

  // Pulse animations
  pulse: keyframes`
    0% {
      transform: scale(1);
    }
    50% {
      transform: scale(1.05);
    }
    100% {
      transform: scale(1);
    }
  `,

  pulseGlow: keyframes`
    0% {
      box-shadow: 0 0 0 0 rgba(25, 118, 210, 0.4);
    }
    70% {
      box-shadow: 0 0 0 10px rgba(25, 118, 210, 0);
    }
    100% {
      box-shadow: 0 0 0 0 rgba(25, 118, 210, 0);
    }
  `,

  // Floating animations
  float: keyframes`
    0%, 100% {
      transform: translateY(0px);
    }
    50% {
      transform: translateY(-10px);
    }
  `,

  floatSlow: keyframes`
    0%, 100% {
      transform: translateY(0px);
    }
    50% {
      transform: translateY(-5px);
    }
  `,

  // Rotation animations
  rotate: keyframes`
    from {
      transform: rotate(0deg);
    }
    to {
      transform: rotate(360deg);
    }
  `,

  rotateIn: keyframes`
    from {
      opacity: 0;
      transform: rotate(-200deg);
    }
    to {
      opacity: 1;
      transform: rotate(0deg);
    }
  `,

  // Slide animations
  slideInUp: keyframes`
    from {
      transform: translateY(100%);
    }
    to {
      transform: translateY(0);
    }
  `,

  slideInDown: keyframes`
    from {
      transform: translateY(-100%);
    }
    to {
      transform: translateY(0);
    }
  `,

  // Shimmer effect
  shimmer: keyframes`
    0% {
      background-position: -468px 0;
    }
    100% {
      background-position: 468px 0;
    }
  `,

  // Gradient animation
  gradientShift: keyframes`
    0% {
      background-position: 0% 50%;
    }
    50% {
      background-position: 100% 50%;
    }
    100% {
      background-position: 0% 50%;
    }
  `,

  // Bounce animations
  bounceIn: keyframes`
    0% {
      opacity: 0;
      transform: scale(0.3);
    }
    50% {
      opacity: 1;
      transform: scale(1.05);
    }
    70% {
      transform: scale(0.9);
    }
    100% {
      opacity: 1;
      transform: scale(1);
    }
  `,

  // Ripple effect
  ripple: keyframes`
    0% {
      transform: scale(0);
      opacity: 1;
    }
    100% {
      transform: scale(4);
      opacity: 0;
    }
  `,
};

// Animation Mixins
export const animationMixins = {
  // Stagger animation delays for multiple elements
  staggerDelay: (index: number, baseDelay: number = 100) => ({
    animationDelay: `${index * baseDelay}ms`,
  }),

  // Hover lift effect
  hoverLift: {
    transition: `all ${durations.standard}ms ${easings.easeOut}`,
    '&:hover': {
      transform: 'translateY(-4px)',
      boxShadow: '0 12px 40px rgba(25, 118, 210, 0.25)',
    },
  },

  // Hover scale effect
  hoverScale: {
    transition: `all ${durations.standard}ms ${easings.easeOut}`,
    '&:hover': {
      transform: 'scale(1.02)',
    },
  },

  // Hover glow effect
  hoverGlow: {
    transition: `all ${durations.standard}ms ${easings.easeOut}`,
    '&:hover': {
      boxShadow: '0 0 20px rgba(25, 118, 210, 0.4)',
    },
  },

  // Button ripple effect
  buttonRipple: {
    position: 'relative',
    overflow: 'hidden',
    '&::before': {
      content: '""',
      position: 'absolute',
      top: '50%',
      left: '50%',
      width: 0,
      height: 0,
      borderRadius: '50%',
      background: 'rgba(255, 255, 255, 0.5)',
      transform: 'translate(-50%, -50%)',
      transition: `width ${durations.standard}ms ${easings.easeOut}, height ${durations.standard}ms ${easings.easeOut}`,
    },
    '&:active::before': {
      width: '300px',
      height: '300px',
    },
  },

  // Glass morphism effect
  glassMorphism: {
    background: 'rgba(255, 255, 255, 0.25)',
    backdropFilter: 'blur(10px)',
    border: '1px solid rgba(255, 255, 255, 0.18)',
    boxShadow: '0 8px 32px 0 rgba(31, 38, 135, 0.37)',
  },

  // Scroll reveal animation
  scrollReveal: {
    opacity: 0,
    transform: 'translateY(50px)',
    transition: `all ${durations.complex}ms ${easings.easeOut}`,
    '&.revealed': {
      opacity: 1,
      transform: 'translateY(0)',
    },
  },

  // Loading skeleton
  skeleton: {
    background: `linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%)`,
    backgroundSize: '200% 100%',
    animation: `${animations.shimmer} 1.5s infinite`,
  },

  // Floating animation
  floating: {
    animation: `${animations.float} 3s ease-in-out infinite`,
  },

  // Pulse animation
  pulsing: {
    animation: `${animations.pulse} 2s ease-in-out infinite`,
  },

  // Gradient background animation
  animatedGradient: {
    background: 'linear-gradient(-45deg, #1976d2, #1565c0, #0d47a1, #1976d2)',
    backgroundSize: '400% 400%',
    animation: `${animations.gradientShift} 15s ease infinite`,
  },
};

// Intersection Observer hook for scroll animations
export const useScrollReveal = () => {
  const observerRef = React.useRef<IntersectionObserver | null>(null);

  React.useEffect(() => {
    observerRef.current = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add('revealed');
          }
        });
      },
      {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px',
      }
    );

    const elements = document.querySelectorAll('[data-scroll-reveal]');
    elements.forEach((el) => observerRef.current?.observe(el));

    return () => {
      observerRef.current?.disconnect();
    };
  }, []);

  return observerRef;
};

// Stagger animation utility
export const staggerChildren = (
  children: React.ReactElement[],
  animationType: keyof typeof animations = 'fadeInUp',
  baseDelay: number = 100
) => {
  return children.map((child, index) => {
    if (React.isValidElement(child)) {
      const childProps = child.props as any;
      return React.cloneElement(child as React.ReactElement<any>, {
        key: index,
        sx: {
          ...childProps.sx,
          animation: `${animations[animationType]} ${durations.complex}ms ${easings.easeOut}`,
          animationDelay: `${index * baseDelay}ms`,
          animationFillMode: 'both',
        },
      });
    }
    return child;
  });
};