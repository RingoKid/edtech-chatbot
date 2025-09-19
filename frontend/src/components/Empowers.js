import React, { useEffect, useState, useRef, useCallback } from 'react';
import styles from './Empowers.module.css';
import AppBubble from './ui/AppBubble';

export default function Empowers() {
  const slides = [
    {
      heading: 'Build Foundational',
      sub: 'Early Language',
      caption: 'The Science Behind Early Composing Lessons',
      thumb: '/media/hero/slide-1.jpg'
    },
    {
      heading: 'Increases',
      sub: 'Executive Functioning',
      caption: 'The Science Behind Early Composing Lessons',
      thumb: '/media/hero/slide-2.png'
    },
    {
      heading: 'Enhances',
      sub: 'Creativity',
      caption: 'The Science Behind Early Composing Lessons',
      thumb: '/media/hero/slide-3.jpg'
    }
  ];

  const n = slides.length;
  const cloned = [slides[n - 1], ...slides, slides[0]];

  const [index, setIndex] = useState(1);
  const [transitionEnabled, setTransitionEnabled] = useState(true);
  const trackRef = useRef(null);
  const intervalRef = useRef(null);

  const goNext = useCallback(() => {
    setTransitionEnabled(true);
    setIndex(i => i + 1);
  }, []);

  const stopAutoplay = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  }, []);

  const startAutoplay = useCallback(() => {
    stopAutoplay();
    intervalRef.current = setInterval(() => goNext(), 4000);
  }, [goNext, stopAutoplay]);

  useEffect(() => {
    startAutoplay();
    return stopAutoplay;
  }, [startAutoplay, stopAutoplay]);

  useEffect(() => {
    const el = trackRef.current;
    if (!el) return;

    function onEnd(e) {
      if (e.propertyName && e.propertyName !== 'transform') return;
      if (index === n + 1) {
        setTransitionEnabled(false);
        setIndex(1);
      }
      if (index === 0) {
        setTransitionEnabled(false);
        setIndex(n);
      }
    }

    el.addEventListener('transitionend', onEnd);
    return () => el.removeEventListener('transitionend', onEnd);
  }, [index, n]);

  useEffect(() => {
    if (transitionEnabled) return;
    const id = setTimeout(() => setTransitionEnabled(true), 40);
    return () => clearTimeout(id);
  }, [transitionEnabled]);

  // Pause autoplay when page is hidden and resume when visible.
  useEffect(() => {
    function onVisibility() {
      if (document.hidden) {
        stopAutoplay();
      } else {
        // force a tiny reflow/reset to ensure transform is rendered
        // turn off transitions briefly then re-enable
        setTransitionEnabled(false);
        setIndex(i => i);
        setTimeout(() => {
          setTransitionEnabled(true);
          startAutoplay();
        }, 50);
      }
    }

    document.addEventListener('visibilitychange', onVisibility);
    return () => document.removeEventListener('visibilitychange', onVisibility);
  }, [startAutoplay, stopAutoplay]);

  const trackStyle = {
    transform: `translateX(${-index * 100}%)`,
    transition: transitionEnabled ? 'transform 600ms ease' : 'none'
  };

  return (
    <section className={styles.empowers} aria-label="How Language Empowers Teachers">
  <AppBubble sx={{ padding: { xs: 1, md: 2 }, borderRadius: 3, background: 'transparent', border: '1px solid rgba(255,255,255,0.18)', boxShadow: 'none', backdropFilter: 'none' }}>
        <div className={styles.carousel}>
          <div className={styles.viewport}>
            <div ref={trackRef} className={styles.track} style={trackStyle}>
              {cloned.map((s, i) => (
                <div key={i} className={styles.slide}>
                  <div className={styles.slideInner}>
                    <div className={styles.slideText}>
                      <h3>{s.heading}</h3>
                      <h4>{s.sub}</h4>
                      <p className={styles.caption}>{s.caption}</p>
                    </div>
                    <div className={styles.slideThumb}>
                      <img src={s.thumb} alt={s.heading} className={styles.slideImg} />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </AppBubble>
    </section>
  );
}
