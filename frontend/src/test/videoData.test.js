import { describe, it, expect } from 'vitest'
import {
  transcriptionVideos,
  languageConstructionVideos,
  ideaGenerationVideos,
  categoryInfo
} from '../data/videoData'

describe('videoData — Transcription practices', () => {
  const expectedOrder = [
    'hold-pencil-correctly',
    'directionality',
    'pronounce-identify-isolate-phonemes',
    'sequenced-segmentation',
    'correct-letter-sequence-strokes',
    'compare-contrast-letter-forms',
    'retrieve-connect-phoneme-grapheme',
    'apply-phoneme-grapheme-patterns',
    'corrective-feedback',
    'encourage-invented-spelling'
  ]

  it('practices are in correct order', () => {
    const ids = transcriptionVideos.map(v => v.id)
    expect(ids).toEqual(expectedOrder)
  })

  it('has 10 practices (9 original + Sequenced Segmentation)', () => {
    expect(transcriptionVideos).toHaveLength(10)
  })

  it('Sequenced Segmentation is at index 3', () => {
    expect(transcriptionVideos[3].id).toBe('sequenced-segmentation')
  })

  it('Sequenced Segmentation has noVideoYet: true and empty videos', () => {
    const ss = transcriptionVideos[3]
    expect(ss.noVideoYet).toBe(true)
    expect(ss.videos).toEqual([])
  })

  it('all Transcription descriptions match doc', () => {
    const expectedDescriptions = {
      'hold-pencil-correctly': 'Teach the proper way to hold a pencil.',
      'directionality': 'Support writing within lines from left to right.',
      'pronounce-identify-isolate-phonemes': 'Help children pronounce, identify, and isolate phonemes correctly.',
      'sequenced-segmentation': 'Have children pull apart the individual sounds in spoken words in a systematic sequence from easier to more complex forms.',
      'correct-letter-sequence-strokes': 'Teach how to form each letter representing a phoneme step by step, showing the exact order and direction of the strokes.',
      'compare-contrast-letter-forms': 'Talk with children about how letters look\u2014compare their shapes and the strokes used to write them.',
      'retrieve-connect-phoneme-grapheme': 'Have children retrieve prior phoneme-grapheme knowledge and connect to new phoneme-grapheme patterns.',
      'apply-phoneme-grapheme-patterns': 'Cue children to apply phoneme-grapheme patterns during activities.',
      'corrective-feedback': 'Provide corrective and confirmatory feedback explaining what part is incorrect and showing them how to fix it.',
      'encourage-invented-spelling': "Encourage children to use what they've learned about sounds, spelling patterns, and word parts to try spelling new words\u2014even if they're not sure (invented spelling)."
    }

    transcriptionVideos.forEach(v => {
      expect(v.description).toBe(expectedDescriptions[v.id])
    })
  })
})

describe('videoData — Category metadata', () => {
  it('categoryInfo.transcription.title is "Transcription"', () => {
    expect(categoryInfo.transcription.title).toBe('Transcription')
  })

  it('categoryInfo language-construction title is "Language Construction"', () => {
    expect(categoryInfo['language-construction'].title).toBe('Language Construction')
  })

  it('categoryInfo.transcription.description is a two-element array', () => {
    expect(Array.isArray(categoryInfo.transcription.description)).toBe(true)
    expect(categoryInfo.transcription.description).toHaveLength(2)
  })

  it('each paragraph of Transcription description starts with expected text', () => {
    expect(categoryInfo.transcription.description[0]).toMatch(/^To transcribe language into text/)
    expect(categoryInfo.transcription.description[1]).toMatch(/^The following practices/)
  })
})

describe('videoData — Cross-category integrity', () => {
  it('all practices with videos have valid S3 URLs', () => {
    const allVideos = [
      ...transcriptionVideos,
      ...languageConstructionVideos,
      ...ideaGenerationVideos
    ]
    allVideos.forEach(practice => {
      practice.videos.forEach(v => {
        expect(v.url).toMatch(/^https:\/\/l4c-videos\.s3\.amazonaws\.com\/videos\//)
      })
    })
  })

  it('no duplicate practice IDs across all categories', () => {
    const allIds = [
      ...transcriptionVideos,
      ...languageConstructionVideos,
      ...ideaGenerationVideos
    ].map(v => v.id)
    expect(new Set(allIds).size).toBe(allIds.length)
  })
})
