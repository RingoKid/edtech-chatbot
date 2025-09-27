import React from 'react'
import { motion, useInView } from 'framer-motion'
import { useRef } from 'react'
import { Palette, Users, Heart } from 'lucide-react'

const FeaturesSection = () => {
  const ref = useRef(null)
  const isInView = useInView(ref, { once: true, margin: "-100px" })

  const features = [
    {
      icon: Palette,
      title: "Enhances Creativity",
      subtitle: "Creative Expression Builder",
      description: "Unlock unlimited creative potential with tools designed to inspire imagination and artistic expression in young learners through structured writing activities.",
      color: "from-purple-500 to-pink-500",
      bgColor: "from-purple-50 to-pink-50"
    },
    {
      icon: Users,
      title: "Collaborative Learning",
      subtitle: "Community Learning Hub",
      description: "Foster collaborative learning environments where teachers and students can share, learn, and grow together in supportive educational communities.",
      color: "from-green-500 to-emerald-500",
      bgColor: "from-green-50 to-emerald-50"
    },
    {
      icon: Heart,
      title: "Nurturing Development",
      subtitle: "Child-Centered Approach",
      description: "Support the whole child through developmentally appropriate practices that nurture both academic growth and social-emotional learning.",
      color: "from-orange-500 to-red-500",
      bgColor: "from-orange-50 to-red-50"
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
            <span className="text-primary-600">Enhancement Features</span>
          </motion.h2>
          
          <motion.p
            variants={itemVariants}
            className="text-xl text-gray-600 max-w-3xl mx-auto leading-relaxed"
          >
            Discover how Language for Composing transforms early childhood education through innovative approaches to writing and language development.
          </motion.p>
        </motion.div>

        {/* Features Grid */}
        <div className="grid lg:grid-cols-3 gap-8 mb-16">
          {features.map((feature, index) => (
            <motion.div
              key={index}
              className={`p-8 rounded-3xl bg-gradient-to-br ${feature.bgColor} border border-primary-200 shadow-xl hover:shadow-2xl transition-all duration-300`}
              initial={{ opacity: 0, y: 30 }}
              animate={isInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 30 }}
              transition={{ duration: 0.8, delay: index * 0.2 }}
              whileHover={{ y: -10 }}
            >
              <div className={`w-20 h-20 rounded-3xl bg-gradient-to-br ${feature.color} flex items-center justify-center text-white shadow-lg mb-6`}>
                <feature.icon className="w-10 h-10" />
              </div>
              
              <h3 className="text-2xl font-bold text-gray-900 mb-3">
                {feature.title}
              </h3>
              
              <p className="text-sm text-primary-600 font-medium mb-4">
                {feature.subtitle}
              </p>
              
              <p className="text-gray-600 leading-relaxed">
                {feature.description}
              </p>
            </motion.div>
          ))}
        </div>

        {/* Educational Philosophy */}
        <motion.div
          className="text-center bg-white rounded-3xl p-12 shadow-xl"
          initial={{ opacity: 0, y: 30 }}
          animate={isInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 30 }}
          transition={{ duration: 0.8, delay: 0.6 }}
        >
          <h3 className="text-3xl font-bold text-gray-900 mb-6">
            Our Educational Philosophy
          </h3>
          <p className="text-lg text-gray-600 max-w-4xl mx-auto leading-relaxed">
            We believe that every child is a natural storyteller. Through structured yet flexible approaches to early writing, 
            we help teachers create environments where children feel confident to express their thoughts, share their experiences, 
            and develop essential literacy skills that will serve them throughout their educational journey.
          </p>
        </motion.div>
      </div>
    </section>
  )
}

export default FeaturesSection