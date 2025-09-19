import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Header from './components/Header';
import Hero from './components/Hero';
import HomeSections from './components/HomeSections';
import AiTool from './pages/AiTool';
import BestPractices from './pages/BestPractices';
import Videos from './pages/Videos';
import VideoDetail from './pages/VideoDetail';
import styles from './App.module.css';

// MUI
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { useState, useMemo, useEffect } from 'react';
import CssBaseline from '@mui/material/CssBaseline';

function makeTheme(mode) {
  return createTheme({
    palette: {
      mode,
      primary: { main: mode === 'dark' ? '#ffffff' : '#000000' },
      secondary: { main: '#d1d1d6' },
      background: { default: mode === 'dark' ? '#07070a' : '#ffffff', paper: mode === 'dark' ? '#0b0b0d' : '#f7f7f8' },
      text: { primary: mode === 'dark' ? '#ffffff' : '#0b0b0d', secondary: '#6b6b6f' }
    },
    typography: {
      fontFamily: ['Poppins', 'Inter', 'Open Sans', 'Arial'].join(','),
      button: {
        textTransform: 'none',
        fontWeight: 700
      }
    },
    shape: { borderRadius: 12 }
  });
}

function App() {
  const [mode, setMode] = useState(() => localStorage.getItem('siteMode') || 'dark');

  useEffect(() => {
    localStorage.setItem('siteMode', mode);
  }, [mode]);

  const theme = useMemo(() => makeTheme(mode), [mode]);

  const toggleMode = () => setMode((m) => (m === 'dark' ? 'light' : 'dark'));

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <BrowserRouter>
        <div className={styles.app}>
          <Header mode={mode} onToggleTheme={toggleMode} />
          <Routes>
            <Route path="/" element={<div className={styles.page + ' backgroundImagePage'}>
              <Hero />
              <HomeSections />
            </div>} />
            <Route path="/ai-tool" element={<AiTool />} />
            <Route path="/best-practices" element={<BestPractices />} />
            <Route path="/videos/:topic" element={<Videos />} />
            <Route path="/watch/:topic/:index" element={<VideoDetail />} />
          </Routes>
        </div>
      </BrowserRouter>
    </ThemeProvider>
  );
}

export default App;
