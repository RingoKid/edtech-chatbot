import React from 'react'
import { motion } from 'framer-motion'
import { Play, ArrowLeft } from 'lucide-react'
import { Link } from 'react-router-dom'

const VocabularySyntax = () => {
  const videoItems = [
    {
      id: 1,
      title: "Multiple Vocabulary Opportunities",
      description: "Provide multiple opportunities for children to use vocabulary words from their unit or theme during sentence generation tasks",
      thumbnail: "/src/assets/images/vocab1.png",
      videoUrl: "https://example.com/vocab-video1"
    },
    {
      id: 2,
      title: "Systematic Language Structure Focus",
      description: "Explicitly and systematically focus on one language structure at a time–like subject-verb clauses or prepositional phrases–to build sentence awareness",
      thumbnail: "/src/assets/images/sstructure.png",
      videoUrl: "https://example.com/vocab-video2"
    },
    {
      id: 3,
      title: "Guided Vocabulary Prompting",
      description: "Prompt children to use specific vocabulary and sentence structures while they compose.",
      thumbnail: "/src/assets/images/cuevocab.png",
      videoUrl: "https://example.com/vocab-video3"
    },
    {
      id: 4,
      title: "Word Play and Connections",
      description: "Encourage children to play with words by making connections, grouping them into categories, and exploring how they relate to the writing topic or unit theme",
      thumbnail: "/src/assets/images/vocab2.png",
      videoUrl: "https://example.com/vocab-video4"
    },
    {
      id: 5,
      title: "Sentence Development Support",
      description: "Support children's sentence development by having them build, rearrange, combine, and expand sentences related to the writing topic or unit theme.",
      thumbnail: "/src/assets/images/sentencecompletion.png",
      videoUrl: "https://example.com/vocab-video5"
    },
    {
      id: 6,
      title: "Phonological Knowledge Application",
      description: "Encourage children to use what they've learned about sounds, spelling patterns, and word parts to try spelling new words. Promotes application of phonological knowledge through invented spelling, strengthening",
      thumbnail: "/src/assets/images/vocab1.png",
      videoUrl: "https://example.com/vocab-video6"
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
              Vocabulary & Sentence Structure
            </h1>
            
            <div className="bg-white rounded-2xl p-8 shadow-lg border border-gray-200">
              <p className="text-lg text-gray-700 leading-relaxed">
                These vocabulary and sentence structure practices strengthen the brain's coordination of motor, visual, and phonological processes—making it easier for children to store, retrieve, and apply letter-sound knowledge when writing.
              </p>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Video Grid */}
      <section className="section-padding pt-0 pb-20">
        <div className="container">
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
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
                  <a
                    href={item.videoUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center justify-center w-full px-4 py-2 bg-primary-600 text-white font-medium rounded-lg hover:bg-primary-700 transition-colors duration-200"
                  >
                    <Play className="w-4 h-4 mr-2" />
                    Watch Video
                  </a>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>
    </div>
  )
}

export default VocabularySyntax