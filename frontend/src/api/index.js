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
  /**
   * Stream a chat response via SSE.
   * Returns { stream, abort } where:
   *   stream({ onMeta, onToken, onDone, onError }) - starts consuming the SSE
   *   abort() - cancels the request
   */
  sendStream: (message, threadId) => {
    const controller = new AbortController()
    const body = threadId ? { message, thread_id: threadId } : { message }

    const stream = async ({ onMeta, onToken, onDone, onError } = {}) => {
      const response = await fetch(`${client.API_BASE}/chat/message/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${client.getAccessToken()}`,
        },
        body: JSON.stringify(body),
        signal: controller.signal,
      })

      if (!response.ok) {
        const errText = await response.text()
        throw new Error(errText || response.statusText)
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      let streamComplete = false

      try {
        while (!streamComplete) {
          const { done, value } = await reader.read()
          if (done) break

          buffer += decoder.decode(value, { stream: true })

          // Normalize CRLF → LF (sse-starlette uses \r\n line endings)
          buffer = buffer.replace(/\r\n/g, '\n')

          // Parse SSE frames: split on double newline
          const frames = buffer.split('\n\n')
          // Keep the last incomplete frame in the buffer
          buffer = frames.pop() || ''

          for (const frame of frames) {
            if (!frame.trim()) continue

            let eventType = 'message'
            let data = ''

            for (const line of frame.split('\n')) {
              if (line.startsWith('event:')) {
                eventType = line.slice(6).trim()
              } else if (line.startsWith('data:')) {
                data = line.slice(5).trim()
              }
            }

            if (!data) continue

            try {
              const parsed = JSON.parse(data)
              switch (eventType) {
                case 'meta':
                  onMeta?.(parsed)
                  break
                case 'token':
                  onToken?.(parsed)
                  break
                case 'done':
                  onDone?.(parsed)
                  streamComplete = true
                  break
                case 'error':
                  onError?.(parsed)
                  streamComplete = true
                  break
              }
            } catch {
              // Non-JSON data lines (e.g. SSE comments) — skip
            }
          }
        }
      } finally {
        reader.cancel()
      }
    }

    return { stream, abort: () => controller.abort() }
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
