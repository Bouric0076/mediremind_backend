import { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAppDispatch, useAppSelector } from '../store/hooks';
import { addToast, removeToast, setLoadingState } from '../store/slices/uiSlice';
import { debounce, storage } from '../utils';
import type { FilterOptions } from '../types';
import type { Toast } from '../store/slices/uiSlice';

// Form Hook
export const useForm = <T extends Record<string, any>>(
  initialValues: T,
  validationRules?: Partial<Record<keyof T, (value: any) => string | null>>
) => {
  const [values, setValues] = useState<T>(initialValues);
  const [errors, setErrors] = useState<Partial<Record<keyof T, string>>>({});
  const [touched, setTouched] = useState<Partial<Record<keyof T, boolean>>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  const setValue = useCallback((name: keyof T, value: any) => {
    setValues(prev => ({ ...prev, [name]: value }));
    
    // Clear error when user starts typing
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: undefined }));
    }
  }, [errors]);

  const setFieldTouched = useCallback((name: keyof T, isTouched: boolean = true) => {
    setTouched(prev => ({ ...prev, [name]: isTouched }));
  }, []);

  const validateField = useCallback((name: keyof T, value: any): string | null => {
    if (validationRules && validationRules[name]) {
      return validationRules[name]!(value);
    }
    return null;
  }, [validationRules]);

  const validateForm = useCallback((): boolean => {
    if (!validationRules) return true;

    const newErrors: Partial<Record<keyof T, string>> = {};
    let isValid = true;

    Object.keys(validationRules).forEach(key => {
      const fieldName = key as keyof T;
      const error = validateField(fieldName, values[fieldName]);
      if (error) {
        newErrors[fieldName] = error;
        isValid = false;
      }
    });

    setErrors(newErrors);
    return isValid;
  }, [validationRules, values, validateField]);

  const handleSubmit = useCallback(async (
    onSubmit: (values: T) => Promise<void> | void
  ) => {
    setIsSubmitting(true);
    
    // Mark all fields as touched
    const allTouched = Object.keys(values).reduce((acc, key) => {
      acc[key as keyof T] = true;
      return acc;
    }, {} as Partial<Record<keyof T, boolean>>);
    setTouched(allTouched);

    if (validateForm()) {
      try {
        await onSubmit(values);
      } catch (error) {
        console.error('Form submission error:', error);
      }
    }
    
    setIsSubmitting(false);
  }, [values, validateForm]);

  const reset = useCallback(() => {
    setValues(initialValues);
    setErrors({});
    setTouched({});
    setIsSubmitting(false);
  }, [initialValues]);

  const isValid = useMemo(() => {
    if (!validationRules) return true;
    return Object.keys(validationRules).every(key => {
      const fieldName = key as keyof T;
      return !validateField(fieldName, values[fieldName]);
    });
  }, [validationRules, values, validateField]);

  return {
    values,
    errors,
    touched,
    isSubmitting,
    isValid,
    setValue,
    setFieldTouched,
    validateField,
    validateForm,
    handleSubmit,
    reset,
  };
};

// Local Storage Hook
export const useLocalStorage = <T>(
  key: string,
  initialValue: T
): [T, (value: T | ((prev: T) => T)) => void, () => void] => {
  const [storedValue, setStoredValue] = useState<T>(() => {
    return storage.get(key, initialValue) ?? initialValue;
  });

  const setValue = useCallback((value: T | ((prev: T) => T)) => {
    try {
      const valueToStore = value instanceof Function ? value(storedValue) : value;
      setStoredValue(valueToStore);
      storage.set(key, valueToStore);
    } catch (error) {
      console.error(`Error setting localStorage key "${key}":`, error);
    }
  }, [key, storedValue]);

  const removeValue = useCallback(() => {
    try {
      setStoredValue(initialValue);
      storage.remove(key);
    } catch (error) {
      console.error(`Error removing localStorage key "${key}":`, error);
    }
  }, [key, initialValue]);

  return [storedValue, setValue, removeValue];
};

// Debounced Value Hook
export const useDebounce = <T>(value: T, delay: number): T => {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
};

// Previous Value Hook
export const usePrevious = <T>(value: T): T | undefined => {
  const ref = useRef<T>(undefined);
  
  useEffect(() => {
    ref.current = value;
  });
  
  return ref.current;
};

// Online Status Hook
export const useOnlineStatus = () => {
  const [isOnline, setIsOnline] = useState(navigator.onLine);

  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  return isOnline;
};

