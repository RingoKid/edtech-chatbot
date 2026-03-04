import React from 'react'
import { Outlet, useLocation } from 'react-router-dom'
import Navigation from '../components/Navigation'
import Footer from '../components/Footer'

const MainLayout = () => {
  const location = useLocation()
  const hideFooter = location.pathname === '/ai-teaching-assistant'

  return (
    <div className="min-h-screen">
      <Navigation />
      <main>
        <Outlet />
      </main>
      {!hideFooter && <Footer />}
    </div>
  )
}

export default MainLayout