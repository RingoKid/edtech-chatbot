import { useRef, useCallback } from 'react';

/**
 * Custom hook to debounce function calls and prevent rapid repeated executions
 * @param {Function} callback - The function to debounce
 * @param {number} delay - Delay in milliseconds
 * @returns {Function} Debounced version of the callback
 */
export const useDebounce = (callback, delay) => {
  const timeoutRef = useRef(null);

  return useCallback((...args) => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    
    timeoutRef.current = setTimeout(() => {
      callback(...args);
    }, delay);
  }, [callback, delay]);
};

/**
 * Custom hook to prevent rapid repeated function calls
 * @param {Function} callback - The function to throttle
 * @param {number} delay - Minimum delay between calls in milliseconds
 * @returns {Function} Throttled version of the callback
 */
export const useThrottle = (callback, delay) => {
  const lastCallRef = useRef(0);
  const timeoutRef = useRef(null);

  return useCallback((...args) => {
    const now = Date.now();
    const timeSinceLastCall = now - lastCallRef.current;

    if (timeSinceLastCall >= delay) {
      lastCallRef.current = now;
      callback(...args);
    } else {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
      
      timeoutRef.current = setTimeout(() => {
        lastCallRef.current = Date.now();
        callback(...args);
      }, delay - timeSinceLastCall);
    }
  }, [callback, delay]);
};

/**
 * Custom hook to prevent duplicate API calls
 * @param {Function} apiCall - The API function to call
 * @param {number} cooldown - Cooldown period in milliseconds (default: 1000ms)
 * @returns {Function} Protected API call function
 */
export const useApiCallProtection = (apiCall, cooldown = 1000) => {
  const lastCallRef = useRef(0);
  const pendingRef = useRef(false);

  return useCallback(async (...args) => {
    const now = Date.now();
    
    // Prevent calls if one is already pending or within cooldown period
    if (pendingRef.current || (now - lastCallRef.current) < cooldown) {
      return null;
    }

    pendingRef.current = true;
    lastCallRef.current = now;

    try {
      const result = await apiCall(...args);
      return result;
    } finally {
      pendingRef.current = false;
    }
  }, [apiCall, cooldown]);
};