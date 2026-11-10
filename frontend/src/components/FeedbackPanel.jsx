import React from 'react';

export default function FeedbackPanel({ feedback }) {
  if (!feedback) return null;
  return (
    <div className="card tip col" style={{ gap: 8 }}>
      <strong>Learning Feedback:</strong>
      <p className="small muted">{feedback}</p>
    </div>
  );
}
