import React, { useEffect, useState, useRef } from 'react';
import Sidebar from './components/layout/Sidebar';
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
import { fetchStudentProfile, generateLearningSession } from './api/learningApi';

export default function App() {
  const [activePage, setActivePage] = useState('home');
  const [studentId, setStudentId] = useState('S001');
  const [currentTopic, setCurrentTopic] = useState('Pointers');

  // Authoritative topic and generation request tracking refs
  const activeRequestIdRef = useRef(0);
  const activeTopicRef = useRef(currentTopic);

  useEffect(() => {
    activeTopicRef.current = currentTopic;
  }, [currentTopic]);

  const [studentProfile, setStudentProfile] = useState({
    student_id: 'S001',
    mastery: 1.0,
    accuracy: 1.0,
    learning_pace: 'Fast',
    recommended_difficulty: 'Advanced',
    predicted_mastery_level: 'High',
    tests_completed: 1,
  });
  const [sessionResult, setSessionResult] = useState(null);
  const [learningState, setLearningState] = useState(null);
  const [testResult, setTestResult] = useState(null);
  const [tutorContextCode, setTutorContextCode] = useState('');
  const [tutorContextQuestion, setTutorContextQuestion] = useState(null);

  const [isLoadingLesson, setIsLoadingLesson] = useState(false);
  const [globalError, setGlobalError] = useState(null);

  // 1. Load student profile when active studentId changes
  useEffect(() => {
    fetchStudentProfile(studentId)
      .then((data) => {
        setStudentProfile(data);
      })
      .catch((err) => {
        console.warn('Student profile fetch notice:', err);
      });
  }, [studentId]);

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

  // 2. Authoritative Topic Switch: Cancels in-flight requests and clears previous topic context
  const handleTopicSwitch = (newTopic) => {
    if (!newTopic) return;
    activeRequestIdRef.current += 1; // Immediately invalidate all in-flight responses
    setCurrentTopic(newTopic);
    activeTopicRef.current = newTopic;
    setSessionResult(null);
    handleGenerateLesson(newTopic, studentId, null, null);
  };

  // 3. Fetch lesson session with strict topic-integrity validation
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
      
      // Guard against race conditions and stale in-flight responses
      if (thisRequestId !== activeRequestIdRef.current) {
        console.warn(`[EduAdapt] Discarding stale in-flight response (request ${thisRequestId} vs active ${activeRequestIdRef.current})`);
        return;
      }
      if (data?.topic && data.topic !== activeTopicRef.current) {
        console.warn(`[EduAdapt] Discarding mismatched response: received '${data.topic}' but active topic is '${activeTopicRef.current}'`);
        return;
      }

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
      const msg = err.message && err.message.includes('Mistral')
        ? err.message
        : 'EduAdapt could not connect to Mistral 7B. Please start Ollama and try again.';
      setGlobalError(msg);
    } finally {
      if (thisRequestId === activeRequestIdRef.current) {
        setIsLoadingLesson(false);
      }
    }
  };

  // Auto-generate lesson on navigation to learn if missing or mismatched
  const handleNavigate = (pageId) => {
    setActivePage(pageId);
    const sessionMatches = sessionResult?.topic === currentTopic || sessionResult?.canonical_topic_context?.topic_name === currentTopic;
    if (pageId === 'learn' && (!sessionResult || !sessionMatches) && !isLoadingLesson) {
      handleGenerateLesson(currentTopic, studentId);
    }
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

  return (
    <div className="platform-layout">
      {/* Sidebar Navigation */}
      <Sidebar
        activePage={activePage}
        onNavigate={handleNavigate}
        studentId={studentId}
        onReset={handleResetStudent}
      />

      {/* Main Content Area */}
      <main className="main-content">
        {globalError && (
          <div className="error-box">
            <h4>Backend Connection Notice</h4>
            <p>{globalError}</p>
          </div>
        )}

        {activePage === 'home' && (
          <Home
            student={studentProfile}
            currentTopic={currentTopic}
            onNavigate={handleNavigate}
            recentActivity={testResult}
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

        {activePage === 'roadmap' && (
          <RoadmapPage
            studentId={studentId}
            studentProfile={studentProfile}
            currentTopic={currentTopic}
            sessionResult={sessionResult}
            onNavigate={handleNavigate}
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

        {activePage === 'curriculum' && (
          <CurriculumPage
            currentTopic={currentTopic}
            onSelectTopic={handleTopicSwitch}
            onNavigate={handleNavigate}
          />
        )}
      </main>
    </div>
  );
}
