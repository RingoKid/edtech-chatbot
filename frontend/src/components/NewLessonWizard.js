import React, { useEffect, useRef, useState } from 'react';
import styles from './NewLessonWizard.module.css';
import AppButton from './ui/AppButton';

export default function NewLessonWizard({ onClose }) {
  const [step, setStep] = useState(1);
  const [title, setTitle] = useState('');
  const [ageGroup, setAgeGroup] = useState('4-5');
  const [objective, setObjective] = useState('');
  const firstInputRef = useRef(null);

  useEffect(() => {
    // focus the first input when the modal opens
    if (firstInputRef.current) firstInputRef.current.focus();
    const onKey = (e) => {
      if (e.key === 'Escape') onClose?.();
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [onClose]);

  function next() {
  if (step === 1 && (!title.trim() || !objective.trim())) return;
    setStep((s) => Math.min(2, s + 1));
  }

  function back() {
    setStep((s) => Math.max(1, s - 1));
  }

  function handleSubmit(e) {
    e.preventDefault();
    // placeholder: would call an API or generate content
    // For now we just close and could pass the form data up
    console.log('New lesson', { title, ageGroup, objective });
    onClose?.();
  }

  return (
    <div className={styles.backdrop} onMouseDown={onClose} role="dialog" aria-modal="true">
      <div className={styles.modal} onMouseDown={(e) => e.stopPropagation()}>
        <header className={styles.header}>
          <h3>New Lesson Wizard</h3>
          <AppButton variantStyle="ghost" onClick={onClose} sx={{ minWidth: 40, height: 36, lineHeight: 1, fontSize: 18 }} aria-label="Close">×</AppButton>
        </header>

        <form className={styles.form} onSubmit={handleSubmit}>
          {step === 1 && (
            <div className={styles.step}>
              <label>
                Lesson title
                <input
                  ref={firstInputRef}
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="e.g. Morning Writing: Describing Pictures"
                />
              </label>

              <label>
                Age group
                <select value={ageGroup} onChange={(e) => setAgeGroup(e.target.value)}>
                  <option value="3-4">3–4</option>
                  <option value="4-5">4–5</option>
                  <option value="5-6">5–6</option>
                </select>
              </label>

              <label>
                Lesson objective (1–2 lines)
                <textarea
                  rows={3}
                  value={objective}
                  onChange={(e) => setObjective(e.target.value)}
                  placeholder="Students will practice using descriptive words to write a short sentence."
                />
              </label>

              <div className={styles.controls}>
                <AppButton onClick={next} variantStyle="primary" disabled={!title.trim() || !objective.trim()}>Next</AppButton>
              </div>
            </div>
          )}

          {step === 2 && (
            <div className={styles.step}>
              <h4>Preview</h4>
              <div className={styles.previewCard}>
                <strong>{title || 'Untitled lesson'}</strong>
                <div className={styles.meta}>Age: {ageGroup}</div>
                <p>{objective || 'No objective provided yet.'}</p>
              </div>

              <div className={styles.controls}>
                <AppButton onClick={back} variantStyle="ghost">Back</AppButton>
                <AppButton type="submit" variantStyle="primary" sx={{ ml: 2 }}>Create Lesson</AppButton>
              </div>
            </div>
          )}
        </form>
      </div>
    </div>
  );
}
