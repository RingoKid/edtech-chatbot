import { motion } from 'framer-motion'
import { BookOpen, Mail, Heart } from 'lucide-react'

const Footer = () => {
  return (
    <footer className="bg-gradient-to-b from-gray-800 to-gray-900 text-white relative overflow-hidden">
      {/* Background Pattern */}
      <div className="absolute inset-0 opacity-5">
        <div className="absolute inset-0" style={{
          backgroundImage: 'radial-gradient(circle at 2px 2px, rgba(255, 255, 255, 0.3) 1px, transparent 0)',
          backgroundSize: '40px 40px'
        }} />
      </div>

      <div className="container relative z-10">
        {/* Main Footer Content */}
        <div className="py-16">
          {/* Brand Section */}
          <motion.div
            className="text-center space-y-6"
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
          >
            <div className="flex items-center justify-center space-x-3">
              <div className="w-12 h-12 bg-gradient-to-br from-primary-500 to-secondary-500 rounded-xl flex items-center justify-center shadow-lg">
                <BookOpen className="w-7 h-7 text-white" />
              </div>
              <span className="text-2xl font-bold font-display">
                Language For Composing
              </span>
            </div>
            
            <p className="text-gray-300 leading-relaxed max-w-2xl mx-auto">
              Supporting early childhood educators in creating meaningful writing experiences that nurture young learners' creativity and language development.
            </p>
            
            <div className="flex items-center justify-center space-x-3 text-gray-300">
              <Mail className="w-5 h-5 text-primary-400" />
              <span>info@languageforcomposing.edu</span>
            </div>
          </motion.div>
        </div>

        {/* Bottom Section */}
        <motion.div
          className="py-8 border-t border-gray-700 text-center"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
        >
          <div className="text-gray-400 text-sm space-y-2">
            <div>
              © 2024 Language For Composing. Educational Platform for Early Childhood Development.
            </div>
            <div className="flex items-center justify-center space-x-1 text-xs">
              <span>Made with</span>
              <Heart className="w-3 h-3 text-red-400 mx-1" />
              <span>for educators and young learners</span>
            </div>
          </div>
        </motion.div>
      </div>
    </footer>
  )
}

export default Footer