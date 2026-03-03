import React from 'react'
import { motion, useInView } from 'framer-motion'
import { useRef } from 'react'

const principleColors = [
  { accent: 'bg-blue-500', light: 'bg-blue-50' },
  { accent: 'bg-purple-500', light: 'bg-purple-50' },
  { accent: 'bg-emerald-500', light: 'bg-emerald-50' },
  { accent: 'bg-amber-500', light: 'bg-amber-50' },
]

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
      {/* Subtle background decoration */}
      <div className="absolute top-0 right-0 w-96 h-96 bg-primary-50 rounded-full -translate-y-1/2 translate-x-1/3 blur-3xl" />
      <div className="absolute bottom-0 left-0 w-72 h-72 bg-secondary-50 rounded-full translate-y-1/3 -translate-x-1/4 blur-3xl" />

      <div className="container relative z-10" ref={ref}>
        <motion.div
          className="text-center mb-16"
          variants={containerVariants}
          initial="hidden"
          animate={isInView ? "visible" : "hidden"}
        >
          <motion.div variants={itemVariants} className="mb-4">
            <span className="inline-block px-4 py-1.5 rounded-full bg-primary-100 text-primary-700 text-sm font-semibold">
              Our Approach
            </span>
          </motion.div>
          <motion.h2
            variants={itemVariants}
            className="text-4xl sm:text-5xl font-bold font-display mb-6 text-primary-600"
          >
            About Us
          </motion.h2>
        </motion.div>

        {/* About Content */}
        <motion.div
          className="mb-20 max-w-4xl mx-auto"
          initial={{ opacity: 0, y: 30 }}
          animate={isInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 30 }}
          transition={{ duration: 0.8, delay: 0.2 }}
        >
          <p className="text-gray-600 leading-relaxed mb-8 text-lg">
            Language for Composing (L4C) is an instructional approach grounded in the Science of Literacy, Learning, and Instruction. Through authentic composing, teachers intentionally support young children as they notice, analyze, and use language structures at multiple levels, including sounds, words, sentences, and discourse. L4C helps teachers make language visible, strengthening the connections among language, writing, and learning.
          </p>

          {/* Highlighted callout */}
          <motion.div
            className="bg-gradient-to-r from-primary-50 to-secondary-50 border border-primary-100 rounded-2xl p-8 mb-8"
            initial={{ opacity: 0, scale: 0.98 }}
            animate={isInView ? { opacity: 1, scale: 1 } : { opacity: 0, scale: 0.98 }}
            transition={{ duration: 0.6, delay: 0.4 }}
          >
            <p className="text-gray-700 leading-relaxed text-lg">
              The L4C LaunchPad helps teachers translate the science of literacy, learning, and instruction into clear, actionable classroom practice. The builder visually supports lesson sequencing and organization, helping teachers plan instruction in ways that reduce cognitive load while making the language demands of writing explicit.
            </p>
          </motion.div>

          <p className="text-gray-600 leading-relaxed text-lg">
            As teachers design composing lessons, they deepen their understanding of how language structures—across phonology, word, sentence, and discourse levels—operate during the writing process and how these structures can be intentionally supported as children generate meaning through text. By making the relationship between language and composing visible, the L4C LaunchPad supports responsive instruction while strengthening teachers' expertise in language-based writing instruction.
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
          className="grid md:grid-cols-2 gap-6"
          variants={containerVariants}
          initial="hidden"
          animate={isInView ? "visible" : "hidden"}
        >
          {principles.map((step, index) => (
            <motion.div
              key={step.number}
              className="group relative"
              variants={itemVariants}
            >
              <div className="bg-white rounded-2xl p-8 shadow-lg border border-gray-100 h-full relative overflow-hidden group-hover:shadow-xl transition-all duration-300">
                {/* Colored top accent bar */}
                <div className={`absolute top-0 left-0 right-0 h-1 ${principleColors[index].accent} rounded-t-2xl`} />

                <div className="relative z-10 pt-2">
                  <div className={`inline-flex items-center justify-center w-14 h-14 rounded-2xl ${principleColors[index].light} mb-6`}>
                    <span className="text-2xl font-bold text-gray-400">
                      {step.number}
                    </span>
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
