import React, { createContext, useState, useContext, useEffect } from 'react'

const AuthContext = createContext(null)

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  // Check if user is logged in on mount and validate token
  useEffect(() => {
    const validateSession = async () => {
      const storedUser = localStorage.getItem('admin_user')
      const storedToken = localStorage.getItem('admin_token')
      
      if (storedUser && storedToken) {
        // Verify token is still valid by calling /me endpoint
        try {
          const response = await fetch('/api/v1/auth/me', {
            headers: {
              'Authorization': `Bearer ${storedToken}`
            }
          })
          
          if (response.ok) {
            const userData = await response.json()
            setUser(userData)
          } else {
            // Token invalid, clear storage
            localStorage.removeItem('admin_user')
            localStorage.removeItem('admin_token')
          }
        } catch (err) {
          // Network error, but keep user logged in (token might still be valid)
          setUser(JSON.parse(storedUser))
        }
      }
      setLoading(false)
    }
    
    validateSession()
  }, [])

  const login = async (email, password) => {
    try {
      const response = await fetch('/api/v1/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password }),
      })

      if (response.ok) {
        const data = await response.json()
        // Store JWT token and user data
        localStorage.setItem('admin_token', data.token)
        localStorage.setItem('admin_user', JSON.stringify(data.user))
        setUser(data.user)
        return { success: true }
      } else {
        const errorData = await response.json().catch(() => ({ detail: 'Login failed' }))
        return { success: false, error: errorData.detail || 'Invalid email or password' }
      }
    } catch (err) {
      return { success: false, error: 'Network error. Please check your connection and try again.' }
    }
  }

  const signup = async (email, password, name) => {
    try {
      const response = await fetch('/api/v1/auth/signup', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password, name }),
      })

      if (response.ok) {
        const data = await response.json()
        // Store JWT token and user data
        localStorage.setItem('admin_token', data.token)
        localStorage.setItem('admin_user', JSON.stringify(data.user))
        setUser(data.user)
        return { success: true }
      } else {
        const errorData = await response.json().catch(() => ({ detail: 'Signup failed' }))
        return { success: false, error: errorData.detail || 'Signup failed. Please try again.' }
      }
    } catch (err) {
      return { success: false, error: 'Network error. Please check your connection and try again.' }
    }
  }

  const logout = () => {
    localStorage.removeItem('admin_user')
    localStorage.removeItem('admin_token')
    setUser(null)
  }

  const value = {
    user,
    login,
    signup,
    logout,
    loading,
    isAuthenticated: !!user,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

