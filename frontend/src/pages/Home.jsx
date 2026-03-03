import React from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Rocket } from 'lucide-react'
import HeroSection from '../components/HeroSection'
import AboutSection from '../components/AboutSection'
import FeaturesSection from '../components/FeaturesSection'

const CTABanner = () => (
  <section className="relative overflow-hidden bg-gradient-to-r from-primary-600 via-primary-700 to-secondary-600 py-16">
    {/* Dot pattern */}
    <div className="absolute inset-0 opacity-10">
      <div className="absolute inset-0" style={{
        backgroundImage: 'radial-gradient(circle at 1px 1px, rgba(255, 255, 255, 0.3) 1px, transparent 0)',
        backgroundSize: '40px 40px'
      }} />
    </div>

    <div className="container relative z-10 text-center">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        viewport={{ once: true }}
      >
        <h2 className="text-3xl sm:text-4xl font-bold font-display text-white mb-4">
          Ready to Build Your Lesson?
        </h2>
        <p className="text-white/80 text-lg mb-8 max-w-2xl mx-auto">
          Use the L4C LaunchPad to create structured composing lessons grounded in what we know about how children learn best.
        </p>
        <Link
          to="/ai-teaching-assistant"
          className="inline-flex items-center gap-2 px-10 py-4 bg-white text-primary-700 font-bold text-lg rounded-xl shadow-lg hover:shadow-xl hover:scale-105 transition-all duration-200"
        >
          <Rocket className="w-5 h-5" />
          Open L4C LaunchPad
        </Link>
      </motion.div>
    </div>
  </section>
)

const Home = () => {
  return (
    <div className="min-h-screen">
      <HeroSection />
      <AboutSection />
      <CTABanner />
      <FeaturesSection />
    </div>
  )
}

export default Home
