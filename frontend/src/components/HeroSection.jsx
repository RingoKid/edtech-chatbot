import React from 'react'
import { motion } from 'framer-motion'
import { ArrowRight, BookOpen } from 'lucide-react'
import { Link } from 'react-router-dom'

const FloatingShape = ({ className, delay = 0, duration = 6 }) => (
  <motion.div
    className={className}
    animate={{
      y: [0, -20, 0],
      rotate: [0, 5, -5, 0],
      scale: [1, 1.05, 1],
    }}
    transition={{ duration, delay, repeat: Infinity, ease: 'easeInOut' }}
  />
)

const HeroSection = () => {
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.3,
        delayChildren: 0.2
      }
    }
  }

  const itemVariants = {
    hidden: { opacity: 0, y: 30 },
    visible: {
      opacity: 1,
      y: 0,
      transition: {
        duration: 0.8,
        ease: [0.6, -0.05, 0.01, 0.99]
      }
    }
  }

  return (
    <section className="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary-600 via-primary-700 to-secondary-600 text-white relative overflow-hidden">
      {/* Background Image Overlay */}
      <div className="absolute inset-0 bg-black/20" />

      {/* Background Pattern */}
      <div className="absolute inset-0 opacity-10">
        <div className="absolute inset-0" style={{
          backgroundImage: 'radial-gradient(circle at 1px 1px, rgba(255, 255, 255, 0.3) 1px, transparent 0)',
          backgroundSize: '50px 50px'
        }} />
      </div>

      {/* Floating decorative shapes */}
      <FloatingShape
        className="absolute top-20 left-[10%] w-64 h-64 rounded-full bg-white/5 blur-2xl"
        delay={0}
        duration={8}
      />
      <FloatingShape
        className="absolute bottom-32 right-[8%] w-80 h-80 rounded-full bg-secondary-400/10 blur-2xl"
        delay={2}
        duration={10}
      />
      <FloatingShape
        className="absolute top-1/3 right-[20%] w-40 h-40 rounded-full bg-white/5 blur-xl"
        delay={1}
        duration={7}
      />
      <FloatingShape
        className="absolute bottom-1/4 left-[15%] w-32 h-32 rounded-full bg-primary-300/10 blur-xl"
        delay={3}
        duration={9}
      />

      {/* Small floating accent circles */}
      <motion.div
        className="absolute top-[15%] right-[12%] w-3 h-3 rounded-full bg-white/30"
        animate={{ y: [0, -15, 0], opacity: [0.3, 0.6, 0.3] }}
        transition={{ duration: 4, repeat: Infinity }}
      />
      <motion.div
        className="absolute top-[40%] left-[8%] w-2 h-2 rounded-full bg-white/20"
        animate={{ y: [0, -10, 0], opacity: [0.2, 0.5, 0.2] }}
        transition={{ duration: 5, delay: 1, repeat: Infinity }}
      />
      <motion.div
        className="absolute bottom-[30%] right-[25%] w-2 h-2 rounded-full bg-secondary-300/30"
        animate={{ y: [0, -12, 0], opacity: [0.3, 0.5, 0.3] }}
        transition={{ duration: 3.5, delay: 2, repeat: Infinity }}
      />

      <div className="container relative z-10 pt-20">
        <motion.div
          className="text-center max-w-5xl mx-auto"
          variants={containerVariants}
          initial="hidden"
          animate="visible"
        >
          {/* Badge */}
          <motion.div
            variants={itemVariants}
            className="mb-8"
          >
            <span className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/10 backdrop-blur-sm border border-white/20 text-sm font-medium">
              <BookOpen className="w-4 h-4" />
              Science of Literacy, Learning &amp; Instruction
            </span>
          </motion.div>

          {/* Main Heading */}
          <motion.h1
            variants={itemVariants}
            className="text-4xl sm:text-5xl lg:text-7xl font-bold font-display mb-6 leading-tight"
          >
            <span className="block">
              Early Childhood Teacher Tool for
            </span>
            <span className="block mt-4 bg-gradient-to-r from-white via-blue-100 to-secondary-200 bg-clip-text text-transparent">
              Structured Composing Lessons
            </span>
          </motion.h1>

          {/* Subtitle */}
          <motion.p
            variants={itemVariants}
            className="text-xl sm:text-2xl mb-12 max-w-3xl mx-auto leading-relaxed text-white/80"
          >
            Where Early Writing and Language Grow Together
          </motion.p>

          {/* CTA Buttons */}
          <motion.div
            variants={itemVariants}
            className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-16"
          >
            <Link to="/best-practices">
              <motion.button
                className="inline-flex items-center px-10 py-4 bg-white text-primary-700 font-bold text-lg rounded-xl shadow-lg hover:shadow-xl transition-all duration-200"
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                Get Started
                <ArrowRight className="w-5 h-5 ml-2" />
              </motion.button>
            </Link>
            <Link to="/science-of-learning">
              <motion.button
                className="inline-flex items-center px-10 py-4 bg-white/10 backdrop-blur-sm text-white font-semibold text-lg rounded-xl border border-white/30 hover:bg-white/20 transition-all duration-200"
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                Learn the Science
              </motion.button>
            </Link>
          </motion.div>
        </motion.div>
      </div>

      {/* Scroll Indicator */}
      <motion.div
        className="absolute bottom-8 left-1/2 transform -translate-x-1/2"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 2 }}
      >
        <motion.div
          className="w-6 h-10 border-2 border-white/50 rounded-full flex justify-center"
          animate={{ y: [0, 10, 0] }}
          transition={{ duration: 2, repeat: Infinity }}
        >
          <motion.div
            className="w-1 h-3 bg-white/50 rounded-full mt-2"
            animate={{ y: [0, 6, 0] }}
            transition={{ duration: 2, repeat: Infinity }}
          />
        </motion.div>
      </motion.div>
    </section>
  )
}

export default HeroSection
