import React from 'react'
import { motion } from 'framer-motion'
import { Play, ArrowLeft, VideoOff } from 'lucide-react'
import { Link } from 'react-router-dom'
import { transcriptionVideos, categoryInfo } from '../data/videoData'

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
              <p className="text-lg text-gray-700 leading-relaxed">
                {category.description}
              </p>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Video Grid */}
      <section className="section-padding pt-0 pb-20">
        <div className="container">
          <div className="grid md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {transcriptionVideos.map((item, index) => (
              <motion.div
                key={item.id}
                className="group relative bg-white rounded-2xl shadow-lg border border-gray-200 overflow-hidden hover:shadow-xl transition-all duration-300"
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: index * 0.1 }}
                whileHover={{ y: -5 }}
              >
                {/* Video Thumbnail */}
                <div className="relative aspect-video bg-gradient-to-br from-primary-100 to-primary-200 overflow-hidden">
                  {item.noVideoYet ? (
                    <div className="absolute inset-0 flex items-center justify-center text-gray-400">
                      <VideoOff className="w-10 h-10" />
                    </div>
                  ) : (
                    <div className="absolute inset-0 bg-black/20 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                      <div className="w-16 h-16 bg-white/90 rounded-full flex items-center justify-center shadow-lg">
                        <Play className="w-8 h-8 text-primary-600 ml-1" />
                      </div>
                    </div>
                  )}
                </div>

                {/* Content */}
                <div className="p-6">
                  <h3 className="text-lg font-bold text-gray-900 mb-3 group-hover:text-primary-600 transition-colors">
                    {item.title}
                  </h3>

                  <p className="text-sm text-gray-600 leading-relaxed mb-4">
                    {item.description}
                  </p>

                  {/* Watch Video Button */}
                  <Link
                    to={`/handwriting-spelling/${item.id}`}
                    className="inline-flex items-center justify-center w-full px-4 py-2 bg-primary-600 text-white font-medium rounded-lg hover:bg-primary-700 transition-colors duration-200"
                  >
                    <Play className="w-4 h-4 mr-2" />
                    {item.noVideoYet ? 'View Practice' : 'Watch Video'}
                  </Link>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>
    </div>
  )
}

export default HandwritingSpelling
