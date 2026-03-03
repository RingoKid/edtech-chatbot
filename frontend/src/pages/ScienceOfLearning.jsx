import React from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Brain, BookOpen, Target, Users, Sparkles, Award, ListOrdered, Rocket } from 'lucide-react'

const cardColors = [
  { border: 'border-l-blue-500', bg: 'from-blue-500 to-blue-600' },
  { border: 'border-l-purple-500', bg: 'from-purple-500 to-purple-600' },
  { border: 'border-l-emerald-500', bg: 'from-emerald-500 to-emerald-600' },
  { border: 'border-l-amber-500', bg: 'from-amber-500 to-amber-600' },
  { border: 'border-l-rose-500', bg: 'from-rose-500 to-rose-600' },
]

const lessonParts = [
  {
    number: 1,
    title: 'Review & Connect',
    icon: Brain,
    description: 'Start with a short review of important prior learning.',
    helpsList: [
      'Remember what they already know',
      'Connect past learning to today\u2019s lesson',
      'Feel prepared for new content',
    ],
    helpsLabel: 'This helps children:',
  },
  {
    number: 2,
    title: 'Model, Explain, Engage',
    icon: BookOpen,
    description: 'This is the teaching part of the lesson.',
    sections: [
      {
        heading: 'You:',
        items: [
          'Clearly explain the new concept or skill',
          'Model your thinking out loud',
          'Give clear definitions',
          'Share examples and non-examples',
        ],
      },
      {
        heading: 'Students:',
        items: [
          'Actively respond',
          'Practice thinking about the new idea',
          'Stay engaged through multiple opportunities to participate',
        ],
      },
    ],
  },
  {
    number: 3,
    title: 'Guided Practice',
    icon: Users,
    description: 'Now students practice \u2014 with your support.',
    sections: [
      {
        heading: 'You:',
        items: [
          'Break the skill into small, manageable steps',
          'Guide students through each step',
          'Provide immediate feedback',
          'Correct misunderstandings right away',
        ],
      },
    ],
    footer: 'The goal is to build accuracy and confidence.',
  },
  {
    number: 4,
    title: 'Application',
    icon: Target,
    description:
      'Students apply the new skill in a slightly different or more challenging situation.',
    sections: [
      {
        heading: 'You continue to:',
        items: [
          'Provide support',
          'Ask guiding questions',
          'Help students transfer their learning',
        ],
      },
    ],
  },
  {
    number: 5,
    title: 'Wrap-Up',
    icon: Award,
    description: 'End the lesson by:',
    helpsList: [
      'Reviewing what students learned',
      'Reinforcing the key idea',
      'Celebrating their effort and progress',
    ],
    footer: 'This helps strengthen learning and builds confidence.',
  },
]

const strategies = [
  { bold: 'Begin with review.', rest: 'Start lessons with brief, routine retrieval practice that builds fluency and gradually increases in complexity over time.' },
  { bold: 'Introduce new learning in small steps.', rest: 'Avoid overwhelming students with too much new information at once.' },
  { bold: 'Sequence instruction intentionally.', rest: 'Plan activities that prepare students for the lesson goal and build toward it step by step.' },
  { bold: 'Model explicitly.', rest: 'Clearly demonstrate new skills or processes, think aloud, and guide students through each step with feedback.' },
  { bold: 'Provide structured practice.', rest: 'Offer ample guided practice before expecting independent work.' },
  { bold: 'Support application and transfer.', rest: 'Give students opportunities to apply new learning in meaningful contexts with continued support.' },
  { bold: 'Keep students actively engaged.', rest: 'Incorporate frequent opportunities to respond so students remain attentive and cognitively involved.' },
]

