import React from 'react'
import { motion } from 'framer-motion'
import { Play, ArrowLeft } from 'lucide-react'
import { Link } from 'react-router-dom'

const IdeaGeneration = () => {
  const videoItems = [
    {
      id: 1,
      title: "Clearly explain the writing topic and its purpose, and identify key features of the genre that support that purpose.",
      description: "Facilitates construction of a mental blueprint for organizing and retrieving relevant ideas related to topic and genre purpose.",
      thumbnail: "/src/assets/images/topicandpurpose.png",
      videoUrl: "https://youtu.be/QUXCkF2ZGRs",
    },
    {
      id: 2,
      title: "Use visuals, read-alouds, and multimedia to help children learn about the topic. These tools support understanding by connecting new information to what children already know, making it easier ",
      description: "Supports creative thinking by prompting comparisons, analogies, and synthesis",
      thumbnail: "/src/assets/images/topicandpurpose.png",
      videoUrl: "https://youtu.be/HZ9SBtU4_3c"
    },
    {
      id: 3,
      title: "Help children connect the writing topic to what they’ve read, learned in the unit, or experienced in real life.",
      description: "Supports ability to distinguish relevant from irrelevant details and identify those that develop a central topic",
      thumbnail: "/src/assets/images/usingq.png",
      videoUrl: "/idea-generation/connector-words",
    },
    {
      id: 4,
      title: "Invite children to share their own experiences related to the topic—things they’ve seen, done, or talked about at school, home, or in their community. ",
      description: "Activates emotional and experiential memory, enhancing idea generation and content richness",
      thumbnail: "/src/assets/images/idea2.png",
      videoUrl: "https://example.com/idea-video4"
    },
    {
      id: 5,
      title: "Model the brainstorming process by thinking out loud. Show children how to come up with ideas by saying your thoughts as you connect the writing topic to personal experiences",
      description: "Strengths fluency through retrieval and consolidation of phoneme-grapheme patterns",
      thumbnail: "/src/assets/images/topicandpurpose.png",
      videoUrl: "https://example.com/idea-video5"
    },
    {
      id: 6,
      title: "Have young children draw their ideas before writing. This helps them clarify what they want to say and supports their memory when turning ideas into written words",
      description: "Supports childrens ability to hold ideas in working memory to clarify and refine ideas in relation to topic",
      thumbnail: "/src/assets/images/topicandpurpose.png",
      videoUrl: "https://youtu.be/BT_ox3OpRLM"
    },
    {
      id: 7,
      title: "Use questions and prompts to help children expand their ideas, clarify their thinking, and revise their language before and during writing.",
      description: "Sustains attention to topic and relevant details while supporting progression from contextualized to decontextualized oral language",
      thumbnail: "/src/assets/images/contentnew.png",
      videoUrl: "https://youtu.be/of4-9NpK2as"
    },
    {
      id: 8,
      title: "Encourage children to orally rehearse their ideas by saying their complete “crafted” sentence aloud before writing.",
      description: "Cements the idea in working memory, supporting transition from oral language to transcription of language in writing",
      thumbnail: "/src/assets/images/drawcontent.png",
      videoUrl: "https://example.com/idea-video8" // video limit reached so will add it later
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
              Idea Organization & Generation
            </h1>
            
            <div className="bg-white rounded-2xl p-8 shadow-lg border border-gray-200">
              <p className="text-lg text-gray-700 leading-relaxed">
                These practices work because they support how the brain retrieves and organizes information for writing
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

export default IdeaGeneration