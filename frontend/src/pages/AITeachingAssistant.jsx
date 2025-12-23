import React from 'react'
import { motion } from 'framer-motion'
import Chatbot2 from '../components/Chatbot2'

const AITeachingAssistant = () => {
  return (
    <div className="min-h-screen bg-gray-50 pt-24 pb-8 px-4">
      <div className="max-w-4xl mx-auto h-full flex flex-col">
        {/* Chatbot Container */}
        <motion.div
          className="bg-white rounded-2xl shadow-lg overflow-hidden h-[calc(100vh-150px)]"
          initial={{ opacity: 0, scale: 0.98 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.8 }}
        >
          <Chatbot2 />
        </motion.div>
      </div>
    </div>
  )
}

export default AITeachingAssistant