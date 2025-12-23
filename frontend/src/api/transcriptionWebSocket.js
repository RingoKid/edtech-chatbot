/**
 * WebSocket client for real-time audio transcription
 * Streams audio chunks to backend and receives live transcript updates
 */

import { getAccessToken } from './client'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'

// Convert HTTP URL to WebSocket URL with auth token
const getWebSocketUrl = () => {
  const wsBase = API_BASE_URL.replace(/^http/, 'ws')
  const token = getAccessToken()
  const baseUrl = `${wsBase}/transcribe`
  return token ? `${baseUrl}?token=${encodeURIComponent(token)}` : baseUrl
}

class TranscriptionWebSocket {
  constructor() {
    this.ws = null
    this.onTranscriptUpdate = null
    this.onTranscriptComplete = null
    this.onError = null
    this.onConnectionChange = null
    this.isConnected = false
    this.reconnectAttempts = 0
    this.maxReconnectAttempts = 3
  }

  /**
   * Connect to WebSocket server
   * @param {Object} callbacks - Event callbacks
   * @param {Function} callbacks.onTranscriptUpdate - Called when partial transcript received
   * @param {Function} callbacks.onTranscriptComplete - Called when final transcript received
   * @param {Function} callbacks.onError - Called on error
   * @param {Function} callbacks.onConnectionChange - Called when connection state changes
   */
  connect({ onTranscriptUpdate, onTranscriptComplete, onError, onConnectionChange }) {
    return new Promise((resolve, reject) => {
      try {
        this.onTranscriptUpdate = onTranscriptUpdate
        this.onTranscriptComplete = onTranscriptComplete
        this.onError = onError
        this.onConnectionChange = onConnectionChange

        const wsUrl = getWebSocketUrl()
        this.ws = new WebSocket(wsUrl)

        this.ws.onopen = () => {
          console.log('WebSocket connected for transcription')
          this.isConnected = true
          this.reconnectAttempts = 0
          if (this.onConnectionChange) {
            this.onConnectionChange(true)
          }
          resolve()
        }

        this.ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data)
            console.log('Received WebSocket message:', data)

            // Handle backend message types: "partial", "final", "error"
            if (data.type === 'partial' && this.onTranscriptUpdate) {
              // Partial transcript received during recording
              console.log('Partial transcript:', data.text)
              this.onTranscriptUpdate(data.text, data.is_final || false)
            } else if (data.type === 'final' && this.onTranscriptUpdate) {
              // Final transcript - send as update first, then complete
              console.log('Final transcript:', data.text)
              this.onTranscriptUpdate(data.text, true)
              if (this.onTranscriptComplete) {
                console.log('Calling onTranscriptComplete')
                this.onTranscriptComplete(data.text)
              }
            } else if (data.type === 'error' && this.onError) {
              console.log('Transcription error:', data.message)
              this.onError(data.message || 'Transcription error occurred')
            }
          } catch (err) {
            console.error('Error parsing WebSocket message:', err)
            if (this.onError) {
              this.onError('Failed to process transcription response')
            }
          }
        }

        this.ws.onerror = (error) => {
          console.error('WebSocket error:', error)
          if (this.onError) {
            this.onError('WebSocket connection error. Please check your connection.')
          }
          reject(error)
        }

        this.ws.onclose = (event) => {
          console.log('WebSocket closed:', event.code, event.reason)
          this.isConnected = false
          if (this.onConnectionChange) {
            this.onConnectionChange(false)
          }

          // Attempt reconnection if not a clean close and haven't exceeded max attempts
          if (!event.wasClean && this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++
            console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`)
            setTimeout(() => {
              this.connect({
                onTranscriptUpdate: this.onTranscriptUpdate,
                onTranscriptComplete: this.onTranscriptComplete,
                onError: this.onError,
                onConnectionChange: this.onConnectionChange
              }).catch(() => {
                // Reconnection failed
              })
            }, 2000)
          }
        }
      } catch (err) {
        console.error('Error creating WebSocket:', err)
        if (this.onError) {
          this.onError('Failed to establish connection')
        }
        reject(err)
      }
    })
  }

  /**
   * Send audio chunk to server
   * @param {Blob} audioChunk - Audio data blob
   */
  sendAudioChunk(audioChunk) {
    if (!this.isConnected || !this.ws || this.ws.readyState !== WebSocket.OPEN) {
      console.warn('WebSocket not connected, cannot send audio chunk')
      return
    }

    // Send audio blob directly (backend will handle binary data)
    this.ws.send(audioChunk)
  }

  /**
   * Signal end of audio stream
   */
  endStream() {
    if (this.isConnected && this.ws && this.ws.readyState === WebSocket.OPEN) {
      // Send stop message to backend
      this.ws.send(JSON.stringify({ type: 'stop' }))
    }
  }

  /**
   * Disconnect WebSocket
   */
  disconnect() {
    this.reconnectAttempts = this.maxReconnectAttempts // Prevent auto-reconnect
    if (this.ws) {
      this.ws.close(1000, 'Client disconnecting')
      this.ws = null
    }
    this.isConnected = false
    this.onTranscriptUpdate = null
    this.onTranscriptComplete = null
    this.onError = null
    this.onConnectionChange = null
  }
}

export default TranscriptionWebSocket