// Window Size Hook
export const useWindowSize = () => {
  const [windowSize, setWindowSize] = useState({
    width: window.innerWidth,
    height: window.innerHeight,
  });

  useEffect(() => {
    const handleResize = debounce(() => {
      setWindowSize({
        width: window.innerWidth,
        height: window.innerHeight,
      });
    }, 100);

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  return windowSize;
};

// Media Query Hook
export const useMediaQuery = (query: string): boolean => {
  const [matches, setMatches] = useState(() => {
    return window.matchMedia(query).matches;
  });

  useEffect(() => {
    const mediaQuery = window.matchMedia(query);
    const handleChange = () => setMatches(mediaQuery.matches);

    mediaQuery.addEventListener('change', handleChange);
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, [query]);

  return matches;
};

// Toast Hook
export const useToast = () => {
  const dispatch = useAppDispatch();

  const toast = useCallback((
    message: string,
    type: Toast['type'] = 'info',
    duration?: number,
    action?: Toast['action']
  ) => {
    const id = Math.random().toString(36).substr(2, 9);
    dispatch(addToast({ id, type, title: message, message: '', duration, action }));
    return id;
  }, [dispatch]);

  const hideToastById = useCallback((id: string) => {
    dispatch(removeToast(id));
  }, [dispatch]);

  return {
    toast,
    success: (message: string, duration?: number) => toast(message, 'success', duration),
    error: (message: string, duration?: number) => toast(message, 'error', duration),
    warning: (message: string, duration?: number) => toast(message, 'warning', duration),
    info: (message: string, duration?: number) => toast(message, 'info', duration),
    hide: hideToastById,
  };
};

// Loading Hook
export const useLoading = () => {
  const dispatch = useAppDispatch();
  const loading = useAppSelector(state => state.ui.loadingStates);

  const setLoadingStateCallback = useCallback((key: string, isLoading: boolean) => {
    dispatch(setLoadingState({ key, loading: isLoading }));
  }, [dispatch]);

  const isLoading = useCallback((key?: string) => {
    if (key) {
      return loading[key] || false;
    }
    return Object.values(loading).some(Boolean);
  }, [loading]);

  return {
    setLoading: setLoadingStateCallback,
    isLoading,
    loading,
  };
};

// Pagination Hook
export const usePagination = (totalItems: number, itemsPerPage: number = 10) => {
  const [currentPage, setCurrentPage] = useState(1);
  
  const totalPages = Math.ceil(totalItems / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = Math.min(startIndex + itemsPerPage, totalItems);
  
  const goToPage = useCallback((page: number) => {
    setCurrentPage(Math.max(1, Math.min(page, totalPages)));
  }, [totalPages]);
  
  const goToNextPage = useCallback(() => {
    goToPage(currentPage + 1);
  }, [currentPage, goToPage]);
  
  const goToPreviousPage = useCallback(() => {
    goToPage(currentPage - 1);
  }, [currentPage, goToPage]);
  
  const reset = useCallback(() => {
    setCurrentPage(1);
  }, []);
  
  return {
    currentPage,
    totalPages,
    startIndex,
    endIndex,
    hasNextPage: currentPage < totalPages,
    hasPreviousPage: currentPage > 1,
    goToPage,
    goToNextPage,
    goToPreviousPage,
    reset,
  };
};

// Search and Filter Hook
export const useSearchAndFilter = <T>(
  data: T[],
  searchFields: (keyof T)[],
  initialFilters: FilterOptions = {}
) => {
  const [filters, setFilters] = useState<FilterOptions>(initialFilters);
  const debouncedSearch = useDebounce(filters.search || '', 300);

  const filteredData = useMemo(() => {
    let result = [...data];

    // Apply search
    if (debouncedSearch) {
      result = result.filter(item =>
        searchFields.some(field => {
          const value = item[field];
          return String(value).toLowerCase().includes(debouncedSearch.toLowerCase());
        })
      );
    }

    // Apply status filter
    if (filters.status && filters.status.length > 0) {
      result = result.filter(item => {
        const status = (item as any).status;
        return filters.status!.includes(status);
      });
    }

    // Apply date range filter
    if (filters.dateRange) {
      result = result.filter(item => {
        const date = new Date((item as any).createdAt || (item as any).startTime);
        const start = new Date(filters.dateRange!.start);
        const end = new Date(filters.dateRange!.end);
        return date >= start && date <= end;
      });
    }

    // Apply sorting
    if (filters.sortBy) {
      result.sort((a, b) => {
        const aValue = (a as any)[filters.sortBy!];
        const bValue = (b as any)[filters.sortBy!];
        
        if (aValue < bValue) return filters.sortOrder === 'desc' ? 1 : -1;
        if (aValue > bValue) return filters.sortOrder === 'desc' ? -1 : 1;
        return 0;
      });
    }

    return result;
  }, [data, searchFields, debouncedSearch, filters]);

  const updateFilter = useCallback((key: keyof FilterOptions, value: any) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  }, []);

  const resetFilters = useCallback(() => {
    setFilters(initialFilters);
  }, [initialFilters]);

  return {
    filteredData,
    filters,
    updateFilter,
    resetFilters,
    setFilters,
  };
};

// Async Hook
export const useAsync = <T, E = string>(
  asyncFunction: () => Promise<T>,
  immediate: boolean = true
) => {
  const [status, setStatus] = useState<'idle' | 'pending' | 'success' | 'error'>('idle');
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<E | null>(null);

  const execute = useCallback(async () => {
    setStatus('pending');
    setData(null);
    setError(null);

    try {
      const response = await asyncFunction();
      setData(response);
      setStatus('success');
      return response;
    } catch (error) {
      setError(error as E);
      setStatus('error');
      throw error;
    }
  }, [asyncFunction]);

  useEffect(() => {
    if (immediate) {
      execute();
    }
  }, [execute, immediate]);

  return {
    execute,
    status,
    data,
    error,
    isIdle: status === 'idle',
    isPending: status === 'pending',
    isSuccess: status === 'success',
    isError: status === 'error',
  };
};

// Interval Hook
export const useInterval = (callback: () => void, delay: number | null) => {
  const savedCallback = useRef(callback);

  useEffect(() => {
    savedCallback.current = callback;
  }, [callback]);

  useEffect(() => {
    if (delay === null) return;

    const tick = () => savedCallback.current();
    const id = setInterval(tick, delay);
    return () => clearInterval(id);
  }, [delay]);
};

// Click Outside Hook
export const useClickOutside = <T extends HTMLElement = HTMLElement>(
  callback: () => void
) => {
  const ref = useRef<T>(null);

  useEffect(() => {
    const handleClick = (event: MouseEvent) => {
      if (ref.current && !ref.current.contains(event.target as Node)) {
        callback();
      }
    };

    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, [callback]);

  return ref;
};

// Keyboard Hook
export const useKeyboard = (key: string, callback: () => void, deps: any[] = []) => {
  useEffect(() => {
    const handleKeyPress = (event: KeyboardEvent) => {
      if (event.key === key) {
        callback();
      }
    };

    document.addEventListener('keydown', handleKeyPress);
    return () => document.removeEventListener('keydown', handleKeyPress);
  }, [key, callback, ...deps]);
};

// Navigation Hook
export const useNavigation = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const goBack = useCallback(() => {
    navigate(-1);
  }, [navigate]);

  const goTo = useCallback((path: string, options?: { replace?: boolean; state?: any }) => {
    navigate(path, options);
  }, [navigate]);

  const isCurrentPath = useCallback((path: string) => {
    return location.pathname === path;
  }, [location.pathname]);

  const getQueryParam = useCallback((key: string) => {
    const params = new URLSearchParams(location.search);
    return params.get(key);
  }, [location.search]);

  return {
    navigate,
    location,
    goBack,
    goTo,
    isCurrentPath,
    getQueryParam,
    pathname: location.pathname,
    search: location.search,
    state: location.state,
  };
};

// Copy to Clipboard Hook
export const useClipboard = () => {
  const [copied, setCopied] = useState(false);
  const toast = useToast();

  const copy = useCallback(async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      toast.success('Copied to clipboard');
      
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      toast.error('Failed to copy to clipboard');
      console.error('Copy failed:', error);
    }
  }, [toast]);

  return { copy, copied };
};

// Export all hooks
export default {
  useForm,
  useLocalStorage,
  useDebounce,
  usePrevious,
  useOnlineStatus,
  useWindowSize,
  useMediaQuery,
  useToast,
  useLoading,
  usePagination,
  useSearchAndFilter,
  useAsync,
  useInterval,
  useClickOutside,
  useKeyboard,
  useNavigation,
  useClipboard,
};