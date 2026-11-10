import React, { useState, useEffect } from 'react';
import { Bar, Icon, StatusPill } from '../components/ui';
import { fetchAuthoritativeRoadmap } from '../api/learningApi';

const PPS_COURSE_MODULES = [
  {
    id: 1,
    title: 'Unit 1: Fundamentals of Computing',
    co: 'CO1',
    topics: ['Variables and Data Types', 'Operators and Expressions'],
  },
  {
    id: 2,
    title: 'Unit 2: Control Structures',
    co: 'CO2',
    topics: ['Conditionals', 'Loops'],
  },
  {
    id: 3,
    title: 'Unit 3: Arrays & Strings',
    co: 'CO3',
    topics: ['Arrays', 'Strings'],
  },
  {
    id: 4,
    title: 'Unit 4: Functions & Pointers',
    co: 'CO4',
    topics: ['Functions', 'Pointers'],
  },
  {
    id: 5,
    title: 'Unit 5: Structures & DMA',
    co: 'CO5',
    topics: ['Structures', 'Dynamic Memory Allocation'],
  },
];

export default function Progress({
  student,
  learningState,
  currentTopic = 'Variables and Data Types',
  roadmapData,
  onNavigate,
}) {
  const current = learningState?.updated_state || learningState?.simulated_twin || student;
  const isDiagComplete = Boolean(current?.has_completed_diagnostic);
  const testsCompleted = current?.tests_completed || (current?.recent_attempts ? current.recent_attempts.length : 0);
  const hasHistory = Boolean(testsCompleted > 0);
  const masteryVal = isDiagComplete && current?.mastery !== undefined ? Math.round(current.mastery * 100) : 0;
  const accuracyVal = isDiagComplete && current?.accuracy !== undefined ? Math.round(current.accuracy * 100) : 0;
  const pace = isDiagComplete ? (current?.learning_pace || 'Moderate') : 'Not determined';
  const difficulty = isDiagComplete ? (current?.recommended_difficulty || 'Beginner') : 'Not determined';
  const predictedMastery = isDiagComplete ? (current?.predicted_mastery_level || 'Learner') : 'New Learner';

  const [stages, setStages] = useState(roadmapData?.stages || []);

  useEffect(() => {
    if (roadmapData?.stages && roadmapData.stages.length > 0) {
      setStages(roadmapData.stages);
    } else if (student?.student_id && isDiagComplete) {
      fetchAuthoritativeRoadmap(student.student_id)
        .then((data) => {
          if (data?.stages && data.stages.length > 0) {
            setStages(data.stages);
          }
        })
        .catch(() => {});
    }
  }, [student?.student_id, isDiagComplete, roadmapData]);

  // Compute authentic module and topic status map without fabricated mastery
  const stageMap = {};
  stages.forEach((st) => {
    if (st.title) stageMap[st.title] = st;
  });

  const computedModules = PPS_COURSE_MODULES.map((m) => {
    const topicsWithStatus = m.topics.map((tName) => {
      if (!isDiagComplete) {
        return { title: tName, status: 'not_assessed', mastery: 0 };
      }
      const stage = stageMap[tName];
      if (stage) {
        return {
          title: tName,
          status: stage.status || 'locked',
          mastery: stage.mastery_score || 0,
        };
      }
      // If diagnostic is completed and stage not yet loaded:
      // First topic is current/upcoming, subsequent topics are locked
      if (tName === 'Variables and Data Types') {
        return { title: tName, status: 'current', mastery: 0 };
      }
      return { title: tName, status: 'locked', mastery: 0 };
    });

    // Calculate module mastery based on verified evidence
    const completedTopics = topicsWithStatus.filter((t) => t.status === 'completed' || t.status === 'mastered').length;
    const masteredTopics = topicsWithStatus.filter((t) => t.status === 'mastered').length;
    let moduleMastery = 0;
    if (masteredTopics === topicsWithStatus.length) {
      moduleMastery = 90;
    } else if (completedTopics > 0) {
      moduleMastery = Math.round((completedTopics / topicsWithStatus.length) * 75);
    }

    return {
      id: m.id,
      title: m.title,
      co: m.co,
      mastery: moduleMastery,
      topics: topicsWithStatus,
    };
  });

  const syllabusSubject = [
    {
      name: 'Programming for Problem Solving',
      code: '21CSS101J',
      mastery: masteryVal,
      modules: computedModules,
    },
  ];

  const assessmentHistory = (current?.recent_attempts && current.recent_attempts.length > 0)
    ? current.recent_attempts
    : (student?.recent_attempts || []);

  return (
    <div className="page">
      <div className="page-head">
        <div>
          <span className="eyebrow plain">Learning Analytics</span>
          <h1>Your Learning Progress</h1>
          <p className="muted">
            Track your topic mastery, practice accuracy, and syllabus progress.
          </p>
        </div>
        <button
          type="button"
          className="btn"
          onClick={() => onNavigate('tests')}
        >
          <Icon name="check" size={16} /> Take New Assessment
        </button>
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
            <Icon name="target" size={14} /> Recommended Level
          </span>
          <div className="num" style={{ fontSize: '1.4em' }}>{difficulty}</div>
        </div>
        <div className="card stat">
          <span className="muted small row">
            <Icon name="flame" size={14} /> Learning Pace
          </span>
          <div className="num" style={{ fontSize: '1.4em' }}>{pace}</div>
        </div>
      </div>

      {/* Current Learning Profile State */}
      <div className="card tip col" style={{ gap: 10 }}>
        <div className="row between">
          <h3>Your Current Learning Profile</h3>
          <span className="pill green">Active</span>
        </div>
        <p className="small muted">
          Current Level: <strong>{predictedMastery}</strong> · Tests Completed: <strong>{testsCompleted}</strong> · Active Focus: <strong>{currentTopic}</strong>
        </p>
        {learningState?.status_message && (
          <p className="tiny muted">{learningState.status_message}</p>
        )}
      </div>

      {/* Unit & Topic Mastery Breakdown */}
      {syllabusSubject.map((sub, sIdx) => (
        <div key={sIdx} className="card col" style={{ gap: 16 }}>
          <div className="row between">
            <div>
              <h3>{sub.name}</h3>
              <p className="hint">{sub.code} · SRMIST PPS Syllabus</p>
            </div>
            <strong>{sub.mastery}% Overall</strong>
          </div>

          <div className="grid g2 mt8">
            {sub.modules.map((m) => (
              <div key={m.id} className="card soft col" style={{ padding: 14, gap: 8 }}>
                <div className="row between small">
                  <strong>{m.title} <span className="pill violet">{m.co}</span></strong>
                  <span className="muted">{m.mastery}%</span>
                </div>
                <Bar value={m.mastery} />
                <div className="col mt8" style={{ gap: 4 }}>
                  {m.topics.map((t, ti) => (
                    <div key={ti} className="row between small">
                      <span className="muted">{t.title}</span>
                      <StatusPill status={t.status} />
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}

      {/* Assessment History */}
      <div className="card col" style={{ gap: 12 }}>
        <h3>Assessment History</h3>
        <p className="hint">Chronological record of formal tests and practice checks.</p>
        {assessmentHistory.length > 0 ? (
          <div className="col mt8" style={{ gap: 8 }}>
            {assessmentHistory.map((att) => (
              <div key={att.id} className="list-item">
                <div className="grow small">
                  <strong>{att.title}</strong>
                  <div className="hint">{att.time}</div>
                </div>
                <span className={`pill ${att.score >= 85 ? 'green' : att.score >= 60 ? 'violet' : 'amber'}`}>
                  {att.score}%
                </span>
                <button
                  type="button"
                  className="btn sm"
                  onClick={() => onNavigate('results')}
                >
                  Review
                </button>
              </div>
            ))}
          </div>
        ) : (
          <div className="empty mt8">
            No assessment attempts recorded yet. Complete your first topic check to view your score history and diagnostic insights.
          </div>
        )}
      </div>
    </div>
  );
}
