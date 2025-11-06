/**
 * WebSocket client for audio streaming and voice chat.
 * Handles binary audio transmission and receives transcription/responses.
 */

const WS_BASE = import.meta.env.VITE_API_BASE_URL?.replace('http', 'ws') || 'ws://localhost:8000/api/v1';

export class AudioWebSocketClient {
  constructor(threadId = null) {
    this.ws = null;
    this.threadId = threadId;
    this.isConnected = false;
    this.listeners = {
      transcript: [],
      response: [],
      status: [],
      error: [],
      bufferStatus: [],
      connected: [],
      disconnected: []
    };
  }

  /**
   * Connect to the audio WebSocket endpoint
   */
  connect() {
    return new Promise((resolve, reject) => {
      try {
        const wsUrl = `${WS_BASE}/chat2/ws/audio`;
        console.log(`🔌 Connecting to audio WebSocket: ${wsUrl}`);

        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
          console.log('✅ Audio WebSocket connected');
          this.isConnected = true;
          this._emit('connected');
          resolve();
        };

        this.ws.onmessage = (event) => {
          this._handleMessage(event);
        };

        this.ws.onerror = (error) => {
          console.error('❌ WebSocket error:', error);
          this._emit('error', { message: 'WebSocket connection error' });
          reject(error);
        };

        this.ws.onclose = () => {
          console.log('🔌 Audio WebSocket disconnected');
          this.isConnected = false;
          this._emit('disconnected');
        };

      } catch (error) {
        console.error('❌ Failed to create WebSocket:', error);
        reject(error);
      }
    });
  }

  /**
   * Handle incoming WebSocket messages
   */
  _handleMessage(event) {
    try {
      const data = JSON.parse(event.data);
      const type = data.type;

      console.log(`📨 Received message:`, data);

      switch (type) {
        case 'transcript':
          this._emit('transcript', { text: data.text });
          break;

        case 'response':
          this.threadId = data.thread_id; // Update thread ID
          this._emit('response', {
            text: data.text,
            threadId: data.thread_id
          });
          break;

        case 'status':
          this._emit('status', { message: data.message });
          break;

        case 'error':
          this._emit('error', { message: data.message });
          break;

        case 'buffer_status':
          this._emit('bufferStatus', { size: data.size });
          break;

        default:
          console.warn('Unknown message type:', type);
      }
    } catch (error) {
      console.error('❌ Error parsing WebSocket message:', error);
    }
  }

  /**
   * Send binary audio data
   * @param {Blob} audioBlob - Audio data to send
   */
  sendAudio(audioBlob) {
    if (!this.isConnected || !this.ws) {
      console.error('❌ WebSocket not connected');
      return;
    }

    if (this.ws.readyState !== WebSocket.OPEN) {
      console.error('❌ WebSocket not in OPEN state');
      return;
    }

    // Send binary audio data
    this.ws.send(audioBlob);
    console.log(`📤 Sent audio chunk: ${audioBlob.size} bytes`);
  }

  /**
   * Signal end of audio recording
   */
  endAudio() {
    if (!this.isConnected || !this.ws) {
      console.error('❌ WebSocket not connected');
      return;
    }

    const message = JSON.stringify({
      type: 'audio_end',
      thread_id: this.threadId
    });

    this.ws.send(message);
    console.log('📤 Sent audio_end signal');
  }

  /**
   * Clear the server-side audio buffer
   */
  clearBuffer() {
    if (!this.isConnected || !this.ws) {
      console.error('❌ WebSocket not connected');
      return;
    }

    const message = JSON.stringify({
      type: 'clear_buffer'
    });

    this.ws.send(message);
    console.log('📤 Sent clear_buffer signal');
  }

  /**
   * Register event listener
   * @param {string} event - Event name (transcript, response, status, error, etc.)
   * @param {Function} callback - Callback function
   */
  on(event, callback) {
    if (this.listeners[event]) {
      this.listeners[event].push(callback);
    } else {
      console.warn(`Unknown event type: ${event}`);
    }
  }

  /**
   * Unregister event listener
   * @param {string} event - Event name
   * @param {Function} callback - Callback function to remove
   */
  off(event, callback) {
    if (this.listeners[event]) {
      this.listeners[event] = this.listeners[event].filter(cb => cb !== callback);
    }
  }

  /**
   * Emit event to all registered listeners
   */
  _emit(event, data = {}) {
    if (this.listeners[event]) {
      this.listeners[event].forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          console.error(`Error in ${event} listener:`, error);
        }
      });
    }
  }

  /**
   * Disconnect and cleanup
   */
  disconnect() {
    if (this.ws) {
      console.log('🔌 Disconnecting audio WebSocket...');
      this.ws.close();
      this.ws = null;
      this.isConnected = false;
    }
  }

  /**
   * Get connection status
   */
  getConnectionStatus() {
    return this.isConnected && this.ws && this.ws.readyState === WebSocket.OPEN;
  }

  /**
   * Get current thread ID
   */
  getThreadId() {
    return this.threadId;
  }

  /**
   * Set thread ID for conversation continuity
   */
  setThreadId(threadId) {
    this.threadId = threadId;
  }
}

export default AudioWebSocketClient;