import { useRef, useCallback, useState, useEffect } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

const RETRY_INTERVAL_MS = 3000
const MAX_RETRIES = 20 // ~60 seconds of retrying

/**
 * Standalone image component with skeleton placeholder + auto-retry.
 * Starts hidden; shows a pulsing skeleton until the image loads.
 * Retries every 3s (up to ~60s) for images that don't exist yet
 * (Gemini is still generating them at the S3 URL).
 */
const LessonImage = ({ src, alt, ...props }) => {
  const [loaded, setLoaded] = useState(false)
  const retryCount = useRef(0)
  const retryTimer = useRef(null)
  const imgRef = useRef(null)

  // Clean up retry timer on unmount
  useEffect(() => {
    return () => clearInterval(retryTimer.current)
  }, [])

  const handleLoad = useCallback(() => {
    clearInterval(retryTimer.current)
    setLoaded(true)
  }, [])

  const handleError = useCallback(() => {
    if (retryTimer.current || retryCount.current >= MAX_RETRIES) return

    retryTimer.current = setInterval(() => {
      retryCount.current++
      if (retryCount.current >= MAX_RETRIES) {
        clearInterval(retryTimer.current)
        return
      }
      if (imgRef.current) {
        imgRef.current.src = src + (src.includes('?') ? '&' : '?') + 't=' + Date.now()
      }
    }, RETRY_INTERVAL_MS)
  }, [src])

  return (
    <span className="block my-3 mx-auto max-w-[300px]">
      <img
        ref={imgRef}
        src={src}
        alt={alt || 'Lesson image'}
        className="max-w-[300px] w-full rounded-lg border border-gray-200 shadow-sm"
        style={{ display: loaded ? 'block' : 'none' }}
        onLoad={handleLoad}
        onError={handleError}
        {...props}
      />
      {!loaded && (
        <span
          className="flex items-center justify-center w-full h-[200px] rounded-lg border border-gray-200 bg-gray-50 animate-pulse"
        >
          <svg className="w-8 h-8 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M2.25 15.75l5.159-5.159a2.25 2.25 0 013.182 0l5.159 5.159m-1.5-1.5l1.409-1.409a2.25 2.25 0 013.182 0l2.909 2.909M3.75 21h16.5A2.25 2.25 0 0022.5 18.75V5.25A2.25 2.25 0 0020.25 3H3.75A2.25 2.25 0 001.5 5.25v13.5A2.25 2.25 0 003.75 21z" />
          </svg>
        </span>
      )}
    </span>
  )
}

const MarkdownRenderer = ({ content, className = '' }) => {
  return (
    <div className={className}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
        // Headings
        h1: ({ node, ...props }) => (
          <h1 className="text-xl font-bold mt-4 mb-2" {...props} />
        ),
        h2: ({ node, ...props }) => (
          <h2 className="text-lg font-bold mt-3 mb-2" {...props} />
        ),
        h3: ({ node, ...props }) => (
          <h3 className="text-base font-bold mt-2 mb-1" {...props} />
        ),

        // Paragraphs
        p: ({ node, ...props }) => (
          <p className="mb-2 last:mb-0" {...props} />
        ),

        // Lists
        ul: ({ node, ...props }) => (
          <ul className="list-disc list-inside mb-2 ml-2 space-y-1" {...props} />
        ),
        ol: ({ node, ...props }) => (
          <ol className="list-decimal list-inside mb-2 ml-2 space-y-1" {...props} />
        ),
        li: ({ node, ...props }) => (
          <li className="ml-2" {...props} />
        ),

        // Code
        code: ({ node, inline, ...props }) =>
          inline ? (
            <code
              className="bg-gray-200 px-1.5 py-0.5 rounded text-sm font-mono"
              {...props}
            />
          ) : (
            <code
              className="block bg-gray-200 p-2 rounded text-sm font-mono my-2 overflow-x-auto"
              {...props}
            />
          ),
        pre: ({ node, ...props }) => (
          <pre className="bg-gray-200 p-2 rounded my-2 overflow-x-auto" {...props} />
        ),

        // Images — skeleton placeholder + auto-retry until loaded
        img: ({ node, src, alt, ...props }) => (
          <LessonImage src={src} alt={alt} {...props} />
        ),

        // Links
        a: ({ node, ...props }) => (
          <a
            className="text-blue-600 hover:text-blue-800 underline"
            target="_blank"
            rel="noopener noreferrer"
            {...props}
          />
        ),

        // Blockquotes — rendered as boxed callouts (Corrective Feedback, Possible words/sounds)
        blockquote: ({ node, ...props }) => (
          <blockquote
            className="border border-gray-300 rounded-md bg-gray-50 px-4 py-3 my-3"
            {...props}
          />
        ),

        // Tables
        table: ({ node, ...props }) => (
          <div className="overflow-x-auto my-2">
            <table className="min-w-full border-collapse border border-gray-300" {...props} />
          </div>
        ),
        thead: ({ node, ...props }) => (
          <thead className="bg-gray-100" {...props} />
        ),
        tbody: ({ node, ...props }) => (
          <tbody {...props} />
        ),
        tr: ({ node, ...props }) => (
          <tr className="border-b border-gray-300" {...props} />
        ),
        th: ({ node, ...props }) => (
          <th className="border border-gray-300 px-3 py-2 text-left font-semibold" {...props} />
        ),
        td: ({ node, ...props }) => (
          <td className="border border-gray-300 px-3 py-2" {...props} />
        ),

        // Horizontal rule
        hr: ({ node, ...props }) => (
          <hr className="my-4 border-gray-300" {...props} />
        ),

        // Strong and emphasis
        strong: ({ node, ...props }) => (
          <strong className="font-bold" {...props} />
        ),
        em: ({ node, ...props }) => (
          <em className="italic" {...props} />
        ),
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  )
}

export default MarkdownRenderer
