import client from "./client";

export const health = {
  get: () => client.apiGet("/health"),
  debug: () => client.apiGet("/debug-test"),
};

export const chat = {
  status: () => client.apiGet("/chat/"),
  // send(message, threadId?) -> POST /api/v1/chat/message
  send: (message, threadId) => {
    const body = threadId ? { message, thread_id: threadId } : { message };
    return client.apiPost("/chat/message", body);
  },
};

// chat2 is an alias for chat with additional methods for Chatbot2 component
export const chat2 = {
  ...chat,
  // init - Initialize a new chat session and get the greeting message
  init: () => client.apiGet("/chat/init"),
  // getHistory - Get list of all conversations for the user
  getHistory: () => client.apiGet("/chat/history"),
  // getMessages - Get all messages for a specific conversation
  getMessages: (threadId) => client.apiGet(`/chat/${threadId}/messages`),
  // exportPdf - Download lesson plan as PDF
  exportPdf: async (threadId) => {
    const response = await fetch(`${client.API_BASE}/chat/${threadId}/export-pdf`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${client.getAccessToken()}` },
    })
    if (!response.ok) {
      throw new Error('Failed to export PDF')
    }
    const blob = await response.blob()
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `lesson-${threadId.slice(0, 8)}.pdf`
    document.body.appendChild(a)
    a.click()
    a.remove()
    window.URL.revokeObjectURL(url)
  },
};

// WebSocket helper (uses environment-based configuration)
import createWsClient from "../utils/wsClient";
import { getWebSocketUrl } from "../config/env";

export function createChatWsClient() {
  const wsUrl = getWebSocketUrl("/api/v1/chat/ws/message");
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

export const handwriting = {
  analyzeImage: async (imageFile, message = null, gradeLevel = null, targetLetter = null) => {
    const formData = new FormData()
    formData.append('image', imageFile)
    if (message) formData.append('message', message)
    if (gradeLevel) formData.append('grade_level', gradeLevel)
    if (targetLetter) formData.append('target_letter', targetLetter)

    const response = await fetch(`${client.API_BASE}/handwriting/analyze-image`, {
      method: 'POST',
      body: formData
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Failed to upload image')
    }

    return response.json()
  },
  analyzeVideo: async (videoFile, message = null, gradeLevel = null, targetLetter = null) => {
    const formData = new FormData()
    formData.append('video', videoFile)
    if (message) formData.append('message', message)
    if (gradeLevel) formData.append('grade_level', gradeLevel)
    if (targetLetter) formData.append('target_letter', targetLetter)

    const response = await fetch(`${client.API_BASE}/handwriting/analyze-video`, {
      method: 'POST',
      body: formData
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Failed to upload video')
    }

    return response.json()
  },
  getAnalysisStatus: (jobId) => client.apiGet(`/handwriting/analysis/${jobId}`),
  getVideoAnalysisStatus: (jobId) => client.apiGet(`/handwriting/video-analysis/${jobId}`)
};

export default { health, chat, chat2, users, auth, handwriting };
