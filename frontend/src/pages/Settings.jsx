import React, { useState } from 'react';
import PreferencesForm from '../components/PreferencesForm';
import { Icon } from '../components/ui';

export default function Settings({ studentId = 'S001', studentProfile }) {
  const [savedNotice, setSavedNotice] = useState(false);

  return (
    <div className="page" style={{ maxWidth: 860 }}>
      <div className="page-head">
        <div>
          <span className="eyebrow plain">Preferences & Universal Design</span>
          <h1>Accessibility & Learning Style</h1>
          <p className="muted">
            Preferences apply immediately across explanations, quizzes, and interface typography.
          </p>
        </div>
        <span className="pill green">Live Previews Active</span>
      </div>

      <PreferencesForm
        initial={studentProfile || {}}
        onSaved={() => {
          setSavedNotice(true);
          setTimeout(() => setSavedNotice(false), 3000);
        }}
      />

      {savedNotice && (
        <div className="pill green" style={{ alignSelf: 'flex-start', marginTop: 12 }}>
          Accessibility and explanation preferences saved successfully.
        </div>
      )}
    </div>
  );
}
