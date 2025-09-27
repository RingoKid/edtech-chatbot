import React from 'react'
import { motion, useInView } from 'framer-motion'
import { useRef } from 'react'

const AboutSection = () => {
  const ref = useRef(null)
  const isInView = useInView(ref, { once: true, margin: "-100px" })

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

  const empowermentSteps = [
    {
      number: "01",
      title: "Build knowledge of the language and writing skills young children need to become confident composors.",
      description: "Understanding developmental stages and foundational literacy skills that support early writing development."
    },
    {
      number: "02", 
      title: "Integrate language and literacy skills during meaningful, authentic writing tasks.",
      description: "Connecting reading, speaking, listening, and writing in purposeful activities that engage young learners."
    },
    {
      number: "03",
      title: "Equip teachers with the tools to seamlessly integrate early writing practices into daily classroom interactions.",
      description: "Providing practical strategies and resources for embedding writing instruction throughout the school day."
    },
    {
      number: "04",
      title: "Equip teachers with the tools to seamlessly integrate early writing processes into daily classroom interactions.",
      description: "Supporting the development of writing as a process through planning, drafting, and sharing in age-appropriate ways."
    }
  ]

  return (
    <section className="section-padding bg-white relative overflow-hidden">
      <div className="container relative z-10" ref={ref}>
        <motion.div
          className="text-center mb-16"
          variants={containerVariants}
          initial="hidden"
          animate={isInView ? "visible" : "hidden"}
        >
          <motion.h2
            variants={itemVariants}
            className="text-4xl sm:text-5xl font-bold font-display mb-6 text-primary-600"
          >
            About Us
          </motion.h2>
        </motion.div>

        {/* Two Column Layout */}
        <div className="grid lg:grid-cols-2 gap-16 items-center mb-20">
          {/* Left Column - Content */}
          <motion.div
            className="space-y-8"
            initial={{ opacity: 0, x: -50 }}
            animate={isInView ? { opacity: 1, x: 0 } : { opacity: 0, x: -50 }}
            transition={{ duration: 0.8, delay: 0.2 }}
          >
            <div className="prose prose-lg">
              <p className="text-gray-700 leading-relaxed mb-6 text-lg">
                Language for Early Childhood Composing is an innovative language immersion program that early childhood teachers enhance their effectiveness with practical support for effective teaching strategies.
              </p>
              
              <p className="text-gray-700 leading-relaxed mb-6 text-lg">
                With our Advanced lesson builder, educators can easily create tailored lessons that connect real-world classroom with engaging writing activities. Join us in fostering a love for writing and effective communication in young learners!
              </p>
            </div>
          </motion.div>

          {/* Right Column - Image */}
          <motion.div
            className="relative"
            initial={{ opacity: 0, x: 50 }}
            animate={isInView ? { opacity: 1, x: 0 } : { opacity: 0, x: 50 }}
            transition={{ duration: 0.8, delay: 0.4 }}
          >
            <div className="text-center">
              <img 
                src="/AboutUs.png" 
                alt="About Language for Early Childhood Composing" 
                className="w-full h-auto max-w-md mx-auto mb-4 rounded-2xl"
              />
              <p className="text-primary-700 font-medium">Early Writing Development</p>
            </div>
          </motion.div>
        </div>

        {/* How Language4Composing Empowers Teachers */}
        <motion.div
          className="text-center mb-16"
          variants={containerVariants}
          initial="hidden"
          animate={isInView ? "visible" : "hidden"}
        >
          <motion.h2
            variants={itemVariants}
            className="text-4xl sm:text-5xl font-bold font-display mb-6"
          >
            <span className="text-primary-600">How Language4Composing</span>
            <br />
            <span className="text-gray-900">Empowers Teachers</span>
          </motion.h2>
        </motion.div>

        {/* Empowerment Steps Grid */}
        <motion.div
          className="grid md:grid-cols-2 gap-8"
          variants={containerVariants}
          initial="hidden"
          animate={isInView ? "visible" : "hidden"}
        >
          {empowermentSteps.map((step) => (
            <motion.div
              key={step.number}
              className="group relative"
              variants={itemVariants}
            >
              <div className="bg-white rounded-2xl p-8 shadow-lg border border-gray-100 h-full relative overflow-hidden group-hover:shadow-xl transition-shadow duration-300">
                {/* Step Number */}
                <div className="relative z-10">
                  <div className="text-6xl font-bold text-primary-200 mb-6">
                    {step.number}
                  </div>
                  
                  {/* Content */}
                  <h3 className="text-xl font-bold text-gray-900 mb-4 leading-snug">
                    {step.title}
                  </h3>
                  
                  <p className="text-gray-600 leading-relaxed">
                    {step.description}
                  </p>
                </div>
              </div>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </section>
  )
}

export default AboutSection