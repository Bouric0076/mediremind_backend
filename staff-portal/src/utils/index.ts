import { format, parseISO, isValid, differenceInYears, differenceInMinutes, addDays, startOfDay, endOfDay } from 'date-fns';
import { DATE_FORMATS, TIME_FORMATS, VALIDATION_RULES } from '../constants';
import type { User, Patient, Priority, UserRole } from '../types';

// Date and Time Utilities
export const formatDate = (date: string | Date, formatStr: string = DATE_FORMATS.DISPLAY): string => {
  try {
    const dateObj = typeof date === 'string' ? parseISO(date) : date;
    return isValid(dateObj) ? format(dateObj, formatStr) : 'Invalid Date';
  } catch {
    return 'Invalid Date';
  }
};

export const formatTime = (time: string | Date, formatStr: string = TIME_FORMATS.DISPLAY): string => {
  try {
    const timeObj = typeof time === 'string' ? parseISO(time) : time;
    return isValid(timeObj) ? format(timeObj, formatStr) : 'Invalid Time';
  } catch {
    return 'Invalid Time';
  }
};

export const formatDateTime = (dateTime: string | Date): string => {
  try {
    const dateObj = typeof dateTime === 'string' ? parseISO(dateTime) : dateTime;
    if (!isValid(dateObj)) return 'Invalid Date';
    
    const dateStr = format(dateObj, DATE_FORMATS.DISPLAY);
    const timeStr = format(dateObj, TIME_FORMATS.DISPLAY);
    return `${dateStr} at ${timeStr}`;
  } catch {
    return 'Invalid Date';
  }
};

export const getRelativeTime = (date: string | Date): string => {
  try {
    const dateObj = typeof date === 'string' ? parseISO(date) : date;
    if (!isValid(dateObj)) return 'Invalid Date';
    
    const now = new Date();
    const diffInMinutes = differenceInMinutes(now, dateObj);
    
    if (diffInMinutes < 1) return 'Just now';
    if (diffInMinutes < 60) return `${diffInMinutes} minute${diffInMinutes > 1 ? 's' : ''} ago`;
    
    const diffInHours = Math.floor(diffInMinutes / 60);
    if (diffInHours < 24) return `${diffInHours} hour${diffInHours > 1 ? 's' : ''} ago`;
    
    const diffInDays = Math.floor(diffInHours / 24);
    if (diffInDays < 7) return `${diffInDays} day${diffInDays > 1 ? 's' : ''} ago`;
    
    return formatDate(dateObj);
  } catch {
    return 'Invalid Date';
  }
};

export const calculateAge = (birthDate: string | Date): number => {
  try {
    const birthDateObj = typeof birthDate === 'string' ? parseISO(birthDate) : birthDate;
    return isValid(birthDateObj) ? differenceInYears(new Date(), birthDateObj) : 0;
  } catch {
    return 0;
  }
};

export const isToday = (date: string | Date): boolean => {
  try {
    const dateObj = typeof date === 'string' ? parseISO(date) : date;
    if (!isValid(dateObj)) return false;
    
    const today = new Date();
    return (
      dateObj.getDate() === today.getDate() &&
      dateObj.getMonth() === today.getMonth() &&
      dateObj.getFullYear() === today.getFullYear()
    );
  } catch {
    return false;
  }
};

export const isTomorrow = (date: string | Date): boolean => {
  try {
    const dateObj = typeof date === 'string' ? parseISO(date) : date;
    if (!isValid(dateObj)) return false;
    
    const tomorrow = addDays(new Date(), 1);
    return (
      dateObj.getDate() === tomorrow.getDate() &&
      dateObj.getMonth() === tomorrow.getMonth() &&
      dateObj.getFullYear() === tomorrow.getFullYear()
    );
  } catch {
    return false;
  }
};

export const getDateRange = (days: number) => {
  const end = endOfDay(new Date());
  const start = startOfDay(addDays(end, -days));
  return { start, end };
};

