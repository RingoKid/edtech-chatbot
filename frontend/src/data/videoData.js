const S3_BASE_URL = 'https://l4c-videos.s3.amazonaws.com/videos/'

const encodeVideoUrl = (filename) => S3_BASE_URL + encodeURIComponent(filename)

// TRANSCRIPTION (Handwriting & Spelling) - 9 Practices
export const transcriptionVideos = [
  {
    id: 'hold-pencil-correctly',
    title: 'Hold Pencil Correctly',
    description: 'Teaching proper pencil grip for comfortable, effective writing.',
    videos: [
      { url: encodeVideoUrl('hold pen 2.mp4'), label: 'Demonstration 1' },
      { url: encodeVideoUrl('Hold Pencil2.mp4'), label: 'Demonstration 2' }
    ]
  },
  {
    id: 'directionality',
    title: 'Directionality',
    description: 'Building left-to-right and top-to-bottom writing habits.',
    videos: [
      { url: encodeVideoUrl('Directionality Left to Right.mp4'), label: 'Left to Right' },
      { url: encodeVideoUrl('Directionality 2 (1).mp4'), label: 'Practice Example' }
    ]
  },
  {
    id: 'pronounce-identify-isolate-phonemes',
    title: 'Pronounce, Identify, & Isolate Phonemes',
    description: 'Helping children hear and distinguish individual sounds in words.',
    videos: [
      { url: encodeVideoUrl('Correct Pronunciation.mp4'), label: 'Correct Pronunciation' },
      { url: encodeVideoUrl('sound iso.mp4'), label: 'Sound Isolation' }
    ]
  },
  {
    id: 'correct-letter-sequence-strokes',
    title: 'Correct Letter Sequence of Strokes',
    description: 'Teaching the proper order of strokes for forming letters.',
    videos: [
      { url: encodeVideoUrl('strokes.mp4'), label: 'Strokes Practice' },
      { url: encodeVideoUrl('Sequence of Strokes.mp4'), label: 'Sequence Demo' }
    ]
  },
  {
    id: 'compare-contrast-letter-forms',
    title: 'Compare and Contrast Letter Forms',
    description: 'Helping children distinguish between similar-looking letters.',
    videos: [
      { url: encodeVideoUrl('comp graph.mp4'), label: 'Compare Graphemes' }
    ]
  },
  {
    id: 'retrieve-connect-phoneme-grapheme',
    title: 'Retrieve and Connect Phoneme-Grapheme Patterns',
    description: 'Strengthening the connection between sounds and their written forms.',
    videos: [
      { url: encodeVideoUrl('Review Phoneme-Grapheme (1).mp4'), label: 'Review Practice' }
    ]
  },
  {
    id: 'apply-phoneme-grapheme-patterns',
    title: 'Apply Phoneme Grapheme Patterns',
    description: 'Practicing the application of sound-letter patterns in writing.',
    videos: [
      { url: encodeVideoUrl('phoneme grapgheme pattern.mp4'), label: 'Pattern Application' }
    ]
  },
  {
    id: 'corrective-feedback',
    title: 'Corrective Feedback',
    description: 'Providing effective feedback to improve spelling and handwriting.',
    videos: [
      { url: encodeVideoUrl('corrective feedback.mp4'), label: 'Feedback Example' }
    ]
  },
  {
    id: 'encourage-invented-spelling',
    title: 'Encourage Invented Spelling',
    description: 'Supporting early spelling attempts to build confidence and phonemic awareness.',
    videos: [
      { url: encodeVideoUrl('Encourage Invented Spelling.mp4'), label: 'Invented Spelling' }
    ]
  }
]

// LANGUAGE CONSTRUCTION (Vocabulary & Syntax) - 5 Practices
export const languageConstructionVideos = [
  {
    id: 'embed-vocabulary-sentence-generation',
    title: 'Embed Vocabulary into Sentence Generation',
    description: 'Helping children use new vocabulary words in their own sentences.',
    videos: [
      { url: encodeVideoUrl('Retrieve Vocabulary in Sentence Building.mp4'), label: 'Sentence Building' },
      { url: encodeVideoUrl('Retrieve Vocabulary 2.mp4'), label: 'Vocabulary Practice' }
    ]
  },
  {
    id: 'build-vocabulary-depth-word-choice',
    title: 'Build Vocabulary Depth to Support Word Choice',
    description: 'Expanding vocabulary through categorization and word connections.',
    videos: [
      { url: encodeVideoUrl('Categorize Words.mp4'), label: 'Categorize Words' },
      { url: encodeVideoUrl('Word Choice.mp4'), label: 'Word Choice' }
    ]
  },
  {
    id: 'connecting-words',
    title: 'Connecting Words',
    description: 'Teaching transition words and conjunctions to connect ideas.',
    noVideoYet: true,
    videos: []
  },
  {
    id: 'build-sentence-awareness',
    title: 'Build Sentence Awareness',
    description: 'Developing understanding of sentence structure with nouns and verbs.',
    videos: [
      { url: encodeVideoUrl('Sentence Structure Nouns and Verbs.mp4'), label: 'Nouns and Verbs' }
    ]
  },
  {
    id: 'build-sentence-manipulation',
    title: 'Build Sentence Manipulation',
    description: 'Practicing rearranging, combining, and expanding sentences.',
    videos: [
      { url: encodeVideoUrl('Build Sentence Manipulation.mp4'), label: 'Sentence Manipulation' }
    ]
  }
]

