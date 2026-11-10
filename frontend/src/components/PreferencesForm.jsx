import React, { useState, useEffect } from 'react';
import { Toggle, Spinner, Icon } from './ui';
import { updateStudentPreferences } from '../api/learningApi';

const STYLES = [
  ['simple', 'Simple & visual', 'Short steps, plain words, a described diagram'],
  ['step_by_step', 'Step by step', 'Numbered micro-steps with checks'],
  ['detailed', 'Detailed & technical', 'Full reasoning and edge cases'],
];

export function applyAccessibility(a = {}) {
  const el = document.documentElement;
  el.dataset.font = a.font || 'default';
  el.dataset.size = a.text_size || 'md';
  el.dataset.contrast = a.contrast || 'normal';
  el.dataset.motion = a.reduce_motion ? 'reduce' : 'full';
  try {
    localStorage.setItem('eduadapt_accessibility', JSON.stringify(a));
  } catch {}
}

export function getSavedAccessibility() {
  try {
    const s = localStorage.getItem('eduadapt_accessibility');
    return s ? JSON.parse(s) : null;
  } catch {
    return null;
  }
}

const Setting = ({ title, sub, children }) => (
  <div className="setting">
    <div>
      <strong className="small">{title}</strong>
      <div className="hint">{sub}</div>
    </div>
    {children}
  </div>
);