// Validation Utilities
export const validateEmail = (email: string): boolean => {
  return VALIDATION_RULES.EMAIL.test(email);
};

export const validatePhone = (phone: string): boolean => {
  return VALIDATION_RULES.PHONE.test(phone.replace(/\s/g, ''));
};

export const validatePassword = (password: string): boolean => {
  return password.length >= VALIDATION_RULES.PASSWORD.MIN_LENGTH &&
         VALIDATION_RULES.PASSWORD.PATTERN.test(password);
};

export const validateName = (name: string): boolean => {
  return VALIDATION_RULES.NAME.test(name.trim());
};

export const getPasswordStrength = (password: string): {
  score: number;
  label: string;
  color: string;
} => {
  let score = 0;
  
  if (password.length >= 8) score++;
  if (/[a-z]/.test(password)) score++;
  if (/[A-Z]/.test(password)) score++;
  if (/\d/.test(password)) score++;
  if (/[@$!%*?&]/.test(password)) score++;
  
  const strength = {
    0: { label: 'Very Weak', color: '#f44336' },
    1: { label: 'Weak', color: '#ff9800' },
    2: { label: 'Fair', color: '#ff9800' },
    3: { label: 'Good', color: '#4caf50' },
    4: { label: 'Strong', color: '#4caf50' },
    5: { label: 'Very Strong', color: '#2e7d32' },
  };
  
  return {
    score,
    ...strength[score as keyof typeof strength],
  };
};

// String Utilities
export const capitalize = (str: string): string => {
  return str.charAt(0).toUpperCase() + str.slice(1).toLowerCase();
};

export const capitalizeWords = (str: string): string => {
  return str.split(' ').map(capitalize).join(' ');
};

export const truncateText = (text: string, maxLength: number): string => {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength).trim() + '...';
};

export const slugify = (text: string): string => {
  return text
    .toLowerCase()
    .replace(/[^\w\s-]/g, '')
    .replace(/[\s_-]+/g, '-')
    .replace(/^-+|-+$/g, '');
};

export const generateInitials = (fullName: string): string => {
  const names = fullName.trim().split(' ');
  if (names.length === 1) {
    return names[0].charAt(0).toUpperCase();
  }
  return `${names[0].charAt(0)}${names[names.length - 1].charAt(0)}`.toUpperCase();
};

// Legacy function for backward compatibility
export const generateInitialsFromNames = (firstName: string, lastName: string): string => {
  return `${firstName.charAt(0)}${lastName.charAt(0)}`.toUpperCase();
};

export const formatPhoneNumber = (phone: string): string => {
  const cleaned = phone.replace(/\D/g, '');
  const match = cleaned.match(/^(\d{3})(\d{3})(\d{4})$/);
  if (match) {
    return `(${match[1]}) ${match[2]}-${match[3]}`;
  }
  return phone;
};

// Number Utilities
export const formatCurrency = (amount: number, currency: string = 'USD'): string => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
  }).format(amount);
};

