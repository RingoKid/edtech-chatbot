import { useState, useRef, useCallback } from 'react';

/**
 * Custom hook for audio recording with WebSocket streaming.
 * Handles microphone access, audio capture, and real-time streaming.
 *
 * @returns {Object} Audio recording state and controls
 */
export const useAudioRecorder = () => {
  const [isRecording, setIsRecording] = useState(false);
  const [isPermissionDenied, setIsPermissionDenied] = useState(false);
  const [error, setError] = useState(null);
  const [audioLevel, setAudioLevel] = useState(0);

  const mediaRecorderRef = useRef(null);
  const audioStreamRef = useRef(null);
  const audioContextRef = useRef(null);
  const analyserRef = useRef(null);
  const animationFrameRef = useRef(null);

  /**
   * Initialize audio visualization (waveform/level meter)
   */
  const initializeAudioVisualization = useCallback((stream) => {
    try {
      const audioContext = new (window.AudioContext || window.webkitAudioContext)();
      const analyser = audioContext.createAnalyser();
      const source = audioContext.createMediaStreamSource(stream);

      analyser.fftSize = 256;
      source.connect(analyser);

      audioContextRef.current = audioContext;
      analyserRef.current = analyser;

      // Start monitoring audio levels
      const dataArray = new Uint8Array(analyser.frequencyBinCount);

      const updateLevel = () => {
        analyser.getByteFrequencyData(dataArray);
        const average = dataArray.reduce((a, b) => a + b) / dataArray.length;
        const normalizedLevel = Math.min(average / 128, 1); // Normalize to 0-1
        setAudioLevel(normalizedLevel);

        animationFrameRef.current = requestAnimationFrame(updateLevel);
      };

      updateLevel();
    } catch (err) {
      console.error('Audio visualization error:', err);
    }
  }, []);

  /**
   * Stop audio visualization
   */
  const stopAudioVisualization = useCallback(() => {
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
    }

    if (audioContextRef.current) {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }

    setAudioLevel(0);
  }, []);

  /**
   * Start audio recording
   * @param {Function} onDataAvailable - Callback for audio data chunks
   * @param {Object} options - Recording options
   */
  const startRecording = useCallback(async (onDataAvailable, options = {}) => {
    try {
      setError(null);
      setIsPermissionDenied(false);

      // Request microphone access
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          sampleRate: 16000, // Optimal for Whisper
          channelCount: 1     // Mono
        }
      });

      audioStreamRef.current = stream;

      // Initialize visualization
      initializeAudioVisualization(stream);

      // Determine best available MIME type
      let mimeType = 'audio/webm;codecs=opus';
      if (!MediaRecorder.isTypeSupported(mimeType)) {
        mimeType = 'audio/webm';
      }
      if (!MediaRecorder.isTypeSupported(mimeType)) {
        mimeType = 'audio/mp4';
      }

      console.log(`🎤 Using MIME type: ${mimeType}`);

      // Create MediaRecorder
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType,
        audioBitsPerSecond: 16000 // Low bitrate for voice
      });

      mediaRecorderRef.current = mediaRecorder;

      // Handle data availability
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          onDataAvailable(event.data);
        }
      };

      // Handle recording stop
      mediaRecorder.onstop = () => {
        console.log('🎤 Recording stopped');
        stopAudioVisualization();
      };

      // Handle errors
      mediaRecorder.onerror = (event) => {
        console.error('MediaRecorder error:', event.error);
        setError(`Recording error: ${event.error.name}`);
      };

      // Start recording with timeslice for streaming
      const timeslice = options.timeslice || 1000; // 1 second chunks
      mediaRecorder.start(timeslice);

      setIsRecording(true);
      console.log('🎤 Recording started');

    } catch (err) {
      console.error('Error starting recording:', err);

      if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
        setIsPermissionDenied(true);
        setError('Microphone access denied. Please allow microphone permissions.');
      } else if (err.name === 'NotFoundError') {
        setError('No microphone found. Please connect a microphone and try again.');
      } else {
        setError(`Failed to start recording: ${err.message}`);
      }

      setIsRecording(false);
    }
  }, [initializeAudioVisualization, stopAudioVisualization]);

  /**
   * Stop audio recording
   */
  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);

      // Stop all audio tracks
      if (audioStreamRef.current) {
        audioStreamRef.current.getTracks().forEach(track => track.stop());
        audioStreamRef.current = null;
      }

      stopAudioVisualization();
      console.log('🎤 Recording stopped by user');
    }
  }, [isRecording, stopAudioVisualization]);

  /**
   * Cancel recording and cleanup
   */
  const cancelRecording = useCallback(() => {
    stopRecording();
    mediaRecorderRef.current = null;
  }, [stopRecording]);

  /**
   * Check if browser supports audio recording
   */
  const isSupported = useCallback(() => {
    return !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia && window.MediaRecorder);
  }, []);

  return {
    isRecording,
    isPermissionDenied,
    error,
    audioLevel,
    startRecording,
    stopRecording,
    cancelRecording,
    isSupported
  };
};