// IDEA GENERATION & ORGANIZATION - 9 Practices
export const ideaGenerationVideos = [
  {
    id: 'define-topic-purpose',
    title: 'Define Topic & Purpose',
    description: 'Clearly explaining the writing topic and its purpose.',
    videos: [
      { url: encodeVideoUrl('Define Topic & Purpose.mp4'), label: 'Topic & Purpose' }
    ]
  },
  {
    id: 'features-of-genre',
    title: 'Features of Genre',
    description: 'Identifying key features that support the purpose of different genres.',
    videos: [
      { url: encodeVideoUrl('relevant details.mp4'), label: 'Relevant Details' },
      { url: encodeVideoUrl('Fact vs Fantasy.mp4'), label: 'Fact vs Fantasy' }
    ]
  },
  {
    id: 'recall-information-topic',
    title: 'Recall Information Related to a Topic',
    description: 'Helping children retrieve and connect prior knowledge to writing topics.',
    videos: [
      { url: encodeVideoUrl('writing be4 drawing.mp4'), label: 'Writing Before Drawing' }
    ]
  },
  {
    id: 'connect-unit-concepts',
    title: 'Connect to Unit Concepts',
    description: 'Linking writing topics to broader unit themes and learning.',
    videos: [
      { url: encodeVideoUrl('Connect to Unit Topics.mp4'), label: 'Unit Connections' }
    ]
  },
  {
    id: 'model-support-genre-features',
    title: 'Model & Support Application of Genre Features',
    description: 'Demonstrating how to apply genre-specific features in writing.',
    noVideoYet: true,
    videos: []
  },
  {
    id: 'draw-together-cueing-content',
    title: 'Draw Together Cueing Content',
    description: 'Using drawing as a tool to generate and organize writing ideas.',
    videos: [
      { url: encodeVideoUrl('writing be4 drawing.mp4'), label: 'Writing Before Drawing' },
      { url: encodeVideoUrl('dbe4 write 2.mp4'), label: 'Draw Before Write' }
    ]
  },
  {
    id: 'oral-rehearsal-ideas',
    title: 'Oral Rehearsal of Ideas',
    description: 'Encouraging children to say their sentences aloud before writing.',
    videos: [
      { url: encodeVideoUrl('Oral Rehearsal.mp4'), label: 'Oral Rehearsal' }
    ]
  },
  {
    id: 'question-cue-elaboration',
    title: 'Question to Cue Elaboration',
    description: 'Using questions to help children expand and clarify their ideas.',
    videos: [
      { url: encodeVideoUrl('using qs.mp4'), label: 'Using Questions' }
    ]
  },
  {
    id: 'revise-linguistic-structural-features',
    title: 'Revise to Apply Linguistic & Structural Features',
    description: 'Teaching revision strategies to improve writing structure and language.',
    videos: [
      { url: encodeVideoUrl('Fact vs Fantasy.mp4'), label: 'Fact vs Fantasy' }
    ]
  }
]

// Helper functions
export const getVideoById = (id) => {
  const allVideos = [
    ...transcriptionVideos,
    ...languageConstructionVideos,
    ...ideaGenerationVideos
  ]
  return allVideos.find(video => video.id === id)
}

export const getRelatedVideos = (currentId, category, limit = 3) => {
  let categoryVideos
  switch (category) {
    case 'transcription':
      categoryVideos = transcriptionVideos
      break
    case 'language-construction':
      categoryVideos = languageConstructionVideos
      break
    case 'idea-generation':
      categoryVideos = ideaGenerationVideos
      break
    default:
      categoryVideos = []
  }
  return categoryVideos
    .filter(video => video.id !== currentId)
    .slice(0, limit)
}

// Category metadata
export const categoryInfo = {
  transcription: {
    title: 'Handwriting & Spelling',
    route: '/handwriting-spelling',
    description: 'These practices help children strengthen their recall of sound–letter correspondences and develop the skills to segment spoken words into individual phonemes.'
  },
  'language-construction': {
    title: 'Vocabulary & Syntax',
    route: '/vocabulary-syntax',
    description: 'These practices help children develop syntax, vocabulary, and morphology, enabling them to build language more fluidly.'
  },
  'idea-generation': {
    title: 'Idea Generation & Organization',
    route: '/idea-generation',
    description: 'These practices help children recall concepts and understand genre features, supporting them in developing and organizing ideas effectively.'
  }
}
