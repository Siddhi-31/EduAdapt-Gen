import React, { useEffect, useState } from 'react';
import {
  fetchPracticeMcqs,
  submitPracticeSession,
  generatePracticeProblems,
  executePracticeCode,
} from '../api/learningApi';
import { Bar, Icon, Loading, Spinner, StatusPill, fmtTime } from '../components/ui';

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

export default function Practice({
  studentId = 'S001',
  currentTopic = 'Pointers',
  onTopicChange,
  onNavigate,
  onAssessmentCompleted,
  onAskTutorWithContext,
}) {
  const [activeTab, setActiveTab] = useState('mcq'); // 'mcq' | 'ai_challenge'

  // Mode 1: 5-Question Curriculum MCQs
  const [practiceQuestions, setPracticeQuestions] = useState([]);
  const [currentQIdx, setCurrentQIdx] = useState(0);
  const [practiceAnswers, setPracticeAnswers] = useState({});
  const [practiceSubmitted, setPracticeSubmitted] = useState(false);
  const [practiceResult, setPracticeResult] = useState(null);
  const [startTime, setStartTime] = useState(Date.now());
  const [isLoadingMcq, setIsLoadingMcq] = useState(true);
  const [isSubmittingMcq, setIsSubmittingMcq] = useState(false);

  // Mode 2: AI Coding Challenge & Sandbox
  const [aiProblems, setAiProblems] = useState(null);
  const [isLoadingAi, setIsLoadingAi] = useState(false);
  const [revealedHints, setRevealedHints] = useState({});
  const [studentCode, setStudentCode] = useState('');
  const [isRunningCode, setIsRunningCode] = useState(false);
  const [isSubmittingCode, setIsSubmittingCode] = useState(false);
  const [execResult, setExecResult] = useState(null);
  const [customStdin, setCustomStdin] = useState('');
  const [errorMessage, setErrorMessage] = useState(null);

  // Load 5-Question MCQs
  useEffect(() => {
    let isMounted = true;
    setIsLoadingMcq(true);
    setErrorMessage(null);
    setPracticeAnswers({});
    setPracticeSubmitted(false);
    setPracticeResult(null);
    setCurrentQIdx(0);
    setStartTime(Date.now());

    fetchPracticeMcqs(studentId, currentTopic)
      .then((data) => {
        if (isMounted) {
          const qs = data?.questions || [];
          setPracticeQuestions(qs);
        }
      })
      .catch((err) => {
        if (isMounted) setErrorMessage(err.message || 'Unable to fetch practice questions.');
      })
      .finally(() => {
        if (isMounted) setIsLoadingMcq(false);
      });

    return () => {
      isMounted = false;
    };
  }, [studentId, currentTopic]);

  useEffect(() => {
    if (activeTab === 'ai_challenge') {
      handleGenerateAiPractice(studentId, currentTopic);
    } else {
      setAiProblems(null);
      setExecResult(null);
    }
  }, [studentId, currentTopic, activeTab]);

  const handleGenerateAiPractice = async (sid = studentId, top = currentTopic) => {
    setIsLoadingAi(true);
    setAiProblems(null);
    setStudentCode('');
    setRevealedHints({});
    setErrorMessage(null);
    setExecResult(null);
    try {
      const data = await generatePracticeProblems(sid, top);
      setAiProblems(data);
      const chal = data?.challenge || (Array.isArray(data?.practice_problems) ? data.practice_problems[0] : null);
      if (chal) {
        if (chal.starter_code) {
          setStudentCode(chal.starter_code);
        } else {
          setStudentCode(
            `#include <stdio.h>\n\n// Complete solution for ${top}\nint main(void) {\n    printf("Hello EduAdapt\\n");\n    return 0;\n}`
          );
        }
        if (chal.sample_input) {
          setCustomStdin(chal.sample_input);
        } else {
          setCustomStdin('');
        }
      }
    } catch (err) {
      setErrorMessage('Unable to load practice challenge: ' + (err.message || 'Check connection status'));
    } finally {
      setIsLoadingAi(false);
    }
  };

  const handleSelectAnswer = (optionStr) => {
    if (practiceSubmitted) return;
    const letter = optionStr.trim().charAt(0).toUpperCase();
    setPracticeAnswers((prev) => ({
      ...prev,
      [currentQIdx]: letter,
    }));
  };

  const handleSubmitPractice = async () => {
    if (isSubmittingMcq || practiceQuestions.length === 0) return;
    setIsSubmittingMcq(true);
    setErrorMessage(null);
    const duration = Math.round((Date.now() - startTime) / 1000) || 25;

    try {
      const res = await submitPracticeSession(studentId, currentTopic, practiceAnswers, duration);
      setPracticeResult(res);
      setPracticeSubmitted(true);
      if (onAssessmentCompleted) {
        onAssessmentCompleted({
          ...res,
          type: 'practice_mcq',
        });
      }
    } catch (err) {
      setErrorMessage('Unable to submit practice session: ' + (err.message || 'Check network connection'));
    } finally {
      setIsSubmittingMcq(false);
    }
  };

  const handleResetPractice = () => {
    setPracticeAnswers({});
    setPracticeSubmitted(false);
    setPracticeResult(null);
    setCurrentQIdx(0);
    setStartTime(Date.now());
  };

  const handleRunCode = async () => {
    if (!studentCode.trim() || isRunningCode) return;
    setIsRunningCode(true);
    setErrorMessage(null);
    const chal = aiProblems?.challenge || (Array.isArray(aiProblems?.practice_problems) ? aiProblems.practice_problems[0] : null);
    try {
      const res = await executePracticeCode(
        studentId,
        currentTopic,
        studentCode,
        null,
        false,
        customStdin !== '' ? customStdin : (chal?.sample_input || null),
        30.0
      );
      setExecResult(res);
    } catch (err) {
      setErrorMessage('Code execution error: ' + (err.message || 'Compiler execution failed'));
    } finally {
      setIsRunningCode(false);
    }
  };

  const handleSubmitCode = async () => {
    if (!studentCode.trim() || isSubmittingCode) return;
    setIsSubmittingCode(true);
    setErrorMessage(null);
    const chal = aiProblems?.challenge || (Array.isArray(aiProblems?.practice_problems) ? aiProblems.practice_problems[0] : null);
    try {
      const allTestCases = chal?.expected_test_cases && chal.expected_test_cases.length > 0
        ? chal.expected_test_cases
        : null;
      const res = await executePracticeCode(
        studentId,
        currentTopic,
        studentCode,
        chal?.expected_output || chal?.sample_output || null,
        true,
        chal?.sample_input || customStdin || null,
        30.0,
        allTestCases
      );
      setExecResult(res);
      if (res.passed && onAssessmentCompleted) {
        onAssessmentCompleted({
          is_correct: true,
          score: 100,
          topic: currentTopic,
          student_id: studentId,
          type: 'coding_challenge',
          updated_student: res.updated_student,
          updated_learning_state: res.updated_learning_state,
        });
      }
    } catch (err) {
      setErrorMessage('Submission evaluation error: ' + (err.message || 'Evaluation failed'));
    } finally {
      setIsSubmittingCode(false);
    }
  };

  const handleResetCode = () => {
    const chal = aiProblems?.challenge || (Array.isArray(aiProblems?.practice_problems) ? aiProblems.practice_problems[0] : null);
    if (chal && chal.starter_code) {
      setStudentCode(chal.starter_code);
    }
    if (chal && chal.sample_input) {
      setCustomStdin(chal.sample_input);
    } else {
      setCustomStdin('');
    }
    setExecResult(null);
  };

  const currentQ = practiceQuestions[currentQIdx];
  const totalQuestions = practiceQuestions.length || 5;
  const answeredCount = Object.keys(practiceAnswers).length;
  const currentChallenge = aiProblems?.challenge || (Array.isArray(aiProblems?.practice_problems) ? aiProblems.practice_problems[0] : null);

  return (
    <div className="page">
      <div className="page-head">
        <div>
          <span className="eyebrow plain">Practice & Code</span>
          <h1>Practice: {currentTopic}</h1>
          <p className="muted">
            Concept checks and interactive C coding practice for Student <strong>{studentId}</strong>.
          </p>
        </div>

        <div className="row">
          {onTopicChange && (
            <select
              className="input"
              style={{ width: 'auto', minWidth: 170 }}
              value={currentTopic}
              onChange={(e) => onTopicChange(e.target.value)}
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
          )}

          <div className="chip-select">
            <button
              type="button"
              className={activeTab === 'mcq' ? 'on' : ''}
              onClick={() => setActiveTab('mcq')}
            >
              <Icon name="check" size={14} /> Concept Checks (5)
            </button>
            <button
              type="button"
              className={activeTab === 'ai_challenge' ? 'on' : ''}
              onClick={() => setActiveTab('ai_challenge')}
            >
              <Icon name="code" size={14} /> C Code Practice
            </button>
          </div>
        </div>
      </div>

      {errorMessage && <p className="error-box">{errorMessage}</p>}

      {/* Mode 1: 5-Question Curriculum MCQs */}
      {activeTab === 'mcq' && (
        <>
          {isLoadingMcq && <Loading />}

          {!isLoadingMcq && practiceQuestions.length > 0 && !practiceSubmitted && currentQ && (
            <div className="grid" style={{ gridTemplateColumns: '2fr 1fr', alignItems: 'start' }}>
              <div className="card col" style={{ gap: 16 }}>
                <div className="row between">
                  <span className="eyebrow">
                    Question {currentQIdx + 1} of {totalQuestions}
                  </span>
                  <div className="row">
                    <span className="pill violet">{currentQ.concept || currentTopic}</span>
                    <span className="pill">{currentQ.difficulty || 'Intermediate'}</span>
                  </div>
                </div>

                <h2 style={{ fontWeight: 500, fontSize: '1.25em', lineHeight: 1.5 }}>
                  {currentQ.question}
                </h2>

                <div className="col" role="radiogroup">
                  {(currentQ.options || []).map((opt, optIdx) => {
                    const letter = opt.trim().charAt(0).toUpperCase();
                    const isSelected = practiceAnswers[currentQIdx] === letter;
                    const cleanLabel = opt.substring(opt.indexOf(')') + 1).trim() || opt;

                    return (
                      <button
                        key={optIdx}
                        type="button"
                        role="radio"
                        aria-checked={isSelected}
                        className={`q-opt ${isSelected ? 'on' : ''}`}
                        onClick={() => handleSelectAnswer(opt)}
                      >
                        <span className="k">{letter}</span>
                        <span>{cleanLabel}</span>
                      </button>
                    );
                  })}
                </div>

                <div className="row between mt16">
                  <button
                    type="button"
                    className="btn"
                    disabled={currentQIdx === 0}
                    onClick={() => setCurrentQIdx((prev) => Math.max(0, prev - 1))}
                  >
                    ← Previous
                  </button>

                  <div className="row">
                    {currentQIdx < totalQuestions - 1 && (
                      <button
                        type="button"
                        className="btn"
                        onClick={() => setCurrentQIdx((prev) => Math.min(totalQuestions - 1, prev + 1))}
                      >
                        Next →
                      </button>
                    )}
                    <button
                      type="button"
                      className="btn primary"
                      disabled={isSubmittingMcq || answeredCount === 0}
                      onClick={handleSubmitPractice}
                    >
                      {isSubmittingMcq ? <Spinner /> : `Submit answers (${answeredCount}/${totalQuestions})`}
                    </button>
                  </div>
                </div>
              </div>

              {/* Question Navigator on the Right */}
              <div className="col">
                <div className="card">
                  <h3>Question Navigator</h3>
                  <p className="hint">{answeredCount} of {totalQuestions} answered</p>
                  <div className="q-nav mt16">
                    {practiceQuestions.map((_, k) => {
                      const isAns = practiceAnswers[k] !== undefined;
                      const isCur = k === currentQIdx;
                      return (
                        <button
                          key={k}
                          type="button"
                          className={`${isAns ? 'ans' : ''} ${isCur ? 'cur' : ''}`}
                          onClick={() => setCurrentQIdx(k)}
                        >
                          {k + 1}
                        </button>
                      );
                    })}
                  </div>
                </div>

                <div className="card tip small">
                  Take your time analyzing each memory address and C operator. You can review all answers before final submission.
                </div>
              </div>
            </div>
          )}

          {/* Mode 1: Results View */}
          {practiceSubmitted && practiceResult && (
            <div className="col" style={{ gap: 20 }}>
              <div className="card tip row" style={{ gap: 20 }}>
                <div
                  className="ring"
                  style={{
                    background: `conic-gradient(${
                      practiceResult.score >= 85 ? 'var(--green)' : practiceResult.score >= 60 ? 'var(--primary)' : 'var(--amber)'
                    } ${(practiceResult.score || 0) * 3.6}deg, #dfe3ee 0)`,
                  }}
                >
                  <span>{Math.round(practiceResult.score || 0)}%</span>
                </div>
                <div className="grow">
                  <h2>
                    {practiceResult.score >= 85
                      ? 'Outstanding! You have mastered these conceptual checks.'
                      : practiceResult.score >= 60
                      ? 'Solid performance! Ready for deeper C coding exercises.'
                      : 'Good attempt. Review the step-by-step explanations below.'}
                  </h2>
                  <p className="muted mt8">
                    {practiceResult.feedback || 'Detailed evaluation of your practice session.'}
                  </p>
                </div>
                <span className={`pill ${practiceResult.score >= 60 ? 'green' : 'amber'}`}>
                  {practiceResult.score >= 60 ? 'Passed' : 'Needs Review'}
                </span>
              </div>

              <div className="grid g4">
                <div className="card stat">
                  <span className="muted small">Score</span>
                  <div className="num">{practiceResult.score} / 100</div>
                  <Bar value={practiceResult.score} />
                </div>
                <div className="card stat">
                  <span className="muted small">Accuracy</span>
                  <div className="num">{Math.round(practiceResult.accuracy * 100)}%</div>
                  <Bar value={Math.round(practiceResult.accuracy * 100)} tone="green" />
                </div>
                <div className="card stat">
                  <span className="muted small">Correct</span>
                  <div className="num">{practiceResult.correct_count} / {practiceResult.total_questions}</div>
                </div>
                <div className="card stat">
                  <span className="muted small">Time Taken</span>
                  <div className="num">{practiceResult.time_taken_seconds}s</div>
                </div>
              </div>

              {/* Weak Concepts */}
              {practiceResult.weak_concepts && practiceResult.weak_concepts.length > 0 && (
                <div className="notice">
                  <strong>Concepts to Review: </strong>
                  {practiceResult.weak_concepts.join(' • ')}
                </div>
              )}

              {/* Detailed Breakdown */}
              <div className="card">
                <h3>Detailed Question Review</h3>
                <div className="col mt16" style={{ gap: 14 }}>
                  {(practiceResult.results || []).map((item, idx) => (
                    <div key={idx} className="list-item" style={{ alignItems: 'flex-start' }}>
                      <span className={`pill ${item.is_correct ? 'green' : 'red'}`} style={{ marginTop: 2 }}>
                        {item.is_correct ? 'Correct' : 'Review'}
                      </span>
                      <div className="grow small">
                        <strong>{idx + 1}. {item.question}</strong>
                        <div className="hint mt8">
                          Your answer: <strong>{item.student_answer || '—'}</strong> · Correct answer: <strong style={{ color: 'var(--green)' }}>{item.correct_answer}</strong>
                        </div>
                        <div className="hint mt8">
                          <strong>Explanation:</strong> {item.explanation}
                        </div>
                      </div>
                      {onAskTutorWithContext && !item.is_correct && (
                        <button
                          type="button"
                          className="btn ghost sm"
                          onClick={() => onAskTutorWithContext({ question: item.question, title: item.concept })}
                        >
                          <Icon name="chat" size={14} /> Ask Tutor
                        </button>
                      )}
                    </div>
                  ))}
                </div>

                <div className="row between mt24">
                  <button type="button" className="btn" onClick={handleResetPractice}>
                    Practice Again
                  </button>
                  <div className="row">
                    <button type="button" className="btn" onClick={() => onNavigate('tutor')}>
                      <Icon name="chat" size={16} /> Open Learning Tutor
                    </button>
                    <button type="button" className="btn primary" onClick={() => onNavigate('tests')}>
                      Take Assessment →
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}
        </>
      )}

      {/* Mode 2: AI Adaptive Coding Challenge & Sandbox Workspace */}
      {activeTab === 'ai_challenge' && (
        <div className="col" style={{ gap: 20 }}>
          <div className="row between">
            <div>
              <span className="eyebrow">C99 Code Practice</span>
              <h2 className="mt8">{currentChallenge?.title || `${currentTopic} C Programming Challenge`}</h2>
            </div>
            <button
              type="button"
              className="btn sm"
              onClick={() => handleGenerateAiPractice(studentId, currentTopic)}
              disabled={isLoadingAi}
            >
              <Icon name="refresh" size={14} /> {isLoadingAi ? 'Loading...' : 'New Challenge'}
            </button>
          </div>

          {isLoadingAi && <Loading />}

          {!isLoadingAi && aiProblems && currentChallenge && (
            <div className="coding-layout">
              {/* Left Column: Problem, Hints, Specifications */}
              <div className="col" style={{ gap: 16 }}>
                <div className="card col" style={{ gap: 12 }}>
                  <div className="row between">
                    <span className="pill violet">{currentTopic}</span>
                    <span className="pill">Difficulty: {aiProblems.recommended_difficulty || 'Standard'}</span>
                  </div>
                  <p style={{ lineHeight: 1.6, whiteSpace: 'pre-line' }}>
                    {currentChallenge.problem_statement || currentChallenge.description}
                  </p>
                </div>

                {/* Input/Output Specifications */}
                <div className="card col" style={{ gap: 10 }}>
                  <span className="eyebrow plain">I/O Specifications</span>
                  <div className="small">
                    <strong>Input Format: </strong>
                    <span className="muted">{currentChallenge.input_format || 'Standard input (stdin).'}</span>
                  </div>
                  <div className="small">
                    <strong>Output Format: </strong>
                    <span className="muted">{currentChallenge.output_format || 'Exact output printed to stdout.'}</span>
                  </div>
                  <div className="small">
                    <strong>Constraints: </strong>
                    <span className="muted">{currentChallenge.constraints || 'Standard C99 compliance, no segmentation faults.'}</span>
                  </div>
                </div>

                {/* Sample Test Case */}
                {(currentChallenge.sample_input || currentChallenge.sample_output) && (
                  <div className="card soft col" style={{ gap: 10 }}>
                    <span className="eyebrow plain">Sample Test Case</span>
                    <div className="grid g2">
                      {currentChallenge.sample_input && (
                        <div>
                          <span className="tiny muted">Sample Input:</span>
                          <pre className="src" style={{ margin: '4px 0', fontFamily: 'var(--font-mono)' }}>
                            {currentChallenge.sample_input}
                          </pre>
                        </div>
                      )}
                      {currentChallenge.sample_output && (
                        <div>
                          <span className="tiny muted">Sample Output:</span>
                          <pre className="src" style={{ margin: '4px 0', fontFamily: 'var(--font-mono)' }}>
                            {currentChallenge.sample_output}
                          </pre>
                        </div>
                      )}
                    </div>
                    {currentChallenge.sample_explanation && (
                      <p className="tiny muted">{currentChallenge.sample_explanation}</p>
                    )}
                  </div>
                )}

                {/* Progressive 4-Tier Hint Ladder */}
                <div className="card col" style={{ gap: 12 }}>
                  <span className="eyebrow plain">Progressive Hint Ladder</span>
                  <p className="hint">Reveal hints as needed without spoiling the entire implementation.</p>
                  {[
                    { key: 'hint_1', label: 'Hint 1: Conceptual Foundation', text: currentChallenge.hint_1 || (currentChallenge.hints && currentChallenge.hints[0]) },
                    { key: 'hint_2', label: 'Hint 2: Approach & Memory', text: currentChallenge.hint_2 || (currentChallenge.hints && currentChallenge.hints[1]) },
                    { key: 'hint_3', label: 'Hint 3: Algorithmic Logic', text: currentChallenge.hint_3 || (currentChallenge.hints && currentChallenge.hints[2]) },
                    { key: 'hint_4', label: 'Hint 4: Implementation Guidance', text: currentChallenge.hint_4 || (currentChallenge.hints && currentChallenge.hints[3]) },
                  ].map((h, hIdx) => {
                    const isRevealed = Boolean(revealedHints[h.key]);
                    if (!h.text) return null;
                    return (
                      <div key={hIdx} className="choice" style={{ padding: '10px 14px' }}>
                        <div
                          className="row between"
                          style={{ cursor: 'pointer' }}
                          onClick={() => setRevealedHints((p) => ({ ...p, [h.key]: !p[h.key] }))}
                        >
                          <strong className="small">{h.label}</strong>
                          <span className="tiny muted">{isRevealed ? 'Hide' : 'Reveal'}</span>
                        </div>
                        {isRevealed && (
                          <p className="small mt8" style={{ color: 'var(--ink-2)', lineHeight: 1.5 }}>
                            {h.text}
                          </p>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Right Column: Code Editor & Execution Terminal */}
              <div className="col" style={{ gap: 16 }}>
                <div className="code-editor-box">
                  <div className="code-editor-header">
                    <div className="row" style={{ gap: 8 }}>
                      <Icon name="code" size={15} />
                      <span>solution.c (C99 Standard)</span>
                    </div>
                    <button
                      type="button"
                      className="btn ghost sm"
                      style={{ color: '#cbd5e1', padding: '2px 8px' }}
                      onClick={handleResetCode}
                    >
                      Reset Starter Code
                    </button>
                  </div>

                  <textarea
                    className="code-editor-textarea"
                    value={studentCode}
                    onChange={(e) => setStudentCode(e.target.value)}
                    rows={18}
                    spellCheck="false"
                    placeholder="// Write your C solution here..."
                  />

                  {/* Standard Input (stdin) Panel */}
                  <div style={{ background: '#151828', padding: '10px 16px', borderTop: '1px solid #282e46' }}>
                    <div className="row between" style={{ marginBottom: 6 }}>
                      <span className="tiny muted" style={{ color: '#94a3b8' }}>Standard Input (stdin):</span>
                    </div>
                    <textarea
                      className="input"
                      style={{
                        background: '#0f121e',
                        color: '#f8fafc',
                        border: '1px solid #282e46',
                        fontFamily: 'var(--font-mono)',
                        fontSize: '12px',
                        padding: 8,
                      }}
                      rows={2}
                      value={customStdin}
                      onChange={(e) => setCustomStdin(e.target.value)}
                      placeholder="Pass program inputs (scanf / fgets)..."
                    />
                  </div>

                  <div className="code-toolbar">
                    <span className="tiny muted" style={{ color: '#94a3b8' }}>
                      C99 Compiler · Protected Execution
                    </span>
                    <div className="row">
                      <button
                        type="button"
                        className="btn sm"
                        onClick={handleRunCode}
                        disabled={isRunningCode || isSubmittingCode}
                      >
                        {isRunningCode ? <Spinner /> : <><Icon name="play" size={14} /> Run Code</>}
                      </button>
                      <button
                        type="button"
                        className="btn primary sm"
                        onClick={handleSubmitCode}
                        disabled={isSubmittingCode || isRunningCode}
                      >
                        {isSubmittingCode ? <Spinner /> : <><Icon name="check" size={14} /> Submit Code</>}
                      </button>
                    </div>
                  </div>
                </div>

                {/* Execution Results Terminal Panel */}
                {execResult && (
                  <div
                    className="card"
                    style={{
                      borderLeft: `4px solid ${
                        execResult.status === 'ACCEPTED' || execResult.passed
                          ? 'var(--green)'
                          : execResult.status === 'WRONG_ANSWER'
                          ? 'var(--amber)'
                          : 'var(--red)'
                      }`,
                    }}
                  >
                    <div className="row between">
                      <strong className="small">
                        {execResult.status === 'ACCEPTED' || execResult.passed
                          ? 'Accepted — All Tests Passed'
                          : execResult.status === 'WRONG_ANSWER'
                          ? 'Wrong Answer — Output Mismatch'
                          : execResult.status === 'COMPILATION_ERROR'
                          ? 'Compilation Error'
                          : execResult.status === 'RUNTIME_ERROR'
                          ? `Runtime Error (Exit Code: ${execResult.exit_code ?? -1})`
                          : execResult.status === 'TIMEOUT'
                          ? 'Time Limit Exceeded'
                          : 'Program Executed Successfully'}
                      </strong>
                      <span className="pill">Execution Time: {execResult.execution_time_seconds ?? 0}s</span>
                    </div>

                    {execResult.diagnostic_message && (
                      <p className="hint mt8">{execResult.diagnostic_message}</p>
                    )}

                    {/* Output comparison for wrong answer */}
                    {execResult.status === 'WRONG_ANSWER' && (
                      <div className="grid g2 mt16">
                        <div>
                          <span className="tiny muted">Expected Output:</span>
                          <div className="terminal-box" style={{ color: 'var(--green)' }}>
                            {execResult.expected_output || '(Empty)'}
                          </div>
                        </div>
                        <div>
                          <span className="tiny muted">Your Actual Output:</span>
                          <div className="terminal-box" style={{ color: 'var(--red)' }}>
                            {execResult.actual_output || '(No stdout)'}
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Standard output on success */}
                    {(execResult.status === 'ACCEPTED' || execResult.status === 'SUCCESS' || execResult.passed) && (
                      <div className="mt16">
                        <span className="tiny muted">Program Output (stdout):</span>
                        <div className="terminal-box">
                          {execResult.stdout || '(Program exited normally with empty stdout)'}
                        </div>
                      </div>
                    )}

                    {/* Compiler or Runtime errors */}
                    {(execResult.status === 'COMPILATION_ERROR' || execResult.status === 'RUNTIME_ERROR') && (
                      <div className="mt16">
                        <span className="tiny muted">Diagnostics (stderr):</span>
                        <div className="terminal-box" style={{ color: '#f87171' }}>
                          {execResult.compiler_output || execResult.stderr || 'Execution failed.'}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
