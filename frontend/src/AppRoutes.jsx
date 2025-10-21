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
import AdminPortal from './pages/AdminPortal'
import TeachProperWayToHold from './pages/handwriting-spelling/TeachProperWayToHoldPencil.jsx'
import SequenceofStroles from './pages/handwriting-spelling/SequenceofStroles.jsx'
import RetrieveandConnectPatterns from './pages/handwriting-spelling/RetrieveandConnectPatterns.jsx'
import PronounceIdentifyIsolatePhoneme from './pages/handwriting-spelling/PronounceIdentifyIsolatePhoneme.jsx'
import PhonemeGraphemePatterns from './pages/handwriting-spelling/PhonemeGraphemePatterns.jsx'
import InventedSpelling from './pages/handwriting-spelling/InventedSpelling.jsx'
import Directionality from './pages/handwriting-spelling/Directionality.jsx'
import CorrectiveFeedback from './pages/handwriting-spelling/CorrectiveFeedback.jsx'
import CompareContrastLetterForms from './pages/handwriting-spelling/CompareContrastLetterForms.jsx'
import ConnectingWords from './pages/vocabulary/ConnectingWords.jsx'
import SentenceAwareness from './pages/vocabulary/SentenceAwareness.jsx'
import SentenceManipulation from './pages/vocabulary/SentenceManipulation.jsx'
import VocabularySentenceGeneration from './pages/vocabulary/VocabularySentenceGeneration.jsx'
import VocabularySentenceStructures from './pages/vocabulary/VocabularySentenceStructures.jsx'
import VocabularySupport from './pages/vocabulary/VocabularySupport.jsx'
import SentenceBuilding from './pages/vocabulary/SentenceBuilding.jsx'
import CompositionCues from "./pages/vocabulary/CompositionCues.jsx";
import TopicandPurposeExplanation from './pages/idea-generation/TopicandPurposeExplanation.jsx'
import TopicRecall from './pages/idea-generation/TopicRecall.jsx'
import ConnectorWords from './pages/idea-generation/ConnectorWords.jsx'
import ContentIntegration from "./pages/idea-generation/ContentIntegration.jsx";
import CueQuestion from './pages/idea-generation/CueQuestion.jsx'


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
        <Route path="admin" element={<AdminPortal />} />
        
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

        {/* Vocabulary Individual Pages */}
        <Route path="vocabulary/connecting-words" element={<ConnectingWords/>} />
        <Route path="vocabulary/sentence-awareness" element={<SentenceAwareness/>} />
        <Route path="vocabulary/sentence-manipulation" element={<SentenceManipulation/>} />
        <Route path="vocabulary/sentence-generation" element={<VocabularySentenceGeneration/>} />
        <Route path="vocabulary/vocabulary-sentence-structures" element={<VocabularySentenceStructures/>} />
        <Route path="vocabulary/vocabulary-support" element={<VocabularySupport/>} />
        <Route path="vocabulary/sentence-building" element={<SentenceBuilding/>} />
        <Route path="vocabulary/composition-cues" element={<CompositionCues/>} />

        {/* Idea Organisation and Generation Individual Pages */}
        <Route path="idea-generation/topic-purpose" element={<TopicandPurposeExplanation/>} />
        <Route path="idea-generation/topic-recall" element={<TopicRecall/>} />
        <Route path="idea-generation/connector-words" element={<ConnectorWords/>} />
        <Route path="idea-generation/content-integration" element={<ContentIntegration/>} />
        <Route path="idea-generation/cue-question" element={<CueQuestion/>} />




      </Route>
    </Routes>
  )
}

export default AppRoutes