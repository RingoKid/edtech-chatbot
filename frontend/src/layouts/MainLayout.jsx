import React from 'react'
import { Outlet } from 'react-router-dom'
import Navigation from '../components/Navigation'
import Footer from '../components/Footer'
import ChatBubble from '../components/ChatBubble'
import ApiStatus from '../components/ApiStatus'

const MainLayout = () => {
  return (
    <div className="min-h-screen">
      <Navigation />
      <main>
        <Outlet />
      </main>
      <Footer />
      <ChatBubble />
      {import.meta.env.DEV && <ApiStatus />}
    </div>
  )
}

export default MainLayout