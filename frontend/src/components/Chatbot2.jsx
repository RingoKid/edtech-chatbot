import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Send, Bot, User, Loader, RotateCcw, ChevronDown, Download } from 'lucide-react'
import { cn } from '../utils/cn'
import { chat2 } from '../api'
import MarkdownRenderer from './MarkdownRenderer'
import jsPDF from 'jspdf'

const Chatbot2 = ({ onNewMessage, hideHeader = false }) => {
  const [messages, setMessages] = useState([
    {
      id: 1,
      type: 'bot',
      content: "Hello there! How can I assist you with your literacy questions today? I can help with handwriting, vocabulary, creative writing, and literacy strategies. Looking forward to supporting you!",
      timestamp: new Date()
    }
  ])
  const [inputValue, setInputValue] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const [isUserScrolling, setIsUserScrolling] = useState(false)
  const [isInitialMount, setIsInitialMount] = useState(true)
  const [threadId, setThreadId] = useState(null) // Store thread_id for conversation persistence
  const messagesEndRef = useRef(null)
  const messagesContainerRef = useRef(null)

  // Check if user is at the bottom of the chat
  const isAtBottom = () => {
    if (!messagesContainerRef.current) return true
    const { scrollTop, scrollHeight, clientHeight } = messagesContainerRef.current
    return scrollTop + clientHeight >= scrollHeight - 10 // 10px threshold
  }

  // Auto-scroll to latest message only if user is at bottom
  const scrollToBottom = () => {
    if (!isUserScrolling || isAtBottom()) {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
      setIsUserScrolling(false)
    }
  }

  // Force scroll to bottom (used by the scroll-to-bottom button)
  const forceScrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
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

  const handleSendMessage = async () => {
    if (!inputValue.trim()) return

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

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  const clearChat = () => {
    setMessages([{
      id: 1,
      type: 'bot',
      content: "Hello! I'm your second AI Teaching Assistant. I'm here to provide additional support and perspectives. How can I help you today?",
      timestamp: new Date()
    }])
    // Reset thread_id to start a new conversation
    setThreadId(null)
  }

  const handleDownloadPDF = async () => {
    if (!threadId) return

    try {
      // Fetch chat history from API
      const history = await chat2.getHistory(threadId)

      // Create new PDF document
      const doc = new jsPDF()
      const pageWidth = doc.internal.pageSize.getWidth()
      const pageHeight = doc.internal.pageSize.getHeight()
      const margin = 20
      const maxWidth = pageWidth - 2 * margin
      let yPosition = margin

      // Helper function to add new page if needed
      const checkAndAddPage = (requiredSpace) => {
        if (yPosition + requiredSpace > pageHeight - margin) {
          doc.addPage()
          yPosition = margin
          return true
        }
        return false
      }

      // Helper function to wrap text
      const wrapText = (text, maxWidth) => {
        return doc.splitTextToSize(text, maxWidth)
      }

      // Add title
      doc.setFontSize(18)
      doc.setFont(undefined, 'bold')
      doc.text('Chat History', margin, yPosition)
      yPosition += 10

      // Add metadata
      doc.setFontSize(10)
      doc.setFont(undefined, 'normal')
      doc.setTextColor(100, 100, 100)
      doc.text(`Thread ID: ${history.thread_id}`, margin, yPosition)
      yPosition += 6

      const date = new Date(history.created_at)
      doc.text(`Date: ${date.toLocaleDateString()} ${date.toLocaleTimeString()}`, margin, yPosition)
      yPosition += 10

      // Add separator line
      doc.setDrawColor(200, 200, 200)
      doc.line(margin, yPosition, pageWidth - margin, yPosition)
      yPosition += 10

      // Add messages
      doc.setTextColor(0, 0, 0)

      if (history.messages && history.messages.length > 0) {
        history.messages.forEach((message, index) => {
          // Determine role label
          const roleLabel = message.role === 'user' ? 'User' : 'Assistant'
          const timestamp = new Date(message.timestamp)
          const timeString = timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })

          // Check if we need a new page for the message header
          checkAndAddPage(20)

          // Add role and timestamp
          doc.setFontSize(11)
          doc.setFont(undefined, 'bold')
          doc.text(`${roleLabel} (${timeString}):`, margin, yPosition)
          yPosition += 7

          // Add message content
          doc.setFontSize(10)
          doc.setFont(undefined, 'normal')
          const wrappedContent = wrapText(message.content, maxWidth)

          wrappedContent.forEach((line) => {
            checkAndAddPage(7)
            doc.text(line, margin, yPosition)
            yPosition += 5
          })

          // Add spacing between messages
          yPosition += 8

          // Add separator line between messages (except for last message)
          if (index < history.messages.length - 1) {
            checkAndAddPage(5)
            doc.setDrawColor(230, 230, 230)
            doc.line(margin, yPosition, pageWidth - margin, yPosition)
            yPosition += 8
          }
        })
      }

      // Generate filename with thread_id
      const filename = `chat-${threadId}.pdf`

      // Save the PDF
      doc.save(filename)
    } catch (error) {
      console.error('Error downloading PDF:', error)
      alert('Failed to download chat history. Please try again.')
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
            <div>
              <h3 className="font-semibold">AI Teaching Assistant 2</h3>
              <div className="text-xs text-white/80 flex items-center">
                <div className="w-2 h-2 bg-green-400 rounded-full mr-2"></div>
                Online
              </div>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={handleDownloadPDF}
              disabled={!threadId}
              className="p-2 hover:bg-white/20 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              title={threadId ? "Download chat as PDF" : "Start a conversation to download"}
            >
              <Download className="w-4 h-4" />
            </button>
            <button
              onClick={clearChat}
              className="p-2 hover:bg-white/20 rounded-lg transition-colors"
              title="Clear conversation"
            >
              <RotateCcw className="w-4 h-4" />
            </button>
          </div>
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
        <div className="flex items-end space-x-2">
          <div className="flex-1">
            <textarea
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask about lesson planning, student assessment, classroom management..."
              className="w-full px-3 py-2 border border-gray-200 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              rows="2"
              disabled={isTyping}
            />
          </div>
          <button
            onClick={handleSendMessage}
            disabled={!inputValue.trim() || isTyping}
            className={cn(
              "p-2 rounded-lg transition-colors",
              inputValue.trim() && !isTyping
                ? "bg-purple-500 text-white hover:bg-purple-600"
                : "bg-gray-200 text-gray-400 cursor-not-allowed"
            )}
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>
  )
}

export default Chatbot2