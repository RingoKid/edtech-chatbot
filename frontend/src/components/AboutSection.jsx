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

  const principles = [
    {
      number: "01",
      title: "Make language visible through responsive and explicit instruction.",
      description: "Teachers intentionally highlight how language works during composing, helping children notice, analyze, and apply language structures as they write."
    },
    {
      number: "02",
      title: "Scaffold children to increase the complexity of their language production and expression.",
      description: "Instruction supports children in moving from simpler to more complex ideas, sentences, and language forms within meaningful writing tasks."
    },
    {
      number: "03",
      title: "Anchor language instruction within authentic composing tasks that build language and concepts.",
      description: "Language development is inseparable from meaning-making and content knowledge; children learn language best when they use it to communicate ideas that matter."
    },
    {
      number: "04",
      title: "Coordinate multiple levels of language to support functional writing.",
      description: "L4C coordinates spelling and handwriting, sentence construction, and idea development so children experience how language works together to communicate ideas and meaning."
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

        {/* About Content */}
        <motion.div
          className="mb-20 text-center"
          initial={{ opacity: 0, y: 30 }}
          animate={isInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 30 }}
          transition={{ duration: 0.8, delay: 0.2 }}
        >
          <p className="text-gray-700 leading-relaxed mb-6 text-lg">
            Language for Composing (L4C) is an instructional approach grounded in the Science of Literacy, Learning, and Instruction. Through authentic composing, teachers intentionally support young children as they notice, analyze, and use language structures at multiple levels, including sounds, words, sentences, and discourse. L4C helps teachers make language visible, strengthening the connections among language, writing, and learning.
          </p>

          <p className="text-gray-700 leading-relaxed mb-6 text-lg">
            L4C's Advanced Lesson Builder helps teachers translate the science of literacy, learning, and instruction into clear, actionable classroom practice. The builder visually supports lesson sequencing and organization, helping teachers plan instruction in ways that reduce cognitive load while making the language demands of writing explicit. As teachers design composing lessons, they deepen their understanding of how language structures—across phonology, word, sentence, and discourse levels—operate during the writing process and how these structures can be intentionally supported as children generate meaning through text. By making the relationship between language and composing visible, the L4C Lesson Builder supports responsive instruction while strengthening teachers' expertise in language-based writing instruction.
          </p>
        </motion.div>

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
            <span className="text-primary-600">Principles of the</span>
            <br />
            <span className="text-gray-900">L4C Approach</span>
          </motion.h2>
        </motion.div>

        {/* Empowerment Steps Grid */}
        <motion.div
          className="grid md:grid-cols-2 gap-8"
          variants={containerVariants}
          initial="hidden"
          animate={isInView ? "visible" : "hidden"}
        >
          {principles.map((step) => (
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