export const formatNumber = (num: number, decimals: number = 0): string => {
  return new Intl.NumberFormat('en-US', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(num);
};

export const formatPercentage = (value: number, total: number): string => {
  if (total === 0) return '0%';
  const percentage = (value / total) * 100;
  return `${Math.round(percentage)}%`;
};

// Array Utilities
export const groupBy = <T>(array: T[], key: keyof T): Record<string, T[]> => {
  return array.reduce((groups, item) => {
    const group = String(item[key]);
    groups[group] = groups[group] || [];
    groups[group].push(item);
    return groups;
  }, {} as Record<string, T[]>);
};

export const sortBy = <T>(array: T[], key: keyof T, order: 'asc' | 'desc' = 'asc'): T[] => {
  return [...array].sort((a, b) => {
    const aVal = a[key];
    const bVal = b[key];
    
    if (aVal < bVal) return order === 'asc' ? -1 : 1;
    if (aVal > bVal) return order === 'asc' ? 1 : -1;
    return 0;
  });
};

export const uniqueBy = <T>(array: T[], key: keyof T): T[] => {
  const seen = new Set();
  return array.filter(item => {
    const value = item[key];
    if (seen.has(value)) return false;
    seen.add(value);
    return true;
  });
};

export const chunk = <T>(array: T[], size: number): T[][] => {
  const chunks: T[][] = [];
  for (let i = 0; i < array.length; i += size) {
    chunks.push(array.slice(i, i + size));
  }
  return chunks;
};

// Object Utilities
export const omit = <T extends Record<string, any>, K extends keyof T>(
  obj: T,
  keys: K[]
): Omit<T, K> => {
  const result = { ...obj };
  keys.forEach(key => delete result[key]);
  return result;
};

export const pick = <T extends Record<string, any>, K extends keyof T>(
  obj: T,
  keys: K[]
): Pick<T, K> => {
  const result = {} as Pick<T, K>;
  keys.forEach(key => {
    if (key in obj) {
      result[key] = obj[key];
    }
  });
  return result;
};

export const isEmpty = (value: any): boolean => {
  if (value == null) return true;
  if (Array.isArray(value) || typeof value === 'string') return value.length === 0;
  if (typeof value === 'object') return Object.keys(value).length === 0;
  return false;
};

export const deepClone = <T>(obj: T): T => {
  if (obj === null || typeof obj !== 'object') return obj;
  if (obj instanceof Date) return new Date(obj.getTime()) as unknown as T;
  if (Array.isArray(obj)) return obj.map(deepClone) as unknown as T;
  
  const cloned = {} as T;
  Object.keys(obj).forEach(key => {
    cloned[key as keyof T] = deepClone((obj as any)[key]);
  });
  return cloned;
};

// User and Role Utilities
export const getFullName = (user: User | Patient): string => {
  // Handle both new full_name format and legacy firstName/lastName format
  if ('full_name' in user && user.full_name) {
    return user.full_name.trim();
  }
  if ('firstName' in user && 'lastName' in user) {
    return `${user.firstName} ${user.lastName}`.trim();
  }
  return '';
};

export const hasPermission = (userRole: UserRole, permission: string): boolean => {
  // This would typically check against ROLE_PERMISSIONS from constants
  // For now, return a basic check
  const adminPermissions = ['users:read', 'users:write', 'users:delete'];
  const doctorPermissions = ['patients:read', 'patients:write', 'appointments:read'];
  
  switch (userRole) {
    case 'admin':
      return true; // Admin has all permissions
    case 'doctor':
      return doctorPermissions.includes(permission) || adminPermissions.includes(permission);
    case 'nurse':
      return ['patients:read', 'appointments:read'].includes(permission);
    case 'receptionist':
      return ['patients:read', 'appointments:read', 'appointments:write'].includes(permission);
    default:
      return false;
  }
};

export const getRoleColor = (role: UserRole): string => {
  const colors = {
    admin: '#f44336',
    doctor: '#2196f3',
    nurse: '#4caf50',
    receptionist: '#ff9800',
    manager: '#9c27b0',
  };
  return colors[role] || '#9e9e9e';
};

export const getPriorityColor = (priority: Priority): string => {
  const colors = {
    low: '#4caf50',
    medium: '#ff9800',
    high: '#f44336',
    urgent: '#9c27b0',
    emergency: '#d32f2f',
  };
  return colors[priority] || '#9e9e9e';
};

// File Utilities
export const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes';
  
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

export const getFileExtension = (filename: string): string => {
  return filename.slice((filename.lastIndexOf('.') - 1 >>> 0) + 2);
};

export const isImageFile = (filename: string): boolean => {
  const imageExtensions = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg'];
  return imageExtensions.includes(getFileExtension(filename).toLowerCase());
};

// URL Utilities
export const buildUrl = (base: string, params: Record<string, any>): string => {
  const url = new URL(base);
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null) {
      url.searchParams.append(key, String(value));
    }
  });
  return url.toString();
};

