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

// WebSocket helper (uses environment-based configuration)
import createWsClient from '../utils/wsClient';
import { getWebSocketUrl } from '../config/env';

export function createChatWsClient() {
  const wsUrl = getWebSocketUrl('/api/v1/chat/ws/message');
  return createWsClient(wsUrl, { maxRetries: 10, baseDelay: 500 });
}

export const users = {
  status: () => client.apiGet('/users')
};

export const auth = {
  status: () => client.apiGet('/auth')
};

export default { health, chat, users, auth };
