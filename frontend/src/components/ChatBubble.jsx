import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { MessageCircle, Bot, Minimize2, RotateCcw, X } from 'lucide-react'
import Chatbot from './Chatbot'
import { cn } from '../utils/cn'

const ChatBubble = () => {
  const [isOpen, setIsOpen] = useState(false)
  const [isMinimized, setIsMinimized] = useState(false)
  const [hasNewMessage, setHasNewMessage] = useState(false)
  const [isFirstLoad, setIsFirstLoad] = useState(true)

  const toggleChat = () => {
    if (isOpen) {
      setIsMinimized(!isMinimized)
    } else {
      setIsOpen(true)
      setIsMinimized(false)
      setHasNewMessage(false)
    }
  }

  const closeChat = () => {
    setIsOpen(false)
    setIsMinimized(false)
    setIsFirstLoad(false)
  }

  const handleNewMessage = () => {
    if (!isOpen) {
      setHasNewMessage(true)
    }
  }

  const clearChat = () => {
    setIsOpen(false)
    setTimeout(() => setIsOpen(true), 100)
  }

  return (
    <>
      {/* Floating Chat Bubble (hidden when open) */}
      {!isOpen && (
        <motion.div
          className="fixed bottom-6 right-6 z-50"
          initial={{ scale: 0, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ 
            type: "spring", 
            stiffness: 260, 
            damping: 20,
            delay: isFirstLoad ? 2 : 0 
          }}
        >
          <motion.button
            onClick={toggleChat}
            className={cn(
              "relative w-14 h-14 rounded-full shadow-lg transition-all duration-300 flex items-center justify-center",
              "bg-gradient-to-r from-primary-500 to-secondary-500 hover:from-primary-600 hover:to-secondary-600",
              "hover:scale-110 active:scale-95"
            )}
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.95 }}
          >
            <MessageCircle className="w-6 h-6 text-white" />

            {/* Notification Badge */}
            {hasNewMessage && (
              <motion.div
                className="absolute -top-1 -right-1 w-4 h-4 bg-red-500 rounded-full flex items-center justify-center"
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ type: "spring", stiffness: 500, damping: 15 }}
              >
                <span className="text-xs text-white font-bold">!</span>
              </motion.div>
            )}

            {/* Pulse Animation */}
            <motion.div
              className="absolute inset-0 rounded-full bg-gradient-to-r from-primary-500 to-secondary-500"
              animate={{ scale: [1, 1.2, 1] }}
              transition={{ duration: 2, repeat: Infinity }}
              style={{ zIndex: -1 }}
            />
          </motion.button>
        </motion.div>
      )}

      {/* Chat Window */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            className={cn(
              "fixed bottom-6 right-6 z-40",
              isMinimized ? "h-16" : "h-[600px] w-80 sm:w-96"
            )}
            initial={{ opacity: 0, scale: 0.8, y: 20, height: 0 }}
            animate={{ opacity: 1, scale: 1, y: 0, height: isMinimized ? 64 : 600 }}
            exit={{ opacity: 0, scale: 0.8, y: 20, height: 0 }}
            transition={{ type: "spring", stiffness: 300, damping: 30 }}
          >
            <div className="bg-white rounded-2xl shadow-2xl border border-gray-200 overflow-hidden h-full flex flex-col">
              {/* Chat Header */}
              <div className="flex items-center justify-between p-4 bg-gradient-to-r from-primary-500 to-secondary-500 text-white flex-shrink-0">
                <div className="flex items-center">
                  <div className="w-8 h-8 bg-white/20 rounded-full flex items-center justify-center mr-3">
                    <Bot className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-sm">L4C LaunchPad</h3>
                    <div className="text-xs text-white/80 flex items-center">
                      <div className="w-2 h-2 bg-green-400 rounded-full mr-2"></div>
                      Online
                    </div>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <button
                    onClick={clearChat}
                    className="p-1.5 hover:bg-white/20 rounded-lg transition-colors"
                    title="Clear conversation"
                  >
                    <RotateCcw className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => setIsMinimized(!isMinimized)}
                    className="p-1.5 hover:bg-white/20 rounded-lg transition-colors"
                    title={isMinimized ? "Expand" : "Minimize"}
                  >
                    <Minimize2 className="w-4 h-4" />
                  </button>
                  <button
                    onClick={closeChat}
                    className="p-1.5 hover:bg-white/20 rounded-lg transition-colors"
                    title="Close"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              </div>

              {/* Chat Content */}
              {!isMinimized && (
                <motion.div
                  className="flex-1 flex flex-col min-h-0"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: 0.2 }}
                >
                  <Chatbot onNewMessage={handleNewMessage} hideHeader={true} />
                </motion.div>
              )}

              {/* Minimized State */}
              {isMinimized && (
                <motion.div
                  className="flex-1 flex items-center justify-center p-4"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: 0.1 }}
                >
                  <Bot className="w-8 h-8 text-primary-500 mx-auto" />
                </motion.div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  )
}

export default ChatBubble
