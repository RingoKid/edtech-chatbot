import React from 'react'
import { motion } from 'framer-motion'
import { Link } from 'react-router-dom'
import { PenTool, BookOpen, Lightbulb, Play } from 'lucide-react'

const BestPractices = () => {
  const practicesSections = [
    {
      icon: PenTool,
      title: "Handwriting and Spelling",
      description: "Children learn to put their thoughts on paper using letters and words. When handwriting and spelling become automatic, it frees up brainpower to focus on what they want to say.",
      videoLink: "/handwriting-spelling"
    },
    {
      icon: BookOpen,
      title: "Vocabulary and Syntax",
      description: "Children use the words they know (vocabulary) to build sentences (syntax). This helps them express their thoughts clearly, using their foundational oral language skills.",
      videoLink: "/vocabulary-syntax"
    },
    {
      icon: Lightbulb,
      title: "Idea Organization and Generation",
      description: "Children pull ideas from what they know and have experienced (memory retrieval). They learn to organize those ideas to respond to a writing prompt or task.",
      videoLink: "/idea-generation"
    }
  ]

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50 via-white to-secondary-50">
      {/* Hero Section */}
      <section className="section-padding pt-32 relative overflow-hidden">
        <div className="container">
          <motion.div
            className="text-center max-w-5xl mx-auto"
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
          >
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold font-display mb-8 text-gray-900">
              Research-Backed Practices Modeled
            </h1>
            
            <p className="text-xl text-gray-600 mb-8 leading-relaxed">
              Navigate through these three strategies to find various examples of real teacher examples
            </p>
            
            <div className="bg-white rounded-2xl p-8 shadow-lg border border-gray-200 mb-12">
              <p className="text-lg text-gray-700 leading-relaxed mb-6">
                Research shows that when teachers embed direct instruction in <strong>handwriting & spelling</strong>, <strong>vocabulary & syntax</strong>, and <strong>idea generation & organization</strong> within authentic writing tasks, children make faster gains in literacy, language, and executive functioning.
              </p>
              
              <p className="text-base text-gray-600">
                Click on each component to explore how it supports young writers' development.
              </p>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Three Main Components */}
      <section className="section-padding bg-white">
        <div className="container">
          <div className="grid lg:grid-cols-3 gap-8">
            {practicesSections.map((section, index) => (
              <motion.div
                key={section.title}
                className="group relative"
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8, delay: index * 0.2 }}
                whileHover={{ y: -10 }}
              >
                <div className="h-full p-8 rounded-3xl bg-white border border-gray-200 shadow-lg group-hover:shadow-2xl transition-all duration-300 relative overflow-hidden">
                  <div className="relative z-10">
                    {/* Icon */}
                    <div className="w-20 h-20 rounded-3xl bg-primary-600 flex items-center justify-center text-white shadow-lg mb-6 group-hover:scale-110 transition-transform mx-auto">
                      <section.icon className="w-10 h-10" />
                    </div>
                    
                    {/* Title */}
                    <h2 className="text-2xl font-bold text-gray-900 mb-6 text-center leading-tight">
                      {section.title}
                    </h2>
                    
                    {/* Description */}
                    <p className="text-gray-600 mb-8 leading-relaxed text-center">
                      {section.description}
                    </p>
                    
                    {/* See Videos Button */}
                    <div className="text-center">
                      <Link 
                        to={section.videoLink}
                        className="inline-flex items-center justify-center px-8 py-3 bg-primary-600 text-white font-semibold rounded-xl shadow-md hover:bg-primary-700 hover:shadow-lg transition-all duration-200"
                      >
                        <Play className="w-5 h-5 mr-2" />
                        See Videos
                      </Link>
                    </div>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>
    </div>
  )
}

export default BestPractices