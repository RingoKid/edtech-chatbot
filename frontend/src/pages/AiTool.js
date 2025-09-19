import React, { useState } from 'react';
import styles from './AiTool.module.css';
import NewLessonWizard from '../components/NewLessonWizard';
import Chatbot from '../components/Chatbot';
import AppButton from '../components/ui/AppButton';
import AppBubble from '../components/ui/AppBubble';
import Typography from '@mui/material/Typography';

export default function AiTool() {
  const [mode, setMode] = useState('task'); // 'task' or 'brainstorm'
  const [showWizard, setShowWizard] = useState(false);

  return (
    <div className={styles.page + ' backgroundImagePage'}>
      <header className={styles.header}>
        <h1>AI Composition Tool</h1>
        <p className={styles.lead}>Create a classroom-ready lesson in minutes.</p>
      </header>

      <main className={styles.main}>
        <section className={styles.left}>
          <AppBubble sx={{ p: { xs: 4, md: 5 }, minHeight: 140 }}>
            <Typography variant="h6" component="h2">Lesson Wizard</Typography>
            <Typography className={styles.cardLead} variant="body2">A short guided flow helps you craft a lesson quickly — no jargon.</Typography>
            <div className={styles.controlsRow} style={{ marginTop: 18 }}>
              <AppButton variantStyle="primary" onClick={() => setShowWizard(true)}>Start New Lesson</AppButton>
              <AppButton variantStyle="ghost" sx={{ ml: 2 }}>Import Existing</AppButton>
            </div>
          </AppBubble>

          {/* Chatbot bubble immediately below the lesson wizard */}
          <AppBubble sx={{ p: { xs: 3, md: 4 } }}>
            <Chatbot />
          </AppBubble>

          <AppBubble sx={{ p: { xs: 3, md: 4 } }}>
            <Typography variant="subtitle1" component="h3">Recent Lessons</Typography>
            <div className={styles.placeholder}>You don't have any saved lessons yet. Start one to see previews here.</div>
          </AppBubble>
        </section>

        <aside className={styles.right}>
          <AppBubble sx={{ p: { xs: 3, md: 4 } }}>
            <Typography variant="subtitle2" component="h4">Mode</Typography>
            <div className={styles.modeRow} role="radiogroup" aria-label="AI mode" style={{ marginTop: 18 }}>
              <AppButton variantStyle={mode === 'task' ? 'primary' : 'ghost'} onClick={() => setMode('task')}>Task-focused</AppButton>
              <AppButton variantStyle={mode === 'brainstorm' ? 'primary' : 'ghost'} onClick={() => setMode('brainstorm')} sx={{ ml: 2 }}>Brainstorming</AppButton>
            </div>
          </AppBubble>

          <AppBubble sx={{ p: { xs: 3, md: 4 } }}>
            <Typography variant="subtitle2" component="h4">Preview</Typography>
            <div className={styles.preview}>Lesson preview will appear here after generation.</div>
          </AppBubble>
        </aside>
      </main>
  {showWizard && <NewLessonWizard onClose={() => setShowWizard(false)} />}
    </div>
  );
}
