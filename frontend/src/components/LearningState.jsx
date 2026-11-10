import React from 'react';
import { Bar } from './ui';

export default function LearningState({ learningState, initialStudent }) {
  const state = learningState?.updated_state || learningState?.simulated_twin || learningState?.initial_state || initialStudent;
  if (!state) return null;

  const masteryVal = state.mastery !== undefined ? Math.round(state.mastery * 100) : 0;
  const accuracyVal = state.accuracy !== undefined ? Math.round(state.accuracy * 100) : 0;

  return (
    <div className="card col" style={{ gap: 12 }}>
      <div className="row between">
        <h3>Current Learning Level</h3>
        <span className="pill green">Active</span>
      </div>
      <div className="grid g3">
        <div>
          <span className="tiny muted">Mastery</span>
          <div className="stat"><div className="num" style={{ fontSize: '1.2em' }}>{masteryVal}%</div></div>
          <Bar value={masteryVal} />
        </div>
        <div>
          <span className="tiny muted">Accuracy</span>
          <div className="stat"><div className="num" style={{ fontSize: '1.2em' }}>{accuracyVal}%</div></div>
          <Bar value={accuracyVal} tone="green" />
        </div>
        <div>
          <span className="tiny muted">Recommended Level</span>
          <div className="stat"><div className="num" style={{ fontSize: '1.2em' }}>{state.recommended_difficulty || 'Standard'}</div></div>
        </div>
      </div>
      {learningState?.status_message && (
        <p className="tiny muted mt8">{learningState.status_message}</p>
      )}
    </div>
  );
}
