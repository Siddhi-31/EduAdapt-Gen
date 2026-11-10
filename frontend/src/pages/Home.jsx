import React, { useState, useEffect } from 'react';
import { Bar, DONE, Icon, StatusPill } from '../components/ui';
import { fetchAuthoritativeRoadmap } from '../api/learningApi';

const PPS_TOPIC_MODULES = {
  'Variables and Data Types': 'Unit 1: Fundamentals of C',
  'Operators and Expressions': 'Unit 1: Fundamentals of C',
  'Conditionals': 'Unit 2: Control Structures',
  'Loops': 'Unit 2: Control Structures',
  'Arrays': 'Unit 3: Arrays & Strings',
  'Strings': 'Unit 3: Arrays & Strings',
  'Functions': 'Unit 4: Functions & Pointers',
  'Pointers': 'Unit 4: Functions & Pointers',
  'Structures': 'Unit 5: Structures & Dynamic Memory',
  'Dynamic Memory Allocation': 'Unit 5: Structures & Dynamic Memory',
};

export default function Home({
  student,
  currentTopic = 'Variables and Data Types',
  onNavigate,
  recentActivity,
}) {
  const isDiagComplete = Boolean(student?.has_completed_diagnostic);
  const studentName = student?.full_name || student?.name || 'Student';
  const masteryVal = isDiagComplete && student?.mastery !== undefined ? Math.round(student.mastery * 100) : 0;
  const accuracyVal = isDiagComplete && student?.accuracy !== undefined ? Math.round(student.accuracy * 100) : 0;
  const pace = isDiagComplete ? (student?.learning_pace || 'Moderate') : 'Not determined';
  const difficulty = isDiagComplete ? (student?.recommended_difficulty || 'Beginner') : 'Not determined';
  const effectiveRecentActivity = recentActivity || student?.recent_activity || (student?.recent_attempts && student.recent_attempts[0]);
  const testsCount = student?.tests_completed !== undefined ? student.tests_completed : (effectiveRecentActivity ? 1 : 0);
  const currentModule = PPS_TOPIC_MODULES[currentTopic] || 'Unit 1: Fundamentals of C';

  const strongTopics = isDiagComplete && student?.strong_topics ? student.strong_topics : (isDiagComplete && masteryVal >= 70 ? [currentTopic] : []);
  const weakTopics = isDiagComplete && student?.weak_topics ? student.weak_topics : (isDiagComplete && masteryVal < 50 && testsCount > 0 ? [currentTopic] : []);

  const [roadmapStages, setRoadmapStages] = useState([]);

  useEffect(() => {
    if (student?.student_id && isDiagComplete) {
      fetchAuthoritativeRoadmap(student.student_id)
        .then((data) => {
          if (data?.stages && data.stages.length > 0) {
            setRoadmapStages(data.stages.slice(0, 5));
          }
        })
        .catch(() => {});
    }
  }, [student?.student_id, isDiagComplete]);

  return (
    <div className="page">
      <div className="page-head">
        <div>
          <span className="eyebrow plain">Learn at Your Pace</span>
          <h1>Welcome back, {studentName}</h1>
          <p className="muted">Build strong foundations, practice with confidence, and master C programming step by step.</p>
        </div>
        <button
          type="button"
          className="btn"
          onClick={() => onNavigate('tutor')}
        >
          <Icon name="chat" size={16} />
          Ask Learning Tutor
        </button>
      </div>

      {/* Top Banner Grid */}
      <div className="grid" style={{ gridTemplateColumns: '2fr 1fr' }}>
        {!isDiagComplete ? (
          <div className="card dark col" style={{ gap: 14, background: 'linear-gradient(135deg, #312e81 0%, #4338ca 100%)' }}>
            <span
              className="eyebrow"
              style={{ alignSelf: 'flex-start', background: 'rgba(255,255,255,0.15)', color: '#fff' }}
            >
              Action Required · Step 1
            </span>
            <div>
              <h2 style={{ fontSize: '1.6em', color: '#fff' }}>Initial Diagnostic Assessment</h2>
              <p className="small" style={{ color: '#c3c6e4', marginTop: 4 }}>
                25 Questions across reasoning, comprehension, and numerical aptitude. Required to calibrate your personalized curriculum path.
              </p>
            </div>
            <div className="row mt8">
              <button
                type="button"
                className="btn primary"
                onClick={() => onNavigate('diagnostic')}
              >
                Start Diagnostic Assessment <Icon name="arrow" size={16} />
              </button>
            </div>
          </div>
        ) : (
          <div className="card dark col" style={{ gap: 14 }}>
            <span
              className="eyebrow"
              style={{ alignSelf: 'flex-start', background: 'rgba(255,255,255,0.15)', color: '#fff' }}
            >
              Continue Learning
            </span>
            <div>
              <h2 style={{ fontSize: '1.6em', color: '#fff' }}>{currentTopic}</h2>
              <p className="small" style={{ color: '#c3c6e4', marginTop: 4 }}>
                {currentModule} · ~15 min · {difficulty} Level
              </p>
            </div>
            <div className="row mt8">
              <button
                type="button"
                className="btn primary"
                onClick={() => onNavigate('learn')}
              >
                Start Lesson <Icon name="arrow" size={16} />
              </button>
              <button
                type="button"
                className="btn"
                style={{ background: 'transparent', color: '#fff', borderColor: 'rgba(255,255,255,0.35)' }}
                onClick={() => onNavigate('practice')}
              >
                Quick Check & Practice
              </button>
            </div>
          </div>
        )}

        <div className="card col" style={{ gap: 12 }}>
          <span className="eyebrow plain">Your Learning Profile</span>
          <div className="small">
            <span className="muted">Learning Level: </span>
            <strong>{difficulty}</strong>
          </div>
          <div className="small">
            <span className="muted">Strengths: </span>
            {isDiagComplete && strongTopics.length ? strongTopics.join(', ') : 'Not determined'}
          </div>
          <div className="small">
            <span className="muted">Focus areas: </span>
            {isDiagComplete ? (weakTopics.length ? weakTopics.join(', ') : 'All current topics solid') : 'Not determined'}
          </div>
          <div className="small">
            <span className="muted">Pace: </span>
            <strong>{pace}</strong>
          </div>
          <p className="hint">
            {isDiagComplete
              ? 'Calibrated from your diagnostic performance and practice exercises.'
              : 'Complete the initial diagnostic assessment to calibrate your learning profile.'}
          </p>
        </div>
      </div>

      {/* 4 Stat Cards */}
      <div className="grid g4">
        <div className="card stat">
          <span className="muted small">Topic Mastery</span>
          <div className="num">{masteryVal}%</div>
          <div className="mt8">
            <Bar value={masteryVal} />
          </div>
        </div>
        <div className="card stat">
          <span className="muted small">Practice Accuracy</span>
          <div className="num">{accuracyVal}%</div>
          <div className="mt8">
            <Bar value={accuracyVal} tone="green" />
          </div>
        </div>
        <div className="card stat">
          <span className="muted small row">
            <Icon name="clock" size={14} />
            Assessments Completed
          </span>
          <div className="num">{testsCount}</div>
        </div>
        <div className="card stat">
          <span className="muted small row">
            <Icon name="flame" size={14} />
            Learning Pace
          </span>
          <div className="num">{pace}</div>
        </div>
      </div>

      {/* Two Column Section */}
      <div className="grid g2">
        <div className="card">
          <div className="row between" style={{ marginBottom: 12 }}>
            <h3>Recommended for You</h3>
            {isDiagComplete && (
              <button
                type="button"
                className="btn ghost sm"
                onClick={() => onNavigate('learn')}
              >
                See details
              </button>
            )}
          </div>

          {!isDiagComplete ? (
            <div className="list-item">
              <span className="icon-chip" style={{ background: '#ede9fe', color: '#6366f1' }}>
                <Icon name="spark" size={16} />
              </span>
              <div className="grow">
                <strong className="small">Take Initial Diagnostic Assessment</strong>
                <div className="hint">Calibrates your learning path, pace, and prerequisite modules</div>
              </div>
              <button
                type="button"
                className="btn sm primary"
                onClick={() => onNavigate('diagnostic')}
              >
                Start Assessment
              </button>
            </div>
          ) : (
            <>
              <div className="list-item">
                <span className="icon-chip">
                  <Icon name="spark" size={16} />
                </span>
                <div className="grow">
                  <strong className="small">{currentTopic} Core Concepts</strong>
                  <div className="hint">Interactive lesson tailored to your explanation style</div>
                </div>
                <button
                  type="button"
                  className="btn sm primary"
                  onClick={() => onNavigate('learn')}
                >
                  Start
                </button>
              </div>
              <div className="list-item">
                <span className="icon-chip">
                  <Icon name="code" size={16} />
                </span>
                <div className="grow">
                  <strong className="small">{currentTopic} Practice Exercises</strong>
                  <div className="hint">Interactive coding exercises with verified test cases</div>
                </div>
                <button
                  type="button"
                  className="btn sm"
                  onClick={() => onNavigate('practice')}
                >
                  Practice
                </button>
              </div>
              <div className="list-item">
                <span className="icon-chip">
                  <Icon name="check" size={16} />
                </span>
                <div className="grow">
                  <strong className="small">{currentTopic} Checkpoint Assessment</strong>
                  <div className="hint">Evaluate your understanding and advance your roadmap</div>
                </div>
                <button
                  type="button"
                  className="btn sm"
                  onClick={() => onNavigate('tests')}
                >
                  Take Assessment
                </button>
              </div>
            </>
          )}
        </div>

        <div className="card">
          <div className="row between" style={{ marginBottom: 12 }}>
            <h3>Your Learning Roadmap</h3>
            {isDiagComplete && (
              <button
                type="button"
                className="btn ghost sm"
                onClick={() => onNavigate('roadmap')}
              >
                View All
              </button>
            )}
          </div>

          {!isDiagComplete ? (
            <div className="card soft" style={{ padding: 16 }}>
              <p className="tiny muted">
                Your personalized learning roadmap will be generated immediately after submitting the Initial Diagnostic Assessment.
              </p>
              <button
                type="button"
                className="btn sm primary mt8"
                onClick={() => onNavigate('diagnostic')}
              >
                Start Diagnostic Now →
              </button>
            </div>
          ) : roadmapStages.length > 0 ? (
            roadmapStages.map((item) => (
              <div key={item.sequence_no} className="list-item">
                <span
                  className={`dot ${
                    DONE.includes(item.status)
                      ? 'done'
                      : item.status === 'current'
                      ? 'now'
                      : item.status === 'in_progress'
                      ? 'rev'
                      : ''
                  }`}
                />
                <span className="grow small">{item.title}</span>
                <StatusPill status={item.status} />
              </div>
            ))
          ) : (
            <div className="hint">Loading verified stages...</div>
          )}
        </div>
      </div>

      {/* Learning Signals & Recent Assessment */}
      <div className="grid g2">
        <div className="card">
          <h3>Your Topic Mastery</h3>
          <p className="hint">Progress across core curriculum topics.</p>
          <div className="mt16">
            <div className="row between small">
              <span>{currentTopic} (Current Focus)</span>
              <span className="muted">{masteryVal}%</span>
            </div>
            <div className="mt8">
              <Bar value={masteryVal} />
            </div>
          </div>
          {isDiagComplete && testsCount > 0 ? (
            <div className="mt16 small muted">
              Topic mastery updates continuously after completing lessons and verified practice checkpoints.
            </div>
          ) : (
            <div className="card soft mt16" style={{ padding: 12 }}>
              <p className="tiny muted">
                Curriculum topic mastery will calibrate as you work through interactive lessons and practice checkpoints.
              </p>
            </div>
          )}
        </div>

        <div className="card">
          <h3>Recent Assessment Activity</h3>
          {effectiveRecentActivity ? (
            <div className="list-item mt16">
              <div className="grow small">
                <strong>{effectiveRecentActivity.title || `${currentTopic} Assessment`}</strong>
                <div className="hint">{effectiveRecentActivity.time || 'Completed recently'}</div>
              </div>
              <span
                className={`pill ${
                  (effectiveRecentActivity.score || 0) >= 85
                    ? 'green'
                    : (effectiveRecentActivity.score || 0) < 60
                    ? 'amber'
                    : 'violet'
                }`}
              >
                {Math.round(effectiveRecentActivity.score || 0)}%
              </span>
              <button
                type="button"
                className="btn sm"
                onClick={() => onNavigate('results')}
              >
                Review
              </button>
            </div>
          ) : (
            <div className="empty">
              No assessments completed yet. Take a quick topic assessment to evaluate your progress.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
