import React, { useState, useRef } from 'react'
import { motion } from 'framer-motion'
import { ArrowLeft, Play, VideoOff, SkipBack, SkipForward, Gauge } from 'lucide-react'
import { Link } from 'react-router-dom'
import ReactPlayer from 'react-player'

const VideoPageTemplate = ({
  video,
  category,
  categoryTitle,
  backLink,
  relatedVideos = []
}) => {
  const [activeVideoIndex, setActiveVideoIndex] = useState(0)
  const [playbackRate, setPlaybackRate] = useState(1)
  const playerRef = useRef(null)

  const hasVideos = video.videos && video.videos.length > 0 && !video.noVideoYet
  const hasMultipleVideos = hasVideos && video.videos.length > 1
  const currentVideo = hasVideos ? video.videos[activeVideoIndex] : null

  const playbackRates = [0.5, 0.75, 1, 1.25, 1.5, 2]

  const handleSkip = (seconds) => {
    if (playerRef.current) {
      const currentTime = playerRef.current.currentTime || 0
      playerRef.current.currentTime = Math.max(0, currentTime + seconds)
    }
  }

  const handlePlaybackRateChange = (rate) => {
    setPlaybackRate(rate)
    if (playerRef.current) {
      playerRef.current.playbackRate = rate
    }
  }

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
              to={backLink}
              className="inline-flex items-center text-primary-600 hover:text-primary-700 font-medium mb-8 transition-colors"
            >
              <ArrowLeft className="w-5 h-5 mr-2" />
              Back to {categoryTitle}
            </Link>
          </motion.div>
        </div>
      </div>

      {/* Main Content */}
      <section className="section-padding pt-0 pb-12">
        <div className="container">
          <div className="max-w-4xl mx-auto">
            {/* Title */}
            <motion.h1
              className="text-3xl sm:text-4xl lg:text-5xl font-bold font-display mb-4 text-gray-900"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6 }}
            >
              {video.title}
            </motion.h1>

            {/* Description */}
            <motion.p
              className="text-lg text-gray-600 mb-8"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.1 }}
            >
              {video.description}
            </motion.p>

            {/* Video Player or Placeholder */}
            <motion.div
              className="bg-white rounded-2xl shadow-lg overflow-hidden mb-4"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.2 }}
            >
              {hasVideos ? (
                <div className="aspect-video bg-black">
                  <ReactPlayer
                    ref={playerRef}
                    src={currentVideo.url}
                    controls
                    playbackRate={playbackRate}
                    width="100%"
                    height="100%"
                    style={{ aspectRatio: '16/9' }}
                  />
                </div>
              ) : (
                <div className="aspect-video bg-gradient-to-br from-gray-100 to-gray-200 flex flex-col items-center justify-center text-gray-500">
                  <VideoOff className="w-16 h-16 mb-4 text-gray-400" />
                  <p className="text-xl font-medium">Video Coming Soon</p>
                  <p className="text-sm mt-2">We're working on adding this content.</p>
                </div>
              )}
            </motion.div>

            {/* Custom Video Controls */}
            {hasVideos && (
              <motion.div
                className="bg-white rounded-xl shadow-md border border-gray-200 p-4 mb-6"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 0.25 }}
              >
                <div className="flex flex-wrap items-center justify-between gap-4">
                  {/* Skip Controls */}
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-gray-500 mr-2">Skip:</span>
                    <button
                      onClick={() => handleSkip(-10)}
                      className="flex items-center gap-1 px-3 py-1.5 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg transition-colors text-sm font-medium"
                      title="Skip back 10 seconds"
                    >
                      <SkipBack className="w-4 h-4" />
                      10s
                    </button>
                    <button
                      onClick={() => handleSkip(-5)}
                      className="flex items-center gap-1 px-3 py-1.5 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg transition-colors text-sm font-medium"
                      title="Skip back 5 seconds"
                    >
                      <SkipBack className="w-4 h-4" />
                      5s
                    </button>
                    <button
                      onClick={() => handleSkip(5)}
                      className="flex items-center gap-1 px-3 py-1.5 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg transition-colors text-sm font-medium"
                      title="Skip forward 5 seconds"
                    >
                      5s
                      <SkipForward className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => handleSkip(10)}
                      className="flex items-center gap-1 px-3 py-1.5 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg transition-colors text-sm font-medium"
                      title="Skip forward 10 seconds"
                    >
                      10s
                      <SkipForward className="w-4 h-4" />
                    </button>
                  </div>

                  {/* Playback Speed */}
                  <div className="flex items-center gap-2">
                    <Gauge className="w-4 h-4 text-gray-500" />
                    <span className="text-sm text-gray-500">Speed:</span>
                    <div className="flex gap-1">
                      {playbackRates.map((rate) => (
                        <button
                          key={rate}
                          onClick={() => handlePlaybackRateChange(rate)}
                          className={`px-2 py-1 rounded text-sm font-medium transition-colors ${
                            playbackRate === rate
                              ? 'bg-primary-600 text-white'
                              : 'bg-gray-100 hover:bg-gray-200 text-gray-700'
                          }`}
                        >
                          {rate}x
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              </motion.div>
            )}

            {/* Video Selector Buttons */}
            {hasMultipleVideos && (
              <motion.div
                className="flex flex-wrap gap-3 mb-8"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 0.3 }}
              >
                <span className="text-sm text-gray-500 self-center mr-2">Videos:</span>
                {video.videos.map((v, index) => (
                  <button
                    key={index}
                    onClick={() => setActiveVideoIndex(index)}
                    className={`px-4 py-2 rounded-lg font-medium transition-all duration-200 ${
                      activeVideoIndex === index
                        ? 'bg-primary-600 text-white shadow-md'
                        : 'bg-white text-gray-700 border border-gray-200 hover:border-primary-300 hover:text-primary-600'
                    }`}
                  >
                    <Play className="w-4 h-4 inline mr-2" />
                    {v.label}
                  </button>
                ))}
              </motion.div>
            )}
          </div>
        </div>
      </section>

      {/* Related Videos Section */}
      {relatedVideos.length > 0 && (
        <section className="section-padding pt-0 pb-20">
          <div className="container">
            <div className="max-w-4xl mx-auto">
              <motion.h2
                className="text-2xl font-bold text-gray-900 mb-6"
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6 }}
              >
                Explore More
              </motion.h2>

              <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {relatedVideos.map((relatedVideo, index) => (
                  <motion.div
                    key={relatedVideo.id}
                    initial={{ opacity: 0, y: 20 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.6, delay: index * 0.1 }}
                  >
                    <Link
                      to={`${backLink}/${relatedVideo.id}`}
                      className="block group bg-white rounded-xl shadow-md border border-gray-200 overflow-hidden hover:shadow-lg transition-all duration-300"
                    >
                      <div className="relative aspect-video bg-gradient-to-br from-primary-100 to-primary-200">
                        {relatedVideo.noVideoYet ? (
                          <div className="absolute inset-0 flex items-center justify-center text-gray-400">
                            <VideoOff className="w-8 h-8" />
                          </div>
                        ) : (
                          <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity duration-300 bg-black/20">
                            <div className="w-12 h-12 bg-white/90 rounded-full flex items-center justify-center shadow-lg">
                              <Play className="w-6 h-6 text-primary-600 ml-0.5" />
                            </div>
                          </div>
                        )}
                      </div>
                      <div className="p-4">
                        <h3 className="font-semibold text-gray-900 group-hover:text-primary-600 transition-colors line-clamp-2">
                          {relatedVideo.title}
                        </h3>
                      </div>
                    </Link>
                  </motion.div>
                ))}
              </div>
            </div>
          </div>
        </section>
      )}
    </div>
  )
}

export default VideoPageTemplate
