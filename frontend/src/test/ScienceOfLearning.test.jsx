import { describe, it, expect, beforeAll } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import ScienceOfLearning from '../pages/ScienceOfLearning'

// framer-motion whileInView uses IntersectionObserver, which jsdom lacks
beforeAll(() => {
  global.IntersectionObserver = class {
    constructor() {}
    observe() {}
    unobserve() {}
    disconnect() {}
  }
})

const renderWithRouter = (ui) =>
  render(<MemoryRouter>{ui}</MemoryRouter>)

describe('ScienceOfLearning page', () => {
  it('page title renders', () => {
    renderWithRouter(<ScienceOfLearning />)
    const heading = screen.getByRole('heading', { level: 1 })
    expect(heading).toHaveTextContent('The Science of Learning')
    expect(screen.getByText('Sequencing a Lesson')).toBeInTheDocument()
  })

  it('"How Learning Sticks" section renders', () => {
    renderWithRouter(<ScienceOfLearning />)
    expect(screen.getByText('How Learning Sticks')).toBeInTheDocument()
  })

  it('all 5 lesson parts render', () => {
    renderWithRouter(<ScienceOfLearning />)
    const expectedParts = [
      'Review & Connect',
      'Model, Explain, Engage',
      'Guided Practice',
      'Application',
      'Wrap-Up',
    ]
    expectedParts.forEach(part => {
      expect(screen.getByText(part)).toBeInTheDocument()
    })
  })

  it('"L4C LaunchPad" section renders', () => {
    renderWithRouter(<ScienceOfLearning />)
    expect(screen.getByText('L4C LaunchPad')).toBeInTheDocument()
  })

  it('instructional strategies list has all 7 items', () => {
    renderWithRouter(<ScienceOfLearning />)
    const expectedPhrases = [
      /Begin with review/,
      /Introduce new learning in small steps/,
      /Sequence instruction intentionally/,
      /Model explicitly/,
      /Provide structured practice/,
      /Support application and transfer/,
      /Keep students actively engaged/,
    ]
    expectedPhrases.forEach(phrase => {
      expect(screen.getByText(phrase)).toBeInTheDocument()
    })
  })
})
