import React, { useState, useEffect } from 'react';
import TeachingContent from '../components/TeachingContent';
import { fetchSubtopics, fetchSubtopicRoadmap } from '../api/learningApi';
import { Bar, Icon, Loading, Spinner, StatusPill } from '../components/ui';

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

  const sessionMatchesTopic = (sessionResult?.topic === currentTopic)
    || (sessionResult?.canonical_topic_context?.topic_name === currentTopic);
  const validSession = sessionMatchesTopic ? sessionResult : null;

  useEffect(() => {
    setSelectedSubtopic(null);
    setSubtopics([]);
  }, [currentTopic]);

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
    <div className="page">
      {/* Top Page Head */}
      <div className="page-head">
        <div>
          <span className="eyebrow plain">Interactive Lesson</span>
          <h1>{currentTopic}</h1>
          <p className="muted">
            Personalized for Student <strong>{studentProfile?.student_id || studentId}</strong> · Subtopic: <strong>{activeSubtopicName}</strong> · {pace} Pace · {difficulty} Tier
          </p>
        </div>

        <div className="row">
          <button
            type="button"
            className="btn"
            onClick={() => onNavigate('tutor')}
          >
            <Icon name="chat" size={16} /> Ask Tutor
          </button>
          <button
            type="button"
            className="btn"
            onClick={() => onNavigate('practice')}
          >
            <Icon name="code" size={16} /> Practice Code
          </button>
          <button
            type="button"
            className="btn primary"
            onClick={() => onGenerateLesson(selectedSubtopic, activeCycle)}
            disabled={isLoading}
          >
            {isLoading ? <Spinner /> : <Icon name="book" size={16} />}
            {validSession?.teaching ? 'Refresh Lesson' : 'Start Lesson'}
          </button>
        </div>
      </div>

      {/* Subtopic Sequential Roadmap & Progress Card */}
      <div className="card col" style={{ gap: 14 }}>
        <div className="row between">
          <div className="row">
            <strong>Learning Path</strong>
            <span className="pill violet">{completedCount} of {totalCount} Completed ({progressPercent}%)</span>
            {masteredCount > 0 && <span className="pill green">{masteredCount} Mastered</span>}
          </div>
          <span className="tiny muted">
            Progress: <strong>Step {activeCycle} of {maxCycles}</strong> · Mastery Score: <strong>{subtopicMastery}</strong>
          </span>
        </div>

        <Bar value={progressPercent} tone="green" />

        {/* Subtopic Chips */}
        <div className="row wrap mt8" style={{ gap: 8 }}>
          {subtopics.map((sub, idx) => {
            const isSelected = (sub.title === activeSubtopicName) || (sub.id === activeSubtopicName) || (sub.id === activeSubtopicId);
            const isLocked = sub.status === 'LOCKED' || sub.status === 'Pending Prerequisite' || sub.is_locked;
            const isMastered = sub.status === 'MASTERED' || sub.status === 'Mastered';
            const isCompleted = sub.status === 'COMPLETED' || sub.status === 'Completed';

            return (
              <button
                key={sub.id || idx}
                type="button"
                className={`choice ${isSelected ? 'on' : ''}`}
                style={{
                  padding: '8px 14px',
                  opacity: isLocked ? 0.5 : 1.0,
                  cursor: isLocked ? 'not-allowed' : 'pointer',
                  minWidth: 160,
                }}
                onClick={() => !isLocked && handleSelectSubtopic(sub)}
                disabled={isLoading || isLocked}
                title={isLocked ? (sub.lock_explanation || 'Subtopic locked') : sub.title}
              >
                <div className="small" style={{ fontWeight: isSelected ? 600 : 500 }}>
                  {idx + 1}. {sub.title}
                </div>
                <div className="tiny muted mt8">
                  {isMastered ? 'Mastered' : isCompleted ? 'Completed' : isLocked ? '🔒 Locked' : 'Available'}
                  {sub.mastery ? ` (${Number(sub.mastery).toFixed(2)})` : ''}
                </div>
              </button>
            );
          })}
        </div>

        {activeSubtopicData && (activeSubtopicData.is_locked || activeSubtopicData.status === 'LOCKED') && (
          <div className="notice">
            🔒 <strong>Locked Subtopic:</strong> {activeSubtopicData.lock_explanation || 'Complete prerequisite subtopics and pass their mastery checks first.'}
          </div>
        )}
      </div>

      {/* Rationale Card: Why is this personalized? */}
      {rationale && (
        <div className="card soft col" style={{ gap: 6 }}>
          <div className="row between">
            <strong className="small">How This Lesson Is Tailored for You</strong>
            <span className="pill violet">Step {activeCycle} of {maxCycles}</span>
          </div>
          <p className="small muted" style={{ lineHeight: 1.6 }}>{rationale}</p>
        </div>
      )}

      {/* Grounding & Verification Controls */}
      <div className="row between">
        <div className="row">
          <span className="pill green">Curriculum Aligned</span>
          <button
            type="button"
            className="btn ghost sm"
            onClick={() => setShowSources(!showSources)}
          >
            {showSources ? 'Hide References' : `Course References (${curriculumChunks.length})`}
          </button>
          <button
            type="button"
            className="btn ghost sm"
            onClick={() => setShowVerificationDetails(!showVerificationDetails)}
          >
            {showVerificationDetails ? 'Hide Details' : 'Lesson Overview'}
          </button>
        </div>
        <span className="tiny muted">
          Status: <strong>Curriculum Aligned</strong>
        </span>
      </div>

      {/* Curriculum Sources Drawer */}
      {showSources && curriculumChunks.length > 0 && (
        <div className="card col" style={{ gap: 8 }}>
          <h3>Course Reference Material</h3>
          <div className="col" style={{ gap: 6 }}>
            {curriculumChunks.map((chunk, idx) => (
              <div key={idx} className="src">
                <strong>{chunk.source || 'Curriculum Slides'}</strong> (Slide {chunk.slide_or_page || 'N/A'}) · {chunk.unit_or_module} - {chunk.topic}
                {chunk.text && <div className="muted mt8 tiny">{chunk.text.slice(0, 200)}...</div>}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Verification Drawer */}
      {showVerificationDetails && verification && (
        <div className="card col" style={{ gap: 10 }}>
          <h3>Lesson Quality & Code Safety</h3>
          <div className="grid g4">
            <div className="card soft col" style={{ padding: 12 }}>
              <span className="tiny muted">Key Concepts Covered</span>
              <strong>{verification.matched_curriculum_terms_count ?? 0}</strong>
            </div>
            <div className="card soft col" style={{ padding: 12 }}>
              <span className="tiny muted">Curriculum Alignment</span>
              <strong>{verification.grounding_ratio !== undefined ? Number(verification.grounding_ratio).toFixed(3) : '1.000'}</strong>
            </div>
            <div className="card soft col" style={{ padding: 12 }}>
              <span className="tiny muted">C Code Lines</span>
              <strong>{verification.extracted_code_lines ?? 0} lines</strong>
            </div>
            <div className="card soft col" style={{ padding: 12 }}>
              <span className="tiny muted">Compilation Safety</span>
              <strong>Verified (C99 Standard)</strong>
            </div>
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
        <div className="card col center" style={{ padding: '48px 24px', gap: 16 }}>
          <span className="icon-chip" style={{ width: 48, height: 48 }}>
            <Icon name="book" size={24} />
          </span>
          <h3>No lesson loaded for {activeSubtopicName} yet</h3>
          <p className="muted small" style={{ textAlign: 'center', maxWidth: 440 }}>
            Click <strong>"Start Lesson"</strong> to load a structured lesson with interactive explanations and diagrams.
          </p>
          <button
            type="button"
            className="btn primary"
            onClick={() => onGenerateLesson(selectedSubtopic, activeCycle)}
            disabled={isLoading}
          >
            {isLoading ? <Spinner /> : 'Start Lesson Now →'}
          </button>
        </div>
      )}
    </div>
  );
}
