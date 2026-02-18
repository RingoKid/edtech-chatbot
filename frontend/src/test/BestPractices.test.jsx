import { describe, it, expect, beforeAll } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import BestPractices from '../pages/BestPractices'

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

describe('BestPractices page', () => {
  it('page heading renders "Best Practices Modeled"', () => {
    renderWithRouter(<BestPractices />)
    const heading = screen.getByRole('heading', { level: 1 })
    expect(heading).toHaveTextContent('Best Practices Modeled')
  })

  it('categories render in correct order', () => {
    renderWithRouter(<BestPractices />)
    const headings = screen.getAllByRole('heading', { level: 2 })
    const titles = headings.map(h => h.textContent)
    expect(titles).toEqual([
      'Idea Generation & Organization',
      'Language Construction',
      'Transcription'
    ])
  })

  it('intro paragraph mentions composing processes', () => {
    renderWithRouter(<BestPractices />)
    // Terms appear in both the opening paragraph and the bold research paragraph,
    // so use getAllByText and verify at least one match exists.
    expect(screen.getAllByText(/idea generation & organization/i).length).toBeGreaterThanOrEqual(1)
    expect(screen.getAllByText(/language construction/i).length).toBeGreaterThanOrEqual(1)
    expect(screen.getAllByText(/transcription/i).length).toBeGreaterThanOrEqual(1)
  })

  it('research paragraph says "early writing ability"', () => {
    renderWithRouter(<BestPractices />)
    expect(screen.getByText(/early writing ability/)).toBeInTheDocument()
    expect(screen.queryByText(/executive functioning/)).not.toBeInTheDocument()
  })

  it('CTA text matches doc', () => {
    renderWithRouter(<BestPractices />)
    expect(screen.getByText(/Find out the early language and literacy skills/)).toBeInTheDocument()
  })
})
