const S3_BASE_URL = 'https://l4c-videos.s3.amazonaws.com/videos/'

const encodeVideoUrl = (filename) => S3_BASE_URL + encodeURIComponent(filename)

// TRANSCRIPTION (Handwriting & Spelling) - 10 Practices
export const transcriptionVideos = [
  {
    id: 'hold-pencil-correctly',
    title: 'Hold Pencil Correctly',
    description: 'Teach the proper way to hold a pencil.',
    videos: [
      { url: encodeVideoUrl('hold pen 2.mp4'), label: 'Demonstration 1' },
      { url: encodeVideoUrl('Hold Pencil2.mp4'), label: 'Demonstration 2' }
    ]
  },
  {
    id: 'directionality',
    title: 'Directionality',
    description: 'Support writing within lines from left to right.',
    videos: [
      { url: encodeVideoUrl('Directionality Left to Right.mp4'), label: 'Left to Right' },
      { url: encodeVideoUrl('Directionality 2 (1).mp4'), label: 'Practice Example' }
    ]
  },
  {
    id: 'pronounce-identify-isolate-phonemes',
    title: 'Pronounce, Identify, & Isolate Phonemes',
    description: 'Help children pronounce, identify, and isolate phonemes correctly.',
    videos: [
      { url: encodeVideoUrl('Correct Pronunciation.mp4'), label: 'Correct Pronunciation' },
      { url: encodeVideoUrl('sound iso.mp4'), label: 'Sound Isolation' }
    ]
  },
  {
    id: 'sequenced-segmentation',
    title: 'Sequenced Segmentation',
    description: 'Have children pull apart the individual sounds in spoken words in a systematic sequence from easier to more complex forms.',
    videos: [
      { url: encodeVideoUrl('Sequenced Segmentation.mp4'), label: 'Demonstration 1' },
      { url: encodeVideoUrl('Sequenced Segmentation 2.mp4'), label: 'Demonstration 2' }
    ]
  },
  {
    id: 'correct-letter-sequence-strokes',
    title: 'Correct Letter Sequence of Strokes',
    description: 'Teach how to form each letter representing a phoneme step by step, showing the exact order and direction of the strokes.',
    videos: [
      { url: encodeVideoUrl('strokes.mp4'), label: 'Strokes Practice' },
      { url: encodeVideoUrl('Sequence of Strokes.mp4'), label: 'Sequence Demo' }
    ]
  },
  {
    id: 'compare-contrast-letter-forms',
    title: 'Compare and Contrast Letter Forms',
    description: 'Talk with children about how letters look—compare their shapes and the strokes used to write them.',
    videos: [
      { url: encodeVideoUrl('comp graph.mp4'), label: 'Compare Graphemes' }
    ]
  },
  {
    id: 'retrieve-connect-phoneme-grapheme',
    title: 'Retrieve and Connect Phoneme-Grapheme Patterns',
    description: 'Have children retrieve prior phoneme-grapheme knowledge and connect to new phoneme-grapheme patterns.',
    videos: [
      { url: encodeVideoUrl('Review Phoneme-Grapheme (1).mp4'), label: 'Review Practice' }
    ]
  },
  {
    id: 'apply-phoneme-grapheme-patterns',
    title: 'Apply Phoneme Grapheme Patterns',
    description: 'Cue children to apply phoneme-grapheme patterns during activities.',
    videos: [
      { url: encodeVideoUrl('phoneme grapgheme pattern.mp4'), label: 'Pattern Application' }
    ]
  },
  {
    id: 'corrective-feedback',
    title: 'Corrective Feedback',
    description: 'Provide corrective and confirmatory feedback explaining what part is incorrect and showing them how to fix it.',
    videos: [
      { url: encodeVideoUrl('corrective feedback.mp4'), label: 'Feedback Example' }
    ]
  },
  {
    id: 'encourage-invented-spelling',
    title: 'Encourage Invented Spelling',
    description: "Encourage children to use what they've learned about sounds, spelling patterns, and word parts to try spelling new words—even if they're not sure (invented spelling).",
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
    title: 'Transcription',
    route: '/handwriting-spelling',
    description: [
      'To transcribe language into text, children coordinate phoneme–grapheme correspondences with the motor processes required for handwriting and spelling. Instructional targets include letter knowledge, accurate letter formation, phonemic awareness, sound–letter correspondences, directionality, and print conventions.',
      'The following practices help teachers optimize instruction to strengthen children\'s recall and written production of sound–letter correspondences, supporting their ability to write words and sentences with increasing accuracy and fluency.'
    ]
  },
  'language-construction': {
    title: 'Language Construction',
    route: '/vocabulary-syntax',
    description: 'These practices help children develop syntax, vocabulary, and morphology, enabling them to build language more fluidly.'
  },
  'idea-generation': {
    title: 'Idea Generation & Organization',
    route: '/idea-generation',
    description: 'These practices help children recall concepts and understand genre features, supporting them in developing and organizing ideas effectively.'
  }
}
