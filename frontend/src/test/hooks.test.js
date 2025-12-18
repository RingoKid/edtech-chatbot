import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useApiCallProtection, useDebounce, useThrottle } from '../hooks/useApiProtection'

describe('API Protection Hooks', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  describe('useApiCallProtection', () => {
    it('prevents rapid repeated calls', async () => {
      const mockApiCall = vi.fn().mockResolvedValue('success')
      const { result } = renderHook(() => useApiCallProtection(mockApiCall, 1000))

      // First call should go through
      await act(async () => {
        const response1 = await result.current('test1')
        expect(response1).toBe('success')
      })

      // Second immediate call should be blocked
      await act(async () => {
        const response2 = await result.current('test2')
        expect(response2).toBe(null)
      })

      expect(mockApiCall).toHaveBeenCalledTimes(1)
    })

    it('allows calls after cooldown period', async () => {
      const mockApiCall = vi.fn().mockResolvedValue('success')
      const { result } = renderHook(() => useApiCallProtection(mockApiCall, 1000))

      // First call
      await act(async () => {
        await result.current('test1')
      })

      // Wait for cooldown
      act(() => {
        vi.advanceTimersByTime(1001)
      })

      // Second call should now be allowed
      await act(async () => {
        const response = await result.current('test2')
        expect(response).toBe('success')
      })

      expect(mockApiCall).toHaveBeenCalledTimes(2)
    })
  })

  describe('useDebounce', () => {
    it('delays function execution', () => {
      const mockFn = vi.fn()
      const { result } = renderHook(() => useDebounce(mockFn, 500))

      act(() => {
        result.current('test')
      })

      expect(mockFn).not.toHaveBeenCalled()

      act(() => {
        vi.advanceTimersByTime(500)
      })

      expect(mockFn).toHaveBeenCalledWith('test')
    })

    it('cancels previous calls when called rapidly', () => {
      const mockFn = vi.fn()
      const { result } = renderHook(() => useDebounce(mockFn, 500))

      act(() => {
        result.current('test1')
        result.current('test2')
        result.current('test3')
      })

      act(() => {
        vi.advanceTimersByTime(500)
      })

      expect(mockFn).toHaveBeenCalledTimes(1)
      expect(mockFn).toHaveBeenCalledWith('test3')
    })
  })

  describe('useThrottle', () => {
    it('limits function calls to specified interval', () => {
      const mockFn = vi.fn()
      const { result } = renderHook(() => useThrottle(mockFn, 1000))

      act(() => {
        result.current('test1')
        result.current('test2')
        result.current('test3')
      })

      expect(mockFn).toHaveBeenCalledTimes(1)
      expect(mockFn).toHaveBeenCalledWith('test1')
    })
  })
})