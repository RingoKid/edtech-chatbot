import React from 'react'
import { motion } from 'framer-motion'
import { Play, ArrowLeft } from 'lucide-react'
import { Link } from 'react-router-dom'

const HandwritingSpelling = () => {
  const videoItems = [
    {
      id: 1,
      title: "Making Letter Formation Automatic",
      description: "Helping children develop fluent letter writing through repetitive practice and muscle memory development.",
      thumbnail: "/src/assets/images/letter-formation-thumbnail.png",
      videoUrl: "/handwriting-spelling/making-letter-formation-automatic"
    },
    {
      id: 2,
      title: "Phonological Awareness Activities",
      description: "Building sound-letter connections through interactive games and systematic phonics instruction.",
      thumbnail: "/src/assets/images/phonological-awareness.jpg",
      videoUrl: "/handwriting-spelling/phonological-awareness-activities"
    },
    {
      id: 3,
      title: "Multi-Sensory Writing Approaches",
      description: "Engaging visual, auditory, and kinesthetic learning styles in handwriting instruction.",
      thumbnail: "/src/assets/images/multisensory-writing.jpg",
      videoUrl: "/handwriting-spelling/multi-sensory-writing-approaches"
    },
    {
      id: 4,
      title: "Letter-Sound Correspondence Practice",
      description: "Systematic practice connecting letters with their corresponding sounds and phonemes.",
      thumbnail: "/src/assets/images/letter-sound.jpg",
      videoUrl: "https://example.com/video4"
    },
    {
      id: 5,
      title: "Writing Posture and Grip Development",
      description: "Teaching proper pencil grip and body positioning for comfortable, effective writing.",
      thumbnail: "/src/assets/images/writing-posture.jpg",
      videoUrl: "https://example.com/video5"
    },
    {
      id: 6,
      title: "High-Frequency Word Recognition",
      description: "Building automatic recognition and spelling of common sight words and vocabulary.",
      thumbnail: "/src/assets/images/sight-words.jpg",
      videoUrl: "https://example.com/video6"
    },
    {
      id: 7,
      title: "Progressive Writing Exercises",
      description: "Structured activities that gradually increase writing complexity and independence.",
      thumbnail: "/src/assets/images/progressive-writing.jpg",
      videoUrl: "https://example.com/video7"
    },
    {
      id: 8,
      title: "Assessment and Tracking Progress",
      description: "Methods for monitoring handwriting development and spelling accuracy improvements.",
      thumbnail: "/src/assets/images/assessment.jpg",
      videoUrl: "https://example.com/video8"
    }
  ]

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
              Handwriting & Spelling
            </h1>
            
            <div className="bg-white rounded-2xl p-8 shadow-lg border border-gray-200">
              <p className="text-lg text-gray-700 leading-relaxed">
                These handwriting and spelling practices strengthen the brain's coordination of motor, visual, and phonological processes—making it easier for children to store, retrieve, and apply letter-sound knowledge when writing.
              </p>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Video Grid */}
      <section className="section-padding pt-0 pb-20">
        <div className="container">
          <div className="grid md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {videoItems.map((item, index) => (
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
                  <img 
                    src={item.thumbnail}
                    alt={item.title}
                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                    onError={(e) => {
                      e.target.style.display = 'none'
                      e.target.nextSibling.style.display = 'flex'
                    }}
                  />
                  {/* Fallback placeholder */}
                  <div className="absolute inset-0 bg-gradient-to-br from-primary-100 to-primary-200 flex items-center justify-center text-primary-600 font-medium text-sm hidden">
                    Video Thumbnail
                  </div>
                  
                  {/* Play Button Overlay */}
                  <div className="absolute inset-0 bg-black/20 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                    <div className="w-16 h-16 bg-white/90 rounded-full flex items-center justify-center shadow-lg">
                      <Play className="w-8 h-8 text-primary-600 ml-1" />
                    </div>
                  </div>
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
                  {item.videoUrl.startsWith('/handwriting-spelling/') || item.videoUrl.startsWith('/video/') ? (
                    <Link
                      to={item.videoUrl}
                      className="inline-flex items-center justify-center w-full px-4 py-2 bg-primary-600 text-white font-medium rounded-lg hover:bg-primary-700 transition-colors duration-200"
                    >
                      <Play className="w-4 h-4 mr-2" />
                      Watch Video
                    </Link>
                  ) : (
                    <a
                      href={item.videoUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center justify-center w-full px-4 py-2 bg-primary-600 text-white font-medium rounded-lg hover:bg-primary-700 transition-colors duration-200"
                    >
                      <Play className="w-4 h-4 mr-2" />
                      Watch Video
                    </a>
                  )}
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