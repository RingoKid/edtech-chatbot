import React from "react";
import { Routes, Route } from "react-router-dom";
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

// Handwriting & Spelling Pages
import MakingLetterFormationAutomatic from "./pages/handwriting-spelling/MakingLetterFormationAutomatic";
import PhonologicalAwarenessActivities from "./pages/handwriting-spelling/PhonologicalAwarenessActivities";
import MultiSensoryWritingApproaches from "./pages/handwriting-spelling/MultiSensoryWritingApproaches";

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

        {/* Handwriting & Spelling Individual Pages */}
        <Route
          path="handwriting-spelling/making-letter-formation-automatic"
          element={<MakingLetterFormationAutomatic />}
        />
        <Route
          path="handwriting-spelling/phonological-awareness-activities"
          element={<PhonologicalAwarenessActivities />}
        />
        <Route
          path="handwriting-spelling/multi-sensory-writing-approaches"
          element={<MultiSensoryWritingApproaches />}
        />
      </Route>
    </Routes>
  );
};

export default AppRoutes;
