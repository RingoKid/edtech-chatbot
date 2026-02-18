import React from 'react'
import { motion } from 'framer-motion'
import { ArrowLeft } from 'lucide-react'
import { Link } from 'react-router-dom'
import { transcriptionVideos, categoryInfo } from '../data/videoData'
import VideoCard from '../components/VideoCard'
import { cn } from '../utils/cn'

const HandwritingSpelling = () => {
  const category = categoryInfo.transcription

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50 via-white to-secondary-50">
      {/* Back Navigation */}
      <div className="section-padding pt-32">
        <div className="container">
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6 }}
          >
            <Link
              to="/best-practices"
              className="inline-flex items-center text-primary-600 hover:text-primary-700 font-medium mb-8 transition-colors"
            >
              <ArrowLeft className="w-5 h-5 mr-2" />
              Back to Best Practices
            </Link>
          </motion.div>
        </div>
      </div>

      {/* Header Section */}
      <section className="section-padding pt-0">
        <div className="container">
          <motion.div
            className="text-center max-w-4xl mx-auto mb-16"
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
          >
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold font-display mb-8 text-gray-900">
              {category.title}
            </h1>

            <div className="bg-white rounded-2xl p-8 shadow-lg border border-gray-200">
              {Array.isArray(category.description) ? (
                category.description.map((paragraph, i) => (
                  <p key={i} className={cn('text-lg text-gray-700 leading-relaxed', i < category.description.length - 1 && 'mb-4')}>
                    {paragraph}
                  </p>
                ))
              ) : (
                <p className="text-lg text-gray-700 leading-relaxed">
                  {category.description}
                </p>
              )}
            </div>
          </motion.div>
        </div>
      </section>

      {/* Video Grid */}
      <section className="section-padding pt-0 pb-20">
        <div className="container">
          <div className="grid md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {transcriptionVideos.map((video, index) => (
              <VideoCard
                key={video.id}
                video={video}
                basePath="/handwriting-spelling"
                index={index}
              />
            ))}
          </div>
        </div>
      </section>
    </div>
  )
}

export default HandwritingSpelling
