import React, { useState } from 'react';
import { Icon } from './ui';

export default function VerificationPanel({ verification, sources }) {
  const [open, setOpen] = useState(false);
  if (!verification) return null;

  return (
    <div className="card col mt8" style={{ gap: 10 }}>
      <div className="row between">
        <div className="row">
          <span className={`pill ${verification.passed ? 'green' : 'amber'}`}>
            {verification.passed ? 'Curriculum Verified' : 'Partly Verified'}
          </span>
          <span className="tiny muted">
            Alignment: {Math.round(verification.grounding_score || 100)}% · {sources?.length || 0} reference slides
          </span>
        </div>
        <button
          type="button"
          className="btn ghost sm"
          onClick={() => setOpen(!open)}
        >
          {open ? 'Hide Details' : 'View Details'}
        </button>
      </div>

      {open && (
        <div className="col mt8" style={{ gap: 6 }}>
          {(sources || []).map((s, i) => (
            <div key={i} className="src">
              <strong>S{i + 1}</strong> · {s.topic || 'Curriculum'}
              <div className="muted tiny">{s.text || s.preview || 'Course curriculum reference'}</div>
            </div>
          ))}
          {verification.issues?.length > 0 && (
            <div className="notice">{verification.issues.join('; ')}</div>
          )}
        </div>
      )}
    </div>
  );
}
