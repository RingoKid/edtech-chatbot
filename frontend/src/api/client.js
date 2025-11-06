// Lightweight fetch-based API client
const API_BASE = import.meta.env.VITE_API_BASE_URL || "https://mkbifgscip.us-east-1.awsapprunner.com/api/v1/";

async function request(path, options = {}) {
  const url = API_BASE + path;
  const opts = Object.assign({
    headers: { 'Content-Type': 'application/json' }
  }, options);

  if (opts.body && typeof opts.body !== 'string') {
    opts.body = JSON.stringify(opts.body);
  }

  const res = await fetch(url, opts);
  const text = await res.text();
  let data;
  try {
    data = text ? JSON.parse(text) : null;
  } catch (e) {
    data = text;
  }

  if (!res.ok) {
    let errorMsg;
    if (data?.detail) {
      if (typeof data.detail === 'string') {
        errorMsg = data.detail;
      } else if (Array.isArray(data.detail)) {
        errorMsg = data.detail.map(item => typeof item === 'string' ? item : JSON.stringify(item)).join('; ');
      } else if (typeof data.detail === 'object') {
        errorMsg = JSON.stringify(data.detail);
      } else {
        errorMsg = String(data.detail);
      }
    } else if (data?.message) {
      errorMsg = data.message;
    } else {
      errorMsg = res.statusText || 'API Error';
    }
    const error = new Error(errorMsg);
    error.status = res.status;
    error.body = data;
    throw error;
  }

  return data;
}

export const apiGet = (path) => request(path, { method: 'GET' });
export const apiPost = (path, body) => request(path, { method: 'POST', body });
export const apiPut = (path, body) => request(path, { method: 'PUT', body });
export const apiDelete = (path) => request(path, { method: 'DELETE' });

export default { API_BASE, request, apiGet, apiPost, apiPut, apiDelete };
