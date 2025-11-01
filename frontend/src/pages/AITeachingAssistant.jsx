import React, { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import Chatbot from '../components/Chatbot'
import Chatbot2 from '../components/Chatbot2'

const AITeachingAssistant = () => {
  const [activeTab, setActiveTab] = useState('chatbot1')

  useEffect(() => {
    // Scroll to top when component mounts
    window.scrollTo(0, 0)
  }, [])

  return (
    <div className="min-h-screen bg-gray-50 pt-24 pb-8 px-4">
      <div className="max-w-4xl mx-auto h-full flex flex-col">
        {/* Header */}
        <motion.div
          className="text-center mb-6 flex-shrink-0"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
        >
          <h1 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-2">
            Compose Early
          </h1>
          <p className="text-lg text-gray-600">
            AI Teaching Assistant
          </p>
        </motion.div>

        {/* Tab Slider */}
        <motion.div
          className="mb-4 flex-shrink-0"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.2 }}
        >
          <div className="bg-white rounded-lg p-1 shadow-md inline-flex w-full sm:w-auto mx-auto">
            <button
              onClick={() => setActiveTab('chatbot1')}
              className={`flex-1 sm:flex-none px-6 py-2 rounded-md transition-all duration-200 font-medium ${
                activeTab === 'chatbot1'
                  ? 'bg-gradient-to-r from-primary-500 to-secondary-500 text-white shadow-md'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              Assistant 1
            </button>
            <button
              onClick={() => setActiveTab('chatbot2')}
              className={`flex-1 sm:flex-none px-6 py-2 rounded-md transition-all duration-200 font-medium ${
                activeTab === 'chatbot2'
                  ? 'bg-gradient-to-r from-purple-500 to-pink-500 text-white shadow-md'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              Assistant 2
            </button>
          </div>
        </motion.div>

        {/* Chatbot Container */}
        <motion.div
          className="bg-white rounded-2xl shadow-lg overflow-hidden h-[calc(100vh-300px)]"
          initial={{  opacity: 0, scale: 0.98 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.8, delay: 0.3 }}
        >
          {activeTab === 'chatbot1' ? <Chatbot /> : <Chatbot2 />}
        </motion.div>
      </div>
    </div>
  )
}

export default AITeachingAssistant