export const getQueryParams = (search: string): Record<string, string> => {
  const params = new URLSearchParams(search);
  const result: Record<string, string> = {};
  params.forEach((value, key) => {
    result[key] = value;
  });
  return result;
};

// Local Storage Utilities
export const storage = {
  get: <T>(key: string, defaultValue?: T): T | null => {
    try {
      const item = localStorage.getItem(key);
      return item ? JSON.parse(item) : defaultValue || null;
    } catch {
      return defaultValue || null;
    }
  },
  
  set: (key: string, value: any): void => {
    try {
      localStorage.setItem(key, JSON.stringify(value));
    } catch (error) {
      console.error('Failed to save to localStorage:', error);
    }
  },
  
  remove: (key: string): void => {
    try {
      localStorage.removeItem(key);
    } catch (error) {
      console.error('Failed to remove from localStorage:', error);
    }
  },
  
  clear: (): void => {
    try {
      localStorage.clear();
    } catch (error) {
      console.error('Failed to clear localStorage:', error);
    }
  },
};

// Debounce Utility
export const debounce = <T extends (...args: any[]) => any>(
  func: T,
  wait: number
): ((...args: Parameters<T>) => void) => {
  let timeout: NodeJS.Timeout;
  
  return (...args: Parameters<T>) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
};

// Throttle Utility
export const throttle = <T extends (...args: any[]) => any>(
  func: T,
  limit: number
): ((...args: Parameters<T>) => void) => {
  let inThrottle: boolean;
  
  return (...args: Parameters<T>) => {
    if (!inThrottle) {
      func(...args);
      inThrottle = true;
      setTimeout(() => (inThrottle = false), limit);
    }
  };
};

// Random Utilities
export const generateId = (): string => {
  return Math.random().toString(36).substr(2, 9);
};

export const generateUUID = (): string => {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = Math.random() * 16 | 0;
    const v = c === 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
};

// Color Utilities
export const hexToRgb = (hex: string): { r: number; g: number; b: number } | null => {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  return result ? {
    r: parseInt(result[1], 16),
    g: parseInt(result[2], 16),
    b: parseInt(result[3], 16),
  } : null;
};

export const rgbToHex = (r: number, g: number, b: number): string => {
  return `#${((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1)}`;
};

export const getContrastColor = (hexColor: string): string => {
  const rgb = hexToRgb(hexColor);
  if (!rgb) return '#000000';
  
  const brightness = (rgb.r * 299 + rgb.g * 587 + rgb.b * 114) / 1000;
  return brightness > 128 ? '#000000' : '#ffffff';
};

// Export all utilities
export default {
  // Date utilities
  formatDate,
  formatTime,
  formatDateTime,
  getRelativeTime,
  calculateAge,
  isToday,
  isTomorrow,
  getDateRange,
  
  // Validation utilities
  validateEmail,
  validatePhone,
  validatePassword,
  validateName,
  getPasswordStrength,
  
  // String utilities
  capitalize,
  capitalizeWords,
  truncateText,
  slugify,
  generateInitials,
  formatPhoneNumber,
  
  // Number utilities
  formatCurrency,
  formatNumber,
  formatPercentage,
  
  // Array utilities
  groupBy,
  sortBy,
  uniqueBy,
  chunk,
  
  // Object utilities
  omit,
  pick,
  isEmpty,
  deepClone,
  
  // User utilities
  getFullName,
  hasPermission,
  getRoleColor,
  getPriorityColor,
  
  // File utilities
  formatFileSize,
  getFileExtension,
  isImageFile,
  
  // URL utilities
  buildUrl,
  getQueryParams,
  
  // Storage utilities
  storage,
  
  // Function utilities
  debounce,
  throttle,
  
  // Random utilities
  generateId,
  generateUUID,
  
  // Color utilities
  hexToRgb,
  rgbToHex,
  getContrastColor,
};