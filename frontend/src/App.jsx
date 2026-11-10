import React, { useEffect, useState, useRef } from 'react';
import Sidebar from './components/layout/Sidebar';
import LandingPage from './pages/LandingPage';
import Login from './pages/Login';
import Otp from './pages/Otp';
import Home from './pages/Home';
import Learn from './pages/Learn';
import Tutor from './pages/Tutor';
import Practice from './pages/Practice';
import Tests from './pages/Tests';
import Results from './pages/Results';
import Progress from './pages/Progress';
import RoadmapPage from './pages/RoadmapPage';
import ProfilePage from './pages/ProfilePage';
import CurriculumPage from './pages/CurriculumPage';
import Settings from './pages/Settings';
import DiagnosticAssessment from './pages/DiagnosticAssessment';
import { fetchStudentProfile, generateLearningSession } from './api/learningApi';
import { applyAccessibility, getSavedAccessibility } from './components/PreferencesForm';
import { Icon, Loading, Logo } from './components/ui';
import { useAuth } from './lib/auth';
import ProfileManagerModal from './components/ProfileManagerModal';
import { recordAuthenticatedSession, updateActiveSlotProfile } from './lib/profileSlots';

const PAGE_CRUMBS = {
  home: ['Learn', 'Dashboard'],
  curriculum: ['Learn', 'Curriculum'],
  learn: ['Learn', 'Personalized Lesson'],
  roadmap: ['Learn', 'Learning Roadmap'],
  diagnostic: ['Learn', 'Diagnostic Assessment'],
  tutor: ['Practice', 'Learning Tutor'],
  practice: ['Practice', 'Practice & Coding'],
  tests: ['Practice', 'Assessments'],
  results: ['Practice', 'Your Results'],
  progress: ['You', 'Your Progress'],
  profile: ['You', 'Your Profile'],
  settings: ['You', 'Accessibility'],
};

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

