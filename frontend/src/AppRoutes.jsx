import React from 'react'
import { Routes, Route } from 'react-router-dom'
import MainLayout from './layouts/MainLayout'
import Home from './pages/Home'
import BestPractices from './pages/BestPractices'
import HandwritingSpelling from './pages/HandwritingSpelling'
import VocabularySyntax from './pages/VocabularySyntax'
import IdeaGeneration from './pages/IdeaGeneration'
import AITeachingAssistant from './pages/AITeachingAssistant'
import VideoPlayer from './pages/VideoPlayer'
import TeachProperWayToHold from './pages/handwriting-spelling/TeachProperWayToHoldPencil.jsx'
import SequenceofStroles from './pages/handwriting-spelling/SequenceofStroles.jsx'
import RetrieveandConnectPatterns from './pages/handwriting-spelling/RetrieveandConnectPatterns.jsx'
import PronounceIdentifyIsolatePhoneme from './pages/handwriting-spelling/PronounceIdentifyIsolatePhoneme.jsx'
import PhonemeGraphemePatterns from './pages/handwriting-spelling/PhonemeGraphemePatterns.jsx'
import InventedSpelling from './pages/handwriting-spelling/InventedSpelling.jsx'
import Directionality from './pages/handwriting-spelling/Directionality.jsx'
import CorrectiveFeedback from './pages/handwriting-spelling/CorrectiveFeedback.jsx'
import CompareContrastLetterForms from './pages/handwriting-spelling/CompareContrastLetterForms.jsx'


const AppRoutes = () => {
  return (
    <Routes>
      <Route path="/" element={<MainLayout />}>
        <Route index element={<Home />} />
        <Route path="best-practices" element={<BestPractices />} />
        <Route path="handwriting-spelling" element={<HandwritingSpelling />} />
        <Route path="videos/vocabulary" element={<VocabularySyntax />} />
        <Route path="videos/idea-generation" element={<IdeaGeneration />} />
        <Route path="video/:videoId" element={<VideoPlayer />} />
        <Route path="ai-teaching-assistant" element={<AITeachingAssistant />} />
        
        {/* Handwriting & Spelling Individual Pages */}
        <Route path="handwriting-spelling/proper-way-to-hold" element={<TeachProperWayToHold/>} />
        <Route path="handwriting-spelling/sequence-strokes" element={<SequenceofStroles/>} />
        <Route path="handwriting-spelling/pronounce-identify" element={<PronounceIdentifyIsolatePhoneme/>} />
        <Route path="handwriting-spelling/retrieve-connect" element={<RetrieveandConnectPatterns/>} />
        <Route path="handwriting-spelling/phoneme-graphene" element={<PhonemeGraphemePatterns/>} />
        <Route path="handwriting-spelling/compare-contrast" element={<CompareContrastLetterForms/>} />
        <Route path="handwriting-spelling/invented-spelling" element={<InventedSpelling/>} />
        <Route path="handwriting-spelling/directionality" element={<Directionality/>} />
        <Route path="handwriting-spelling/corrective-feedback" element={<CorrectiveFeedback/>} />

      </Route>
    </Routes>
  )
}

export default AppRoutes