import client from './client';

export const health = {
  get: () => client.apiGet('/health'),
  debug: () => client.apiGet('/debug-test')
};

export const chat = {
  status: () => client.apiGet('/chat')
  , send: (message) => client.apiPost('/message', { message })
};

export const users = {
  status: () => client.apiGet('/users')
};

export const auth = {
  status: () => client.apiGet('/auth')
};

export default { health, chat, users, auth };
