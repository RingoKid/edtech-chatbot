import client from "./client";

export const health = {
  get: () => client.apiGet("/health"),
  debug: () => client.apiGet("/debug-test"),
};

export const chat = {
  status: () => client.apiGet("/chat"),
  // send(message, threadId?) -> POST /api/v1/chat/message
  send: (message, threadId) => {
    const body = threadId ? { message, thread_id: threadId } : { message };
    return client.apiPost("/chat/message", body);
  },
};

// WebSocket helper (uses environment-based configuration)
import createWsClient from '../utils/wsClient';
import { getWebSocketUrl } from '../config/env';

export function createChatWsClient() {
  const wsUrl = getWebSocketUrl('/api/v1/chat/ws/message');
  return createWsClient(wsUrl, { maxRetries: 10, baseDelay: 500 });
}

export const users = {
  status: () => client.apiGet("/users"),
};

export const auth = {
  signup: ({ email, password, full_name, role }) =>
    client.apiPost("/auth/signup", {
      email,
      password,
      full_name,
      role,
    }),
  login: ({ email, password }) => {
    const formParams = new URLSearchParams();
    formParams.append("username", email);
    formParams.append("password", password);
    return client.apiPostForm("/auth/login", formParams, {
      credentials: "include",
    });
  },
  me: () => client.apiGet("/auth/me"),
  refresh: () =>
    client.apiPost("/auth/refresh", undefined, { credentials: "include" }),
  logout: () =>
    client.apiPost("/auth/logout", undefined, { credentials: "include" }),
  logoutAll: () =>
    client.apiPost("/auth/logout-all", undefined, { credentials: "include" }),
};

export default { health, chat, users, auth };
