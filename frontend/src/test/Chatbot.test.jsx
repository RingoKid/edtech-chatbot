import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import Chatbot from '../components/Chatbot'

// Mock the API module
vi.mock('../api', () => ({
  chat: {
    send: vi.fn(() => Promise.resolve({ reply: 'Test response', thread_id: 'test-thread' }))
  },
  createChatWsClient: vi.fn(() => ({
    connect: vi.fn(() => Promise.resolve()),
    subscribe: vi.fn(() => () => {}),
    send: vi.fn(),
    close: vi.fn(),
    isConnected: vi.fn(() => false)
  }))
}))

describe('Chatbot Component', () => {
  it('renders initial welcome message', () => {
    render(<Chatbot />)
    expect(screen.getByText(/Hello! I'm your AI Teaching Assistant/)).toBeInTheDocument()
  })

  it('allows user to type and send messages', async () => {
    const user = userEvent.setup()
    render(<Chatbot />)
    
    const input = screen.getByPlaceholderText(/Ask about lesson planning, student assessment, classroom management.../i)
    const sendButton = screen.getByRole('button', { name: /send message/i })
    
    await user.type(input, 'Test message')
    expect(input.value).toBe('Test message')
    
    await user.click(sendButton)
    
    // Check that user message appears
    expect(screen.getByText('Test message')).toBeInTheDocument()
  })

  it('processes messages correctly with API response', async () => {
    const user = userEvent.setup()
    render(<Chatbot />)
    
    const input = screen.getByPlaceholderText(/Ask about lesson planning, student assessment, classroom management.../i)
    const sendButton = screen.getByRole('button', { name: /send message/i })
    
    await user.type(input, 'Test message')
    await user.click(sendButton)
    
    // Check that both user message and bot response appear
    expect(screen.getByText('Test message')).toBeInTheDocument()
    await waitFor(() => {
      expect(screen.getByText('Test response')).toBeInTheDocument()
    })
  })

  it('prevents sending empty messages', async () => {
    const user = userEvent.setup()
    render(<Chatbot />)
    
    const sendButton = screen.getByRole('button', { name: /send message/i })
    
    // Initially only welcome message
    expect(screen.getAllByText(/Hello! I'm your AI Teaching Assistant/)).toHaveLength(1)
    
    await user.click(sendButton)
    
    // Should still only have welcome message
    expect(screen.getAllByText(/Hello! I'm your AI Teaching Assistant/)).toHaveLength(1)
  })

  it('handles Enter key to send message', async () => {
    const user = userEvent.setup()
    render(<Chatbot />)
    
    const input = screen.getByPlaceholderText(/Ask about lesson planning, student assessment, classroom management.../i)
    
    await user.type(input, 'Test message{enter}')
    
    // Check that user message appears
    expect(screen.getByText('Test message')).toBeInTheDocument()
  })
})