import client from './client';

export const health = {
  get: () => client.apiGet('/health'),
  debug: () => client.apiGet('/debug-test')
};

export const chat = {
  status: () => client.apiGet('/chat/ws/info'),
  send: (message, threadId = null) => client.apiPost('/chat/message', { message, thread_id: threadId })
};

export const chat2 = {
  status: () => client.apiGet('/chat2/ws/info'),
  send: (message, threadId = null) => client.apiPost('/chat2/message', { message, thread_id: threadId })
};

export const users = {
  status: () => client.apiGet('/users')
};

export const auth = {
  status: () => client.apiGet('/auth')
};

export default { health, chat, users, auth };