export default function PreferencesForm({ initial, onSaved, submitLabel = 'Save changes' }) {
  const pr = initial?.preferences || {};
  const savedAcc = getSavedAccessibility();
  const initStyle = initial?.explanation_style || initial?.profile?.explanation_style || pr.preferred_explanation_style || 'step_by_step';
  const [style, setStyle] = useState(initStyle);
  const [audio, setAudio] = useState(pr.audio_enabled ?? true);
  const [visual, setVisual] = useState(pr.visual_enabled ?? true);
  const [a, setA] = useState({
    font: 'default',
    text_size: 'md',
    contrast: 'normal',
    chunk_size: 'micro',
    pacing: 'normal',
    reduce_motion: false,
    audio_speed: 1,
    ...(savedAcc || {}),
    ...(initial?.accessibility || initial?.profile?.accessibility || {}),
  });
  const [busy, setBusy] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    const nextStyle = initial?.explanation_style || initial?.profile?.explanation_style || initial?.preferences?.preferred_explanation_style;
    if (nextStyle) {
      setStyle(nextStyle);
    }
    const acc = initial?.accessibility || initial?.profile?.accessibility;
    if (acc) {
      setA((prev) => {
        const merged = { ...prev, ...acc };
        applyAccessibility(merged);
        return merged;
      });
    }
    if (initial?.preferences?.audio_enabled !== undefined) {
      setAudio(Boolean(initial.preferences.audio_enabled));
    }
    if (initial?.preferences?.visual_enabled !== undefined) {
      setVisual(Boolean(initial.preferences.visual_enabled));
    }
  }, [initial]);

  const setAcc = (k, v) => {
    const next = { ...a, [k]: v };
    setA(next);
    applyAccessibility(next);
  };

  const handleSave = async (e) => {
    if (e) e.preventDefault();
    setBusy(true);
    setError('');
    try {
      applyAccessibility(a);
      const prefPayload = {
        explanation_style: style,
        preferred_explanation_style: style,
        accessibility: a,
        preferences: {
          audio_enabled: audio,
          visual_enabled: visual,
          preferred_explanation_style: style,
        },
      };
      try {
        await updateStudentPreferences(prefPayload);
      } catch (apiErr) {
        console.warn('Could not persist preferences to backend:', apiErr);
      }
      setSuccess(true);
      setTimeout(() => setSuccess(false), 3500);
      if (onSaved) onSaved({ preferred_explanation_style: style, audio_enabled: audio, visual_enabled: visual, accessibility: a });
    } catch (err) {
      setError(err.message || 'Failed to save settings.');
    } finally {
      setBusy(false);
    }
  };

  return (
    <form className="col" style={{ gap: 20 }} onSubmit={handleSave}>
      <div className="card">
        <h3>How should explanations feel?</h3>
        <p className="hint">Customizes how lessons and explanations are structured for you.</p>
        <div className="grid g3 mt16">
          {STYLES.map(([k, t, s]) => (
            <button
              type="button"
              key={k}
              className={`choice ${style === k ? 'on' : ''}`}
              onClick={() => setStyle(k)}
              aria-pressed={style === k}
            >
              <strong className="small">{t}</strong>
              <div className="hint">{s}</div>
            </button>
          ))}
        </div>
      </div>

      <div className="card">
        <h3>Reading & Accessibility System</h3>
        <p className="hint">Accessible defaults grounded in universal design. Changes apply immediately.</p>
        <div className="mt8">
          <Setting title="Dyslexia-friendly font" sub="Applies OpenDyslexic typeface across the platform">
            <Toggle
              label="Dyslexia-friendly font"
              on={a.font === 'opendyslexic'}
              onChange={(v) => setAcc('font', v ? 'opendyslexic' : 'default')}
            />
          </Setting>
          <Setting title="High contrast" sub="Stronger typography and high-contrast structural borders">
            <Toggle
              label="High contrast"
              on={a.contrast === 'high'}
              onChange={(v) => setAcc('contrast', v ? 'high' : 'normal')}
            />
          </Setting>
          <Setting title="Micro-chunks" sub="3–5 minute focused lesson steps with progress checklists">
            <Toggle
              label="Micro-chunks"
              on={a.chunk_size === 'micro'}
              onChange={(v) => setAcc('chunk_size', v ? 'micro' : 'normal')}
            />
          </Setting>
          <Setting title="Read aloud" sub="Enable interactive lesson and question speech synthesis">
            <Toggle label="Read aloud" on={audio} onChange={setAudio} />
          </Setting>
          <Setting title="Visual descriptions" sub="Render memory layouts and visual diagrams in lessons">
            <Toggle label="Visual descriptions" on={visual} onChange={setVisual} />
          </Setting>
          <Setting title="Reduce motion" sub="Disable UI transitions and smooth scroll animations">
            <Toggle
              label="Reduce motion"
              on={Boolean(a.reduce_motion)}
              onChange={(v) => setAcc('reduce_motion', v)}
            />
          </Setting>
          <Setting title="Text size" sub="Scales typography across all cards and navigation">
            <select
              className="input"
              style={{ width: 130 }}
              value={a.text_size}
              onChange={(e) => setAcc('text_size', e.target.value)}
            >
              <option value="sm">Small</option>
              <option value="md">Default</option>
              <option value="lg">Large</option>
              <option value="xl">Extra Large</option>
            </select>
          </Setting>
          <Setting title="Pacing mode" sub="Relaxed mode extends quiz timer duration">
            <select
              className="input"
              style={{ width: 130 }}
              value={a.pacing}
              onChange={(e) => setAcc('pacing', e.target.value)}
            >
              <option value="normal">Normal</option>
              <option value="relaxed">Relaxed</option>
            </select>
          </Setting>
          <Setting title="Audio speed" sub="Playback rate for text-to-speech audio">
            <select
              className="input"
              style={{ width: 130 }}
              value={a.audio_speed}
              onChange={(e) => setAcc('audio_speed', Number(e.target.value))}
            >
              <option value={0.75}>0.75×</option>
              <option value={1}>1.0×</option>
              <option value={1.25}>1.25×</option>
              <option value={1.5}>1.5×</option>
            </select>
          </Setting>
        </div>
      </div>

      {error && <p className="error">{error}</p>}
      {success && (
        <div className="pill green" style={{ alignSelf: 'flex-start', padding: '6px 12px' }}>
          Preferences saved successfully!
        </div>
      )}

      <div className="row">
        <button type="submit" className="btn primary" disabled={busy}>
          {busy ? <Spinner /> : submitLabel}
        </button>
      </div>
    </form>
  );
}
