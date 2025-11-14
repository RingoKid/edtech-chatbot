import { useState, useRef, useCallback } from 'react'

/**
 * Custom hook for audio recording with real-time streaming capabilities
 * Captures audio using MediaRecorder API and streams chunks via callback
 */
const useAudioRecorder = () => {
  const [isRecording, setIsRecording] = useState(false)
  const [error, setError] = useState(null)

  const mediaRecorderRef = useRef(null)
  const streamRef = useRef(null)
  const onAudioChunkRef = useRef(null)

  /**
   * Start recording audio
   * @param {Function} onAudioChunk - Callback function that receives audio chunks
   * @returns {Promise<void>}
   */
  const startRecording = useCallback(async (onAudioChunk) => {
    try {
      setError(null)

      // Request microphone access
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          sampleRate: 48000,
          echoCancellation: true,
          noiseSuppression: true,
        }
      })

      streamRef.current = stream
      onAudioChunkRef.current = onAudioChunk

      // Create MediaRecorder with WebM/Opus format (default for modern browsers)
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus',
        audioBitsPerSecond: 128000
      })

      // Handle audio data chunks
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0 && onAudioChunkRef.current) {
          onAudioChunkRef.current(event.data)
        }
      }

      // Handle recording errors
      mediaRecorder.onerror = (event) => {
        console.error('MediaRecorder error:', event.error)
        setError('Recording error occurred')
        stopRecording()
      }

      // Start recording with chunks every 250ms for real-time streaming
      mediaRecorder.start(250)
      mediaRecorderRef.current = mediaRecorder
      setIsRecording(true)

    } catch (err) {
      console.error('Error starting recording:', err)

      if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
        setError('Microphone access denied. Please grant permission to use voice recording.')
      } else if (err.name === 'NotFoundError') {
        setError('No microphone found. Please connect a microphone and try again.')
      } else {
        setError('Failed to start recording. Please check your microphone settings.')
      }
    }
  }, [])

  /**
   * Stop recording audio
   */
  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop()
    }

    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop())
      streamRef.current = null
    }

    mediaRecorderRef.current = null
    onAudioChunkRef.current = null
    setIsRecording(false)
  }, [])

  /**
   * Reset error state
   */
  const clearError = useCallback(() => {
    setError(null)
  }, [])

  return {
    isRecording,
    error,
    startRecording,
    stopRecording,
    clearError
  }
}

export default useAudioRecorder