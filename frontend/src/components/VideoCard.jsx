import React from 'react'
import { motion } from 'framer-motion'
import { Play, VideoOff } from 'lucide-react'
import { Link } from 'react-router-dom'

const VideoCard = ({ video, basePath, index = 0 }) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 30 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, delay: index * 0.1 }}
      whileHover={{ y: -5 }}
    >
      <Link
        to={`${basePath}/${video.id}`}
        className="group flex flex-col h-full bg-white rounded-2xl shadow-lg border border-gray-200 overflow-hidden hover:shadow-xl transition-all duration-300"
      >
        {/* Video Thumbnail */}
        <div className="relative aspect-video bg-gradient-to-br from-primary-100 to-primary-200 overflow-hidden flex-shrink-0">
          {video.noVideoYet ? (
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
        <div className="p-6 flex flex-col flex-grow">
          <h3 className="text-lg font-bold text-gray-900 mb-3 group-hover:text-primary-600 transition-colors">
            {video.title}
          </h3>

          <p className="text-sm text-gray-600 leading-relaxed flex-grow">
            {video.description}
          </p>

          {/* Watch Video Button */}
          <div className="mt-4 inline-flex items-center justify-center w-full px-4 py-2 bg-primary-600 text-white font-medium rounded-lg group-hover:bg-primary-700 transition-colors duration-200">
            <Play className="w-4 h-4 mr-2" />
            {video.noVideoYet ? 'View Practice' : 'Watch Video'}
          </div>
        </div>
      </Link>
    </motion.div>
  )
}

export default VideoCard
