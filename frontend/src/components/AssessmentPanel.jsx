import React from 'react';

export default function AssessmentPanel({ assessment }) {
  if (!assessment) return null;
  return (
    <div className="card col" style={{ gap: 10 }}>
      <h3>Assessment Details</h3>
      <p className="small muted">{assessment.summary || 'Cognitive check completed.'}</p>
    </div>
  );
}
