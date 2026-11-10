import React, { useState, useEffect, useRef } from 'react';
import {
  startDiagnosticAssessment,
  saveDiagnosticProgress,
  submitDiagnosticAssessment,
  fetchDiagnosticResults,
} from '../api/learningApi';
import { Bar, Icon, Loading, Spinner, StatusPill } from '../components/ui';

export default function DiagnosticAssessment({
  student,
  onCompleted,
  onNavigate,
}) {
  const [viewState, setViewState] = useState('loading'); // 'loading' | 'intro' | 'assessment' | 'confirm_submit' | 'results'
  const [attemptId, setAttemptId] = useState(null);
  const [questions, setQuestions] = useState([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [answers, setAnswers] = useState({}); // { [questionId]: 'A' | 'B' | ... }
  const [flaggedIds, setFlaggedIds] = useState(new Set());
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorNotice, setErrorNotice] = useState(null);
  const [resultsData, setResultsData] = useState(null);
  const [questionStartTime, setQuestionStartTime] = useState(Date.now());
  const [questionTimes, setQuestionTimes] = useState({}); // { [questionId]: seconds }
  const [remainingSeconds, setRemainingSeconds] = useState(1200); // Strict 20:00 (1200s)
  const [deadline, setDeadline] = useState(null);
  const [isTimerExpired, setIsTimerExpired] = useState(false);
  const submittedRef = useRef(false);

  const formatTimer = (totalSec) => {
    const s = Math.max(0, Number(totalSec) || 0);
    const mins = Math.floor(s / 60);
    const secs = s % 60;
    return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
  };

  const handleAutoSubmitExpired = async (attIdOverride) => {
    const targetAttemptId = attIdOverride || attemptId;
    if (!targetAttemptId || submittedRef.current) return;
    submittedRef.current = true;
    setIsSubmitting(true);
    setIsTimerExpired(true);

    const submissionAnswers = {};
    questions.forEach((q) => {
      submissionAnswers[q.id] = {
        selected_option: answers[q.id] || null,
        time_taken_seconds: questionTimes[q.id] || 0,
      };
    });

    try {
      const summary = await submitDiagnosticAssessment(targetAttemptId, submissionAnswers);
      setResultsData(summary);
      setViewState('results');
      if (onCompleted) {
        onCompleted(summary);
      }
    } catch (err) {
      console.warn('Auto-submit expired notice:', err);
      try {
        const res = await fetchDiagnosticResults();
        if (res?.has_completed && res?.results) {
          setResultsData(res.results);
          setViewState('results');
          if (onCompleted) onCompleted(res.results);
        }
      } catch {}
    } finally {
      setIsSubmitting(false);
    }
  };

  // Load existing or initialize diagnostic assessment
  useEffect(() => {
    let isMounted = true;
    startDiagnosticAssessment()
      .then((data) => {
        if (!isMounted) return;
        if (data.status === 'completed' && data.result_summary) {
          setResultsData(data.result_summary);
          setViewState('results');
          return;
        }

        setAttemptId(data.attempt_id);
        const qs = data.questions || [];
        setQuestions(qs);

        // Server authoritative deadline and countdown
        if (data.deadline) {
          setDeadline(data.deadline);
          const deadlineMs = new Date(data.deadline).getTime();
          const diff = Math.max(0, Math.floor((deadlineMs - Date.now()) / 1000));
          setRemainingSeconds(diff);
          if (diff <= 0 || data.is_expired) {
            setIsTimerExpired(true);
            setTimeout(() => {
              handleAutoSubmitExpired(data.attempt_id);
            }, 50);
            return;
          }
        } else if (data.time_remaining_seconds !== undefined) {
          setRemainingSeconds(data.time_remaining_seconds);
          if (data.time_remaining_seconds <= 0) {
            setIsTimerExpired(true);
            setTimeout(() => {
              handleAutoSubmitExpired(data.attempt_id);
            }, 50);
            return;
          }
        }

        // Restore saved answers and index
        const initialAnswers = {};
        const initialTimes = {};
        qs.forEach((q) => {
          if (q.selected_answer) initialAnswers[q.id] = q.selected_answer;
          if (q.time_taken_seconds) initialTimes[q.id] = q.time_taken_seconds;
        });
        setAnswers(initialAnswers);
        setQuestionTimes(initialTimes);
        setFlaggedIds(new Set(data.flagged_question_ids || []));
        setCurrentIndex(data.current_question_index || 0);

        // If student has answered any questions, resume immediately into assessment
        if (Object.keys(initialAnswers).length > 0 || (data.current_question_index || 0) > 0) {
          setViewState('assessment');
        } else {
          setViewState('intro');
        }
      })
      .catch((err) => {
        if (!isMounted) return;
        fetchDiagnosticResults()
          .then((res) => {
            if (res?.has_completed && res?.results) {
              setResultsData(res.results);
              setViewState('results');
            } else {
              setErrorNotice('Unable to initialize diagnostic: ' + (err.message || 'Check network connection.'));
              setViewState('intro');
            }
          })
          .catch(() => {
            setErrorNotice('Unable to initialize diagnostic: ' + (err.message || 'Check network connection.'));
            setViewState('intro');
          });
      });

    return () => {
      isMounted = false;
    };
  }, []);

  // Strict Countdown Timer Effect (derives remaining time from authoritative deadline)
  useEffect(() => {
    if (viewState !== 'assessment' && viewState !== 'confirm_submit') return;
    if (!deadline) return;

    const interval = setInterval(() => {
      const deadlineMs = new Date(deadline).getTime();
      const diff = Math.max(0, Math.floor((deadlineMs - Date.now()) / 1000));
      setRemainingSeconds(diff);
      if (diff <= 0) {
        clearInterval(interval);
        setIsTimerExpired(true);
        handleAutoSubmitExpired();
      }
    }, 1000);

    return () => clearInterval(interval);
  }, [viewState, deadline, attemptId, answers, questions]);

  // Track elapsed time per question
  useEffect(() => {
    setQuestionStartTime(Date.now());
  }, [currentIndex]);

  const currentQuestion = questions[currentIndex] || null;

  const handleSelectOption = (optionKey) => {
    if (!currentQuestion || !attemptId || isTimerExpired || isSubmitting) return;
    const elapsedSec = Math.round((Date.now() - questionStartTime) / 1000);
    const prevSec = questionTimes[currentQuestion.id] || 0;
    const newTimes = { ...questionTimes, [currentQuestion.id]: prevSec + elapsedSec };
    const newAnswers = { ...answers, [currentQuestion.id]: optionKey };

    setAnswers(newAnswers);
    setQuestionTimes(newTimes);

    // Auto-save in background
    const savePayload = {};
    Object.keys(newAnswers).forEach((qid) => {
      savePayload[qid] = {
        selected_option: newAnswers[qid],
        time_taken_seconds: newTimes[qid] || 0,
      };
    });

    saveDiagnosticProgress(attemptId, savePayload, currentIndex, Array.from(flaggedIds)).catch((e) =>
      console.warn('Auto-save notice:', e)
    );
  };

  const handleToggleFlag = () => {
    if (!currentQuestion || !attemptId) return;
    const newFlags = new Set(flaggedIds);
    if (newFlags.has(currentQuestion.id)) {
      newFlags.delete(currentQuestion.id);
    } else {
      newFlags.add(currentQuestion.id);
    }
    setFlaggedIds(newFlags);

    saveDiagnosticProgress(attemptId, answers, currentIndex, Array.from(newFlags)).catch(() => {});
  };

  const handleNavigateIndex = (newIdx) => {
    if (newIdx < 0 || newIdx >= questions.length) return;
    setCurrentIndex(newIdx);
    if (attemptId) {
      saveDiagnosticProgress(attemptId, answers, newIdx, Array.from(flaggedIds)).catch(() => {});
    }
  };

  const handleSubmitAttempt = async () => {
    if (!attemptId || submittedRef.current) return;
    submittedRef.current = true;
    setIsSubmitting(true);
    setErrorNotice(null);

    const submissionAnswers = {};
    questions.forEach((q) => {
      submissionAnswers[q.id] = {
        selected_option: answers[q.id] || null,
        time_taken_seconds: questionTimes[q.id] || 0,
      };
    });

    try {
      const summary = await submitDiagnosticAssessment(attemptId, submissionAnswers);
      setResultsData(summary);
      setViewState('results');
      if (onCompleted) {
        onCompleted(summary);
      }
    } catch (err) {
      setErrorNotice('Submission failed: ' + (err.message || 'Please try again.'));
      setViewState('assessment');
    } finally {
      setIsSubmitting(false);
    }
  };

  // 1. Loading View
  if (viewState === 'loading') {
    return <Loading />;
  }

  // 2. Introduction Screen
  if (viewState === 'intro') {
    return (
      <div className="page" style={{ maxWidth: 860, margin: '0 auto' }}>
        <div className="card col" style={{ padding: '36px 32px', gap: 20 }}>
          <div className="row between">
            <span className="eyebrow plain">Phase 1 · Calibration</span>
            <span className="pill violet">25 Questions · ~15-20 min</span>
          </div>

          <div>
            <h1 style={{ fontSize: '2em' }}>Initial Diagnostic Assessment</h1>
            <p className="muted mt8" style={{ fontSize: '1.05em', lineHeight: 1.6 }}>
              Welcome, <strong>{student?.full_name || 'Learner'}</strong>! Before we generate your personalized
              curriculum and lessons, this assessment evaluates your foundational thinking across numerical,
              logical, verbal, and problem-solving skills.
            </p>
          </div>

          {errorNotice && <div className="notice" role="alert">{errorNotice}</div>}

          <div className="grid g3 mt8">
            <div className="card soft col" style={{ padding: 16 }}>
              <span className="icon-chip" style={{ width: 36, height: 36 }}>
                <Icon name="spark" size={18} />
              </span>
              <strong className="mt8 small">Adaptive Calibration</strong>
              <p className="tiny muted mt8">
                Your performance determines your initial learning tier, explanation style, and pacing recommendation.
              </p>
            </div>
            <div className="card soft col" style={{ padding: 16 }}>
              <span className="icon-chip" style={{ width: 36, height: 36 }}>
                <Icon name="check" size={18} />
              </span>
              <strong className="mt8 small">10 Cognitive Domains</strong>
              <p className="tiny muted mt8">
                Tests reasoning, quantitative ability, pattern recognition, reading comprehension, and problem solving.
              </p>
            </div>
            <div className="card soft col" style={{ padding: 16 }}>
              <span className="icon-chip" style={{ width: 36, height: 36 }}>
                <Icon name="refresh" size={18} />
              </span>
              <strong className="mt8 small">Safe & Auto-Saved</strong>
              <p className="tiny muted mt8">
                Your question set and responses are saved continuously. You can refresh or resume without losing progress.
              </p>
            </div>
          </div>

          <div className="card soft col" style={{ padding: 20, gap: 10 }}>
            <strong>Assessment Rules & Guidelines:</strong>
            <ul className="muted small" style={{ paddingLeft: 20, lineHeight: 1.8 }}>
              <li>Total 25 questions selected deterministically from our verified question bank.</li>
              <li>Each question has exactly one correct answer. No negative marking.</li>
              <li>You may flag questions for review and navigate freely between them.</li>
              <li>Correct answers and detailed pedagogical explanations are revealed immediately after submission.</li>
            </ul>
          </div>

          <div className="row end mt8">
            <button
              type="button"
              className="btn primary"
              style={{ padding: '12px 28px', fontSize: '1em' }}
              onClick={() => setViewState('assessment')}
            >
              Start Diagnostic Assessment →
            </button>
          </div>
        </div>
      </div>
    );
  }

  // 3. Results Screen
  if (viewState === 'results' && resultsData) {
    const accuracy = resultsData.accuracy_pct || 0;
    const score = resultsData.correct_count ?? Math.round((accuracy / 100) * (resultsData.total_questions || 25));
    const total = resultsData.total_questions || 25;
    const level = resultsData.learning_level || 'Beginner';
    const pace = resultsData.recommended_pace || 'Moderate';
    const catBreakdown = resultsData.category_breakdown || {};
    const reviewList = resultsData.questions_review || [];

    return (
      <div className="page" style={{ maxWidth: 960, margin: '0 auto', gap: 24 }}>
        <div className="page-head">
          <div>
            <span className="eyebrow plain">Assessment Complete</span>
            <h1>Your Diagnostic Results & Profile</h1>
            <p className="muted">
              Diagnostic assessment submitted successfully. Your personalized learning roadmap has been calibrated.
            </p>
          </div>
          <button
            type="button"
            className="btn primary"
            onClick={() => onNavigate('roadmap')}
          >
            Explore Your Roadmap →
          </button>
        </div>

        {/* Top Metric Cards */}
        <div className="card soft row between" style={{ padding: '12px 20px', alignItems: 'center' }}>
          <div>
            <strong>Student: {student?.full_name || resultsData.student_id || 'Student'}</strong>
            <span className="tiny muted" style={{ marginLeft: 8 }}>({student?.student_id || resultsData.student_id})</span>
          </div>
          <div className="row" style={{ gap: 10 }}>
            <span className="pill green">✓ {resultsData.correct_count ?? score} Correct</span>
            <span className="pill amber">✗ {resultsData.incorrect_count ?? (total - score)} Incorrect</span>
            <span className="pill">○ {resultsData.unanswered_count ?? 0} Unanswered</span>
          </div>
        </div>

        <div className="grid g4">
          <div className="card stat">
            <span className="muted small">Diagnostic Score</span>
            <div className="num" style={{ color: accuracy >= 70 ? '#10b981' : '#6366f1' }}>
              {score} / {total}
            </div>
            <div className="mt8">
              <Bar value={accuracy} tone={accuracy >= 70 ? 'green' : 'violet'} />
            </div>
            <span className="tiny muted mt8">{accuracy}% Overall Accuracy</span>
          </div>

          <div className="card stat">
            <span className="muted small">Assigned Learning Level</span>
            <div className="num" style={{ fontSize: '1.5em' }}>{level}</div>
            <span className="tiny muted mt8">Calibrated from verified score</span>
          </div>

          <div className="card stat">
            <span className="muted small">Recommended Pace</span>
            <div className="num" style={{ fontSize: '1.5em' }}>{pace}</div>
            <span className="tiny muted mt8">Adaptive pacing recommendation</span>
          </div>

          <div className="card stat">
            <span className="muted small">Assessment Status</span>
            <div className="num" style={{ fontSize: '1.2em', color: '#10b981' }}>Verified</div>
            <span className="tiny muted mt8">Saved to PostgreSQL Profile</span>
          </div>
        </div>

        {/* Cognitive Strengths & Focus Areas */}
        <div className="grid g2">
          <div className="card col" style={{ gap: 12 }}>
            <div className="row">
              <span className="icon-chip" style={{ width: 28, height: 28, background: '#dcfce7', color: '#15803d' }}>
                <Icon name="check" size={14} />
              </span>
              <strong>Demonstrated Strengths</strong>
            </div>
            <div className="row wrap" style={{ gap: 8 }}>
              {(resultsData.strengths && resultsData.strengths.length > 0) ? (
                resultsData.strengths.map((s, idx) => (
                  <span key={idx} className="pill green">
                    {s}
                  </span>
                ))
              ) : (
                <span className="pill">Foundational Comprehension</span>
              )}
            </div>
            <p className="tiny muted">
              Concepts where you showed high accuracy and quick deductive problem solving.
            </p>
          </div>

          <div className="card col" style={{ gap: 12 }}>
            <div className="row">
              <span className="icon-chip" style={{ width: 28, height: 28, background: '#fef3c7', color: '#b45309' }}>
                <Icon name="flame" size={14} />
              </span>
              <strong>Target Focus Areas</strong>
            </div>
            <div className="row wrap" style={{ gap: 8 }}>
              {(resultsData.focus_areas && resultsData.focus_areas.length > 0) ? (
                resultsData.focus_areas.map((f, idx) => (
                  <span key={idx} className="pill amber">
                    {f}
                  </span>
                ))
              ) : (
                <span className="pill green">All Core Areas Strong</span>
              )}
            </div>
            <p className="tiny muted">
              Topics where tailored visual analogies and step-by-step scaffolding will be prioritized.
            </p>
          </div>
        </div>

        {/* Category Breakdown */}
        <div className="card col" style={{ gap: 16 }}>
          <h3>Cognitive Category Performance</h3>
          <div className="grid g2" style={{ gap: 16 }}>
            {Object.keys(catBreakdown).map((catName) => {
              const item = catBreakdown[catName];
              const acc = item.accuracy_pct || 0;
              return (
                <div key={catName} className="card soft col" style={{ padding: 14, gap: 6 }}>
                  <div className="row between">
                    <strong className="small">{catName}</strong>
                    <span className="small muted">
                      {item.correct} / {item.total} ({acc}%)
                    </span>
                  </div>
                  <Bar value={acc} tone={acc >= 75 ? 'green' : acc >= 50 ? 'violet' : 'amber'} />
                </div>
              );
            })}
          </div>
        </div>

        {/* Detailed Question Review */}
        {reviewList.length > 0 && (
          <div className="card col" style={{ gap: 16 }}>
            <div className="row between">
              <h3>Detailed Question Review ({reviewList.length} Questions)</h3>
              <span className="tiny muted">Verified Explanations & Correct Answers</span>
            </div>

            <div className="col" style={{ gap: 14 }}>
              {reviewList.map((q, idx) => {
                const isCorrect = q.is_correct;
                return (
                  <div
                    key={q.question_id || idx}
                    className="card soft col"
                    style={{
                      padding: 16,
                      gap: 10,
                      borderLeft: `4px solid ${isCorrect ? '#10b981' : '#ef4444'}`,
                    }}
                  >
                    <div className="row between">
                      <span className="small">
                        <strong>Q{idx + 1}.</strong> {q.category} · {q.difficulty}
                      </span>
                      <span className={`pill ${isCorrect ? 'green' : 'amber'}`}>
                        {isCorrect ? 'Correct' : 'Needs Review'}
                      </span>
                    </div>

                    <p style={{ whiteSpace: 'pre-wrap', lineHeight: 1.5 }}>{q.question_text}</p>

                    <div className="grid g2" style={{ gap: 8 }}>
                      {q.options &&
                        Object.keys(q.options).map((optKey) => {
                          const optText = q.options[optKey];
                          const isStudentPick = String(q.selected_answer).toUpperCase() === optKey.toUpperCase();
                          const isRealCorrect = String(q.correct_answer).toUpperCase() === optKey.toUpperCase();

                          let bg = 'transparent';
                          let border = 'var(--border, #e2e8f0)';
                          if (isRealCorrect) {
                            bg = 'rgba(16, 185, 129, 0.12)';
                            border = '#10b981';
                          } else if (isStudentPick && !isCorrect) {
                            bg = 'rgba(239, 68, 68, 0.12)';
                            border = '#ef4444';
                          }

                          return (
                            <div
                              key={optKey}
                              style={{
                                padding: '8px 12px',
                                borderRadius: 6,
                                background: bg,
                                border: `1px solid ${border}`,
                                fontSize: '0.9em',
                              }}
                            >
                              <strong>{optKey}.</strong> {optText}
                              {isStudentPick && <em> (Your Answer)</em>}
                              {isRealCorrect && <strong> (Correct)</strong>}
                            </div>
                          );
                        })}
                    </div>

                    {q.explanation && (
                      <div className="card" style={{ padding: 10, background: 'rgba(0,0,0,0.02)', fontSize: '0.85em' }}>
                        <strong>Explanation: </strong> {q.explanation}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}

        <div className="card dark col center" style={{ padding: '32px 24px', gap: 14 }}>
          <h2 style={{ color: '#fff' }}>Ready to Begin Your PPS Learning Path?</h2>
          <p className="small" style={{ color: '#c3c6e4', textAlign: 'center', maxWidth: 480 }}>
            Your initial diagnostic profile has been saved to your account. Your learning roadmap is now unlocked.
          </p>
          <div className="row mt8">
            <button
              type="button"
              className="btn primary"
              style={{ padding: '10px 24px' }}
              onClick={() => onNavigate('home')}
            >
              Go to Dashboard →
            </button>
            <button
              type="button"
              className="btn"
              style={{ background: 'transparent', color: '#fff', borderColor: 'rgba(255,255,255,0.35)' }}
              onClick={() => onNavigate('roadmap')}
            >
              View Learning Roadmap
            </button>
          </div>
        </div>
      </div>
    );
  }

  // 4. In-Progress Assessment View
  const answeredCount = Object.keys(answers).length;
  const totalCount = questions.length || 25;
  const progressPercent = Math.round((answeredCount / totalCount) * 100);
  const isFlagged = currentQuestion ? flaggedIds.has(currentQuestion.id) : false;
  const selectedOption = currentQuestion ? answers[currentQuestion.id] : null;

  return (
    <div className="page" style={{ maxWidth: 1000, margin: '0 auto', gap: 18 }}>
      {/* Top Header */}
      <div className="row between">
        <div>
          <span className="eyebrow plain">Initial Diagnostic Assessment</span>
          <h2>
            Question {currentIndex + 1} of {totalCount}
          </h2>
        </div>
        <div className="row" style={{ gap: 10, alignItems: 'center' }}>
          {/* Prominent Authoritative 20-Minute Countdown Timer */}
          <div
            className={`pill ${remainingSeconds < 180 ? 'amber' : 'violet'}`}
            style={{
              fontSize: '1em',
              fontWeight: 700,
              padding: '6px 14px',
              display: 'inline-flex',
              alignItems: 'center',
              gap: 8,
              background: remainingSeconds < 180 ? '#fef3c7' : '#ede9fe',
              color: remainingSeconds < 180 ? '#b45309' : '#4338ca',
              borderColor: remainingSeconds < 180 ? '#f59e0b' : '#a5b4fc',
            }}
          >
            <Icon name="clock" size={16} />
            <span>Time Remaining: {formatTimer(remainingSeconds)}</span>
          </div>

          <span className="pill violet">{currentQuestion?.category || 'General Reasoning'}</span>
          <span className="pill">{currentQuestion?.difficulty || 'Beginner'}</span>
          <button
            type="button"
            className={`btn sm ${isFlagged ? 'amber' : 'ghost'}`}
            onClick={handleToggleFlag}
            title="Flag question to review later"
            disabled={isTimerExpired || isSubmitting}
          >
            <Icon name="spark" size={14} />
            {isFlagged ? 'Flagged for Review' : 'Flag for Review'}
          </button>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="card soft col" style={{ padding: '10px 14px', gap: 6 }}>
        <div className="row between tiny muted">
          <span>{answeredCount} of {totalCount} Answered ({progressPercent}%)</span>
          <span>{flaggedIds.size} Flagged</span>
        </div>
        <Bar value={progressPercent} tone="green" />
      </div>

      {isTimerExpired && (
        <div className="notice" role="alert" style={{ background: '#fef2f2', borderColor: '#f87171', color: '#991b1b', fontWeight: 600 }}>
          <Icon name="clock" size={16} />
          Assessment time limit (20:00) reached. Automatically submitting your saved answers...
        </div>
      )}

      {errorNotice && <div className="notice" role="alert">{errorNotice}</div>}

      {/* Main Assessment Grid: Question Left, Navigation Palette Right */}
      <div className="grid" style={{ gridTemplateColumns: '1fr 280px', gap: 20, alignItems: 'start' }}>
        {/* Left: Active Question Card */}
        <div className="card col" style={{ padding: '28px 24px', gap: 20 }}>
          <div className="row between">
            <span className="small muted">
              Category: <strong>{currentQuestion?.category}</strong>
            </span>
            <span className="tiny muted">1 Mark</span>
          </div>

          <div
            style={{
              fontSize: '1.15em',
              lineHeight: 1.65,
              fontWeight: 500,
              whiteSpace: 'pre-wrap',
            }}
          >
            {currentQuestion?.question_text}
          </div>

          {/* Option Choices */}
          <div className="col" style={{ gap: 10, marginTop: 10 }}>
            {currentQuestion?.options &&
              Object.keys(currentQuestion.options).map((optKey) => {
                const optText = currentQuestion.options[optKey];
                const isSelected = selectedOption === optKey;

                return (
                  <button
                    key={optKey}
                    type="button"
                    className={`choice ${isSelected ? 'on' : ''}`}
                    style={{
                      padding: '14px 18px',
                      display: 'flex',
                      alignItems: 'center',
                      gap: 14,
                      textAlign: 'left',
                      cursor: 'pointer',
                      borderWidth: isSelected ? '2px' : '1px',
                    }}
                    onClick={() => handleSelectOption(optKey)}
                    disabled={isTimerExpired || isSubmitting}
                  >
                    <span
                      style={{
                        width: 28,
                        height: 28,
                        borderRadius: '50%',
                        display: 'inline-flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        background: isSelected ? 'var(--primary, #4338ca)' : 'var(--bg-card, #f1f5f9)',
                        color: isSelected ? '#fff' : 'inherit',
                        fontWeight: 600,
                        fontSize: '0.9em',
                        flexShrink: 0,
                      }}
                    >
                      {optKey}
                    </span>
                    <span style={{ fontSize: '1em', lineHeight: 1.5 }}>{optText}</span>
                  </button>
                );
              })}
          </div>

          {/* Prev / Next / Submit Controls */}
          <div className="row between mt16" style={{ paddingTop: 16, borderTop: '1px solid var(--border, #e2e8f0)' }}>
            <button
              type="button"
              className="btn"
              disabled={currentIndex === 0}
              onClick={() => handleNavigateIndex(currentIndex - 1)}
            >
              ← Previous
            </button>

            <div className="row" style={{ gap: 10 }}>
              {currentIndex < totalCount - 1 ? (
                <button
                  type="button"
                  className="btn primary"
                  onClick={() => handleNavigateIndex(currentIndex + 1)}
                >
                  Next Question →
                </button>
              ) : (
                <button
                  type="button"
                  className="btn primary"
                  style={{ background: '#10b981', borderColor: '#10b981' }}
                  onClick={() => setViewState('confirm_submit')}
                  disabled={isTimerExpired || isSubmitting}
                >
                  Review & Submit Assessment
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Right: Question Navigation Palette */}
        <div className="card col" style={{ padding: 18, gap: 14 }}>
          <div className="row between">
            <strong className="small">Questions Palette</strong>
            <span className="tiny muted">{answeredCount}/{totalCount}</span>
          </div>

          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(5, 1fr)',
              gap: 8,
            }}
          >
            {questions.map((q, idx) => {
              const isAns = Boolean(answers[q.id]);
              const isCur = idx === currentIndex;
              const isFlg = flaggedIds.has(q.id);

              let bg = 'var(--bg-card, #f8fafc)';
              let color = 'inherit';
              let border = '1px solid var(--border, #cbd5e1)';

              if (isCur) {
                border = '2px solid #4338ca';
                bg = '#e0e7ff';
                color = '#3730a3';
              } else if (isFlg) {
                bg = '#fef3c7';
                border = '1px solid #f59e0b';
                color = '#b45309';
              } else if (isAns) {
                bg = '#dcfce7';
                border = '1px solid #10b981';
                color = '#15803d';
              }

              return (
                <button
                  key={q.id || idx}
                  type="button"
                  style={{
                    height: 38,
                    borderRadius: 6,
                    background: bg,
                    color: color,
                    border: border,
                    fontWeight: isCur ? 700 : 500,
                    fontSize: '0.85em',
                    cursor: 'pointer',
                  }}
                  onClick={() => handleNavigateIndex(idx)}
                >
                  {idx + 1}
                </button>
              );
            })}
          </div>

          {/* Palette Legend */}
          <div className="col mt8 tiny muted" style={{ gap: 6 }}>
            <div className="row" style={{ gap: 8 }}>
              <span style={{ width: 12, height: 12, borderRadius: 3, background: '#dcfce7', border: '1px solid #10b981' }} />
              Answered ({answeredCount})
            </div>
            <div className="row" style={{ gap: 8 }}>
              <span style={{ width: 12, height: 12, borderRadius: 3, background: '#fef3c7', border: '1px solid #f59e0b' }} />
              Flagged ({flaggedIds.size})
            </div>
            <div className="row" style={{ gap: 8 }}>
              <span style={{ width: 12, height: 12, borderRadius: 3, background: 'var(--bg-card, #f8fafc)', border: '1px solid #cbd5e1' }} />
              Unanswered ({totalCount - answeredCount})
            </div>
          </div>

          <button
            type="button"
            className="btn primary mt8"
            style={{ width: '100%' }}
            onClick={() => setViewState('confirm_submit')}
            disabled={isTimerExpired || isSubmitting}
          >
            Submit Assessment
          </button>
        </div>
      </div>

      {/* Confirmation Modal */}
      {viewState === 'confirm_submit' && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(0, 0, 0, 0.5)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
            padding: 16,
          }}
        >
          <div className="card col" style={{ maxWidth: 460, width: '100%', padding: 28, gap: 16 }}>
            <h3>Ready to submit your diagnostic?</h3>

            {totalCount - answeredCount > 0 ? (
              <div className="notice" role="alert">
                ⚠️ You have <strong>{totalCount - answeredCount} unanswered questions</strong>. Unanswered questions will receive 0 marks.
              </div>
            ) : (
              <p className="small muted">
                You have answered all {totalCount} questions. Once submitted, your scores and initial learning profile will be generated.
              </p>
            )}

            <div className="row between small muted">
              <span>Total Questions: <strong>{totalCount}</strong></span>
              <span>Answered: <strong>{answeredCount}</strong></span>
              <span>Flagged: <strong>{flaggedIds.size}</strong></span>
            </div>

            <div className="row end mt8" style={{ gap: 10 }}>
              <button
                type="button"
                className="btn"
                disabled={isSubmitting}
                onClick={() => setViewState('assessment')}
              >
                Back to Questions
              </button>
              <button
                type="button"
                className="btn primary"
                disabled={isSubmitting}
                onClick={handleSubmitAttempt}
              >
                {isSubmitting ? <Spinner /> : 'Confirm & Submit'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
