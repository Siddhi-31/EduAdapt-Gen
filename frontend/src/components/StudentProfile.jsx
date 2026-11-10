import React from 'react';
import { Bar, StatusPill } from './ui';

export default function StudentProfile({ student }) {
  if (!student) return null;
  const mastery = student.mastery !== undefined ? Math.round(student.mastery * 100) : 0;
  const accuracy = student.accuracy !== undefined ? Math.round(student.accuracy * 100) : 0;

  return (
    <div className="card col" style={{ gap: 14 }}>
      <div className="row between">
        <h3>Student Profile: {student.student_id}</h3>
        <span className="pill violet">{student.recommended_difficulty || 'Adaptive'}</span>
      </div>
      <div className="grid g3">
        <div>
          <span className="tiny muted">Mastery</span>
          <strong>{mastery}%</strong>
          <Bar value={mastery} />
        </div>
        <div>
          <span className="tiny muted">Accuracy</span>
          <strong>{accuracy}%</strong>
          <Bar value={accuracy} tone="green" />
        </div>
        <div>
          <span className="tiny muted">Pace</span>
          <strong>{student.learning_pace || 'Moderate'}</strong>
        </div>
      </div>
    </div>
  );
}
