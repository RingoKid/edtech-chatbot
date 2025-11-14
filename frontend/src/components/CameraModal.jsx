import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X, Camera, RotateCcw } from 'lucide-react'
import { cn } from '../utils/cn'

const CameraModal = ({ isOpen, onClose, onCapture }) => {
  const [stream, setStream] = useState(null)
  const [error, setError] = useState(null)
  const [facingMode, setFacingMode] = useState('environment') // 'user' for front camera, 'environment' for back
  const videoRef = useRef(null)
  const canvasRef = useRef(null)

  // Initialize camera when modal opens
  useEffect(() => {
    if (isOpen) {
      startCamera()
    } else {
      stopCamera()
    }

    // Cleanup on unmount
    return () => {
      stopCamera()
    }
  }, [isOpen, facingMode])

  const startCamera = async () => {
    try {
      setError(null)

      // Stop any existing stream first
      stopCamera()

      // Request camera access
      const mediaStream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: facingMode,
          width: { ideal: 1920 },
          height: { ideal: 1080 }
        },
        audio: false
      })

      setStream(mediaStream)

      // Attach stream to video element
      if (videoRef.current) {
        videoRef.current.srcObject = mediaStream
      }
    } catch (err) {
      console.error('Error accessing camera:', err)

      let errorMessage = 'Failed to access camera. Please try again.'
      if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
        errorMessage = 'Camera access denied. Please grant camera permission and try again.'
      } else if (err.name === 'NotFoundError' || err.name === 'DevicesNotFoundError') {
        errorMessage = 'No camera found. Please connect a camera and try again.'
      } else if (err.name === 'NotReadableError' || err.name === 'TrackStartError') {
        errorMessage = 'Camera is already in use by another application.'
      }

      setError(errorMessage)
    }
  }

  const stopCamera = () => {
    if (stream) {
      stream.getTracks().forEach(track => track.stop())
      setStream(null)
    }
  }

  const handleCapture = () => {
    if (!videoRef.current || !canvasRef.current) return

    const video = videoRef.current
    const canvas = canvasRef.current

    // Set canvas dimensions to match video
    canvas.width = video.videoWidth
    canvas.height = video.videoHeight

    // Draw current video frame to canvas
    const context = canvas.getContext('2d')
    context.drawImage(video, 0, 0, canvas.width, canvas.height)

    // Convert canvas to blob
    canvas.toBlob((blob) => {
      if (blob) {
        // Create file from blob
        const file = new File([blob], `photo-${Date.now()}.jpg`, { type: 'image/jpeg' })

        // Call onCapture callback with the file
        onCapture(file)

        // Close modal
        handleClose()
      }
    }, 'image/jpeg', 0.95)
  }

  const handleFlipCamera = () => {
    setFacingMode(prev => prev === 'user' ? 'environment' : 'user')
  }

  const handleClose = () => {
    stopCamera()
    setError(null)
    onClose()
  }

  if (!isOpen) return null

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.9 }}
          className="relative w-full max-w-2xl mx-4 bg-white rounded-lg overflow-hidden shadow-2xl"
        >
          {/* Header */}
          <div className="flex items-center justify-between p-4 bg-gradient-to-r from-purple-500 to-pink-500 text-white">
            <h3 className="font-semibold text-lg">Take Photo</h3>
            <button
              onClick={handleClose}
              className="p-1 hover:bg-white/20 rounded-lg transition-colors"
              title="Close"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Camera view */}
          <div className="relative bg-black aspect-video">
            {error ? (
              <div className="absolute inset-0 flex items-center justify-center p-8">
                <div className="text-center">
                  <p className="text-red-400 mb-4">{error}</p>
                  <button
                    onClick={startCamera}
                    className="px-4 py-2 bg-purple-500 text-white rounded-lg hover:bg-purple-600 transition-colors"
                  >
                    Try Again
                  </button>
                </div>
              </div>
            ) : (
              <>
                <video
                  ref={videoRef}
                  autoPlay
                  playsInline
                  muted
                  className="w-full h-full object-cover"
                />
                {!stream && (
                  <div className="absolute inset-0 flex items-center justify-center">
                    <div className="text-white text-center">
                      <div className="w-12 h-12 border-4 border-white border-t-transparent rounded-full animate-spin mx-auto mb-3"></div>
                      <p>Starting camera...</p>
                    </div>
                  </div>
                )}
              </>
            )}

            {/* Hidden canvas for capturing */}
            <canvas ref={canvasRef} className="hidden" />
          </div>

          {/* Controls */}
          <div className="flex items-center justify-center space-x-4 p-6 bg-gray-50">
            {/* Flip camera button */}
            <button
              onClick={handleFlipCamera}
              disabled={!stream}
              className={cn(
                "p-3 rounded-full transition-colors",
                stream
                  ? "bg-gray-200 text-gray-700 hover:bg-gray-300"
                  : "bg-gray-100 text-gray-400 cursor-not-allowed"
              )}
              title="Flip camera"
            >
              <RotateCcw className="w-5 h-5" />
            </button>

            {/* Capture button */}
            <button
              onClick={handleCapture}
              disabled={!stream}
              className={cn(
                "w-16 h-16 rounded-full transition-all transform hover:scale-105",
                stream
                  ? "bg-purple-500 text-white hover:bg-purple-600 shadow-lg"
                  : "bg-gray-200 text-gray-400 cursor-not-allowed"
              )}
              title="Take photo"
            >
              <Camera className="w-8 h-8 mx-auto" />
            </button>

            {/* Cancel button */}
            <button
              onClick={handleClose}
              className="p-3 rounded-full bg-gray-200 text-gray-700 hover:bg-gray-300 transition-colors"
              title="Cancel"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  )
}

export default CameraModal