import client from './client';

export const health = {
  get: () => client.apiGet('/health'),
  debug: () => client.apiGet('/debug-test')
};

export const chat = {
  status: () => client.apiGet('/chat'),
  // send(message, thread_id?) -> POST /api/v1/chat/message
  send: (message, thread_id = undefined) => {
    const body = thread_id ? { message, thread_id } : { message };
    return client.apiPost('/chat/message', body);
  }
};

// WebSocket helper (uses Vite env var VITE_WS_BASE_URL)
import createWsClient from '../utils/wsClient';
export function createChatWsClient() {
  const base = import.meta.env.VITE_WS_BASE_URL || 'ws://localhost:8000';
  const wsUrl = base.replace(/\/$/, '') + '/api/v1/chat/ws/message';
  return createWsClient(wsUrl, { maxRetries: 10, baseDelay: 500 });
}

export const users = {
  status: () => client.apiGet('/users')
};

export const auth = {
  status: () => client.apiGet('/auth')
};

export default { health, chat, users, auth };
