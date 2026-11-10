import React, { useEffect, useState } from 'react';
import { fetchTopicQuestions, submitAssessmentFull } from '../api/learningApi';
import { Bar, Icon, Loading, Spinner, StatusPill } from '../components/ui';

export default function Tests({
  studentId = 'S001',
  currentTopic = 'Pointers',
  onTestCompleted,
}) {
  const [testState, setTestState] = useState('intro'); // 'intro' | 'active'
  const [questions, setQuestions] = useState([]);
  const [currentIdx, setCurrentIdx] = useState(0);
  const [answers, setAnswers] = useState({});
  const [startTime, setStartTime] = useState(null);
  const [timeLeft, setTimeLeft] = useState(600); // 10 minutes default
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [testError, setTestError] = useState(null);
  const [isLoadingQuestions, setIsLoadingQuestions] = useState(true);

  useEffect(() => {
    setIsLoadingQuestions(true);
    fetchTopicQuestions(studentId, currentTopic)
      .then((data) => {
        if (data && data.questions && data.questions.length > 0) {
          setQuestions(data.questions);
        }
      })
      .catch((err) => {
        setTestError('Unable to load assessment questions: ' + (err.message || 'Check network connection'));
      })
      .finally(() => {
        setIsLoadingQuestions(false);
      });
  }, [studentId, currentTopic]);

  useEffect(() => {
    if (testState !== 'active') return;
    const interval = setInterval(() => {
      setTimeLeft((prev) => {
        if (prev <= 1) {
          clearInterval(interval);
          handleSubmitTest();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
    return () => clearInterval(interval);
  }, [testState, answers]);

  const handleStartTest = () => {
    setTestState('active');
    setStartTime(Date.now());
    setTimeLeft(questions.length * 60 || 600);
    setCurrentIdx(0);
    setAnswers({});
  };

  const handleSelectOption = (letter) => {
    setAnswers((prev) => ({
      ...prev,
      [currentIdx]: letter,
    }));
  };

  const handleSubmitTest = async () => {
    if (isSubmitting) return;
    setIsSubmitting(true);
    setTestError(null);
    const durationSec = Math.round((Date.now() - (startTime || Date.now())) / 1000) || 120;

    try {
      const res = await submitAssessmentFull(studentId, currentTopic, answers, durationSec);
      if (onTestCompleted) {
        onTestCompleted({
          ...res,
          questions: questions,
          studentAnswers: answers,
          timeTaken: durationSec,
          title: `Assessment: ${currentTopic}`,
        });
      }
    } catch (err) {
      setTestError('Error submitting test evaluation: ' + (err.message || 'Check network connection'));
      setIsSubmitting(false);
    }
  };

  if (isLoadingQuestions) return <Loading />;

  // Intro state
  if (testState === 'intro') {
    return (
      <div className="page" style={{ maxWidth: 860 }}>
        <div className="page-head">
          <div>
            <span className="eyebrow plain">Assessment</span>
            <h1>Assessment: {currentTopic}</h1>
            <p className="muted">
              10-question evaluation for Student <strong>{studentId}</strong>.
            </p>
          </div>
          <span className="pill violet">Course Evaluation</span>
        </div>

        {testError && <p className="error-box">{testError}</p>}

        <div className="card col" style={{ gap: 20 }}>
          <div className="row between">
            <h3>Assessment Overview</h3>
            <span className="pill green">10 Questions</span>
          </div>

          <div className="grid g2">
            <div className="card soft col" style={{ padding: 14 }}>
              <span className="tiny muted">Subject & Syllabus Unit</span>
              <strong>Programming for Problem Solving (PPS)</strong>
            </div>
            <div className="card soft col" style={{ padding: 14 }}>
              <span className="tiny muted">Target Curriculum Topic</span>
              <strong>{currentTopic}</strong>
            </div>
            <div className="card soft col" style={{ padding: 14 }}>
              <span className="tiny muted">Time Limit</span>
              <strong>10 Minutes (60s / question)</strong>
            </div>
            <div className="card soft col" style={{ padding: 14 }}>
              <span className="tiny muted">Target Passing Mastery</span>
              <strong>85% Advancement Threshold (≥ 60% Passing)</strong>
            </div>
          </div>

          <div className="card tip small">
            <strong>Continuous Progress:</strong> Your score helps tailor subsequent practice problems and updates your topic mastery.
          </div>

          <div className="row between">
            <span className="small muted">{questions.length} questions loaded from question bank</span>
            <button
              type="button"
              className="btn primary"
              onClick={handleStartTest}
              disabled={questions.length === 0}
            >
              Start Assessment →
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Active Test State
  const q = questions[currentIdx] || {};
  const answeredCount = Object.keys(answers).length;
  const currentLetter = answers[currentIdx];

  return (
    <div className="page">
      <div className="page-head">
        <div>
          <span className="eyebrow plain">Timed Evaluation</span>
          <h1>Assessment: {currentTopic}</h1>
          <p className="muted">Answer all 10 questions to complete this assessment.</p>
        </div>
        <div className="row">
          <div className="card stat" style={{ padding: '8px 16px' }}>
            <span className="muted tiny row">
              <Icon name="clock" size={14} /> Time Remaining
            </span>
            <div className="num" style={{ fontSize: '1.3em', margin: 0 }}>
              {Math.floor(timeLeft / 60)}:{String(timeLeft % 60).padStart(2, '0')}
            </div>
          </div>
        </div>
      </div>

      {testError && <p className="error-box">{testError}</p>}

      <div className="grid" style={{ gridTemplateColumns: '2fr 1fr', alignItems: 'start' }}>
        {/* Left Column: Current Question */}
        <div className="card col" style={{ gap: 16 }}>
          <div className="row between">
            <span className="eyebrow">
              Question {currentIdx + 1} of {questions.length}
            </span>
            <span className="pill violet">{q.concept || currentTopic}</span>
          </div>

          <h2 style={{ fontWeight: 500, fontSize: '1.25em', lineHeight: 1.5 }}>
            {q.question}
          </h2>

          <div className="col" role="radiogroup">
            {(q.options || []).map((opt, optIdx) => {
              const letter = opt.trim().charAt(0).toUpperCase();
              const isSelected = currentLetter === letter;
              const cleanText = opt.substring(opt.indexOf(')') + 1).trim() || opt;

              return (
                <button
                  key={optIdx}
                  type="button"
                  role="radio"
                  aria-checked={isSelected}
                  className={`q-opt ${isSelected ? 'on' : ''}`}
                  onClick={() => handleSelectOption(letter)}
                >
                  <span className="k">{letter}</span>
                  <span>{cleanText}</span>
                </button>
              );
            })}
          </div>

          <div className="row between mt16">
            <button
              type="button"
              className="btn"
              disabled={currentIdx === 0}
              onClick={() => setCurrentIdx((p) => Math.max(0, p - 1))}
            >
              ← Previous
            </button>

            <div className="row">
              {currentIdx < questions.length - 1 ? (
                <button
                  type="button"
                  className="btn"
                  onClick={() => setCurrentIdx((p) => Math.min(questions.length - 1, p + 1))}
                >
                  Next →
                </button>
              ) : null}

              <button
                type="button"
                className="btn primary"
                disabled={isSubmitting || answeredCount === 0}
                onClick={handleSubmitTest}
              >
                {isSubmitting ? <Spinner /> : `Submit Assessment (${answeredCount}/${questions.length})`}
              </button>
            </div>
          </div>
        </div>

        {/* Right Column: Navigator */}
        <div className="col">
          <div className="card">
            <h3>Question Navigator</h3>
            <p className="hint">{answeredCount} of {questions.length} answered</p>
            <div className="q-nav mt16">
              {questions.map((_, k) => (
                <button
                  key={k}
                  type="button"
                  className={`${answers[k] !== undefined ? 'ans' : ''} ${k === currentIdx ? 'cur' : ''}`}
                  onClick={() => setCurrentIdx(k)}
                >
                  {k + 1}
                </button>
              ))}
            </div>
          </div>

          <div className="card tip small">
            Take your time. Questions help ensure you have mastered the core concepts before advancing.
          </div>
        </div>
      </div>
    </div>
  );
}
