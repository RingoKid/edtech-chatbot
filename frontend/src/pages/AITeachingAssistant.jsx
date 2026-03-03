import React from 'react'
import { motion } from 'framer-motion'
import { Rocket, Brain, BookOpen, Target } from 'lucide-react'
import Chatbot2 from '../components/Chatbot2'

const tips = [
  { icon: Brain, text: 'Start with your grade level and topic' },
  { icon: BookOpen, text: 'Include the skill focus for targeted lessons' },
  { icon: Target, text: 'Review and refine the generated lesson' },
]

const AITeachingAssistant = () => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-primary-50/30 pt-20">
      {/* Slim branding bar */}
      <div className="bg-gradient-to-r from-primary-600 to-secondary-600 text-white">
        <div className="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-white/20 flex items-center justify-center">
              <Rocket className="w-4 h-4" />
            </div>
            <div>
              <h1 className="font-bold text-sm">L4C LaunchPad</h1>
              <p className="text-xs text-white/70">Build structured composing lessons</p>
            </div>
          </div>
          <div className="hidden md:flex items-center gap-6">
            {tips.map((tip, i) => (
              <div key={i} className="flex items-center gap-1.5 text-xs text-white/70">
                <tip.icon className="w-3.5 h-3.5" />
                <span>{tip.text}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Chat area */}
      <div className="max-w-5xl mx-auto px-4 py-6 h-[calc(100vh-130px)]">
        <motion.div
          className="bg-white rounded-2xl shadow-lg border border-gray-200/50 overflow-hidden h-full"
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <Chatbot2 />
        </motion.div>
      </div>
    </div>
  )
}

export default AITeachingAssistant