const ScienceOfLearning = () => {
  return (
    <div className="min-h-screen">
      {/* Hero Section — gradient with dot pattern like HeroSection */}
      <section className="relative overflow-hidden bg-gradient-to-br from-primary-600 via-primary-700 to-secondary-600 text-white pt-28 pb-20">
        {/* Dot pattern overlay */}
        <div className="absolute inset-0 opacity-10">
          <div className="absolute inset-0" style={{
            backgroundImage: 'radial-gradient(circle at 1px 1px, rgba(255, 255, 255, 0.3) 1px, transparent 0)',
            backgroundSize: '50px 50px'
          }} />
        </div>

        {/* Decorative blobs */}
        <div className="absolute -top-24 -right-24 w-96 h-96 bg-white/5 rounded-full blur-3xl" />
        <div className="absolute -bottom-32 -left-32 w-[500px] h-[500px] bg-secondary-500/10 rounded-full blur-3xl" />

        <div className="container relative z-10">
          <motion.div
            className="text-center max-w-4xl mx-auto"
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
          >
            <motion.div
              className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/10 backdrop-blur-sm border border-white/20 text-sm font-medium mb-8"
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.6, delay: 0.2 }}
            >
              <Brain className="w-4 h-4" />
              Evidence-Based Instructional Design
            </motion.div>
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold font-display mb-6 leading-tight">
              The Science of Learning
            </h1>
            <p className="text-xl sm:text-2xl text-white/80 font-light">
              Sequencing a Lesson
            </p>
          </motion.div>
        </div>
      </section>

      {/* Section 1: How Learning Sticks */}
      <section className="py-20 bg-white relative overflow-hidden">
        {/* Subtle background pattern */}
        <div className="absolute top-0 right-0 w-72 h-72 bg-primary-50 rounded-full -translate-y-1/2 translate-x-1/3 blur-3xl" />
        <div className="absolute bottom-0 left-0 w-64 h-64 bg-secondary-50 rounded-full translate-y-1/3 -translate-x-1/4 blur-3xl" />

        <div className="container max-w-4xl mx-auto relative z-10">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            viewport={{ once: true }}
          >
            <div className="flex items-center gap-3 mb-10">
              <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-primary-500 to-primary-700 flex items-center justify-center text-white shadow-lg">
                <Brain className="w-6 h-6" />
              </div>
              <h2 className="text-3xl sm:text-4xl font-bold font-display text-gray-900">
                How Learning Sticks
              </h2>
            </div>

            <div className="space-y-6 text-lg text-gray-600 leading-relaxed">
              <p>
                Learning means developing the ability to retrieve information
                from long-term memory. So how does information get stored in
                long-term memory in the first place?
              </p>
              <p>
                Information is stored when students actively think about it and
                work with it in their working memory. Repeatedly retrieving
                previously learned information and using it in different ways
                — such as comparing, contrasting, connecting, and
                synthesizing — helps strengthen and solidify that learning
                over time.
              </p>
              <p>
                However, teachers must consider potential barriers to this
                process. Students have a limited amount of space in their
                working memory. The younger the child, the more limited that
                space tends to be. Very young children can typically hold only
                2–3 pieces of information in mind at once, and there is
                individual variability, meaning some children can manage more
                information while others can manage less.
              </p>

              {/* Callout box for key concept */}
              <motion.div
                className="bg-amber-50 border-l-4 border-amber-400 rounded-r-xl p-6 my-8"
                initial={{ opacity: 0, x: -20 }}
                whileInView={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.6 }}
                viewport={{ once: true }}
              >
                <p className="text-amber-900 font-medium">
                  Key takeaway: Very young children can typically hold only 2–3
                  pieces of information in mind at once.
                </p>
              </motion.div>
              <p>
                When students are given too much new information or too many
                steps at once — especially if the material is unfamiliar or
                not yet mastered — they may experience <strong>cognitive overload</strong>.
                Cognitive overload occurs when the amount of information exceeds
                a student's working memory capacity, leading to confusion,
                frustration, and interruptions in learning.
              </p>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Section: What Does This Mean for Instruction? */}
      <section className="py-20 bg-gradient-to-b from-gray-50 to-white relative">
        <div className="container max-w-4xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            viewport={{ once: true }}
          >
            <div className="flex items-center gap-3 mb-8">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-secondary-500 to-secondary-700 flex items-center justify-center text-white shadow-lg">
                <ListOrdered className="w-5 h-5" />
              </div>
              <h3 className="text-2xl sm:text-3xl font-bold text-gray-900">
                What Does This Mean for Instruction?
              </h3>
            </div>
            <p className="text-lg text-gray-600 mb-8">
              To support learning and manage cognitive load, teachers should:
            </p>
            <div className="grid gap-4">
              {strategies.map((strategy, index) => (
                <motion.div
                  key={index}
                  className="flex gap-4 items-start bg-white rounded-xl p-5 shadow-sm border border-gray-100 hover:shadow-md transition-shadow duration-200"
                  initial={{ opacity: 0, x: -20 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.4, delay: index * 0.08 }}
                  viewport={{ once: true }}
                >
                  <span className="flex-shrink-0 w-8 h-8 rounded-lg bg-gradient-to-br from-primary-500 to-secondary-500 text-white font-bold text-sm flex items-center justify-center shadow-sm">
                    {index + 1}
                  </span>
                  <p className="text-gray-700 leading-relaxed">
                    <strong className="text-gray-900">{strategy.bold}</strong>{' '}
                    {strategy.rest}
                  </p>
                </motion.div>
              ))}
            </div>
          </motion.div>
        </div>
      </section>

      {/* Section 2: L4C LaunchPad */}
      <section className="py-20 bg-white relative overflow-hidden">
        {/* Background decoration */}
        <div className="absolute top-1/2 right-0 w-96 h-96 bg-primary-50 rounded-full -translate-y-1/2 translate-x-1/2 blur-3xl" />

        <div className="container max-w-5xl mx-auto relative z-10">
          <motion.div
            className="text-center mb-16"
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            viewport={{ once: true }}
          >
            <div className="flex items-center justify-center gap-3 mb-6">
              <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-primary-500 to-secondary-600 flex items-center justify-center text-white shadow-lg">
                <Sparkles className="w-6 h-6" />
              </div>
              <h2 className="text-3xl sm:text-4xl font-bold font-display text-gray-900">
                L4C LaunchPad
              </h2>
            </div>
            <div className="max-w-3xl mx-auto space-y-4 text-lg text-gray-600">
              <p>
                The L4C LaunchPad helps you quickly create lessons using the L4C
                approach and what we know about how children learn best.
              </p>
              <p className="font-medium text-gray-700">Every lesson includes five simple parts:</p>
            </div>
          </motion.div>

          {/* 5 Lesson Parts — colored left borders */}
          <div className="space-y-5">
            {lessonParts.map((part, index) => (
              <motion.div
                key={part.number}
                className={`bg-white rounded-2xl p-8 shadow-md border border-gray-100 border-l-4 ${cardColors[index].border} hover:shadow-lg transition-all duration-300`}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                viewport={{ once: true }}
              >
                <div className="flex items-start gap-5">
                  <div className="flex-shrink-0">
                    <div className={`w-14 h-14 rounded-2xl bg-gradient-to-br ${cardColors[index].bg} flex items-center justify-center text-white shadow-lg`}>
                      <span className="text-2xl font-bold">{part.number}</span>
                    </div>
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-3">
                      <part.icon className="w-5 h-5 text-gray-500" />
                      <h3 className="text-xl font-bold text-gray-900">
                        {part.title}
                      </h3>
                    </div>
                    <p className="text-gray-600 mb-4">{part.description}</p>

                    {part.helpsLabel && (
                      <p className="text-gray-700 font-medium mb-2">
                        {part.helpsLabel}
                      </p>
                    )}

                    {part.helpsList && (
                      <ul className="space-y-1.5 ml-1">
                        {part.helpsList.map((item, i) => (
                          <li
                            key={i}
                            className="text-gray-600 flex items-start gap-2"
                          >
                            <span className="text-primary-400 mt-0.5">&#10003;</span>
                            {item}
                          </li>
                        ))}
                      </ul>
                    )}

                    {part.sections &&
                      part.sections.map((section, si) => (
                        <div key={si} className="mb-3">
                          <p className="text-gray-700 font-medium mb-2">
                            {section.heading}
                          </p>
                          <ul className="space-y-1.5 ml-1">
                            {section.items.map((item, ii) => (
                              <li
                                key={ii}
                                className="text-gray-600 flex items-start gap-2"
                              >
                                <span className="text-primary-400 mt-0.5">
                                  &#10003;
                                </span>
                                {item}
                              </li>
                            ))}
                          </ul>
                        </div>
                      ))}

                    {part.footer && (
                      <p className="text-gray-500 italic mt-3">{part.footer}</p>
                    )}
                  </div>
                </div>
              </motion.div>
            ))}
          </div>

          {/* CTA */}
          <motion.div
            className="text-center mt-16"
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            viewport={{ once: true }}
          >
            <p className="text-gray-500 mb-4">Ready to build your lesson?</p>
            <Link
              to="/ai-teaching-assistant"
              className="inline-flex items-center gap-2 px-10 py-4 bg-gradient-to-r from-primary-600 to-secondary-600 text-white font-semibold text-lg rounded-xl shadow-lg hover:shadow-xl hover:scale-105 transition-all duration-200"
            >
              <Rocket className="w-5 h-5" />
              Open L4C LaunchPad
            </Link>
          </motion.div>
        </div>
      </section>
    </div>
  )
}

export default ScienceOfLearning
