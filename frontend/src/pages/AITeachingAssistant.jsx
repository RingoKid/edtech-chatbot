import React from 'react'
import { motion } from 'framer-motion'
import Chatbot from '../components/Chatbot'

const AITeachingAssistant = () => {
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

        {/* Chatbot Container */}
        <motion.div
          className="bg-white rounded-2xl shadow-lg overflow-hidden h-[calc(100vh-250px)]"
          initial={{ opacity: 0, scale: 0.98 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.8, delay: 0.3 }}
        >
          <Chatbot />
        </motion.div>
      </div>
    </div>
  )
}

export default AITeachingAssistant