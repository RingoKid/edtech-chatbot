import React from 'react'
import { motion, useInView } from 'framer-motion'
import { useRef } from 'react'
import { Users, Video, BookOpen } from 'lucide-react'

const FeaturesSection = () => {
  const ref = useRef(null)
  const isInView = useInView(ref, { once: true, margin: "-100px" })

  const hubs = [
    {
      icon: Users,
      title: "Community Learning Hub",
      subtitle: "Connect & Share",
      description: "Teachers, families, and researchers come together to share questions, insights, and classroom experiences. This space supports responsive instruction by helping educators learn from one another and from research on how children use language in real writing contexts.",
      color: "from-green-500 to-emerald-500",
      bgColor: "from-green-50 to-emerald-50"
    },
    {
      icon: Video,
      title: "Knowledge Builder Hub",
      subtitle: "Learn & Grow",
      description: "Short videos for teachers to deepen their understanding of the language skills and processes involved in early writing development.",
      color: "from-blue-500 to-cyan-500",
      bgColor: "from-blue-50 to-cyan-50"
    },
    {
      icon: BookOpen,
      title: "Resource Hub",
      subtitle: "Explore & Discover",
      description: "A curated collection of trusted resources to help teachers explore research and practical strategies for supporting language, writing, and learning in the classroom.",
      color: "from-purple-500 to-pink-500",
      bgColor: "from-purple-50 to-pink-50"
    }
  ]

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.2,
        delayChildren: 0.3
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
    <section className="section-padding bg-gradient-to-br from-primary-50 via-white to-secondary-50 relative overflow-hidden">
      <div className="container relative z-10" ref={ref}>
        {/* Header */}
        <motion.div
          className="text-center mb-20"
          variants={containerVariants}
          initial="hidden"
          animate={isInView ? "visible" : "hidden"}
        >
          <motion.h2
            variants={itemVariants}
            className="text-4xl sm:text-5xl font-bold font-display mb-6"
          >
            <span className="text-gray-900">Educational</span>
            <br />
            <span className="text-primary-600">Enhancement</span>
          </motion.h2>

          <motion.p
            variants={itemVariants}
            className="text-xl text-gray-600 max-w-3xl mx-auto leading-relaxed"
          >
            L4C supports teachers by making language learning visible, connected, and meaningful—both in and beyond the classroom.
          </motion.p>
        </motion.div>

        {/* Features Grid */}
        <div className="grid lg:grid-cols-3 gap-8 mb-16">
          {hubs.map((hub, index) => (
            <motion.div
              key={index}
              className={`p-8 rounded-3xl bg-gradient-to-br ${hub.bgColor} border border-primary-200 shadow-xl hover:shadow-2xl transition-all duration-300`}
              initial={{ opacity: 0, y: 30 }}
              animate={isInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 30 }}
              transition={{ duration: 0.8, delay: index * 0.2 }}
              whileHover={{ y: -10 }}
            >
              <div className={`w-20 h-20 rounded-3xl bg-gradient-to-br ${hub.color} flex items-center justify-center text-white shadow-lg mb-6`}>
                <hub.icon className="w-10 h-10" />
              </div>

              <h3 className="text-2xl font-bold text-gray-900 mb-3">
                {hub.title}
              </h3>

              <p className="text-sm text-primary-600 font-medium mb-4">
                {hub.subtitle}
              </p>

              <p className="text-gray-600 leading-relaxed">
                {hub.description}
              </p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  )
}

export default FeaturesSection