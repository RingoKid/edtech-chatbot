// Configuration utility for environment-based settings
const isDevelopment = import.meta.env.DEV;
const isProduction = import.meta.env.PROD;

// API Configuration
export const API_CONFIG = {
  BASE_URL: import.meta.env.VITE_API_BASE_URL || (
    isDevelopment 
      ? "http://localhost:8000/api/v1" 
      : "/api/v1" // Relative URL for production deployments
  ),
  WS_BASE_URL: import.meta.env.VITE_WS_BASE_URL || (
    isDevelopment 
      ? "ws://localhost:8000" 
      : `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}`
  ),
};

// WebSocket URL builder
export const getWebSocketUrl = (endpoint = '/api/v1/chat/ws/message') => {
  return API_CONFIG.WS_BASE_URL.replace(/\/$/, '') + endpoint;
};

// Environment info
export const ENV_INFO = {
  isDevelopment,
  isProduction,
  mode: import.meta.env.MODE,
};

export default {
  API_CONFIG,
  getWebSocketUrl,
  ENV_INFO,
};