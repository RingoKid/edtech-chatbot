import React from 'react'
import { motion } from 'framer-motion'
import { ArrowLeft, Play } from 'lucide-react'
import { Link } from 'react-router-dom'

const SentenceManipulation = () => {
  const videoData = {
    title: "Build Sentence Manipulation",
    description: "Learning the proper order of strokes when forming letters supports neat handwriting, consistency, and speed",
    videoUrl: "https://www.youtube-nocookie.com/embed/sample-sentence-manipulation?modestbranding=1&rel=0&showinfo=0&controls=1&disablekb=1&fs=0&iv_load_policy=3&cc_load_policy=0&loop=0&color=white&theme=light&origin=localhost",
    content: "How to practice correct strokes?\n" +
        "Guide children to start each letter at the correct point, moving in the right direction, and finishing with a smooth flow. Use lined paper or tracing sheets to help them follow the sequence and build muscle memory for clear, legible writing."
  }

  const exploreMoreVideos = [
    {
      id: 1,
      title: "Vocabulary Sentence Structures",
      thumbnail: "/src/assets/images/sentence-structures.jpg",
      videoUrl: "/vocabulary/vocabulary-sentence-structures"
    },
    {
      id: 2,
      title: "Sentence Awareness",
      thumbnail: "/src/assets/images/sentence-awareness.jpg",
      videoUrl: "/vocabulary/sentence-awareness"
    },
    {
      id: 3,
      title: "Vocabulary Support",
      thumbnail: "/src/assets/images/vocabulary-support.jpg",
      videoUrl: "/vocabulary/vocabulary-support"
    }
  ]

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50 via-white to-secondary-50">
      <div className="section-padding pt-32">
        <div className="container">
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6 }}
          >
            <Link 
              to="/vocabulary"
              className="inline-flex items-center text-primary-600 hover:text-primary-700 font-medium mb-8 transition-colors"
            >
              <ArrowLeft className="w-5 h-5 mr-2" />
              Back to Vocabulary
            </Link>
          </motion.div>
        </div>
      </div>

      <section className="section-padding pt-0">
        <div className="container">
          <motion.div
            className="max-w-6xl mx-auto"
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
          >
            <h1 className="text-3xl sm:text-4xl lg:text-5xl font-bold font-display mb-6 text-gray-900 text-center">
              {videoData.title}
            </h1>
            
            <p className="text-lg text-gray-700 leading-relaxed mb-12 text-center max-w-4xl mx-auto">
              {videoData.description}
            </p>

            <div className="bg-white rounded-2xl p-4 shadow-lg border border-gray-200 mb-12">
              <div className="aspect-video rounded-xl overflow-hidden">
                <iframe
                  src={videoData.videoUrl}
                  title={videoData.title}
                  className="w-full h-full"
                  frameBorder="0"
                  allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                  allowFullScreen
                ></iframe>
              </div>
            </div>

            {videoData.content && (
              <div className="bg-white rounded-2xl p-8 shadow-lg border border-gray-200 mb-16">
                <div className="max-w-2xl mx-auto">
                  <p className="text-lg text-gray-800 leading-relaxed whitespace-pre-line">
                    {videoData.content}
                  </p>
                </div>
              </div>
            )}
          </motion.div>
        </div>
      </section>

      <section className="section-padding pt-0 pb-20">
        <div className="container">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.2 }}
          >
            <h2 className="text-3xl sm:text-4xl font-bold font-display mb-12 text-gray-900 text-center">
              Explore More
            </h2>
            
            <div className="grid md:grid-cols-3 gap-8 max-w-6xl mx-auto">
              {exploreMoreVideos.map((video, index) => (
                <motion.div
                  key={video.id}
                  className="group relative bg-white rounded-2xl shadow-lg border border-gray-200 overflow-hidden hover:shadow-xl transition-all duration-300"
                  initial={{ opacity: 0, y: 30 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.6, delay: 0.3 + index * 0.1 }}
                  whileHover={{ y: -5 }}
                >
                  <div className="relative aspect-video bg-gradient-to-br from-primary-100 to-primary-200 overflow-hidden">
                    <img 
                      src={video.thumbnail}
                      alt={video.title}
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                      onError={(e) => {
                        e.target.style.display = 'none'
                        e.target.nextSibling.style.display = 'flex'
                      }}
                    />
                    <div className="absolute inset-0 bg-gradient-to-br from-primary-100 to-primary-200 flex items-center justify-center text-primary-600 font-medium text-sm hidden">
                      Video Thumbnail
                    </div>
                    
                    <div className="absolute inset-0 bg-black/20 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                      <div className="w-12 h-12 bg-white/90 rounded-full flex items-center justify-center shadow-lg">
                        <Play className="w-6 h-6 text-primary-600 ml-1" />
                      </div>
                    </div>
                  </div>

                  <div className="p-6">
                    <h3 className="text-lg font-bold text-gray-900 mb-4 group-hover:text-primary-600 transition-colors leading-tight">
                      {video.title}
                    </h3>
                    
                    <Link
                      to={video.videoUrl}
                      className="inline-flex items-center justify-center w-full px-4 py-2 bg-primary-600 text-white font-medium rounded-lg hover:bg-primary-700 transition-colors duration-200"
                    >
                      View
                    </Link>
                  </div>
                </motion.div>
              ))}
            </div>
          </motion.div>
        </div>
      </section>
    </div>
  )
}

export default SentenceManipulation