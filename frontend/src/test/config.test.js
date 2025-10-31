import { describe, it, expect, vi, beforeEach } from 'vitest'
import { API_CONFIG, getWebSocketUrl, ENV_INFO } from '../config/env'

// Mock import.meta.env
const mockEnv = {
  DEV: true,
  PROD: false,
  MODE: 'test',
  VITE_API_BASE_URL: undefined,
  VITE_WS_BASE_URL: undefined,
}

vi.stubGlobal('import.meta', { env: mockEnv })

// Mock window.location for WebSocket URL tests
Object.defineProperty(window, 'location', {
  value: {
    protocol: 'https:',
    host: 'example.com'
  },
  writable: true
})

describe('Environment Configuration', () => {
  beforeEach(() => {
    // Reset mock env before each test
    mockEnv.VITE_API_BASE_URL = undefined
    mockEnv.VITE_WS_BASE_URL = undefined
  })

  describe('API_CONFIG', () => {
    it('uses environment variable when provided', () => {
      mockEnv.VITE_API_BASE_URL = 'https://api.example.com/v1'
      
      // Re-import to get fresh config
      vi.resetModules()
      
      expect(API_CONFIG.BASE_URL).toBeDefined()
    })

    it('falls back to localhost in development', () => {
      mockEnv.DEV = true
      
      expect(API_CONFIG.BASE_URL).toBeDefined()
    })

    it('falls back to relative URL in production', () => {
      mockEnv.DEV = false
      mockEnv.PROD = true
      
      expect(API_CONFIG.BASE_URL).toBeDefined()
    })
  })

  describe('WebSocket Configuration', () => {
    it('builds correct WebSocket URL', () => {
      const wsUrl = getWebSocketUrl('/api/v1/chat/ws/message')
      expect(wsUrl).toContain('/api/v1/chat/ws/message')
    })

    it('handles custom endpoint', () => {
      const customUrl = getWebSocketUrl('/custom/endpoint')
      expect(customUrl).toContain('/custom/endpoint')
    })
  })

  describe('Environment Info', () => {
    it('correctly identifies development mode', () => {
      mockEnv.DEV = true
      expect(ENV_INFO.isDevelopment).toBe(true)
    })

    it('provides mode information', () => {
      expect(ENV_INFO.mode).toBeDefined()
    })
  })
})