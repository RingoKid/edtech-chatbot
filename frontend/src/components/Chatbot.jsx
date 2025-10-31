import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Send, Bot, User, Loader, RotateCcw, ChevronDown } from 'lucide-react'
import { cn } from '../utils/cn'
import { chat, createChatWsClient } from '../api'
import { useApiCallProtection } from '../hooks/useApiProtection'

const Chatbot = ({ onNewMessage, hideHeader = false }) => {
  const [messages, setMessages] = useState([
    {
      id: 1,
      type: 'bot',
      content: "Hello! I'm your AI Teaching Assistant. I'm here to help with early childhood education questions, lesson planning, and classroom strategies. How can I assist you today?",
      timestamp: new Date()
    }
  ])
  const [inputValue, setInputValue] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const [wsConnected, setWsConnected] = useState(false)
  const [threadId, setThreadId] = useState(() => {
    try { return localStorage.getItem('chat_thread_id') || null } catch (e) { return null }
  })
  
  // Protect API calls from rapid repeated execution
  const protectedChatSend = useApiCallProtection(chat.send, 1000)
  const [isUserScrolling, setIsUserScrolling] = useState(false)
  const messagesEndRef = useRef(null)
  const messagesContainerRef = useRef(null)
  const wsRef = useRef(null)
  const placeholderIdRef = useRef(null)
  const chunkTimeoutRef = useRef(null)

  // Check if user is at the bottom of the chat
  const isAtBottom = () => {
    if (!messagesContainerRef.current) return true
    const { scrollTop, scrollHeight, clientHeight } = messagesContainerRef.current
    return scrollTop + clientHeight >= scrollHeight - 10 // 10px threshold
  }

  // Auto-scroll to latest message only if user is at bottom
  const scrollToBottom = () => {
    const el = messagesContainerRef.current
    if (!el) return
    // Only auto-scroll if user is not actively scrolling and chat is at (or near) bottom
    if (!isUserScrolling && isAtBottom()) {
      // Only scroll the chat container if it can scroll; avoid scrolling the whole page
      if (el.scrollHeight > el.clientHeight) {
        el.scrollTo({ top: el.scrollHeight, behavior: 'smooth' })
      }
      setIsUserScrolling(false)
    }
  }

  // Force scroll to bottom (used by the scroll-to-bottom button)
  const forceScrollToBottom = () => {
    const el = messagesContainerRef.current
    if (!el) return
    if (el.scrollHeight > el.clientHeight) {
      el.scrollTo({ top: el.scrollHeight, behavior: 'smooth' })
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

  // Wheel handler: allow page to scroll when chat is at top/bottom; otherwise keep wheel for chat
  const handleWheel = (e) => {
    const el = messagesContainerRef.current
    if (!el) return
    const { scrollTop, scrollHeight, clientHeight } = el
    const delta = e.deltaY

    const atTop = scrollTop <= 0
    const atBottom = scrollTop + clientHeight >= scrollHeight - 1

    // If user scrolls up but chat already at top -> allow page to scroll (do nothing)
    // If user scrolls down but chat already at bottom -> allow page to scroll
    // Otherwise stop propagation so the chat scrolls instead of the page
    if ((delta < 0 && !atTop) || (delta > 0 && !atBottom)) {
      e.stopPropagation()
    }
    // else: let the event bubble so the outer page can scroll
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages, isTyping])

  // Setup WebSocket on mount
  useEffect(() => {
    let unsub = null
    const client = createChatWsClient()
    wsRef.current = client
    // store the unsubscribe function so we can remove listener on cleanup
    unsub = client.subscribe((evt) => {
      if (evt.type === 'open') setWsConnected(true)
      if (evt.type === 'close') {
        setWsConnected(false)
        // Streaming finished (connection closed) -> stop typing indicator
        setIsTyping(false)
        placeholderIdRef.current = null
      }
      if (evt.type === 'error') {
        setWsConnected(false)
        setIsTyping(false)
      }
      if (evt.type === 'message') {
        const data = evt.data || {}
        // If server signals done, clear typing indicator and placeholder
        if (data.done) {
          setIsTyping(false)
          placeholderIdRef.current = null
          return
        }
        // Backend token stream may use `reply` (accumulated chunk) or `response`.
        const chunk = data.reply ?? data.response ?? data.message ?? data.content ?? null
        if (chunk) {
          // If we have a placeholder message id, append to that message; otherwise create a new bot message
          if (placeholderIdRef.current) {
            const pid = placeholderIdRef.current
            setMessages(prev => prev.map(m => m.id === pid ? { ...m, content: (m.content || '') + chunk } : m))
          } else {
            const botMessage = {
              id: Date.now() + Math.floor(Math.random() * 1000),
              type: 'bot',
              content: chunk,
              timestamp: new Date()
            }
            setMessages(prev => [...prev, botMessage])
          }
        }
        if (data.thread_id) {
          setThreadId(data.thread_id)
          try { localStorage.setItem('chat_thread_id', data.thread_id) } catch (e) {}
        }
      }
          // reset idle timeout: if no more chunks arrive within 800ms, consider stream finished
          if (chunkTimeoutRef.current) clearTimeout(chunkTimeoutRef.current)
          chunkTimeoutRef.current = setTimeout(() => {
            setIsTyping(false)
            placeholderIdRef.current = null
            chunkTimeoutRef.current = null
          }, 800)
    })
    client.connect().catch(err => console.warn('WS connect failed', err))

    return () => {
      try { client.close() } catch (e) {}
      if (typeof unsub === 'function') unsub()
    }
  }, [])

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
    if (!inputValue.trim() || isTyping) return // Prevent sending while already processing

    const currentInput = inputValue.trim()
    const newUserMessage = {
      id: Date.now(),
      type: 'user',
      content: currentInput,
      timestamp: new Date()
    }

    setMessages(prev => [...prev, newUserMessage])
    setInputValue('')

    // Notify parent component of new message
    if (onNewMessage) {
      onNewMessage()
    }

    // Use WebSocket if connected; otherwise fallback to HTTP POST or local generator
    const client = wsRef.current
    console.log('WebSocket client status:', { client: !!client, connected: client?.isConnected?.() })
    
    if (client && client.isConnected && client.isConnected()) {
      try {
        // Create a single placeholder bot message that will be appended to as tokens arrive
        const placeholderId = Date.now() + Math.floor(Math.random() * 1000)
        const placeholder = { id: placeholderId, type: 'bot', content: '', timestamp: new Date() }
        placeholderIdRef.current = placeholderId
        setMessages(prev => [...prev, placeholder])
        setIsTyping(true)

        const payload = { message: currentInput }
        if (threadId) payload.thread_id = threadId
        console.log('Sending WebSocket message:', payload)
        client.send(payload)
        // Server will stream back tokens and we'll append them to the placeholder
      } catch (err) {
        console.warn('WS send failed, falling back to HTTP', err)
        placeholderIdRef.current = null
        setIsTyping(true)
        try {
          console.log('Attempting HTTP fallback with protectedChatSend')
          const res = await protectedChatSend(currentInput, threadId)
          console.log('HTTP response:', res)
          if (res) { // Only process if API call wasn't blocked
            const botResponse = {
              id: Date.now() + 1,
              type: 'bot',
              content: res?.reply ?? generateResponse(currentInput),
              timestamp: new Date()
            }
            setMessages(prev => [...prev, botResponse])
          } else {
            console.warn('API call was blocked by protection, using fallback')
            const response = generateResponse(currentInput)
            const botResponse = { id: Date.now() + 1, type: 'bot', content: response, timestamp: new Date() }
            setMessages(prev => [...prev, botResponse])
          }
        } catch (err2) {
          console.error('HTTP fallback failed:', err2)
          const response = generateResponse(currentInput)
          const botResponse = { id: Date.now() + 1, type: 'bot', content: response, timestamp: new Date() }
          setMessages(prev => [...prev, botResponse])
        } finally {
          setIsTyping(false)
        }
      }
    } else {
      // No WS connection — fallback to HTTP
      console.log('No WebSocket connection, using HTTP fallback')
      setIsTyping(true)
      try {
        console.log('Attempting HTTP call with protectedChatSend')
        const res = await protectedChatSend(currentInput, threadId)
        console.log('HTTP response:', res)
        if (res) { // Only process if API call wasn't blocked
          const botResponse = {
            id: Date.now() + 1,
            type: 'bot',
            content: res?.reply ?? generateResponse(currentInput),
            timestamp: new Date()
          }
          setMessages(prev => [...prev, botResponse])
        } else {
          console.warn('API call was blocked by protection, using fallback response')
          const response = generateResponse(currentInput)
          const botResponse = { id: Date.now() + 1, type: 'bot', content: response, timestamp: new Date() }
          setMessages(prev => [...prev, botResponse])
        }
      } catch (err) {
        console.error('HTTP call failed:', err)
        const response = generateResponse(currentInput)
        const botResponse = { id: Date.now() + 1, type: 'bot', content: response, timestamp: new Date() }
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

  const clearChat = () => {
    setMessages([{
      id: 1,
      type: 'bot',
      content: "Hello! I'm your AI Teaching Assistant. I'm here to help with early childhood education questions, lesson planning, and classroom strategies. How can I assist you today?",
      timestamp: new Date()
    }])
  }


  return (
    <div className={cn(
      "flex flex-col h-full bg-white",
      hideHeader ? "border-0 shadow-none rounded-none" : "border border-gray-200 rounded-xl shadow-lg overflow-hidden"
    )}>
      {/* Header */}
      {!hideHeader && (
        <div className="flex items-center justify-between p-4 bg-gradient-to-r from-primary-500 to-secondary-500 text-white">
          <div className="flex items-center">
            <div className="w-8 h-8 bg-white/20 rounded-full flex items-center justify-center mr-3">
              <Bot className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-semibold">AI Teaching Assistant</h3>
              <div className="text-xs text-white/80 flex items-center">
                <div className="w-2 h-2 bg-green-400 rounded-full mr-2"></div>
                Online
              </div>
            </div>
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
        onWheel={handleWheel}
        className="flex-1 overflow-y-auto p-4 space-y-4 relative min-h-0 overscroll-auto"
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
                    ? 'bg-primary-500 ml-2' 
                    : 'bg-gradient-to-br from-secondary-500 to-accent-500 mr-2'
                )}>
                  {message.type === 'user' ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
                </div>
                
                <div className={cn(
                  "rounded-lg px-4 py-2 shadow-sm",
                  message.type === 'user'
                    ? 'bg-primary-500 text-white'
                    : 'bg-gray-100 text-gray-900'
                )}>
                  <p className="text-sm leading-relaxed">{message.content}</p>
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
            data-testid="typing-indicator"
          >
            <div className="flex items-center">
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-secondary-500 to-accent-500 flex items-center justify-center text-white mr-2">
                <Bot className="w-4 h-4" />
              </div>
              <div className="bg-gray-100 rounded-lg px-4 py-2 flex items-center space-x-1">
                <Loader className="w-4 h-4 animate-spin text-gray-500" />
                {/* No text label - visual loader is sufficient */}
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
            className="absolute bottom-4 right-4 w-10 h-10 bg-primary-500 text-white rounded-full shadow-lg hover:bg-primary-600 transition-colors flex items-center justify-center z-10"
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
              className="w-full px-3 py-2 border border-gray-200 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              rows="2"
              disabled={isTyping}
            />
          </div>
          <button
            onClick={handleSendMessage}
            disabled={!inputValue.trim() || isTyping}
            aria-label="Send message"
            title="Send message"
            className={cn(
              "p-2 rounded-lg transition-colors",
              inputValue.trim() && !isTyping
                ? "bg-primary-500 text-white hover:bg-primary-600"
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

export default Chatbot