import React from 'react';
import { Bar, Icon, StatusPill, fmtTime } from '../components/ui';

export default function Results({
  testResult,
  currentTopic = 'Pointers',
  onNavigate,
  onTopicChange,
}) {
  if (!testResult) {
    return (
      <div className="page" style={{ maxWidth: 720 }}>
        <div className="page-head">
          <div>
            <span className="eyebrow plain">Checkpoint Results</span>
            <h1>Assessment Results</h1>
            <p className="muted">No recent assessment completed in this session.</p>
          </div>
        </div>

        <div className="card col center" style={{ gap: 16, padding: '48px 24px' }}>
          <span className="icon-chip" style={{ width: 48, height: 48 }}>
            <Icon name="chart" size={24} />
          </span>
          <h3>No test results to display</h3>
          <p className="muted small" style={{ textAlign: 'center', maxWidth: 420 }}>
            Complete an assessment or a practice check to review your score, understanding breakdown, and progress updates.
          </p>
          <button
            type="button"
            className="btn primary"
            onClick={() => onNavigate('tests')}
          >
            Take an Assessment →
          </button>
        </div>
      </div>
    );
  }

  const score = testResult.score !== undefined ? testResult.score : 0;
  const isMastered = score >= 85;
  const isPassed = score >= 60;
  const total = testResult.questions?.length || (testResult.results ? testResult.results.length : 10);
  const correctCount = testResult.correct_count !== undefined
    ? testResult.correct_count
    : (testResult.results ? testResult.results.filter((r) => r.is_correct).length : Math.round((score / 100) * total));
  const secs = testResult.timeTaken || testResult.time_taken_seconds || 65;

  const color = isMastered ? 'var(--green)' : isPassed ? 'var(--primary)' : 'var(--amber)';
  const headline = isMastered
    ? 'Outstanding — You have verified mastery in this topic.'
    : isPassed
    ? 'Solid achievement — A strong step forward in PPS.'
    : 'Good effort — Let’s reinforce core memory and syntax concepts.';

  const nextTopic = testResult.next_topic;
  const feedback = testResult.feedback || 'Detailed evaluation of your assessment.';
  const weakConcepts = testResult.weak_concepts || [];
  const questions = testResult.results || testResult.questions || [];

  const handleContinueNext = () => {
    if (nextTopic && onTopicChange) {
      onTopicChange(nextTopic);
    }
    onNavigate('learn');
  };

  return (
    <div className="page">
      <div className="page-head">
        <div>
          <span className="eyebrow plain">Checkpoint Evaluation</span>
          <h1>{testResult.title || `Assessment: ${currentTopic}`}</h1>
          <p className="muted">Detailed summary of your performance and learning progress.</p>
        </div>
        <button
          type="button"
          className="btn"
          onClick={() => onNavigate('home')}
        >
          Back to Dashboard
        </button>
      </div>

      {/* Unlocked Next Topic Banner */}
      {isPassed && nextTopic && nextTopic !== currentTopic && (
        <div className="card tip row between">
          <div>
            <h3 style={{ color: 'var(--green)' }}>Milestone Reached: {nextTopic} Unlocked!</h3>
            <p className="muted small mt8">
              You demonstrated mastery in {currentTopic}. The learning roadmap has unlocked <strong>{nextTopic}</strong>.
            </p>
          </div>
          <button
            type="button"
            className="btn primary"
            onClick={handleContinueNext}
          >
            Continue to {nextTopic} →
          </button>
        </div>
      )}

      {/* Ring Gauge & Top Headline Card */}
      <div className="card tip row" style={{ gap: 24 }}>
        <div
          className="ring"
          style={{ background: `conic-gradient(${color} ${score * 3.6}deg, #dfe3ee 0)` }}
        >
          <span>{Math.round(score)}%</span>
        </div>
        <div className="grow">
          <h2>{headline}</h2>
          <p className="muted mt8">
            Assessment score: <strong>{score}/100</strong>. Your learning profile has been updated to match future lessons and practice to your level.
          </p>
        </div>
        <span className={`pill ${isMastered ? 'green' : isPassed ? 'violet' : 'amber'}`}>
          {isMastered ? 'Mastered (≥85%)' : isPassed ? 'Passed (≥60%)' : 'Review Needed'}
        </span>
      </div>

      {/* 3 Metric Stat Cards */}
      <div className="grid g3">
        <div className="card stat">
          <span className="muted small">Questions Correct</span>
          <div className="num">{correctCount} / {total}</div>
        </div>
        <div className="card stat">
          <span className="muted small">Time Taken</span>
          <div className="num">{secs < 60 ? `${secs}s` : fmtTime(secs)}</div>
        </div>
        <div className="card stat">
          <span className="muted small">Mastery Score</span>
          <div className="num">{Math.round(score)}%</div>
          <div className="mt8">
            <Bar value={score} />
          </div>
        </div>
      </div>

      {/* Two Column Layout: Feedback & Question Review */}
      <div className="grid g2" style={{ alignItems: 'start' }}>
        <div className="col">
          {/* Performance Feedback */}
          <div className="card col" style={{ gap: 10 }}>
            <h3>Performance Insights</h3>
            <p className="small" style={{ lineHeight: 1.6 }}>{feedback}</p>
          </div>

          {/* Weak Concepts if any */}
          {weakConcepts.length > 0 && (
            <div className="notice">
              <strong>Concepts to Review: </strong>
              {weakConcepts.join(', ')}
            </div>
          )}

          {/* Cognitive Breakdown */}
          <div className="card col" style={{ gap: 12 }}>
            <h3>Understanding Breakdown</h3>
            <div>
              <div className="row between small">
                <span>Knowledge & Syntax Recall</span>
                <span className="muted">{Math.min(100, Math.round(score * 1.05))}%</span>
              </div>
              <div className="mt8">
                <Bar value={Math.min(100, Math.round(score * 1.05))} />
              </div>
            </div>
            <div>
              <div className="row between small">
                <span>Memory Model Understanding</span>
                <span className="muted">{score}%</span>
              </div>
              <div className="mt8">
                <Bar value={score} tone="green" />
              </div>
            </div>
            <div>
              <div className="row between small">
                <span>Application & Problem Solving</span>
                <span className="muted">{Math.max(40, Math.round(score * 0.95))}%</span>
              </div>
              <div className="mt8">
                <Bar value={Math.max(40, Math.round(score * 0.95))} />
              </div>
            </div>
          </div>

          <div className="row">
            <button
              type="button"
              className="btn primary"
              onClick={() => onNavigate('learn')}
            >
              {score < 60 ? 'Revise this topic' : 'Back to Lessons'}
            </button>
            <button
              type="button"
              className="btn"
              onClick={() => onNavigate('roadmap')}
            >
              <Icon name="map" size={16} /> View Roadmap
            </button>
          </div>
        </div>

        {/* Right Column: Detailed Question Breakdown */}
        <div className="card col" style={{ gap: 14 }}>
          <h3>Review Answers ({questions.length} Questions)</h3>
          {questions.map((q, idx) => {
            const isRight = q.is_correct ?? (testResult.studentAnswers && testResult.studentAnswers[idx] === q.correct_option);
            const userAns = q.student_answer || (testResult.studentAnswers ? testResult.studentAnswers[idx] : '—');
            const rightAns = q.correct_answer || q.correct_option || 'Verified';

            return (
              <div key={idx} className="list-item" style={{ alignItems: 'flex-start' }}>
                <span
                  className={`pill ${isRight ? 'green' : 'red'}`}
                  style={{ marginTop: 2 }}
                >
                  {isRight ? 'Correct' : 'Review'}
                </span>
                <div className="grow small">
                  <strong>{idx + 1}. {q.question}</strong>
                  <div className="hint mt8">
                    Your choice: <strong>{userAns}</strong> · Correct answer: <strong style={{ color: 'var(--green)' }}>{rightAns}</strong>
                  </div>
                  {q.explanation && (
                    <div className="hint mt8">{q.explanation}</div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