export default function App() {
  const [activePage, setActivePage] = useState('landing');
  const [studentId, setStudentId] = useState('S001');
  const [currentTopic, setCurrentTopic] = useState('Variables and Data Types');
  const [isProfileModalOpen, setIsProfileModalOpen] = useState(false);

  const { me, loading: authLoading, logout, isAuthenticated, refresh } = useAuth();

  // Load saved accessibility preferences on startup
  useEffect(() => {
    const saved = getSavedAccessibility();
    if (saved) applyAccessibility(saved);
  }, []);

  // Synchronize authenticated identity from backend
  useEffect(() => {
    if (me?.student) {
      const code = me.student.student_code || 'S001';
      setStudentId(code);
      const isDiagDone = Boolean(me.student.has_completed_diagnostic);
      setStudentProfile((prev) => ({
        ...prev,
        ...me.student,
        student_id: code,
        full_name: me.student.full_name || prev.full_name,
        college: me.student.college || prev.college,
        department: me.student.department || prev.department,
        recommended_difficulty: isDiagDone ? (me.student.current_skill_level || 'Beginner') : 'Not determined',
        learning_pace: isDiagDone ? (me.student.learning_pace || 'Moderate') : 'Not determined',
        has_completed_diagnostic: isDiagDone,
        tests_completed: me.student.tests_completed || (isDiagDone ? 1 : 0),
        recent_attempts: me.student.recent_attempts || [],
        recent_activity: me.student.recent_activity || null,
      }));

      // Record authenticated session in profile slots
      try {
        const t = localStorage.getItem('ea_token');
        if (t && me.user) {
          recordAuthenticatedSession(t, me.user, me.student);
        }
      } catch {}

      if (!isDiagDone && activePage !== 'landing' && activePage !== 'login' && activePage !== 'verify') {
        setActivePage('diagnostic');
      }
    }
  }, [me]);

  // Handle multi-profile switching with total cache purge
  const handleProfileSwitched = async (authData) => {
    setSessionResult(null);
    setLearningState(null);
    setTestResult(null);
    setTutorContextCode('');
    setTutorContextQuestion(null);
    setGlobalError(null);

    // Refresh AuthProvider state for newly selected profile
    try {
      if (refresh) await refresh();
    } catch {}

    if (authData?.student) {
      const code = authData.student.student_code || 'S001';
      setStudentId(code);
      const isDiagDone = Boolean(authData.student.has_completed_diagnostic);
      setStudentProfile({
        student_id: code,
        full_name: authData.student.full_name || 'Student',
        college: authData.student.college || '',
        department: authData.student.department || '',
        recommended_difficulty: isDiagDone ? (authData.student.current_skill_level || 'Beginner') : 'Not determined',
        learning_pace: isDiagDone ? (authData.student.learning_pace || 'Moderate') : 'Not determined',
        has_completed_diagnostic: isDiagDone,
        tests_completed: authData.student.tests_completed || (isDiagDone ? 1 : 0),
        recent_attempts: authData.student.recent_attempts || [],
        recent_activity: authData.student.recent_activity || null,
        mastery: 0.0,
        accuracy: 0.0,
      });

      if (!isDiagDone) {
        setActivePage('diagnostic');
      } else {
        setActivePage('home');
      }
    }
  };

  // Multi-tab storage listener
  useEffect(() => {
    const handleStorageChange = (e) => {
      if (e.key === 'ea_token' || e.key === 'ea_active_slot_index') {
        fetchStudentProfile(studentId)
          .then((p) => {
            if (p) setStudentProfile((prev) => ({ ...prev, ...p }));
          })
          .catch(() => {});
      }
    };
    window.addEventListener('storage', handleStorageChange);
    return () => window.removeEventListener('storage', handleStorageChange);
  }, [studentId]);

  // Request tracking refs for race-condition prevention
  const activeRequestIdRef = useRef(0);
  const activeTopicRef = useRef(currentTopic);

  useEffect(() => {
    activeTopicRef.current = currentTopic;
  }, [currentTopic]);

  const [studentProfile, setStudentProfile] = useState({
    student_id: 'S001',
    full_name: 'Student',
    mastery: 0.0,
    accuracy: 0.0,
    learning_pace: 'Moderate',
    recommended_difficulty: 'Beginner',
    predicted_mastery_level: 'New Learner',
    tests_completed: 0,
  });
  const [sessionResult, setSessionResult] = useState(null);
  const [learningState, setLearningState] = useState(null);
  const [testResult, setTestResult] = useState(null);
  const [tutorContextCode, setTutorContextCode] = useState('');
  const [tutorContextQuestion, setTutorContextQuestion] = useState(null);

  const [isLoadingLesson, setIsLoadingLesson] = useState(false);
  const [globalError, setGlobalError] = useState(null);

  // Load student profile when active studentId changes
  useEffect(() => {
    fetchStudentProfile(studentId)
      .then((data) => {
        setStudentProfile((prev) => ({
          ...prev,
          ...data,
          full_name: me?.student?.full_name || data?.full_name || prev.full_name,
        }));
        if (data?.accessibility) {
          applyAccessibility(data.accessibility);
        }
      })
      .catch((err) => {
        console.warn('Student profile fetch notice:', err);
      });
  }, [studentId, me]);

  const handleResetStudent = () => {
    setStudentProfile({
      student_id: studentId,
      mastery: 0.0,
      accuracy: 0.0,
      learning_pace: 'Moderate',
      recommended_difficulty: 'Beginner',
      predicted_mastery_level: 'New Learner',
      tests_completed: 0,
    });
    setLearningState(null);
    setTestResult(null);
    setSessionResult(null);
    setTutorContextCode('');
    setTutorContextQuestion(null);
    setActivePage('home');
  };

  const handleTopicSwitch = (newTopic) => {
    if (!newTopic) return;
    activeRequestIdRef.current += 1;
    setCurrentTopic(newTopic);
    activeTopicRef.current = newTopic;
    setSessionResult(null);
  };

  const handleGenerateLesson = async (
    topicToUse = currentTopic,
    sId = studentId,
    subtopicToUse = null,
    cycleToUse = null
  ) => {
    const thisRequestId = ++activeRequestIdRef.current;
    activeTopicRef.current = topicToUse;
    setIsLoadingLesson(true);
    setGlobalError(null);
    try {
      const data = await generateLearningSession(sId, topicToUse, 3, 'ollama', 'mistral:7b', subtopicToUse, cycleToUse);

      if (thisRequestId !== activeRequestIdRef.current) return;

      setSessionResult(data);
      if (data.student) {
        setStudentProfile((prev) => ({
          ...prev,
          ...data.student,
        }));
      }
      if (data.learning_state) setLearningState(data.learning_state);
    } catch (err) {
      if (thisRequestId !== activeRequestIdRef.current) return;
      setGlobalError('Lesson loading notice: ' + (err.message || 'Please try again.'));
    } finally {
      setIsLoadingLesson(false);
    }
  };

  const handleNavigate = (pageId) => {
    // Protected student routes requiring authentication
    const protectedPages = ['home', 'learn', 'roadmap', 'tutor', 'practice', 'tests', 'results', 'progress', 'profile', 'settings', 'diagnostic'];
    if (protectedPages.includes(pageId) && !isAuthenticated && !authLoading) {
      setActivePage('login');
      window.scrollTo({ top: 0, behavior: 'smooth' });
      return;
    }

    // New student without completed diagnostic MUST complete diagnostic before entering personalized pages
    if (
      studentProfile?.has_completed_diagnostic === false &&
      !['diagnostic', 'settings', 'login', 'landing', 'verify'].includes(pageId)
    ) {
      setActivePage('diagnostic');
      window.scrollTo({ top: 0, behavior: 'smooth' });
      return;
    }

    setActivePage(pageId);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleLogout = async () => {
    await logout();
    setActivePage('landing');
  };

  const handleSelectStudent = (newStudentId, newProfile) => {
    setStudentId(newStudentId);
    setStudentProfile(newProfile);
    setSessionResult(null);
    setLearningState(null);
    setTestResult(null);
  };

  const handleOpenTutorWithCode = (code) => {
    setTutorContextQuestion(null);
    setTutorContextCode(code);
    setActivePage('tutor');
  };

  const handleOpenTutorWithQuestion = (qContext) => {
    setTutorContextCode('');
    setTutorContextQuestion(qContext);
    setActivePage('tutor');
  };

  const handleAssessmentCompleted = (res) => {
    if (res.updated_learning_state) setLearningState(res.updated_learning_state);
    if (res.updated_student) {
      setStudentProfile((prev) => ({
        ...prev,
        ...res.updated_student,
        tests_completed: (prev?.tests_completed || 0) + 1,
      }));
    }
  };

  const handleTestCompleted = (res) => {
    setTestResult(res);
    if (res.updated_learning_state) setLearningState(res.updated_learning_state);
    if (res.updated_student) {
      setStudentProfile((prev) => ({
        ...prev,
        ...res.updated_student,
        mastery: res.score !== undefined ? res.score / 100 : prev.mastery,
        accuracy: res.score !== undefined ? res.score / 100 : prev.accuracy,
        tests_completed: (prev?.tests_completed || 0) + 1,
      }));
    }
    setActivePage('results');
  };

  if (authLoading) {
    return <Loading />;
  }

  if (activePage === 'login') {
    return (
      <Login
        onLoginSuccess={(authData) => {
          if (authData?.student?.student_code) {
            setStudentId(authData.student.student_code);
          }
          if (authData?.student?.has_completed_diagnostic === false) {
            setActivePage('diagnostic');
          } else {
            setActivePage('home');
          }
        }}
        onNavigate={handleNavigate}
      />
    );
  }

  if (activePage === 'verify') {
    return (
      <Otp
        onVerifySuccess={(data) => {
          if (data?.student?.has_completed_diagnostic === false) {
            setActivePage('diagnostic');
          } else {
            setActivePage('home');
          }
        }}
        onNavigate={handleNavigate}
      />
    );
  }

  if (activePage === 'landing') {
    return (
      <LandingPage
        onNavigate={handleNavigate}
        studentProfile={studentProfile}
        isAuthenticated={isAuthenticated}
      />
    );
  }

  const crumbs = PAGE_CRUMBS[activePage] || ['Learn', 'Dashboard'];

  // Mandatory Diagnostic-First Gating for authenticated students
  if (isAuthenticated && !studentProfile?.has_completed_diagnostic) {
    return (
      <div style={{ minHeight: '100vh', background: 'var(--bg-app, #f8fafc)', display: 'flex', flexDirection: 'column' }}>
        {/* Authoritative Focused Diagnostic Header */}
        <header
          style={{
            background: '#ffffff',
            borderBottom: '1px solid #e2e8f0',
            padding: '12px 24px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <div className="row" style={{ gap: 14, alignItems: 'center' }}>
            <Logo />
            <div style={{ borderLeft: '1px solid #e2e8f0', paddingLeft: 14 }}>
              <span className="eyebrow" style={{ color: '#6366f1' }}>Initial Diagnostic Assessment</span>
              <div className="tiny muted">Mandatory Calibration · Access Gated</div>
            </div>
          </div>

          <div className="row" style={{ gap: 10, alignItems: 'center' }}>
            <div className="row" style={{ gap: 8, alignItems: 'center', padding: '4px 12px', background: '#f1f5f9', borderRadius: 20 }}>
              <span className="avatar" style={{ width: 28, height: 28, fontSize: '0.85em' }}>
                {(studentProfile?.full_name || 'S')[0].toUpperCase()}
              </span>
              <span className="small">
                <strong>{studentProfile?.full_name || 'Student'}</strong> ({studentId})
              </span>
              <span className="pill amber" style={{ padding: '2px 8px', fontSize: '0.75em' }}>Diagnostic Pending</span>
            </div>

            <button
              type="button"
              className="btn sm"
              style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}
              onClick={() => setIsProfileModalOpen(true)}
              title="Open 5-Profile Account Manager"
            >
              <Icon name="user" size={14} />
              <span>Profiles (5 Slots)</span>
            </button>

            <button
              type="button"
              className="btn ghost sm"
              onClick={handleLogout}
              title="Sign Out"
            >
              <Icon name="out" size={14} />
              <span>Sign Out</span>
            </button>
          </div>
        </header>

        {/* Focused Diagnostic Experience */}
        <main style={{ flex: 1, padding: '24px 16px' }}>
          <DiagnosticAssessment
            student={studentProfile}
            onCompleted={(summary) => {
              setStudentProfile((prev) => ({
                ...prev,
                has_completed_diagnostic: true,
                recommended_difficulty: summary.learning_level,
                learning_pace: summary.recommended_pace,
                accuracy: summary.accuracy_pct / 100,
                tests_completed: (prev?.tests_completed || 0) + 1,
                recent_activity: {
                  title: 'Initial Diagnostic Assessment',
                  score: summary.accuracy_pct,
                  time: 'Just now',
                },
                recent_attempts: [
                  {
                    id: summary.attempt_id,
                    title: 'Initial Diagnostic Assessment',
                    type: 'diagnostic',
                    score: summary.accuracy_pct,
                    time: 'Just now',
                    level: summary.learning_level,
                  },
                  ...(prev?.recent_attempts || []),
                ],
              }));
              updateActiveSlotProfile({
                has_completed_diagnostic: true,
                current_skill_level: summary.learning_level,
                learning_pace: summary.recommended_pace,
              });
              setActivePage('diagnostic');
            }}
            onNavigate={handleNavigate}
          />
        </main>

        <ProfileManagerModal
          isOpen={isProfileModalOpen}
          onClose={() => setIsProfileModalOpen(false)}
          onProfileSwitched={handleProfileSwitched}
          currentStudent={studentProfile}
        />
      </div>
    );
  }

  return (
    <div className="shell">
      {/* Sleek Reference Sidebar */}
      <Sidebar
        activePage={activePage}
        onNavigate={handleNavigate}
        studentId={studentId}
        studentProfile={studentProfile}
        onReset={handleResetStudent}
        onLogout={handleLogout}
        onOpenProfileManager={() => setIsProfileModalOpen(true)}
      />

      {/* Main App Content */}
      <main className="main">
        {/* Authoritative Top Navigation Bar */}
        <header className="main-top">
          <div className="row" style={{ gap: 8 }}>
            <span>{crumbs[0]}</span>
            <span>›</span>
            <strong>{crumbs[1]}</strong>
          </div>

          <div className="row">
            {/* Quick Topic Selector */}
            <div className="row" style={{ gap: 6 }}>
              <span className="tiny muted">Topic:</span>
              <select
                className="input"
                style={{ padding: '4px 10px', fontSize: '0.85em', width: 'auto' }}
                value={currentTopic}
                onChange={(e) => handleTopicSwitch(e.target.value)}
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
            </div>

            <button
              type="button"
              className="btn sm"
              style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}
              onClick={() => setIsProfileModalOpen(true)}
              title="Open 5-Profile Account Manager"
            >
              <Icon name="user" size={14} />
              <span>Profiles (5 Slots)</span>
            </button>

            <span className="pill violet">{studentProfile?.recommended_difficulty || 'Beginner'} Level</span>
            <span className="pill green">PPS Course</span>
          </div>
        </header>

        {globalError && (
          <div className="page" style={{ paddingBottom: 0 }}>
            <div className="notice" role="alert">
              <strong>Notice: </strong>
              {globalError}
            </div>
          </div>
        )}

        {/* Dynamic Route Pages */}
        {activePage === 'diagnostic' && (
          <DiagnosticAssessment
            student={studentProfile}
            onCompleted={(summary) => {
              setStudentProfile((prev) => ({
                ...prev,
                has_completed_diagnostic: true,
                recommended_difficulty: summary.learning_level,
                learning_pace: summary.recommended_pace,
                accuracy: summary.accuracy_pct / 100,
                tests_completed: (prev?.tests_completed || 0) + 1,
              }));
              setActivePage('roadmap');
            }}
            onNavigate={handleNavigate}
          />
        )}

        {activePage === 'home' && (
          <Home
            student={studentProfile}
            currentTopic={currentTopic}
            onNavigate={handleNavigate}
            recentActivity={testResult}
          />
        )}

        {activePage === 'curriculum' && (
          <CurriculumPage
            currentTopic={currentTopic}
            onSelectTopic={handleTopicSwitch}
            onNavigate={handleNavigate}
          />
        )}

        {activePage === 'learn' && (
          <Learn
            studentId={studentId}
            currentTopic={currentTopic}
            onTopicChange={handleTopicSwitch}
            sessionResult={sessionResult}
            onGenerateLesson={(subtopic, cycle) => handleGenerateLesson(currentTopic, studentId, subtopic, cycle)}
            isLoading={isLoadingLesson}
            onNavigate={handleNavigate}
            onOpenTutorWithCode={handleOpenTutorWithCode}
            studentProfile={studentProfile}
          />
        )}

        {activePage === 'roadmap' && (
          <RoadmapPage
            studentId={studentId}
            studentProfile={studentProfile}
            currentTopic={currentTopic}
            sessionResult={sessionResult}
            onNavigate={handleNavigate}
          />
        )}

        {activePage === 'tutor' && (
          <Tutor
            studentId={studentId}
            currentTopic={currentTopic}
            initialContextCode={tutorContextCode}
            initialContextQuestion={tutorContextQuestion}
          />
        )}

        {activePage === 'practice' && (
          <Practice
            studentId={studentId}
            currentTopic={currentTopic}
            onTopicChange={handleTopicSwitch}
            onNavigate={handleNavigate}
            onAssessmentCompleted={handleAssessmentCompleted}
            onAskTutorWithContext={handleOpenTutorWithQuestion}
          />
        )}

        {activePage === 'tests' && (
          <Tests
            studentId={studentId}
            currentTopic={currentTopic}
            onTestCompleted={handleTestCompleted}
          />
        )}

        {activePage === 'results' && (
          <Results
            testResult={testResult}
            currentTopic={currentTopic}
            onNavigate={handleNavigate}
            onTopicChange={handleTopicSwitch}
          />
        )}

        {activePage === 'progress' && (
          <Progress
            student={studentProfile}
            learningState={learningState}
            currentTopic={currentTopic}
            roadmapData={sessionResult?.roadmap}
            onNavigate={handleNavigate}
          />
        )}

        {activePage === 'profile' && (
          <ProfilePage
            currentStudentId={studentId}
            studentProfile={studentProfile}
            onSelectStudent={handleSelectStudent}
            onNavigate={handleNavigate}
          />
        )}

        {activePage === 'settings' && (
          <Settings
            studentId={studentId}
            studentProfile={studentProfile}
          />
        )}

        <ProfileManagerModal
          isOpen={isProfileModalOpen}
          onClose={() => setIsProfileModalOpen(false)}
          onProfileSwitched={handleProfileSwitched}
          currentStudent={studentProfile}
        />
      </main>
    </div>
  );
}
