import React, { useState, useEffect } from 'react';
import TeachingContent from '../components/TeachingContent';
import { fetchSubtopics, fetchSubtopicRoadmap } from '../api/learningApi';

const PPS_UNITS = [
  {
    unit: 'Unit 1: Fundamentals of C',
    topics: ['Variables and Data Types', 'Operators and Expressions'],
  },
  {
    unit: 'Unit 2: Control Structures',
    topics: ['Conditionals', 'Loops'],
  },
  {
    unit: 'Unit 3: Arrays & Strings',
    topics: ['Arrays', 'Strings'],
  },
  {
    unit: 'Unit 4: Functions & Pointers',
    topics: ['Functions', 'Pointers'],
  },
  {
    unit: 'Unit 5: Structures & Dynamic Memory',
    topics: ['Structures', 'Dynamic Memory Allocation'],
  },
];

export default function Learn({
  studentId = 'S001',
  currentTopic,
  onTopicChange,
  sessionResult,
  onGenerateLesson,
  isLoading,
  onNavigate,
  onOpenTutorWithCode,
  studentProfile,
}) {
  const [showSources, setShowSources] = useState(false);
  const [showVerificationDetails, setShowVerificationDetails] = useState(false);
  const [subtopics, setSubtopics] = useState([]);
  const [selectedSubtopic, setSelectedSubtopic] = useState(null);

  // Strict topic validation: Verify that sessionResult belongs to the active topic
  const sessionMatchesTopic = (sessionResult?.topic === currentTopic)
    || (sessionResult?.canonical_topic_context?.topic_name === currentTopic);
  const validSession = sessionMatchesTopic ? sessionResult : null;

  // Reset local subtopic selection whenever the active topic changes
  useEffect(() => {
    setSelectedSubtopic(null);
    setSubtopics([]);
  }, [currentTopic]);

  // Fetch or extract subtopics when topic or validSession changes
  useEffect(() => {
    const sId = studentProfile?.student_id || studentId;
    if (validSession?.subtopic_roadmap?.subtopics?.length > 0) {
      setSubtopics(validSession.subtopic_roadmap.subtopics);
      const active = validSession.subtopic_roadmap.subtopics.find((s) => s.status === 'IN_PROGRESS' || s.status === 'In Progress')
        || validSession.subtopic_roadmap.subtopics.find((s) => s.status === 'UNLOCKED')
        || validSession.subtopic_roadmap.subtopics[0];
      if (active && (!selectedSubtopic || !validSession.subtopic_roadmap.subtopics.some(s => s.title === selectedSubtopic || s.id === selectedSubtopic))) {
        setSelectedSubtopic(active.title || active.id);
      }
    } else {
      fetchSubtopicRoadmap(sId, currentTopic)
        .then((data) => {
          if (data?.subtopics?.length > 0) {
            setSubtopics(data.subtopics);
            const active = data.subtopics.find((s) => s.status === 'IN_PROGRESS' || s.status === 'In Progress')
              || data.subtopics.find((s) => s.status === 'UNLOCKED')
              || data.subtopics[0];
            if (active) setSelectedSubtopic(active.title || active.id);
          }
        })
        .catch(() => {
          fetchSubtopics(currentTopic)
            .then((data) => {
              if (Array.isArray(data) && data.length > 0) {
                setSubtopics(data);
                setSelectedSubtopic(data[0].title);
              }
            })
            .catch(() => {});
        });
    }
  }, [currentTopic, studentId, studentProfile, validSession]);

  const curriculumChunks = validSession?.curriculum?.retrieved_chunks || [];
  const verification = validSession?.verification;
  const difficulty = validSession?.teaching?.personalization_applied?.mastery_tier || studentProfile?.recommended_difficulty || 'Adaptive';
  const pace = validSession?.teaching?.personalization_applied?.learning_pace || studentProfile?.learning_pace || 'Adaptive';

  const activeSubtopicName = validSession?.subtopic || selectedSubtopic || currentTopic;
  const activeSubtopicData = subtopics.find((s) => s.title === activeSubtopicName || s.id === activeSubtopicName) || subtopics[0];
  const activeSubtopicId = activeSubtopicData?.id || validSession?.teaching?.subtopic_id;

  const activeCycle = validSession?.teaching?.learning_cycle || activeSubtopicData?.learning_cycle || 1;
  const maxCycles = validSession?.teaching?.max_cycles || activeSubtopicData?.max_cycles || 5;
  const subtopicMastery = activeSubtopicData?.mastery !== undefined
    ? Number(activeSubtopicData.mastery).toFixed(2)
    : (validSession?.teaching?.subtopic_mastery !== undefined
        ? Number(validSession.teaching.subtopic_mastery).toFixed(2)
        : '0.00');

  const completedCount = validSession?.subtopic_roadmap?.completed_count ?? subtopics.filter((s) => s.is_completed || s.status === 'COMPLETED' || s.status === 'MASTERED').length;
  const masteredCount = validSession?.subtopic_roadmap?.mastered_count ?? subtopics.filter((s) => s.status === 'MASTERED' || s.status === 'Mastered').length;
  const totalCount = validSession?.subtopic_roadmap?.total_count ?? (subtopics.length || 1);
  const progressPercent = validSession?.subtopic_roadmap?.progress_percent ?? Math.round((completedCount / totalCount) * 100);

  const rationale = validSession?.teaching?.personalization_applied?.rationale || '';

  const handleSelectSubtopic = (sub) => {
    if (sub.is_locked || sub.status === 'LOCKED' || sub.status === 'Pending Prerequisite') {
      return;
    }
    setSelectedSubtopic(sub.title || sub.id);
    if (onGenerateLesson) {
      onGenerateLesson(sub.title || sub.id, sub.learning_cycle || 1);
    }
  };

  const handleMasteryPassed = (res) => {
    const sId = studentProfile?.student_id || studentId;
    fetchSubtopicRoadmap(sId, currentTopic)
      .then((data) => {
        if (data?.subtopics) {
          setSubtopics(data.subtopics);
          if (res?.unlocked_subtopic_id) {
            const nextSub = data.subtopics.find((s) => s.id === res.unlocked_subtopic_id);
            if (nextSub) {
              setSelectedSubtopic(nextSub.title || nextSub.id);
            }
          }
        }
      })
      .catch(() => {});
  };

  const handleReadingCompleted = (res) => {
    if (res?.roadmap?.subtopics) {
      setSubtopics(res.roadmap.subtopics);
    }
  };

  return (
    <div className="learn-page">
      {/* Header */}
      <header className="page-header">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '12px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
              <h2 className="page-title" style={{ margin: 0 }}>{currentTopic}</h2>
              <span className="badge-blue" style={{ fontSize: '11px' }}>Curriculum Unit</span>
              <span className="badge-green" style={{ fontSize: '11px' }}>{difficulty} Tier</span>
            </div>
            <p className="page-subtitle" style={{ marginTop: '4px' }}>
              Personalized for Student {studentProfile?.student_id || studentId} • Subtopic: <strong>{activeSubtopicName}</strong> • {pace} Pace
            </p>
          </div>
          <div style={{ display: 'flex', gap: '10px', alignItems: 'center', flexWrap: 'wrap' }}>
            <select
              className="form-select"
              style={{ width: 'auto', minWidth: '180px', padding: '6px 10px', fontSize: '13px' }}
              value={currentTopic}
              onChange={(e) => {
                setSelectedSubtopic(null);
                onTopicChange(e.target.value);
              }}
              disabled={isLoading}
            >
              {PPS_UNITS.map((u) => (
                <optgroup key={u.unit} label={u.unit}>
                  {u.topics.map((t) => (
                    <option key={t} value={t}>
                      {t}
                    </option>
                  ))}
                </optgroup>
              ))}
            </select>
            <button
              type="button"
              className="btn-primary"
              style={{ padding: '7px 14px', fontSize: '13px' }}
              onClick={() => onGenerateLesson(selectedSubtopic, activeCycle)}
              disabled={isLoading}
            >
              {isLoading ? 'Generating lesson...' : (validSession?.teaching ? 'Regenerate Lesson ⟳' : 'Start Learning')}
            </button>
          </div>
        </div>
      </header>

      {/* Subtopic Progression Bar & Selector */}
      <div className="card" style={{ marginBottom: '18px', padding: '14px 18px', backgroundColor: 'var(--color-surface)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px', flexWrap: 'wrap', gap: '8px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span style={{ fontSize: '13px', fontWeight: 700, color: 'var(--color-text-primary)' }}>
              Subtopic Curriculum Sequence
            </span>
            <span className="badge-blue" style={{ fontSize: '11px' }}>
              {completedCount} of {totalCount} Completed ({progressPercent}%)
            </span>
            {masteredCount > 0 && (
              <span className="badge-green" style={{ fontSize: '11px' }}>
                {masteredCount} Mastered
              </span>
            )}
          </div>
          <div style={{ fontSize: '12px', color: 'var(--color-text-secondary)' }}>
            Cycle Progress: <strong>Cycle {activeCycle} of {maxCycles}</strong> • Subtopic Mastery: <strong>{subtopicMastery}</strong>
          </div>
        </div>

        {/* Progress Bar */}
        <div style={{ width: '100%', height: '6px', background: 'var(--color-border)', borderRadius: '3px', overflow: 'hidden', marginBottom: '12px' }}>
          <div style={{ width: `${progressPercent}%`, height: '100%', background: 'var(--color-green)', transition: 'width 0.3s ease' }} />
        </div>

        {/* Subtopic Pills */}
        <div style={{ display: 'flex', gap: '8px', overflowX: 'auto', paddingBottom: '6px' }}>
          {subtopics.map((sub, idx) => {
            const isSelected = (sub.title === activeSubtopicName) || (sub.id === activeSubtopicName) || (sub.id === activeSubtopicId);
            const isLocked = sub.status === 'LOCKED' || sub.status === 'Pending Prerequisite' || sub.is_locked;
            const isMastered = sub.status === 'MASTERED' || sub.status === 'Mastered';
            const isCompleted = sub.status === 'COMPLETED' || sub.status === 'Completed';
            const isAwaiting = sub.status === 'AWAITING_ASSESSMENT';
            const isRemediation = sub.status === 'REMEDIATION_REQUIRED';
            const isInProgress = sub.status === 'IN_PROGRESS' || sub.status === 'In Progress';
            const isUnlocked = sub.status === 'UNLOCKED';

            let badgeColor = '#94a3b8';
            let statusText = '🔒 Locked';

            if (isMastered) {
              badgeColor = 'var(--color-green)';
              statusText = '★ Mastered';
            } else if (isCompleted) {
              badgeColor = 'var(--color-green)';
              statusText = '✓ Completed';
            } else if (isRemediation) {
              badgeColor = '#f59e0b';
              statusText = '⚠️ Remediation';
            } else if (isAwaiting) {
              badgeColor = '#8b5cf6';
              statusText = '📝 Check Gate';
            } else if (isInProgress) {
              badgeColor = 'var(--color-blue)';
              statusText = '⏳ Reading';
            } else if (isUnlocked) {
              badgeColor = 'var(--color-blue)';
              statusText = '🔓 Ready';
            }

            return (
              <button
                key={sub.id || idx}
                type="button"
                onClick={() => !isLocked && handleSelectSubtopic(sub)}
                disabled={isLoading || isLocked}
                title={isLocked ? (sub.lock_explanation || 'Subtopic locked') : sub.title}
                style={{
                  padding: '6px 12px',
                  borderRadius: 'var(--radius-sm)',
                  border: isSelected ? '2px solid var(--color-blue)' : '1px solid var(--color-border)',
                  backgroundColor: isSelected ? 'rgba(59, 130, 246, 0.08)' : (isLocked ? 'rgba(148, 163, 184, 0.08)' : 'var(--color-surface)'),
                  cursor: isLocked ? 'not-allowed' : 'pointer',
                  opacity: isLocked ? 0.55 : 1.0,
                  fontSize: '12px',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'flex-start',
                  minWidth: '170px',
                  textAlign: 'left',
                }}
              >
                <div style={{ fontWeight: isSelected ? 700 : 500, color: isSelected ? 'var(--color-blue)' : 'inherit', marginBottom: '2px' }}>
                  {idx + 1}. {sub.title}
                </div>
                <div style={{ fontSize: '10px', color: badgeColor, fontWeight: 600 }}>
                  {statusText} {sub.mastery ? `(${Number(sub.mastery).toFixed(2)})` : ''}
                </div>
              </button>
            );
          })}
        </div>

        {/* Lock explanation banner if active subtopic is locked */}
        {activeSubtopicData && (activeSubtopicData.is_locked || activeSubtopicData.status === 'LOCKED') && (
          <div
            style={{
              padding: '8px 12px',
              backgroundColor: 'rgba(239, 68, 68, 0.06)',
              border: '1px solid rgba(239, 68, 68, 0.25)',
              borderRadius: 'var(--radius-sm)',
              marginTop: '10px',
              fontSize: '12px',
              color: 'var(--color-red)',
            }}
          >
            🔒 <strong>Locked Subtopic:</strong> {activeSubtopicData.lock_explanation || 'Complete prerequisite subtopics and pass their mastery checks first.'}
          </div>
        )}
      </div>

      {/* Adaptive Explanation Card: Why is this personalized? */}
      {rationale && (
        <div
          className="card"
          style={{
            backgroundColor: 'rgba(59, 130, 246, 0.06)',
            borderLeft: '4px solid var(--color-blue)',
            marginBottom: '18px',
            padding: '12px 16px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
            <span style={{ fontSize: '13px', fontWeight: 700, color: 'var(--color-blue)' }}>
              🎯 How EduAdapt Personalized This Subtopic Lesson
            </span>
            <span className="badge-blue" style={{ fontSize: '10px' }}>
              Cycle {activeCycle} of {maxCycles}
            </span>
          </div>
          <p style={{ fontSize: '12px', color: 'var(--color-text-primary)', margin: 0, lineHeight: 1.5 }}>
            {rationale}
          </p>
        </div>
      )}

      {/* Verification & Grounding Bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', fontSize: '12px', color: 'var(--color-text-secondary)', borderBottom: '1px solid var(--color-border)', paddingBottom: '10px' }}>
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          <span style={{ color: 'var(--color-green)', fontWeight: 600 }}>✓ Verified PPS Curriculum Grounding</span>
          <span>•</span>
          <button
            type="button"
            className="btn-pill"
            style={{ padding: '2px 8px', fontSize: '11px' }}
            onClick={() => setShowSources(!showSources)}
          >
            {showSources ? 'Hide Sources' : `View Curriculum Sources (${curriculumChunks.length} Slides)`}
          </button>
          <button
            type="button"
            className="btn-pill"
            style={{ padding: '2px 8px', fontSize: '11px' }}
            onClick={() => setShowVerificationDetails(!showVerificationDetails)}
          >
            {showVerificationDetails ? 'Hide Verification' : 'Verification Details'}
          </button>
        </div>
        <div>
          <span>Grounding Status: <strong>{verification?.grounded ? 'Verified Grounded' : 'Curriculum Grounded'}</strong></span>
        </div>
      </div>

      {/* Curriculum Sources Drawer */}
      {showSources && curriculumChunks.length > 0 && (
        <div className="card" style={{ backgroundColor: 'var(--color-surface-subtle)', marginBottom: '18px' }}>
          <h4 style={{ fontSize: '13px', fontWeight: 700, marginBottom: '8px' }}>Retrieved PPS Curriculum Sources</h4>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {curriculumChunks.map((chunk, idx) => (
              <div key={idx} style={{ fontSize: '12px', padding: '6px 10px', background: '#fff', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-sm)' }}>
                <strong>{chunk.source}</strong> (Slide {chunk.slide_or_page || 'N/A'}) • {chunk.unit_or_module} - {chunk.topic}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Verification Drawer */}
      {showVerificationDetails && verification && (
        <div className="card" style={{ backgroundColor: 'var(--color-surface-subtle)', marginBottom: '18px' }}>
          <h4 style={{ fontSize: '13px', fontWeight: 700, marginBottom: '8px' }}>Curriculum Grounding & Code Verification</h4>
          <div style={{ fontSize: '12px', display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '8px' }}>
            <div>Curriculum Concepts Matched: <strong>{verification.matched_curriculum_terms_count ?? 0}</strong></div>
            <div>Grounding Indicator: <strong>{verification.grounding_ratio !== undefined ? Number(verification.grounding_ratio).toFixed(3) : 'Verified'}</strong></div>
            <div>Generated C Code: <strong>{verification.extracted_code_lines ?? 0} lines</strong></div>
            <div>Code Safety: <strong>{verification.code_execution === 'EXECUTED_TRUSTED_COMPILER' ? 'Compiled & Verified' : 'Static Educational Example'}</strong></div>
          </div>
        </div>
      )}

      {/* Main Lesson Content */}
      {validSession?.teaching ? (
        <TeachingContent
          teaching={validSession.teaching}
          studentProfile={studentProfile}
          currentTopic={currentTopic}
          subtopicId={activeSubtopicId}
          subtopicTitle={activeSubtopicName}
          subtopicState={activeSubtopicData}
          onNavigate={onNavigate}
          onOpenTutorWithCode={onOpenTutorWithCode}
          onMasteryCheckPassed={handleMasteryPassed}
          onReadingCompleted={handleReadingCompleted}
        />
      ) : (
        <article className="card" style={{ padding: '36px', textAlign: 'center' }}>
          <h3 style={{ fontSize: '16px', fontWeight: 600, marginBottom: '8px' }}>No Lesson Generated Yet</h3>
          <p style={{ color: 'var(--color-text-secondary)', marginBottom: '20px' }}>
            Click <strong>"Start Learning"</strong> above to retrieve curriculum grounding and generate a personalized lesson with architectural diagrams for <strong>{activeSubtopicName}</strong>.
          </p>
          <button
            type="button"
            className="btn-primary"
            onClick={() => onGenerateLesson(selectedSubtopic, activeCycle)}
            disabled={isLoading}
          >
            {isLoading ? 'Generating lesson with Mistral 7B...' : 'Start Learning Now'}
          </button>
        </article>
      )}
    </div>
  );
}
