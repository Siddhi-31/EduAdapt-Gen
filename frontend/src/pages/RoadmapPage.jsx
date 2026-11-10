import React, { useState, useEffect } from 'react';
import { fetchAuthoritativeRoadmap } from '../api/learningApi';
import { Bar, DONE, Icon, Loading, Spinner, StatusPill } from '../components/ui';

const FILTERS = [
  ['all', 'All Stages'],
  ['done', 'Done'],
  ['current', 'Current'],
  ['upcoming', 'Upcoming'],
  ['locked', 'Locked'],
];

export default function RoadmapPage({
  studentId = 'S001',
  studentProfile,
  currentTopic = 'Variables and Data Types',
  sessionResult,
  onNavigate,
}) {
  const [filter, setFilter] = useState('all');
  const [stages, setStages] = useState([]);
  const [roadmapSummary, setRoadmapSummary] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const isDiagComplete = Boolean(studentProfile?.has_completed_diagnostic);
  const studentDisplayName = studentProfile?.full_name || studentProfile?.name || 'Student';

  const loadRoadmap = async () => {
    if (!studentId || !isDiagComplete) return;
    setIsLoading(true);
    setError(null);
    try {
      const data = await fetchAuthoritativeRoadmap(studentId);
      setRoadmapSummary(data);
      if (data?.stages && data.stages.length > 0) {
        setStages(data.stages);
      }
    } catch (err) {
      setError('Unable to load learning roadmap: ' + (err.message || 'Check connection'));
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadRoadmap();
  }, [studentId, isDiagComplete]);

  // If student has not completed initial diagnostic, show friendly pre-diagnostic callout
  if (!isDiagComplete) {
    return (
      <div className="page" style={{ maxWidth: 860, margin: '0 auto', gap: 20 }}>
        <div className="page-head">
          <div>
            <span className="eyebrow plain">Learning Roadmap</span>
            <h1>Curriculum Roadmap</h1>
            <p className="muted">
              Personalized milestone sequence for <strong>{studentDisplayName}</strong>.
            </p>
          </div>
        </div>

        <div className="card dark col center" style={{ padding: '48px 32px', gap: 18, background: 'linear-gradient(135deg, #1e1b4b 0%, #312e81 100%)' }}>
          <span className="icon-chip" style={{ width: 48, height: 48, background: 'rgba(255,255,255,0.15)', color: '#fff' }}>
            <Icon name="spark" size={24} />
          </span>
          <h2 style={{ color: '#fff', textAlign: 'center' }}>Initial Diagnostic Assessment Required</h2>
          <p className="small" style={{ color: '#c7d2fe', textAlign: 'center', maxWidth: 480, lineHeight: 1.6 }}>
            Your personalized learning path and topic sequence are generated from your diagnostic results.
            Complete the 25-question diagnostic to unlock your customized curriculum roadmap.
          </p>
          <div className="row mt8">
            <button
              type="button"
              className="btn primary"
              style={{ padding: '12px 28px', fontSize: '1em' }}
              onClick={() => onNavigate('diagnostic')}
            >
              Start Diagnostic Assessment →
            </button>
          </div>
        </div>

        {/* Informational Curriculum Overview */}
        <div className="card col" style={{ gap: 14 }}>
          <h3>Programming for Problem Solving (PPS) Course Modules</h3>
          <p className="hint">The course contains 10 sequential topics organized into 5 university curriculum units:</p>
          <div className="grid g2 mt8" style={{ gap: 10 }}>
            <div className="card soft col" style={{ padding: 12 }}>
              <strong>Unit 1: Fundamentals of C</strong>
              <span className="tiny muted">Variables and Data Types · Operators and Expressions</span>
            </div>
            <div className="card soft col" style={{ padding: 12 }}>
              <strong>Unit 2: Control Structures</strong>
              <span className="tiny muted">Conditionals · Loops</span>
            </div>
            <div className="card soft col" style={{ padding: 12 }}>
              <strong>Unit 3: Arrays & Strings</strong>
              <span className="tiny muted">Arrays · Strings</span>
            </div>
            <div className="card soft col" style={{ padding: 12 }}>
              <strong>Unit 4: Functions & Pointers</strong>
              <span className="tiny muted">Functions · Pointers</span>
            </div>
            <div className="card soft col" style={{ padding: 12 }}>
              <strong>Unit 5: Structures & Memory</strong>
              <span className="tiny muted">Structures · Dynamic Memory Allocation</span>
            </div>
          </div>
        </div>
      </div>
    );
  }

  const show = stages.filter((item) => {
    if (filter === 'all') return true;
    if (filter === 'done') return item.status === 'completed' || item.status === 'mastered';
    return item.status === filter;
  });

  const completedCount = roadmapSummary?.completed_count ?? stages.filter((s) => s.status === 'completed' || s.status === 'mastered').length;
  const masteredCount = roadmapSummary?.mastered_count ?? stages.filter((s) => s.status === 'mastered').length;
  const totalStages = stages.length || 10;
  const progressVal = roadmapSummary?.progress_percent ?? Math.round((completedCount / totalStages) * 100);
  const currentStage = stages.find((s) => s.status === 'current') || stages[0];

  return (
    <div className="page">
      <div className="page-head">
        <div>
          <span className="eyebrow plain">Learning Path</span>
          <h1>Your Learning Roadmap</h1>
          <p className="muted">
            Personalized milestone sequence for <strong>{studentDisplayName}</strong> · Pacing: <strong>{studentProfile?.learning_pace || 'Moderate'}</strong> · Level: <strong>{studentProfile?.recommended_difficulty || 'Beginner'}</strong>
          </p>
        </div>
        <button
          type="button"
          className="btn"
          disabled={isLoading}
          onClick={loadRoadmap}
        >
          {isLoading ? <Spinner /> : <Icon name="refresh" size={16} />}
          Refresh Plan
        </button>
      </div>

      {error && <p className="error-box">{error}</p>}

      {/* Goal & Mastery Overview */}
      <div className="grid" style={{ gridTemplateColumns: '2fr 1fr' }}>
        <div className="card col" style={{ gap: 12 }}>
          <div className="row between">
            <span className="tiny muted">Course Competency Progress</span>
            <span className="pill green">{completedCount} of {totalStages} Stages Completed ({progressVal}%)</span>
          </div>
          <h3>Programming for Problem Solving (PPS C99)</h3>
          <div className="mt8">
            <Bar value={progressVal} tone="green" />
          </div>
          <div className="row between tiny muted">
            <span>{completedCount} Completed · {masteredCount} Mastered</span>
            <span>Current Focus: <strong>{roadmapSummary?.current_focus_topic || currentTopic}</strong></span>
          </div>
        </div>

        <div className="card stat">
          <span className="muted small">Topic Mastery</span>
          <div className="num">{currentStage?.mastery_score ? `${Math.round(currentStage.mastery_score)}%` : '0%'}</div>
          <div className="mt8">
            <Bar value={currentStage?.mastery_score ? Math.round(currentStage.mastery_score) : 0} />
          </div>
          <p className="hint mt8">Verified average across completed checks</p>
        </div>
      </div>

      {/* Main Roadmap Timeline */}
      <div className="grid" style={{ gridTemplateColumns: '2fr 1fr', alignItems: 'start' }}>
        <div className="col">
          <div className="chip-select">
            {FILTERS.map(([k, l]) => (
              <button
                key={k}
                type="button"
                className={filter === k ? 'on' : ''}
                onClick={() => setFilter(k)}
              >
                {l}
              </button>
            ))}
          </div>

          <div className="timeline mt16">
            {show.map((it, idx) => {
              const isDone = it.status === 'completed' || it.status === 'mastered';
              const isLocked = it.status === 'locked';

              return (
                <div key={idx} className={`tl-item ${it.status}`}>
                  <div className="tl-rail">
                    <span className="node">
                      {isDone ? <Icon name="check" size={12} /> : it.sequence_no}
                    </span>
                    {idx < show.length - 1 && <span className="line" />}
                  </div>

                  <div className="tl-body">
                    <div className="card" style={{ padding: 18, opacity: isLocked ? 0.65 : 1.0 }}>
                      <div className="row between">
                        <div>
                          <strong>{it.sequence_no}. {it.title}</strong>
                          <div className="tiny muted mt4">{it.unit}</div>
                        </div>
                        <StatusPill status={it.status} />
                      </div>

                      <p className="hint mt8" style={{ lineHeight: 1.5 }}>
                        {it.description || `~${it.estimated_minutes} min · Level: ${it.recommended_difficulty}`}
                      </p>

                      {it.prerequisites && it.prerequisites.length > 0 && (
                        <div className="tiny muted mt8">
                          Prerequisites: <em>{it.prerequisites.join(', ')}</em>
                          {isLocked && <span style={{ color: '#f59e0b', marginLeft: 6 }}>🔒 Prerequisite required</span>}
                        </div>
                      )}

                      {!isLocked && (
                        <div className="row mt16">
                          <button
                            type="button"
                            className="btn sm primary"
                            onClick={() => onNavigate('learn')}
                          >
                            {isDone ? 'Review Concept' : 'Start Lesson'}
                          </button>
                          <button
                            type="button"
                            className="btn sm"
                            onClick={() => onNavigate('practice')}
                          >
                            Practice Exercises
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Why this path card */}
        <div className="col" style={{ gap: 14 }}>
          <div className="card col" style={{ gap: 12 }}>
            <h3>Why this path?</h3>
            <p className="small muted" style={{ lineHeight: 1.6 }}>
              Curriculum topics follow strict prerequisite sequence. Foundations in variables and control structures precede arrays and pointers. Demonstrating mastery unlocks subsequent modules automatically.
            </p>
            <div className="card soft col" style={{ padding: 12, gap: 6 }}>
              <span className="tiny"><strong>Active Topic:</strong> {roadmapSummary?.current_focus_topic || currentTopic}</span>
              <span className="tiny"><strong>Next In Sequence:</strong> {roadmapSummary?.next_in_sequence || 'Functions'}</span>
            </div>
          </div>

          <div className="card col" style={{ gap: 10 }}>
            <h3>Next Recommended Action</h3>
            <div className="list-item">
              <span className="icon-chip">
                <Icon name="spark" size={16} />
              </span>
              <div className="grow small">
                <strong>{roadmapSummary?.current_focus_topic || currentTopic}</strong>
                <div className="hint">Interactive lesson & practice</div>
              </div>
              <button
                type="button"
                className="btn sm primary"
                onClick={() => onNavigate('learn')}
              >
                Go →
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
