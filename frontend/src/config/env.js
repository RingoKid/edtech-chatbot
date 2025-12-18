// Configuration utility for environment-based settings
const isDevelopment = Boolean(import.meta.env?.DEV);
const isProduction = Boolean(import.meta.env?.PROD);

const FALLBACK_API_BASE_URL = "http://127.0.0.1:8000/api/v1";
const FALLBACK_WS_BASE_URL = "ws://127.0.0.1:8000";

const readRuntimeValue = (key) =>
  typeof window !== "undefined" ? window.__APP_CONFIG?.[key] : undefined;

const stripTrailingSlash = (value) =>
  typeof value === "string" && value.endsWith("/") ? value.slice(0, -1) : value;

const selectApiBaseUrl = () => {
  const envValue = import.meta.env?.VITE_API_BASE_URL;
  const runtimeValue = readRuntimeValue("VITE_API_BASE_URL");
  if (envValue || runtimeValue) {
    return stripTrailingSlash(envValue || runtimeValue);
  }
  const fallback = isDevelopment ? FALLBACK_API_BASE_URL : "/api/v1";
  return stripTrailingSlash(fallback);
};

const selectWsBaseUrl = () => {
  const envValue = import.meta.env?.VITE_WS_BASE_URL;
  const runtimeValue = readRuntimeValue("VITE_WS_BASE_URL");
  if (envValue || runtimeValue) {
    return stripTrailingSlash(envValue || runtimeValue);
  }
  if (!isProduction && isDevelopment) {
    return stripTrailingSlash(FALLBACK_WS_BASE_URL);
  }
  if (typeof window !== "undefined") {
    const scheme = window.location.protocol === "https:" ? "wss:" : "ws:";
    return `${scheme}//${window.location.host}`;
  }
  return stripTrailingSlash(FALLBACK_WS_BASE_URL);
};

// API Configuration
export const API_CONFIG = {
  BASE_URL: selectApiBaseUrl(),
  WS_BASE_URL: selectWsBaseUrl(),
};

// WebSocket URL builder
export const getWebSocketUrl = (endpoint = "/api/v1/chat/ws/message") => {
  const base = API_CONFIG.WS_BASE_URL?.replace(/\/$/, "") || "";
  return `${base}${endpoint}`;
};

// Environment info
export const ENV_INFO = {
  isDevelopment,
  isProduction,
  mode: import.meta.env?.MODE,
};

export default {
  API_CONFIG,
  getWebSocketUrl,
  ENV_INFO,
};
