import { useRef, useCallback } from 'react';
import AudioWebSocketClient from '../api/audioWebSocket';
import { useAudioRecorder } from './useAudioRecorder';

/**
 * Custom hook for voice chat functionality.
 * Combines audio recording and WebSocket streaming.
 *
 * @param {Object} options - Configuration options
 * @param {string} options.threadId - Current thread ID
 * @param {Function} options.onTranscript - Callback when transcript received
 * @param {Function} options.onResponse - Callback when LLM response received
 * @param {Function} options.onStatus - Callback for status updates
 * @param {Function} options.onError - Callback for errors
 * @returns {Object} Voice chat controls
 */
export const useVoiceChat = ({
  threadId,
  onTranscript,
  onResponse,
  onStatus,
  onError
}) => {
  const audioWSClientRef = useRef(null);

  const {
    isRecording,
    isPermissionDenied,
    error: audioError,
    audioLevel,
    startRecording,
    stopRecording,
    isSupported
  } = useAudioRecorder();

  /**
   * Initialize WebSocket client and set up event listeners
   */
  const setupWebSocket = useCallback(async () => {
    try {
      const client = new AudioWebSocketClient(threadId);
      audioWSClientRef.current = client;

      // Register event listeners
      client.on('transcript', (data) => {
        console.log('📝 Transcript:', data.text);
        if (onTranscript) onTranscript(data.text);
      });

      client.on('response', (data) => {
        console.log('💬 Response:', data.text);
        if (onResponse) onResponse(data.text, data.threadId);
      });

      client.on('status', (data) => {
        console.log('ℹ️ Status:', data.message);
        if (onStatus) onStatus(data.message);
      });

      client.on('error', (data) => {
        console.error('❌ Error:', data.message);
        if (onError) onError(data.message);
      });

      client.on('disconnected', () => {
        console.log('🔌 WebSocket disconnected');
      });

      // Connect to WebSocket
      await client.connect();
      return client;
    } catch (error) {
      console.error('Failed to setup WebSocket:', error);
      if (onError) onError('Failed to connect to voice service');
      return null;
    }
  }, [threadId, onTranscript, onResponse, onStatus, onError]);

  /**
   * Start voice recording and streaming
   */
  const startVoiceRecording = useCallback(async () => {
    if (!isSupported()) {
      if (onError) onError('Voice recording not supported in this browser');
      return;
    }

    try {
      // Setup WebSocket first
      const client = await setupWebSocket();
      if (!client) {
        if (onError) onError('Failed to connect to voice service');
        return;
      }

      // Start audio recording with data callback
      await startRecording((audioBlob) => {
        if (client && client.getConnectionStatus()) {
          client.sendAudio(audioBlob);
        }
      }, {
        timeslice: 1000 // Send audio chunks every 1 second
      });

      if (onStatus) onStatus('Recording...');
    } catch (error) {
      console.error('Failed to start voice recording:', error);
      if (onError) onError(`Failed to start recording: ${error.message}`);
    }
  }, [isSupported, setupWebSocket, startRecording, onError, onStatus]);

  /**
   * Stop voice recording and finalize
   */
  const stopVoiceRecording = useCallback(() => {
    // Stop audio recording
    stopRecording();

    // Signal end of audio to backend
    if (audioWSClientRef.current) {
      audioWSClientRef.current.endAudio();

      if (onStatus) onStatus('Processing...');

      // Disconnect after a delay (let server finish processing)
      setTimeout(() => {
        if (audioWSClientRef.current) {
          audioWSClientRef.current.disconnect();
          audioWSClientRef.current = null;
        }
      }, 10000); // 10 second timeout
    }
  }, [stopRecording, onStatus]);

  /**
   * Toggle voice recording on/off
   */
  const toggleVoiceRecording = useCallback(async () => {
    console.log('🎤 Toggle clicked, isRecording:', isRecording);
    if (isRecording) {
      console.log('🛑 Stopping recording...');
      stopVoiceRecording();
    } else {
      console.log('▶️ Starting recording...');
      await startVoiceRecording();
    }
  }, [isRecording, startVoiceRecording, stopVoiceRecording]);

  /**
   * Cleanup function
   */
  const cleanup = useCallback(() => {
    if (audioWSClientRef.current) {
      audioWSClientRef.current.disconnect();
      audioWSClientRef.current = null;
    }
    if (isRecording) {
      stopRecording();
    }
  }, [isRecording, stopRecording]);

  return {
    isRecording,
    isPermissionDenied,
    audioError,
    audioLevel,
    startVoiceRecording,
    stopVoiceRecording,
    toggleVoiceRecording,
    cleanup,
    isSupported: isSupported()
  };
};