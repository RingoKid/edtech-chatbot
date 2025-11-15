import React, { useState } from 'react'
import { useAuth } from '../contexts/AuthContext'
import Login from './Login'
import Signup from './Signup'
import { LogOut } from 'lucide-react'

const ProtectedRoute = ({ children }) => {
  const { isAuthenticated, loading, logout, user } = useAuth()
  const [showSignup, setShowSignup] = useState(false)

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-gray-600">Loading...</p>
        </div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
        <div className="w-full max-w-md">
          {showSignup ? (
            <Signup onSwitchToLogin={() => setShowSignup(false)} />
          ) : (
            <Login onSwitchToSignup={() => setShowSignup(true)} />
          )}
        </div>
      </div>
    )
  }

  return (
    <div>
      {/* Logout button in top right */}
      <div className="fixed top-4 right-4 z-50">
        <button
          onClick={logout}
          className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition-colors flex items-center gap-2 shadow-lg"
          title={`Logged in as ${user?.email || user?.name}`}
        >
          <LogOut className="w-4 h-4" />
          Logout
        </button>
      </div>
      {children}
    </div>
  )
}

export default ProtectedRoute

