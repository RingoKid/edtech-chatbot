import { API_CONFIG } from "../config/env";

const API_BASE = API_CONFIG.BASE_URL;
const defaultHeaders = { "Content-Type": "application/json" };
let accessToken = null;

// Token refresh state to handle concurrent requests
let isRefreshing = false;
let refreshPromise = null;
let onTokenRefreshed = null; // Callback to notify AuthContext of new token

export const setAccessToken = (token) => {
  accessToken = token || null;
};

export const clearAccessToken = () => {
  accessToken = null;
};

export const getAccessToken = () => accessToken;

// Register callback for when token is refreshed (called by AuthContext)
export const setOnTokenRefreshed = (callback) => {
  onTokenRefreshed = callback;
};

// Attempt to refresh the access token
async function refreshAccessToken() {
  const res = await fetch(`${API_BASE}/auth/refresh`, {
    method: "POST",
    credentials: "include",
  });

  if (!res.ok) {
    throw new Error("Token refresh failed");
  }

  const data = await res.json();
  setAccessToken(data.access_token);

  // Notify AuthContext to update its state
  if (onTokenRefreshed) {
    onTokenRefreshed(data.access_token);
  }

  return data.access_token;
}

// Paths that should not trigger token refresh on 401
const AUTH_PATHS = ["/auth/login", "/auth/refresh", "/auth/signup"];

async function request(path, options = {}, isRetry = false) {
  const url = API_BASE + path;
  const { body, headers = {}, credentials, ...rest } = options;
  const finalHeaders = { ...defaultHeaders, ...headers };

  if (accessToken) {
    finalHeaders.Authorization = `Bearer ${accessToken}`;
  }

  let resolvedBody = body;
  const shouldJsonEncode =
    resolvedBody !== undefined &&
    resolvedBody !== null &&
    typeof resolvedBody !== "string" &&
    finalHeaders["Content-Type"]?.includes("application/json");
  if (shouldJsonEncode) {
    resolvedBody = JSON.stringify(resolvedBody);
  }

  const fetchOptions = {
    ...rest,
    method: rest.method || "GET",
    headers: finalHeaders,
    credentials: credentials ?? "include",
  };

  if (resolvedBody !== undefined && resolvedBody !== null) {
    fetchOptions.body = resolvedBody;
  }

  const res = await fetch(url, fetchOptions);
  const text = await res.text();
  let data;
  try {
    data = text ? JSON.parse(text) : null;
  } catch (e) {
    data = text;
  }

  if (!res.ok) {
    // Handle 401 Unauthorized - attempt token refresh and retry
    const shouldAttemptRefresh =
      res.status === 401 &&
      !isRetry &&
      !AUTH_PATHS.some((authPath) => path.startsWith(authPath));

    if (shouldAttemptRefresh) {
      try {
        // Use a single refresh promise for concurrent requests
        if (!isRefreshing) {
          isRefreshing = true;
          refreshPromise = refreshAccessToken();
        }

        await refreshPromise;
        isRefreshing = false;
        refreshPromise = null;

        // Retry the original request with new token
        return request(path, options, true);
      } catch (refreshError) {
        isRefreshing = false;
        refreshPromise = null;
        // Refresh failed - throw original 401 error
      }
    }

    // Normalize various FastAPI error shapes into a readable message
    let errorMsg;
    if (data?.detail) {
      if (typeof data.detail === "string") {
        errorMsg = data.detail;
      } else if (Array.isArray(data.detail)) {
        errorMsg = data.detail
          .map((item) =>
            typeof item === "string" ? item : JSON.stringify(item)
          )
          .join("; ");
      } else if (typeof data.detail === "object") {
        errorMsg = JSON.stringify(data.detail);
      } else {
        errorMsg = String(data.detail);
      }
    } else if (data?.message) {
      errorMsg = data.message;
    } else {
      errorMsg = res.statusText || "API Error";
    }
    const error = new Error(errorMsg);
    error.status = res.status;
    error.body = data;
    throw error;
  }

  return data;
}

export const apiGet = (path, options = {}) =>
  request(path, { method: "GET", ...options });
export const apiPost = (path, body, options = {}) =>
  request(path, { method: "POST", body, ...options });
export const apiPostForm = (path, body, options = {}) => {
  const headers = {
    "Content-Type": "application/x-www-form-urlencoded",
    ...(options.headers || {}),
  };
  return request(path, { method: "POST", body, ...options, headers });
};
export const apiPut = (path, body, options = {}) =>
  request(path, { method: "PUT", body, ...options });
export const apiDelete = (path, options = {}) =>
  request(path, { method: "DELETE", ...options });

// For FormData uploads (files) - doesn't set Content-Type, lets browser handle it
export const apiPostFormData = (path, formData, options = {}) => {
  const { headers = {}, ...rest } = options;
  // Remove Content-Type to let browser set multipart boundary
  const formDataHeaders = { ...headers };
  delete formDataHeaders["Content-Type"];
  return request(path, {
    method: "POST",
    body: formData,
    headers: formDataHeaders,
    ...rest,
  });
};

export default {
  API_BASE,
  request,
  apiGet,
  apiPost,
  apiPostForm,
  apiPostFormData,
  apiPut,
  apiDelete,
  setAccessToken,
  clearAccessToken,
  getAccessToken,
  setOnTokenRefreshed,
};
