import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Send, Bot, User, Loader, RotateCcw, ChevronDown, Mic, MicOff, Image, Camera, Plus, X } from 'lucide-react'
import { cn } from '../utils/cn'
import { chat2, handwriting } from '../api'
import MarkdownRenderer from './MarkdownRenderer'
import useAudioRecorder from '../hooks/useAudioRecorder'
import TranscriptionWebSocket from '../api/transcriptionWebSocket'
import CameraModal from './CameraModal'


const Chatbot2 = ({ onNewMessage, hideHeader = false }) => {
  const [messages, setMessages] = useState([])
  const [inputValue, setInputValue] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const [isUserScrolling, setIsUserScrolling] = useState(false)
  const [isInitialMount, setIsInitialMount] = useState(true)
  const [threadId, setThreadId] = useState(null) // Store thread_id for conversation persistence
  const [liveTranscript, setLiveTranscript] = useState('') // Live transcript display
  const [transcriptionError, setTranscriptionError] = useState(null) // Transcription errors
  const [selectedImage, setSelectedImage] = useState(null) // Store selected image file
  const [imagePreview, setImagePreview] = useState(null) // Store image preview URL
  const [selectedVideo, setSelectedVideo] = useState(null) // Store selected video file
  const [videoPreview, setVideoPreview] = useState(null) // Store video preview URL
  const [fileType, setFileType] = useState(null) // Track if selected file is 'image' or 'video'
  const [showAttachmentMenu, setShowAttachmentMenu] = useState(false) // Show/hide attachment menu
  const [showCameraModal, setShowCameraModal] = useState(false) // Show/hide camera modal
  const messagesEndRef = useRef(null)
  const messagesContainerRef = useRef(null)
  const transcriptionWsRef = useRef(null)
  const wsConnectedRef = useRef(false) // Track if WebSocket was successfully connected
  const accumulatedTranscriptRef = useRef('') // Accumulate all transcripts during recording session
  const fileInputRef = useRef(null) // Reference for file input
  const textareaRef = useRef(null) // Reference for textarea to restore focus

  // Initialize audio recorder hook
  const { isRecording, error: recorderError, startRecording, stopRecording, clearError } = useAudioRecorder()

  // Cleanup WebSocket on unmount
  useEffect(() => {
    return () => {
      if (transcriptionWsRef.current) {
        transcriptionWsRef.current.disconnect()
      }
    }
  }, [])

  // Restore focus to textarea when typing indicator disappears
  useEffect(() => {
    if (!isTyping && !isRecording && textareaRef.current) {
      textareaRef.current.focus()
    }
  }, [isTyping, isRecording])

  // Initialize chat session on mount
  useEffect(() => {
    const initChat = async () => {
      setIsTyping(true)
      try {
        const res = await chat2.init()
        if (res?.thread_id) {
          setThreadId(res.thread_id)
        }
        setMessages([{
          id: Date.now(),
          type: 'bot',
          content: res?.reply || "Hello! How can I help you today?",
          timestamp: new Date()
        }])
      } catch (err) {
        console.error('Failed to initialize chat:', err)
        // Fallback message on error
        setMessages([{
          id: Date.now(),
          type: 'bot',
          content: "Hello! How can I help you today?",
          timestamp: new Date()
        }])
      } finally {
        setIsTyping(false)
      }
    }

    initChat()
  }, [])




  // Check if user is at the bottom of the chat
  const isAtBottom = () => {
    if (!messagesContainerRef.current) return true
    const { scrollTop, scrollHeight, clientHeight } = messagesContainerRef.current
    return scrollTop + clientHeight >= scrollHeight - 10 // 10px threshold
  }

  // Auto-scroll to latest message only if user is at bottom
  const scrollToBottom = () => {
    if (!isUserScrolling || isAtBottom()) {
      if (messagesContainerRef.current) {
        messagesContainerRef.current.scrollTop = messagesContainerRef.current.scrollHeight
      }
      setIsUserScrolling(false)
    }
  }

  // Force scroll to bottom (used by the scroll-to-bottom button)
  const forceScrollToBottom = () => {
    if (messagesContainerRef.current) {
      messagesContainerRef.current.scrollTo({
        top: messagesContainerRef.current.scrollHeight,
        behavior: 'smooth'
      })
    }
    setIsUserScrolling(false)
  }

  // Handle scroll events to detect manual scrolling
  const handleScroll = () => {
    if (!messagesContainerRef.current) return

    const isScrolledToBottom = isAtBottom()
    if (!isScrolledToBottom) {
      setIsUserScrolling(true)
    } else {
      setIsUserScrolling(false)
    }
  }

  useEffect(() => {
    if (isInitialMount) {
      setIsInitialMount(false)
      return
    }
    scrollToBottom()
  }, [messages, isTyping])

  const simulateTyping = async () => {
    setIsTyping(true)
    await new Promise(resolve => setTimeout(resolve, 1000 + Math.random() * 2000))
    setIsTyping(false)
  }

  const generateResponse = (userMessage) => {
    const responses = {
      phonics: "For phonics instruction, I recommend multi-sensory approaches! Try letter-sound activities with movement, sand tray writing, and interactive games. Would you like specific activity suggestions for particular letters or sounds?",
      behavior: "Positive behavior support is key! Consider implementing a visual schedule, clear expectations, and consistent routines. Praise specific behaviors and use redirection for challenging moments. What specific behaviors are you addressing?",
      assessment: "For authentic assessment, try portfolio documentation, observation notes, and photo evidence of learning. Focus on developmental milestones rather than just academic skills. Would you like help creating assessment rubrics?",
      lesson: "I'd be happy to help with lesson planning! For effective early childhood lessons, include hands-on activities, movement breaks, and opportunities for choice. What subject and age group are you planning for?",
      writing: "Early writing development progresses through stages: scribbling, letter-like forms, invented spelling, to conventional writing. Encourage all attempts and focus on meaning-making. What writing challenges are you seeing?",
      reading: "Building reading readiness involves phonological awareness, print concepts, and vocabulary development. Use interactive read-alouds, rhyming games, and environmental print. What specific reading skills are you targeting?",
      parent: "Parent communication is essential! Try weekly newsletters, photo documentation of learning, and regular check-ins. Be specific about what children are learning and how families can support at home. What communication challenges are you facing?",
      default: "That's a great question! In early childhood education, it's important to consider developmental appropriateness, individual needs, and engaging, hands-on approaches. Could you provide more specific details about your situation so I can give you more targeted suggestions?"
    }

    const message = userMessage.toLowerCase()

    if (message.includes('phonics') || message.includes('letter') || message.includes('sound')) {
      return responses.phonics
    } else if (message.includes('behavior') || message.includes('discipline') || message.includes('management')) {
      return responses.behavior
    } else if (message.includes('assess') || message.includes('evaluation') || message.includes('progress')) {
      return responses.assessment
    } else if (message.includes('lesson') || message.includes('plan') || message.includes('activity')) {
      return responses.lesson
    } else if (message.includes('writing') || message.includes('handwriting')) {
      return responses.writing
    } else if (message.includes('reading') || message.includes('literacy')) {
      return responses.reading
    } else if (message.includes('parent') || message.includes('family') || message.includes('communication')) {
      return responses.parent
    } else {
      return responses.default
    }
  }

  // Poll for handwriting analysis results (image)
  const pollAnalysisStatus = async (jobId, maxAttempts = 30) => {
    for (let attempt = 0; attempt < maxAttempts; attempt++) {
      try {
        const statusRes = await handwriting.getAnalysisStatus(jobId)

        if (statusRes.status === 'completed' && statusRes.result) {
          return statusRes.result
        } else if (statusRes.status === 'failed') {
          throw new Error(statusRes.result?.error_message || 'Analysis failed')
        }

        // Wait 2 seconds before next poll
        await new Promise(resolve => setTimeout(resolve, 2000))
      } catch (error) {
        console.error('Error polling analysis status:', error)
        throw error
      }
    }

    throw new Error('Analysis timed out. Please try again.')
  }

  // Poll for video analysis results
  const pollVideoAnalysisStatus = async (jobId, maxAttempts = 60) => {
    for (let attempt = 0; attempt < maxAttempts; attempt++) {
      try {
        const statusRes = await handwriting.getVideoAnalysisStatus(jobId)

        if (statusRes.status === 'completed' && statusRes.result) {
          return statusRes.result
        } else if (statusRes.status === 'failed') {
          throw new Error(statusRes.result?.error_message || 'Video analysis failed')
        }

        // Wait 2 seconds before next poll (videos take longer)
        await new Promise(resolve => setTimeout(resolve, 2000))
      } catch (error) {
        console.error('Error polling video analysis status:', error)
        throw error
      }
    }

    throw new Error('Video analysis timed out. Please try again.')
  }

  const handleSendMessage = async () => {
    // Check if we have an image, video, or text message
    const hasImage = selectedImage !== null
    const hasVideo = selectedVideo !== null
    const hasText = inputValue.trim().length > 0

    if (!hasImage && !hasVideo && !hasText) return

    // If we have a video, use video handwriting analysis API
    if (hasVideo) {
      const userMessage = inputValue.trim() || 'Please analyze this handwriting video.'
      const videoFile = selectedVideo
      const videoUrl = videoPreview

      // Create user message with video
      const newUserMessage = {
        id: Date.now(),
        type: 'user',
        content: userMessage,
        video: videoUrl, // Store video preview URL for display
        timestamp: new Date()
      }

      setMessages(prev => [...prev, newUserMessage])
      setInputValue('')
      setSelectedVideo(null)
      setVideoPreview(null)
      setFileType(null)

      // Reset file input
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }

      // Notify parent component
      if (onNewMessage) {
        onNewMessage()
      }

      // Send video for analysis
      setIsTyping(true)
      try {
        // Upload video and get job_id
        const uploadRes = await handwriting.analyzeVideo(videoFile, userMessage)

        if (uploadRes?.thread_id) {
          setThreadId(uploadRes.thread_id)
        }

        // Poll for results
        const analysisResult = await pollVideoAnalysisStatus(uploadRes.job_id)

        // Format VIDEO analysis results for display
        let responseContent = `**Video Handwriting Analysis Complete**\n\n`
        responseContent += `**Frames Analyzed:** ${analysisResult.total_frames_analyzed}\n\n`

        if (analysisResult.feedback) {
          responseContent += `**Feedback:** ${analysisResult.feedback}\n\n`
        }

        if (analysisResult.suggestions && analysisResult.suggestions.length > 0) {
          responseContent += `**Suggestions:**\n`
          analysisResult.suggestions.forEach(suggestion => {
            responseContent += `- ${suggestion}\n`
          })
          responseContent += `\n`
        }

        if (analysisResult.progression_analysis) {
          const prog = analysisResult.progression_analysis
          responseContent += `**Progression Analysis:**\n`
          responseContent += `- Type: ${prog.progression_type}\n`
          responseContent += `- Consistency Score: ${(prog.consistency_score * 100).toFixed(1)}%\n`
          if (prog.stroke_count_change) {
            responseContent += `- Stroke Count Change: ${prog.stroke_count_change}\n`
          }
          responseContent += `\n`
        }

        if (analysisResult.aggregated_features) {
          const agg = analysisResult.aggregated_features
          responseContent += `**Average Metrics:**\n`
          responseContent += `- Stroke Count: ${agg.avg_stroke_count?.toFixed(1)}\n`
          responseContent += `- Line Straightness: ${(agg.avg_line_straightness * 100)?.toFixed(1)}%\n`
          responseContent += `- Most Common Baseline: ${agg.most_common_baseline}\n`
          responseContent += `\n`
        }

        if (analysisResult.analysis_summary) {
          responseContent += `**Summary:** ${analysisResult.analysis_summary}\n\n`
        }

        const botResponse = {
          id: Date.now() + 1,
          type: 'bot',
          content: responseContent,
          timestamp: new Date()
        }

        setMessages(prev => [...prev, botResponse])
      } catch (error) {
        console.error('Failed to analyze video:', error)
        const errorResponse = {
          id: Date.now() + 1,
          type: 'bot',
          content: `Sorry, I encountered an error analyzing the video: ${error.message}. Please try again.`,
          timestamp: new Date()
        }
        setMessages(prev => [...prev, errorResponse])
      } finally {
        setIsTyping(false)
      }
    }
    // If we have an image, use handwriting analysis API
    else if (hasImage) {
      const userMessage = inputValue.trim() || 'Please analyze this handwriting.'
      const imageFile = selectedImage
      const imageUrl = imagePreview

      // Create user message with image
      const newUserMessage = {
        id: Date.now(),
        type: 'user',
        content: userMessage,
        image: imageUrl, // Store image preview URL for display
        timestamp: new Date()
      }

      setMessages(prev => [...prev, newUserMessage])
      setInputValue('')
      setSelectedImage(null)
      setImagePreview(null)

      // Reset file input
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }

      // Notify parent component
      if (onNewMessage) {
        onNewMessage()
      }

      // Send image for analysis
      setIsTyping(true)
      try {
        // Upload image and get job_id
        const uploadRes = await handwriting.analyzeImage(imageFile, userMessage)

        if (uploadRes?.thread_id) {
          setThreadId(uploadRes.thread_id)
        }

        // Poll for results
        const analysisResult = await pollAnalysisStatus(uploadRes.job_id)

        // Format analysis results for display
        let responseContent = `**Handwriting Analysis Complete**\n\n`

        if (analysisResult.detected_character) {
          responseContent += `**Detected Character:** ${analysisResult.detected_character}\n\n`
        }

        if (analysisResult.feedback) {
          responseContent += `**Feedback:** ${analysisResult.feedback}\n\n`
        }

        if (analysisResult.suggestions && analysisResult.suggestions.length > 0) {
          responseContent += `**Suggestions:**\n`
          analysisResult.suggestions.forEach(suggestion => {
            responseContent += `- ${suggestion}\n`
          })
          responseContent += `\n`
        }

        if (analysisResult.analysis_summary) {
          responseContent += `**Summary:** ${analysisResult.analysis_summary}\n\n`
        }

        const botResponse = {
          id: Date.now() + 1,
          type: 'bot',
          content: responseContent,
          timestamp: new Date()
        }

        setMessages(prev => [...prev, botResponse])
      } catch (error) {
        console.error('Failed to analyze handwriting:', error)
        const errorResponse = {
          id: Date.now() + 1,
          type: 'bot',
          content: `Sorry, I encountered an error analyzing the handwriting: ${error.message}. Please try again.`,
          timestamp: new Date()
        }
        setMessages(prev => [...prev, errorResponse])
      } finally {
        setIsTyping(false)
      }
    } else {
      // No image, send regular text message
      const newUserMessage = {
        id: Date.now(),
        type: 'user',
        content: inputValue,
        timestamp: new Date()
      }

      setMessages(prev => [...prev, newUserMessage])
      setInputValue('')

      // Notify parent component of new message
      if (onNewMessage) {
        onNewMessage()
      }

      // First try backend chat endpoint; if it fails fall back to local generator
      setIsTyping(true)
      try {
        // Pass the thread_id to maintain conversation context
        const res = await chat2.send(inputValue, threadId)

        // Store the thread_id from response for next request
        if (res?.thread_id) {
          setThreadId(res.thread_id)
        }

        const botResponse = {
          id: Date.now() + 1,
          type: 'bot',
          content: res?.reply ?? generateResponse(inputValue),
          timestamp: new Date()
        }
        setMessages(prev => [...prev, botResponse])
      } catch (err) {
        // fallback to local response
        const response = generateResponse(inputValue)
        const botResponse = {
          id: Date.now() + 1,
          type: 'bot',
          content: response,
          timestamp: new Date()
        }
        setMessages(prev => [...prev, botResponse])
      } finally {
        setIsTyping(false)
      }
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  const clearChat = async () => {
    // Reset messages and start a new chat session
    setMessages([])
    setThreadId(null)
    setIsTyping(true)

    try {
      const res = await chat2.init()
      if (res?.thread_id) {
        setThreadId(res.thread_id)
      }
      setMessages([{
        id: Date.now(),
        type: 'bot',
        content: res?.reply || "Hello! How can I help you today?",
        timestamp: new Date()
      }])
    } catch (err) {
      console.error('Failed to initialize chat:', err)
      setMessages([{
        id: Date.now(),
        type: 'bot',
        content: "Hello! How can I help you today?",
        timestamp: new Date()
      }])
    } finally {
      setIsTyping(false)
    }
  }

  // Handle file selection (image or video)
  const handleImageSelect = (event) => {
    const file = event.target.files?.[0]
    if (!file) return

    const isImage = file.type.startsWith('image/')
    const isVideo = file.type.startsWith('video/')

    // Validate file type
    if (!isImage && !isVideo) {
      alert('Please select an image or video file')
      return
    }

    // Validate file size
    if (isImage) {
      if (file.size > 10 * 1024 * 1024) {
        alert('Image size should be less than 10MB')
        return
      }
    } else if (isVideo) {
      if (file.size > 50 * 1024 * 1024) {
        alert('Video size should be less than 50MB')
        return
      }

      // Validate video format
      const supportedFormats = ['video/mp4', 'video/quicktime', 'video/webm', 'video/x-msvideo']
      if (!supportedFormats.includes(file.type)) {
        alert('Unsupported video format. Please use MP4, MOV, WebM, or AVI.')
        return
      }
    }

    // Set file and file type
    if (isImage) {
      setSelectedImage(file)
      setSelectedVideo(null)
      setVideoPreview(null)
      setFileType('image')

      // Create preview URL for image
      const reader = new FileReader()
      reader.onloadend = () => {
        setImagePreview(reader.result)
      }
      reader.readAsDataURL(file)
    } else if (isVideo) {
      setSelectedVideo(file)
      setSelectedImage(null)
      setImagePreview(null)
      setFileType('video')

      // Create preview URL for video
      const reader = new FileReader()
      reader.onloadend = () => {
        setVideoPreview(reader.result)
      }
      reader.readAsDataURL(file)
    }
  }

  // Remove selected file (image or video)
  const handleRemoveImage = () => {
    setSelectedImage(null)
    setImagePreview(null)
    setSelectedVideo(null)
    setVideoPreview(null)
    setFileType(null)
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  // Handle plus button click
  const handlePlusButtonClick = () => {
    setShowAttachmentMenu(!showAttachmentMenu)
  }

  // Handle photo/video upload
  const handlePhotoVideoClick = () => {
    fileInputRef.current?.click()
    setShowAttachmentMenu(false)
  }

  // Handle camera click - open camera modal
  const handleCameraClick = () => {
    setShowCameraModal(true)
    setShowAttachmentMenu(false)
  }

  // Handle camera capture
  const handleCameraCapture = (file) => {
    // Check file size (max 10MB)
    if (file.size > 10 * 1024 * 1024) {
      alert('Image size should be less than 10MB')
      return
    }

    setSelectedImage(file)

    // Create preview URL
    const reader = new FileReader()
    reader.onloadend = () => {
      setImagePreview(reader.result)
    }
    reader.readAsDataURL(file)
  }

  // Handle voice recording toggle
  const handleVoiceToggle = async () => {
    if (isRecording) {
      // Stop recording
      stopRecording()

      // Clear live transcript immediately when stopping
      setLiveTranscript('')

      // Send end-of-stream signal and disconnect
      if (transcriptionWsRef.current) {
        transcriptionWsRef.current.endStream()

        // Disconnect WebSocket after user stops recording
        setTimeout(() => {
          if (transcriptionWsRef.current) {
            transcriptionWsRef.current.disconnect()
            transcriptionWsRef.current = null
          }
        }, 500) // Small delay to allow final messages to arrive
      }

      // Create final message with accumulated transcript and send to chat API
      if (accumulatedTranscriptRef.current.trim()) {
        const transcriptContent = accumulatedTranscriptRef.current.trim()

        const transcriptMessage = {
          id: Date.now(),
          type: 'user',
          content: transcriptContent,
          timestamp: new Date()
        }
        setMessages(prev => [...prev, transcriptMessage])

        // Notify parent component of new message
        if (onNewMessage) {
          onNewMessage()
        }

        // Send transcript to chat API and get bot response
        setIsTyping(true)
        try {
          // Pass the thread_id to maintain conversation context
          const res = await chat2.send(transcriptContent, threadId)

          // Store the thread_id from response for next request
          if (res?.thread_id) {
            setThreadId(res.thread_id)
          }

          const botResponse = {
            id: Date.now() + 1,
            type: 'bot',
            content: res?.reply ?? generateResponse(transcriptContent),
            timestamp: new Date()
          }
          setMessages(prev => [...prev, botResponse])
        } catch (err) {
          // fallback to local response
          const response = generateResponse(transcriptContent)
          const botResponse = {
            id: Date.now() + 1,
            type: 'bot',
            content: response,
            timestamp: new Date()
          }
          setMessages(prev => [...prev, botResponse])
        } finally {
          setIsTyping(false)
        }
      }

      // Reset accumulated transcript
      accumulatedTranscriptRef.current = ''
      setLiveTranscript('')

      // Reset connection tracking
      wsConnectedRef.current = false
    } else {
      // Start recording
      try {
        // Clear any previous errors and accumulated transcript
        setTranscriptionError(null)
        clearError()
        setLiveTranscript('')
        accumulatedTranscriptRef.current = ''

        // FIRST: Start audio recording to request microphone permission
        await startRecording((audioChunk) => {
          if (transcriptionWsRef.current) {
            transcriptionWsRef.current.sendAudioChunk(audioChunk)
          }
        })

        // SECOND: After mic permission granted, initialize WebSocket connection
        transcriptionWsRef.current = new TranscriptionWebSocket()
        await transcriptionWsRef.current.connect({
          onTranscriptUpdate: (transcript, isFinal) => {
            // Ignore partial transcripts - we only care about final ones
          },
          onTranscriptComplete: (finalTranscript) => {
            console.log('onTranscriptComplete called with:', finalTranscript)

            // Only process non-empty final transcripts
            if (finalTranscript.trim()) {
              // Add space if there's already accumulated text
              if (accumulatedTranscriptRef.current) {
                accumulatedTranscriptRef.current += ' ' + finalTranscript.trim()
              } else {
                accumulatedTranscriptRef.current = finalTranscript.trim()
              }
              console.log('Accumulated transcript:', accumulatedTranscriptRef.current)

              // Update live transcript to show accumulated final text only
              setLiveTranscript(accumulatedTranscriptRef.current)
            }

            // DON'T disconnect - keep listening for more speech!
            // WebSocket will only disconnect when user clicks stop button
            // Final message will be created when user stops recording
          },
          onError: (error) => {
            setTranscriptionError(error)
            setLiveTranscript('')
            stopRecording()
          },
          onConnectionChange: (connected) => {
            if (connected) {
              // Mark that WebSocket successfully connected
              wsConnectedRef.current = true
            } else if (!connected && wsConnectedRef.current && isRecording) {
              // Only show error if we were previously connected (i.e., connection was lost)
              setTranscriptionError('Connection lost. Please try again.')
              stopRecording()
              wsConnectedRef.current = false
            }
          }
        })

      } catch (error) {
        console.error('Failed to start voice recording:', error)

        // Provide more specific error messages
        let errorMessage = 'Failed to start voice recording. Please try again.'
        if (error.name === 'NotAllowedError' || error.name === 'PermissionDeniedError') {
          errorMessage = 'Microphone access denied. Please grant permission to use voice recording.'
        } else if (error.name === 'NotFoundError') {
          errorMessage = 'No microphone found. Please connect a microphone and try again.'
        }

        setTranscriptionError(errorMessage)
        stopRecording()
        if (transcriptionWsRef.current) {
          transcriptionWsRef.current.disconnect()
          transcriptionWsRef.current = null
        }
      }
    }
  }

  return (
    <div className={cn(
      "flex flex-col h-full bg-white",
      hideHeader ? "border-0 shadow-none rounded-none" : "border border-gray-200 rounded-xl shadow-lg overflow-hidden"
    )}>
      {/* Header */}
      {!hideHeader && (
        <div className="flex items-center justify-between p-4 bg-gradient-to-r from-purple-500 to-pink-500 text-white">
          <div className="flex items-center">
            <div className="w-8 h-8 bg-white/20 rounded-full flex items-center justify-center mr-3">
              <Bot className="w-5 h-5" />
            </div>
            <h3 className="font-semibold">AI Teaching Assistant</h3>
          </div>
          <button
            onClick={clearChat}
            className="p-2 hover:bg-white/20 rounded-lg transition-colors"
            title="Clear conversation"
          >
            <RotateCcw className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Messages */}
      <div
        ref={messagesContainerRef}
        onScroll={handleScroll}
        className="flex-1 overflow-y-auto p-4 space-y-4 relative min-h-0"
      >
        <AnimatePresence>
          {messages.map((message) => (
            <motion.div
              key={message.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className={cn(
                "flex",
                message.type === 'user' ? 'justify-end' : 'justify-start'
              )}
            >
              <div className={cn(
                "flex max-w-[80%]",
                message.type === 'user' ? 'flex-row-reverse' : 'flex-row'
              )}>
                <div className={cn(
                  "flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-white text-sm",
                  message.type === 'user'
                    ? 'bg-purple-500 ml-2'
                    : 'bg-gradient-to-br from-pink-500 to-purple-500 mr-2'
                )}>
                  {message.type === 'user' ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
                </div>

                <div className={cn(
                  "rounded-lg px-4 py-2 shadow-sm",
                  message.type === 'user'
                    ? 'bg-purple-500 text-white'
                    : 'bg-gray-100 text-gray-900'
                )}>
                  {/* Show image if present */}
                  {message.image && (
                    <img
                      src={message.image}
                      alt="Uploaded"
                      className="max-w-full rounded-lg mb-2 max-h-48 object-contain"
                    />
                  )}

                  {/* Show video if present */}
                  {message.video && (
                    <video
                      src={message.video}
                      controls
                      className="max-w-full rounded-lg mb-2 max-h-48"
                    />
                  )}

                  {message.type === 'user' ? (
                    <p className="text-sm leading-relaxed">{message.content}</p>
                  ) : (
                    <MarkdownRenderer
                      content={message.content}
                      className="text-sm leading-relaxed"
                    />
                  )}
                  <div className={cn(
                    "text-xs mt-1 opacity-70",
                    message.type === 'user' ? 'text-white/70' : 'text-gray-500'
                  )}>
                    {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </div>
                </div>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>

        {/* Live transcript display */}
        {liveTranscript && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex justify-end"
          >
            <div className="flex flex-row-reverse max-w-[80%]">
              <div className="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-white text-sm bg-purple-500 ml-2">
                <Mic className="w-4 h-4 animate-pulse" />
              </div>
              <div className="rounded-lg px-4 py-2 shadow-sm bg-purple-400 text-white">
                <p className="text-sm leading-relaxed italic">{liveTranscript}</p>
                <div className="text-xs mt-1 opacity-70 text-white/70">
                  Listening...
                </div>
              </div>
            </div>
          </motion.div>
        )}

        {/* Typing indicator */}
        {isTyping && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex justify-start"
          >
            <div className="flex items-center">
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-pink-500 to-purple-500 flex items-center justify-center text-white mr-2">
                <Bot className="w-4 h-4" />
              </div>
              <div className="bg-gray-100 rounded-lg px-4 py-2 flex items-center space-x-1">
                <Loader className="w-4 h-4 animate-spin text-gray-500" />
                <span className="text-sm text-gray-500">Thinking...</span>
              </div>
            </div>
          </motion.div>
        )}

        {/* Scroll anchor */}
        <div ref={messagesEndRef} />

        {/* Scroll to bottom button */}
        {isUserScrolling && (
          <motion.button
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.8 }}
            onClick={forceScrollToBottom}
            className="absolute bottom-4 right-4 w-10 h-10 bg-purple-500 text-white rounded-full shadow-lg hover:bg-purple-600 transition-colors flex items-center justify-center z-10"
            title="Scroll to bottom"
          >
            <ChevronDown className="w-5 h-5" />
          </motion.button>
        )}
      </div>


      {/* Input */}
      <div className="p-4 border-t bg-gray-50">
        {/* Error messages */}
        {(transcriptionError || recorderError) && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-3 p-3 bg-red-50 border border-red-200 rounded-lg"
          >
            <p className="text-sm text-red-600 font-medium">
              {transcriptionError || recorderError}
            </p>
          </motion.div>
        )}

        {/* Image preview */}
        {imagePreview && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-3 relative inline-block"
          >
            <img
              src={imagePreview}
              alt="Selected"
              className="max-h-32 rounded-lg border border-gray-200"
            />
            <button
              onClick={handleRemoveImage}
              className="absolute -top-2 -right-2 w-6 h-6 bg-red-500 text-white rounded-full flex items-center justify-center hover:bg-red-600 transition-colors"
              title="Remove image"
            >
              ×
            </button>
          </motion.div>
        )}

        {/* Video preview */}
        {videoPreview && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-3 relative inline-block"
          >
            <video
              src={videoPreview}
              controls
              className="max-h-32 rounded-lg border border-gray-200"
            />
            <button
              onClick={handleRemoveImage}
              className="absolute -top-2 -right-2 w-6 h-6 bg-red-500 text-white rounded-full flex items-center justify-center hover:bg-red-600 transition-colors"
              title="Remove video"
            >
              ×
            </button>
          </motion.div>
        )}

        <div className="flex items-end space-x-2">
          {/* Hidden file input for gallery */}
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*,video/*"
            onChange={handleImageSelect}
            className="hidden"
          />

          <div className="flex-1">
            <textarea
              ref={textareaRef}
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask about lesson planning, student assessment, classroom management..."
              className="w-full px-3 py-2 border border-gray-200 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              rows="2"
              disabled={isTyping || isRecording}
            />
          </div>

          {/* Plus button with attachment menu */}
          <div className="relative">
            <button
              onClick={handlePlusButtonClick}
              disabled={isTyping || isRecording}
              className={cn(
                "p-2 rounded-lg transition-colors",
                isTyping || isRecording
                  ? "bg-gray-200 text-gray-400 cursor-not-allowed"
                  : "bg-purple-500 text-white hover:bg-purple-600"
              )}
              title="Add attachment"
            >
              {showAttachmentMenu ? <X className="w-5 h-5" /> : <Plus className="w-5 h-5" />}
            </button>

            {/* Attachment menu */}
            {showAttachmentMenu && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 10 }}
                className="absolute bottom-full mb-2 right-0 bg-white border border-gray-200 rounded-lg shadow-lg overflow-hidden"
              >
                <button
                  onClick={handleCameraClick}
                  className="flex items-center space-x-3 w-full px-4 py-3 hover:bg-gray-50 transition-colors"
                >
                  <Camera className="w-5 h-5 text-purple-500" />
                  <span className="text-sm text-gray-700 whitespace-nowrap">Take Photo</span>
                </button>
                <div className="border-t border-gray-100" />
                <button
                  onClick={handlePhotoVideoClick}
                  className="flex items-center space-x-3 w-full px-4 py-3 hover:bg-gray-50 transition-colors"
                >
                  <Image className="w-5 h-5 text-purple-500" />
                  <span className="text-sm text-gray-700 whitespace-nowrap">Photo/Video</span>
                </button>
              </motion.div>
            )}
          </div>

          {/* Microphone button */}
          <button
            onClick={handleVoiceToggle}
            disabled={isTyping}
            className={cn(
              "p-2 rounded-lg transition-all duration-200",
              isRecording
                ? "bg-red-500 text-white hover:bg-red-600 animate-pulse"
                : "bg-purple-500 text-white hover:bg-purple-600",
              isTyping && "opacity-50 cursor-not-allowed"
            )}
            title={isRecording ? "Stop recording" : "Start voice recording"}
          >
            {isRecording ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
          </button>

          {/* Send button */}
          <button
            onClick={handleSendMessage}
            disabled={(!inputValue.trim() && !selectedImage && !selectedVideo) || isTyping || isRecording}
            className={cn(
              "p-2 rounded-lg transition-colors",
              (inputValue.trim() || selectedImage || selectedVideo) && !isTyping && !isRecording
                ? "bg-purple-500 text-white hover:bg-purple-600"
                : "bg-gray-200 text-gray-400 cursor-not-allowed"
            )}
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Camera Modal */}
      <CameraModal
        isOpen={showCameraModal}
        onClose={() => setShowCameraModal(false)}
        onCapture={handleCameraCapture}
      />
    </div>
  )
}

export default Chatbot2