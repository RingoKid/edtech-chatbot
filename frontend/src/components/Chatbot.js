import React, { useEffect, useRef, useState } from 'react';
import styles from './Chatbot.module.css';
import AppButton from './ui/AppButton';

export default function Chatbot() {
  const [messages, setMessages] = useState([
    { id: 1, role: 'bot', text: 'Hi — I can help you draft a lesson or refine objectives. Ask me anything.' },
  ]);
  const [text, setText] = useState('');
  const fileRef = useRef(null);
  const listRef = useRef(null);
  const textRef = useRef(null);

  // Autosize the textarea so the input grows with content instead of showing an internal scrollbar
  useEffect(() => {
    const el = textRef.current;
    if (!el) return;
    // set to auto to measure
    el.style.height = 'auto';
    el.style.height = el.scrollHeight + 'px';
  }, [text, messages]);

  function send() {
    if (!text.trim()) return;
    const user = { id: Date.now(), role: 'user', text: text.trim() };
    setMessages((m) => [...m, user]);
    setText('');
    // fake bot reply
    setTimeout(() => {
      setMessages((m) => [...m, { id: Date.now() + 1, role: 'bot', text: 'Got it — here is a short suggestion based on your input.' }]);
    }, 700);
  }

  function onKey(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  }

  return (
    <div className={styles.wrapper}>
      <div className={styles.header}>
        <div className={styles.title}>Assistant</div>
        <div className={styles.caption}>Lesson helper</div>
      </div>

      <div className={styles.list} ref={listRef}>
        {messages.map((m) => (
          <div key={m.id} className={m.role === 'user' ? styles.msgUser : styles.msgBot}>
            <div className={styles.msgText}>{m.text}</div>
          </div>
        ))}
      </div>

      <div className={styles.inputRow}>
        <button className={styles.iconBtn} title="Attach file" onClick={() => fileRef.current?.click()}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M16.5 6.5L9.5 13.5C8.7 14.3 7.3 14.3 6.5 13.5C5.7 12.7 5.7 11.3 6.5 10.5L13.5 3.5C15 2 17.5 2 19 3.5C20.5 5 20.5 7.5 19 9L12 16" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round"/></svg>
        </button>
        <input type="file" ref={fileRef} style={{ display: 'none' }} />

        <textarea
          ref={textRef}
          className={styles.input}
          placeholder="Ask the assistant to draft a short activity, objective, or prompt..."
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={onKey}
          rows={1}
        />

        <div className={styles.rightIcons}>
          <button className={styles.iconBtn} title="Camera">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M21 7h-3.2l-1.6-2.4A1 1 0 0 0 15.6 4H8.4a1 1 0 0 0-.6.6L6.2 7H3a1 1 0 0 0-1 1v10a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V8a1 1 0 0 0-1-1z" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round"/>
              <circle cx="12" cy="13" r="3" stroke="currentColor" strokeWidth="1.2" />
            </svg>
          </button>
          <button className={styles.iconBtn} title="Record voice">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M12 15a3 3 0 0 0 3-3V6a3 3 0 0 0-6 0v6a3 3 0 0 0 3 3z" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round"/><path d="M19 11v1a7 7 0 0 1-14 0v-1" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round"/></svg>
          </button>
          <AppButton variantStyle={text.trim() ? 'primary' : 'ghost'} onClick={send} disabled={!text.trim()} sx={{ ml: 1, minWidth: 72 }}>
            Send
          </AppButton>
        </div>
      </div>
    </div>
  );
}
