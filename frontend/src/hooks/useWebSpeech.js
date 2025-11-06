import { useState, useEffect, useRef, useCallback } from 'react';

/**
 * Custom hook for Web Speech API (Browser-native speech recognition)
 * Works in Chrome, Edge, and Safari
 *
 * @returns {Object} Speech recognition state and controls
 */
export const useWebSpeech = () => {
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [interimTranscript, setInterimTranscript] = useState('');
  const [isSupported, setIsSupported] = useState(false);
  const [error, setError] = useState(null);

  const recognitionRef = useRef(null);

  // Check browser support on mount
  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

    if (SpeechRecognition) {
      setIsSupported(true);

      // Initialize speech recognition
      const recognition = new SpeechRecognition();
      recognition.continuous = true; // Keep listening until stopped
      recognition.interimResults = true; // Get real-time results
      recognition.lang = 'en-US'; // Language
      recognition.maxAlternatives = 1;

      recognitionRef.current = recognition;

      // Event handlers
      recognition.onstart = () => {
        console.log('🎤 Speech recognition started');
        setIsListening(true);
        setError(null);
      };

      recognition.onresult = (event) => {
        let interim = '';
        let final = '';

        // Process all results
        for (let i = event.resultIndex; i < event.results.length; i++) {
          const transcript = event.results[i][0].transcript;

          if (event.results[i].isFinal) {
            final += transcript + ' ';
          } else {
            interim += transcript;
          }
        }

        // Update states
        if (interim) {
          setInterimTranscript(interim);
        }

        if (final) {
          setTranscript(prev => prev + final);
          setInterimTranscript(''); // Clear interim when we get final
        }
      };

      recognition.onerror = (event) => {
        console.error('❌ Speech recognition error:', event.error);

        if (event.error === 'no-speech') {
          setError('No speech detected. Please try again.');
        } else if (event.error === 'audio-capture') {
          setError('Microphone not accessible. Please check permissions.');
        } else if (event.error === 'not-allowed') {
          setError('Microphone permission denied. Please allow access.');
        } else {
          setError(`Error: ${event.error}`);
        }

        setIsListening(false);
      };

      recognition.onend = () => {
        console.log('🛑 Speech recognition ended');
        setIsListening(false);
        setInterimTranscript('');
      };

    } else {
      setIsSupported(false);
      console.warn('⚠️ Web Speech API not supported in this browser');
    }

    // Cleanup
    return () => {
      if (recognitionRef.current) {
        try {
          recognitionRef.current.stop();
        } catch (e) {
          // Ignore errors on cleanup
        }
      }
    };
  }, []);

  /**
   * Start listening for speech
   */
  const startListening = useCallback(() => {
    if (!recognitionRef.current || !isSupported) {
      setError('Speech recognition not supported in this browser. Please use Chrome or Edge.');
      return;
    }

    try {
      // Reset transcript
      setTranscript('');
      setInterimTranscript('');
      setError(null);

      recognitionRef.current.start();
    } catch (error) {
      console.error('Error starting speech recognition:', error);
      setError('Failed to start speech recognition');
    }
  }, [isSupported]);

  /**
   * Stop listening
   */
  const stopListening = useCallback(() => {
    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch (error) {
        console.error('Error stopping speech recognition:', error);
      }
    }
  }, []);

  /**
   * Toggle listening on/off
   */
  const toggleListening = useCallback(() => {
    if (isListening) {
      stopListening();
    } else {
      startListening();
    }
  }, [isListening, startListening, stopListening]);

  /**
   * Reset transcript
   */
  const resetTranscript = useCallback(() => {
    setTranscript('');
    setInterimTranscript('');
  }, []);

  /**
   * Get full transcript (final + interim)
   */
  const getFullTranscript = useCallback(() => {
    const full = transcript + (interimTranscript ? ' ' + interimTranscript : '');
    return full.trim();
  }, [transcript, interimTranscript]);

  return {
    isListening,
    transcript, // Final transcript
    interimTranscript, // Real-time interim transcript
    fullTranscript: getFullTranscript(), // Combined transcript
    isSupported,
    error,
    startListening,
    stopListening,
    toggleListening,
    resetTranscript
  };
};