import React from "react";
import { Routes, Route, useParams, Navigate } from "react-router-dom";
import MainLayout from "./layouts/MainLayout";
import Home from "./pages/Home";
import BestPractices from "./pages/BestPractices";
import HandwritingSpelling from "./pages/HandwritingSpelling";
import VocabularySyntax from "./pages/VocabularySyntax";
import IdeaGeneration from "./pages/IdeaGeneration";
import AITeachingAssistant from "./pages/AITeachingAssistant";
import VideoPlayer from "./pages/VideoPlayer";
import AuthPortal from "./pages/AuthPortal";
import RequireAuth from "./components/RequireAuth";
import VideoPageTemplate from "./components/VideoPageTemplate";
import {
  transcriptionVideos,
  languageConstructionVideos,
  ideaGenerationVideos,
  getVideoById,
  getRelatedVideos,
  categoryInfo
} from "./data/videoData";

// Dynamic video page wrapper for Handwriting & Spelling
const HandwritingSpellingVideoPage = () => {
  const { videoId } = useParams();
  const video = transcriptionVideos.find(v => v.id === videoId);

  if (!video) {
    return <Navigate to="/handwriting-spelling" replace />;
  }

  return (
    <VideoPageTemplate
      video={video}
      category="transcription"
      categoryTitle={categoryInfo.transcription.title}
      backLink="/handwriting-spelling"
      relatedVideos={getRelatedVideos(videoId, 'transcription', 3)}
    />
  );
};

// Dynamic video page wrapper for Vocabulary & Syntax
const VocabularySyntaxVideoPage = () => {
  const { videoId } = useParams();
  const video = languageConstructionVideos.find(v => v.id === videoId);

  if (!video) {
    return <Navigate to="/vocabulary-syntax" replace />;
  }

  return (
    <VideoPageTemplate
      video={video}
      category="language-construction"
      categoryTitle={categoryInfo['language-construction'].title}
      backLink="/vocabulary-syntax"
      relatedVideos={getRelatedVideos(videoId, 'language-construction', 3)}
    />
  );
};

// Dynamic video page wrapper for Idea Generation
const IdeaGenerationVideoPage = () => {
  const { videoId } = useParams();
  const video = ideaGenerationVideos.find(v => v.id === videoId);

  if (!video) {
    return <Navigate to="/idea-generation" replace />;
  }

  return (
    <VideoPageTemplate
      video={video}
      category="idea-generation"
      categoryTitle={categoryInfo['idea-generation'].title}
      backLink="/idea-generation"
      relatedVideos={getRelatedVideos(videoId, 'idea-generation', 3)}
    />
  );
};

const AppRoutes = () => {
  return (
    <Routes>
      <Route path="/" element={<MainLayout />}>
        <Route index element={<Home />} />
        <Route path="best-practices" element={<BestPractices />} />

        {/* Category listing pages */}
        <Route path="handwriting-spelling" element={<HandwritingSpelling />} />
        <Route path="vocabulary-syntax" element={<VocabularySyntax />} />
        <Route path="idea-generation" element={<IdeaGeneration />} />

        {/* Individual video pages - dynamic routes */}
        <Route path="handwriting-spelling/:videoId" element={<HandwritingSpellingVideoPage />} />
        <Route path="vocabulary-syntax/:videoId" element={<VocabularySyntaxVideoPage />} />
        <Route path="idea-generation/:videoId" element={<IdeaGenerationVideoPage />} />

        {/* Legacy routes - redirect to new paths */}
        <Route path="videos/vocabulary" element={<Navigate to="/vocabulary-syntax" replace />} />
        <Route path="videos/idea-generation" element={<Navigate to="/idea-generation" replace />} />

        {/* Generic video player (legacy) */}
        <Route path="video/:videoId" element={<VideoPlayer />} />

        {/* Auth routes */}
        <Route
          path="ai-teaching-assistant"
          element={
            <RequireAuth>
              <AITeachingAssistant />
            </RequireAuth>
          }
        />
        <Route path="login" element={<AuthPortal />} />
        <Route path="signup" element={<AuthPortal defaultMode="signup" />} />
      </Route>
    </Routes>
  );
};

export default AppRoutes;
