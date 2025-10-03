import React from 'react'
import { motion } from 'framer-motion'
import { Play, ArrowLeft } from 'lucide-react'
import { Link } from 'react-router-dom'

const HandwritingSpelling = () => {
  const videoItems = [
    {
      id: 1,
      title: "Teaching Proper Pencil Grip",
      description: "Learn effective techniques for teaching children the correct way to hold a pencil for comfortable, legible writing.",
      thumbnail: "/src/assets/images/pencil-grip.jpg",
      videoUrl: "/handwriting-spelling/proper-way-to-hold",
    },
    {
      id: 2,
      title: "Help children pronounce, identify, and isolate phonemes correctly",
      description: "Enhances phoneme isolation and focuses attention for accurate sound-symbol mapping and memory encoding",
      thumbnail: "/src/assets/images/pronounce-identify.jpg",
      videoUrl: "/handwriting-spelling/pronounce-identify",
    },
    {
      id: 3,
      title: "Teach how to form each letter step by step, showing the exact order and direction of strokes",
      description: "Supports coordination of timed movement with correct stroke order",
      thumbnail: "/src/assets/images/letter-formation.jpg",
      videoUrl: "/handwriting-spelling/sequence-strokes"
    },
    {
      id: 4,
      title: "Have children retrieve prior phoneme-grapheme knowledge and connect to new phoneme-grapheme patterns",
      description: "Activates prior phoneme-graphene knowledge to support orthographic mapping",
      thumbnail: "/src/assets/images/phonemic-awareness.jpg",
      videoUrl: "/handwriting-spelling/retrieve-connect"
    },
    {
      id: 5,
      title: "Cue children to apply phoneme-grapheme patterns during activities",
      description: "Strengths Fluency through retrieval and consolidation of phoneme-graphene patterns",
      thumbnail: "/src/assets/images/phoneme-grapheme.jpg",
      videoUrl: "/handwriting-spelling/phoneme-graphene"
    },
    {
      id: 6,
      title: "Talk with children about how letters look—compare their shapes and the strokes used to write them.",
      description: "Promotes deep encoding of letter forms for memory retention",
      thumbnail: "/src/assets/images/invented-spelling.jpg",
      videoUrl: "/handwriting-spelling/compare-contrast"
    },
    {
      id: 7,
      title: "Provide corrective and confirmatory feedback explaining what part is incorrect and showing them how to fix it.",
      description: "Supports deeper processing of spelling patterns to enhance retrieval and automaticity",
      thumbnail: "/src/assets/images/directionality.jpg",
      videoUrl: "/handwriting-spelling/corrective-feedback"
    },
    {
      id: 8,
      title: "Encourage children to use what they’ve learned about sounds, spelling patterns, and word parts to try spelling new words",
      description: "Promotes application of phonological and knowledge through invented spelling, strengthening",
      thumbnail: "/src/assets/images/corrective-feedback.jpg",
      videoUrl: "/handwriting-spelling/invented-spelling"
    },
    {
      id: 9,
      title: "Support writing within lines left to right (directionality)",
      description: "Helps children learn to keep letter on the line and moves smoothly from left to right.",
      thumbnail: "/src/assets/images/phonological-awareness.jpg",
      videoUrl: "/handwriting-spelling/directionality"
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