// Lightweight fetch-based API client
const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1";

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
    const error = new Error(data?.message || res.statusText || 'API Error');
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
