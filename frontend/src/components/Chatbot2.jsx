import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Send, User, Loader, RotateCcw, ChevronDown, Mic, MicOff, Image, Camera, Plus, X, Menu, MessageSquare, Download } from 'lucide-react'
import { cn } from '../utils/cn'
import { chat2, handwriting } from '../api'
import MarkdownRenderer from './MarkdownRenderer'
import useAudioRecorder from '../hooks/useAudioRecorder'
import TranscriptionWebSocket from '../api/transcriptionWebSocket'
import CameraModal from './CameraModal'


const BG_LETTERS = 'abcdefghjkmnpqrstuvwxyz'
const BG_ROTATIONS = Array.from({ length: 600 }, (_, i) => ((i * 17 + 5) % 30) - 15)

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
  const [sidebarOpen, setSidebarOpen] = useState(false) // Sidebar visibility
  const [conversations, setConversations] = useState([]) // List of past conversations
  const [loadingHistory, setLoadingHistory] = useState(false) // Loading state for history
  const [hasLessonImages, setHasLessonImages] = useState(false) // Track if current thread has generated images
  const [exportingPdf, setExportingPdf] = useState(false) // PDF export loading state
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

        // Check if lesson images are embedded in the reply (S3 URLs in markdown)
        if (res?.reply?.includes('l4c-videos.s3.amazonaws.com')) {
          setHasLessonImages(true)
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

  const handleExportPdf = async () => {
    if (!threadId || exportingPdf) return
    setExportingPdf(true)
    try {
      await chat2.exportPdf(threadId)
    } catch (err) {
      console.error('Failed to export PDF:', err)
    } finally {
      setExportingPdf(false)
    }
  }

  const clearChat = async () => {
    // Reset messages and start a new chat session
    setMessages([])
    setThreadId(null)
    setHasLessonImages(false)
    setIsTyping(true)
    setSidebarOpen(false)

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
      // Refresh conversation list
      fetchConversations()
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

  // Fetch list of past conversations
  const fetchConversations = async () => {
    setLoadingHistory(true)
    try {
      const res = await chat2.getHistory()
      setConversations(res?.conversations || [])
    } catch (err) {
      console.error('Failed to fetch conversations:', err)
    } finally {
      setLoadingHistory(false)
    }
  }

  // Load a specific conversation
  const loadConversation = async (selectedThreadId) => {
    if (selectedThreadId === threadId) {
      setSidebarOpen(false)
      return
    }

    setIsTyping(true)
    setSidebarOpen(false)

    try {
      const res = await chat2.getMessages(selectedThreadId)
      setThreadId(selectedThreadId)

      // Transform messages to UI format
      const loadedMessages = (res?.messages || []).map((msg, index) => ({
        id: Date.now() + index,
        type: msg.role === 'user' ? 'user' : 'bot',
        content: msg.content,
        timestamp: msg.timestamp ? new Date(msg.timestamp) : new Date()
      }))

      setMessages(loadedMessages)
    } catch (err) {
      console.error('Failed to load conversation:', err)
    } finally {
      setIsTyping(false)
    }
  }

  // Toggle sidebar and fetch conversations if opening
  const toggleSidebar = () => {
    if (!sidebarOpen) {
      fetchConversations()
    }
    setSidebarOpen(!sidebarOpen)
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
    <div className="flex flex-col h-full bg-white relative overflow-hidden">
      {/* Background — dense tiling letter pattern with rectangular center cutout */}
      <div
        className="absolute inset-0 pointer-events-none select-none font-handwritten flex flex-wrap content-start overflow-hidden"
        aria-hidden="true"
        style={{
          maskImage: [
            'linear-gradient(to right, black 0%, black 33%, transparent 40%, transparent 60%, black 67%, black 100%)',
            'linear-gradient(to bottom, black 0%, black 3%, transparent 7%, transparent 93%, black 97%, black 100%)',
          ].join(', '),
          WebkitMaskImage: [
            'linear-gradient(to right, black 0%, black 33%, transparent 40%, transparent 60%, black 67%, black 100%)',
            'linear-gradient(to bottom, black 0%, black 3%, transparent 7%, transparent 93%, black 97%, black 100%)',
          ].join(', '),
          maskComposite: 'add',
          WebkitMaskComposite: 'source-over',
        }}
      >
        {Array.from({ length: 600 }).map((_, i) => (
          <span
            key={i}
            className="w-12 h-12 flex items-center justify-center text-lg text-gray-400/[0.18]"
            style={{ transform: `rotate(${BG_ROTATIONS[i]}deg)` }}
          >
            {BG_LETTERS[i % BG_LETTERS.length]}
          </span>
        ))}
      </div>

{/* z-[1] spacer — mask on the letters container handles the fade */}

      {/* Minimal top bar */}
      <div className="flex items-center justify-between px-4 h-12 border-b border-gray-100 bg-white relative z-10">
        <button
          onClick={toggleSidebar}
          className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          title="View conversations"
        >
          <Menu className="w-5 h-5 text-gray-500" />
        </button>
        <span className="text-sm font-medium text-gray-700">L4C LaunchPad</span>
        <button
          onClick={clearChat}
          className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          title="New conversation"
        >
          <RotateCcw className="w-4 h-4 text-gray-500" />
        </button>
      </div>

      {/* Sidebar Overlay */}
      <AnimatePresence>
        {sidebarOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 bg-black/20 z-20"
            onClick={() => setSidebarOpen(false)}
          />
        )}
      </AnimatePresence>

      {/* Sidebar */}
      <AnimatePresence>
        {sidebarOpen && (
          <motion.div
            initial={{ x: '-100%' }}
            animate={{ x: 0 }}
            exit={{ x: '-100%' }}
            transition={{ type: 'spring', damping: 25, stiffness: 300 }}
            className="absolute top-0 left-0 h-full w-72 bg-gray-50 shadow-xl z-30 flex flex-col border-r border-gray-200"
          >
            {/* Sidebar Header */}
            <div className="flex items-center h-12 px-3 border-b border-gray-200 bg-white">
              <button
                onClick={() => setSidebarOpen(false)}
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors mr-2"
                title="Close conversations"
              >
                <Menu className="w-5 h-5 text-gray-500" />
              </button>
              <span className="text-sm font-medium text-gray-700">Conversations</span>
            </div>

            {/* New Chat Button */}
            <button
              onClick={clearChat}
              className="mx-3 mt-3 mb-1 p-2.5 border border-gray-200 text-gray-700 rounded-lg hover:bg-white transition-colors flex items-center gap-2 text-sm"
            >
              <Plus className="w-4 h-4" />
              New conversation
            </button>

            {/* Conversation List */}
            <div className="flex-1 overflow-y-auto px-2 py-2">
              {loadingHistory ? (
                <div className="flex items-center justify-center p-4">
                  <Loader className="w-5 h-5 animate-spin text-gray-400" />
                </div>
              ) : conversations.length === 0 ? (
                <div className="p-4 text-center text-gray-400 text-sm">
                  No conversations yet
                </div>
              ) : (
                <div className="space-y-0.5">
                  {conversations.map((conv) => (
                    <button
                      key={conv.thread_id}
                      onClick={() => loadConversation(conv.thread_id)}
                      className={cn(
                        "w-full px-3 py-2.5 rounded-lg text-left transition-colors text-sm",
                        conv.thread_id === threadId
                          ? "bg-white shadow-sm text-gray-900"
                          : "text-gray-600 hover:bg-white/60"
                      )}
                    >
                      <div className="truncate font-medium">
                        {conv.title || 'New Conversation'}
                      </div>
                      {conv.last_message_preview && (
                        <div className="text-xs text-gray-400 truncate mt-0.5">
                          {conv.last_message_preview}
                        </div>
                      )}
                    </button>
                  ))}
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Messages Area */}
      <div
        ref={messagesContainerRef}
        onScroll={handleScroll}
        className="flex-1 overflow-y-auto relative min-h-0 z-[2]"
      >
        <div className="max-w-3xl mx-auto px-4 sm:px-6 py-6 space-y-6">
          <AnimatePresence>
            {messages.map((message) => (
              <motion.div
                key={message.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
              >
                {message.type === 'bot' ? (
                  /* Bot message — white card with border */
                  <div className="flex gap-3">
                    <div className="flex-shrink-0 w-7 h-7 rounded-full bg-primary-600 flex items-center justify-center mt-0.5">
                      <span className="text-[10px] font-bold text-white leading-none">L4C</span>
                    </div>
                    <div className="min-w-0 flex-1 bg-white border border-gray-200 rounded-2xl px-4 py-3 shadow-sm">
                      {message.image && (
                        <img src={message.image} alt="Uploaded" className="max-w-sm rounded-lg mb-3 max-h-64 object-contain" />
                      )}
                      {message.video && (
                        <video src={message.video} controls className="max-w-sm rounded-lg mb-3 max-h-64" />
                      )}
                      <MarkdownRenderer
                        content={message.content}
                        className="text-[15px] leading-relaxed text-gray-800"
                      />
                    </div>
                  </div>
                ) : (
                  /* User message — subtle bubble, right-aligned */
                  <div className="flex justify-end">
                    <div className="max-w-[80%] bg-gray-100 rounded-2xl px-4 py-3">
                      {message.image && (
                        <img src={message.image} alt="Uploaded" className="max-w-full rounded-lg mb-2 max-h-48 object-contain" />
                      )}
                      {message.video && (
                        <video src={message.video} controls className="max-w-full rounded-lg mb-2 max-h-48" />
                      )}
                      <p className="text-[15px] leading-relaxed text-gray-900">{message.content}</p>
                    </div>
                  </div>
                )}
              </motion.div>
            ))}
          </AnimatePresence>

          {/* Export PDF button — appears when lesson images have been generated */}
          {hasLessonImages && !isTyping && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex justify-center mb-3"
            >
              <button
                onClick={handleExportPdf}
                disabled={exportingPdf}
                className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-primary-700 bg-primary-50 border border-primary-200 rounded-lg hover:bg-primary-100 transition-colors disabled:opacity-50"
              >
                {exportingPdf ? (
                  <Loader className="w-4 h-4 animate-spin" />
                ) : (
                  <Download className="w-4 h-4" />
                )}
                {exportingPdf ? 'Generating PDF...' : 'Export Lesson as PDF'}
              </button>
            </motion.div>
          )}

          {/* Live transcript display */}
          {liveTranscript && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex justify-end"
            >
              <div className="max-w-[80%] bg-primary-50 border border-primary-100 rounded-2xl px-4 py-3">
                <p className="text-sm leading-relaxed text-primary-700 italic">{liveTranscript}</p>
                <div className="flex items-center gap-1.5 mt-1.5">
                  <Mic className="w-3 h-3 text-primary-400 animate-pulse" />
                  <span className="text-xs text-primary-400">Listening...</span>
                </div>
              </div>
            </motion.div>
          )}

          {/* Typing indicator */}
          {isTyping && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex gap-3"
            >
              <div className="flex-shrink-0 w-7 h-7 rounded-full bg-primary-600 flex items-center justify-center">
                <span className="text-[10px] font-bold text-white leading-none">L4C</span>
              </div>
              <div className="flex items-center gap-1 pt-1">
                <span className="w-2 h-2 bg-gray-300 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                <span className="w-2 h-2 bg-gray-300 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                <span className="w-2 h-2 bg-gray-300 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
            </motion.div>
          )}

          {/* Scroll anchor */}
          <div ref={messagesEndRef} />
        </div>

        {/* Scroll to bottom button */}
        {isUserScrolling && (
          <motion.button
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.8 }}
            onClick={forceScrollToBottom}
            className="sticky bottom-4 left-1/2 -translate-x-1/2 w-8 h-8 bg-white border border-gray-200 text-gray-500 rounded-full shadow-md hover:bg-gray-50 transition-colors flex items-center justify-center z-10"
            title="Scroll to bottom"
          >
            <ChevronDown className="w-4 h-4" />
          </motion.button>
        )}
      </div>

      {/* Input Area */}
      <div className="bg-white px-4 pb-4 pt-2 relative z-10">
        <div className="max-w-3xl mx-auto">
          {/* Error messages */}
          {(transcriptionError || recorderError) && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="mb-2 p-2.5 bg-red-50 border border-red-200 rounded-xl text-sm text-red-600"
            >
              {transcriptionError || recorderError}
            </motion.div>
          )}

          {/* Image preview */}
          {imagePreview && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="mb-2 relative inline-block"
            >
              <img src={imagePreview} alt="Selected" className="max-h-24 rounded-lg border border-gray-200" />
              <button
                onClick={handleRemoveImage}
                className="absolute -top-1.5 -right-1.5 w-5 h-5 bg-gray-800 text-white rounded-full flex items-center justify-center hover:bg-gray-900 transition-colors text-xs"
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
              className="mb-2 relative inline-block"
            >
              <video src={videoPreview} controls className="max-h-24 rounded-lg border border-gray-200" />
              <button
                onClick={handleRemoveImage}
                className="absolute -top-1.5 -right-1.5 w-5 h-5 bg-gray-800 text-white rounded-full flex items-center justify-center hover:bg-gray-900 transition-colors text-xs"
                title="Remove video"
              >
                ×
              </button>
            </motion.div>
          )}

          {/* Input container — pill shape with tools inside */}
          <div className="relative flex items-end border border-gray-200 rounded-2xl bg-gray-50 focus-within:border-gray-300 focus-within:bg-white focus-within:shadow-sm transition-all">
            {/* Hidden file input */}
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*,video/*"
              onChange={handleImageSelect}
              className="hidden"
            />

            {/* Attachment button */}
            <div className="relative flex-shrink-0 self-end p-2">
              <button
                onClick={handlePlusButtonClick}
                disabled={isTyping || isRecording}
                className={cn(
                  "p-1.5 rounded-lg transition-colors",
                  isTyping || isRecording
                    ? "text-gray-300 cursor-not-allowed"
                    : "text-gray-400 hover:text-gray-600 hover:bg-gray-200/50"
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
                  className="absolute bottom-full mb-2 left-0 bg-white border border-gray-200 rounded-xl shadow-lg overflow-hidden"
                >
                  <button
                    onClick={handleCameraClick}
                    className="flex items-center gap-3 w-full px-4 py-2.5 hover:bg-gray-50 transition-colors"
                  >
                    <Camera className="w-4 h-4 text-gray-500" />
                    <span className="text-sm text-gray-700 whitespace-nowrap">Take Photo</span>
                  </button>
                  <div className="border-t border-gray-100" />
                  <button
                    onClick={handlePhotoVideoClick}
                    className="flex items-center gap-3 w-full px-4 py-2.5 hover:bg-gray-50 transition-colors"
                  >
                    <Image className="w-4 h-4 text-gray-500" />
                    <span className="text-sm text-gray-700 whitespace-nowrap">Photo / Video</span>
                  </button>
                </motion.div>
              )}
            </div>

            {/* Textarea */}
            <textarea
              ref={textareaRef}
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Message L4C LaunchPad..."
              className="flex-1 bg-transparent resize-none focus:outline-none text-[15px] py-3 max-h-36 leading-relaxed"
              rows="1"
              disabled={isTyping || isRecording}
            />

            {/* Right-side buttons */}
            <div className="flex items-center gap-0.5 flex-shrink-0 self-end p-2">
              {/* Mic button */}
              <button
                onClick={handleVoiceToggle}
                disabled={isTyping}
                className={cn(
                  "p-1.5 rounded-lg transition-all duration-200",
                  isRecording
                    ? "text-red-500 bg-red-50 animate-pulse"
                    : "text-gray-400 hover:text-gray-600 hover:bg-gray-200/50",
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
                  "p-1.5 rounded-lg transition-colors",
                  (inputValue.trim() || selectedImage || selectedVideo) && !isTyping && !isRecording
                    ? "text-white bg-primary-600 hover:bg-primary-700"
                    : "text-gray-300 cursor-not-allowed"
                )}
              >
                <Send className="w-5 h-5" />
              </button>
            </div>
          </div>

          <p className="text-xs text-gray-400 text-center mt-2">
            L4C LaunchPad helps you build structured composing lessons
          </p>
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