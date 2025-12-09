import { API_CONFIG } from "../config/env";

const API_BASE = API_CONFIG.BASE_URL;
const defaultHeaders = { "Content-Type": "application/json" };
let accessToken = null;

export const setAccessToken = (token) => {
  accessToken = token || null;
};

export const clearAccessToken = () => {
  accessToken = null;
};

export const getAccessToken = () => accessToken;

async function request(path, options = {}) {
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

export default {
  API_BASE,
  request,
  apiGet,
  apiPost,
  apiPostForm,
  apiPut,
  apiDelete,
  setAccessToken,
  clearAccessToken,
  getAccessToken,
};
