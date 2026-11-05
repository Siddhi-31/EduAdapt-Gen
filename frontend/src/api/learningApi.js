const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export async function fetchStudentProfile(studentId = 'S001') {
  const res = await fetch(`${API_BASE_URL}/api/student/${encodeURIComponent(studentId)}`);
  if (!res.ok) {
    throw new Error(`HTTP ${res.status}: ${res.statusText}`);
  }
  return await res.json();
}

export async function fetchStudentsList() {
  const res = await fetch(`${API_BASE_URL}/api/students`);
  if (!res.ok) {
    throw new Error(`HTTP ${res.status}: ${res.statusText}`);
  }
  return await res.json();
}

export async function generateLearningSession(
  studentId = 'S001',
  topic = 'Pointers',
  topK = 3,
  provider = 'ollama',
  model = 'mistral:7b',
  subtopic = null,
  learningCycle = null
) {
  const payload = {
    student_id: studentId,
    topic: topic,
    top_k: Number(topK),
    provider: provider,
    model: model,
  };
  if (subtopic) payload.subtopic = subtopic;
  if (learningCycle) payload.learning_cycle = Number(learningCycle);

  const res = await fetch(`${API_BASE_URL}/api/session/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const j = await res.json();
      if (j.detail) detail = j.detail;
    } catch {}
    throw new Error(detail);
  }
  return await res.json();
}

export async function askAiTutor(studentId = 'S001', topic = 'Pointers', message = '', promptVariation = null) {
  const res = await fetch(`${API_BASE_URL}/api/tutor/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      student_id: studentId,
      topic: topic,
      message: message,
      prompt_variation: promptVariation,
    }),
  });
  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const j = await res.json();
      if (j.detail) detail = j.detail;
    } catch {}
    throw new Error(detail);
  }
  return await res.json();
}

export async function fetchTutorHistory(studentId = 'S001', topic = 'Pointers') {
  const res = await fetch(`${API_BASE_URL}/api/tutor/history/${encodeURIComponent(studentId)}/${encodeURIComponent(topic)}`);
  if (!res.ok) {
    throw new Error(`HTTP ${res.status}: ${res.statusText}`);
  }
  return await res.json();
}

export async function clearTutorHistory(studentId = 'S001', topic = 'Pointers') {
  const res = await fetch(`${API_BASE_URL}/api/tutor/history/${encodeURIComponent(studentId)}/${encodeURIComponent(topic)}`, {
    method: 'DELETE',
  });
  if (!res.ok) {
    throw new Error(`HTTP ${res.status}: ${res.statusText}`);
  }
  return await res.json();
}

export async function fetchTopicAssessment(studentId = 'S001', topic = 'Pointers') {
  const res = await fetch(`${API_BASE_URL}/api/assessment/${encodeURIComponent(studentId)}/${encodeURIComponent(topic)}`);
  if (!res.ok) {
    throw new Error(`HTTP ${res.status}: ${res.statusText}`);
  }
  return await res.json();
}

export async function fetchTopicQuestions(studentId = 'S001', topic = 'Pointers') {
  const res = await fetch(`${API_BASE_URL}/api/assessment/${encodeURIComponent(studentId)}/${encodeURIComponent(topic)}/all`);
  if (!res.ok) {
    throw new Error(`HTTP ${res.status}: ${res.statusText}`);
  }
  return await res.json();
}

export async function fetchPracticeMcqs(studentId = 'S001', topic = 'Pointers') {
  const res = await fetch(`${API_BASE_URL}/api/practice/${encodeURIComponent(studentId)}/${encodeURIComponent(topic)}/mcqs`);
  if (!res.ok) {
    throw new Error(`HTTP ${res.status}: ${res.statusText}`);
  }
  return await res.json();
}

export async function submitPracticeSession(studentId = 'S001', topic = 'Pointers', answers = {}, timeTaken = 25) {
  const res = await fetch(`${API_BASE_URL}/api/practice/submit`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      student_id: studentId,
      topic: topic,
      answers: answers,
      time_taken_seconds: Number(timeTaken),
    }),
  });
  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const j = await res.json();
      if (j.detail) detail = j.detail;
    } catch {}
    throw new Error(detail);
  }
  return await res.json();
}

export async function submitAssessmentFull(studentId = 'S001', topic = 'Pointers', answers = {}, timeTaken = 120) {
  const res = await fetch(`${API_BASE_URL}/api/assessment/submit`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      student_id: studentId,
      topic: topic,
      answers: answers,
      time_taken_seconds: Number(timeTaken),
    }),
  });
  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const j = await res.json();
      if (j.detail) detail = j.detail;
    } catch {}
    throw new Error(detail);
  }
  return await res.json();
}

export async function fetchStudentRoadmap(studentId = 'S001') {
  const res = await fetch(`${API_BASE_URL}/api/roadmap/${encodeURIComponent(studentId)}`);
  if (!res.ok) {
    throw new Error(`HTTP ${res.status}: ${res.statusText}`);
  }
  return await res.json();
}

export async function advanceStudentTopic(studentId = 'S001', topic = 'Pointers') {
  const res = await fetch(`${API_BASE_URL}/api/roadmap/${encodeURIComponent(studentId)}/advance?topic=${encodeURIComponent(topic)}`, {
    method: 'POST',
  });
  if (!res.ok) {
    throw new Error(`HTTP ${res.status}: ${res.statusText}`);
  }
  return await res.json();
}

export async function submitAssessmentAnswer(studentId = 'S001', topic = 'Pointers', selectedOption = 'B', timeTaken = 25) {
  const res = await fetch(`${API_BASE_URL}/api/assessment/submit`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      student_id: studentId,
      topic: topic,
      selected_option: selectedOption,
      time_taken_seconds: Number(timeTaken),
    }),
  });
  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const j = await res.json();
      if (j.detail) detail = j.detail;
    } catch {}
    throw new Error(detail);
  }
  return await res.json();
}

export async function generatePracticeProblems(studentId = 'S001', topic = 'Pointers') {
  const res = await fetch(`${API_BASE_URL}/api/practice/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      student_id: studentId,
      topic: topic,
    }),
  });
  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const j = await res.json();
      if (j.detail) detail = j.detail;
    } catch {}
    throw new Error(detail);
  }
  return await res.json();
}

export async function executePracticeCode(studentId = 'S001', topic = 'Pointers', sourceCode = '', expectedOutput = null, isSubmission = false, stdinInput = null, timeoutSeconds = 30.0, testCases = null) {
  const res = await fetch(`${API_BASE_URL}/api/practice/execute`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      student_id: studentId,
      topic: topic,
      source_code: sourceCode,
      expected_output: expectedOutput,
      stdin_input: stdinInput,
      test_cases: testCases,
      timeout_seconds: Number(timeoutSeconds),
      is_submission: isSubmission,
    }),
  });
  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const j = await res.json();
      if (j.detail) detail = j.detail;
    } catch {}
    throw new Error(detail);
  }
  return await res.json();
}

export async function generateAdaptiveRoadmap(studentId = 'S001', topic = 'Pointers') {
  const res = await fetch(`${API_BASE_URL}/api/roadmap/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      student_id: studentId,
      topic: topic,
    }),
  });
  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const j = await res.json();
      if (j.detail) detail = j.detail;
    } catch {}
    throw new Error(detail);
  }
  return await res.json();
}

export async function fetchCurriculumTopics() {
  const res = await fetch(`${API_BASE_URL}/api/curriculum/topics`);
  if (!res.ok) {
    throw new Error(`HTTP ${res.status}: ${res.statusText}`);
  }
  return await res.json();
}

export async function searchCurriculum(query, topK = 3) {
  const res = await fetch(`${API_BASE_URL}/api/curriculum/search`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      query: query,
      top_k: Number(topK),
    }),
  });
  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const j = await res.json();
      if (j.detail) detail = j.detail;
    } catch {}
    throw new Error(detail);
  }
  return await res.json();
}

export async function fetchAudioStatus() {
  const res = await fetch(`${API_BASE_URL}/api/audio/status`);
  if (!res.ok) {
    throw new Error(`HTTP ${res.status}: ${res.statusText}`);
  }
  return await res.json();
}

export async function synthesizeLessonAudio(text, rate = 170) {
  const res = await fetch(`${API_BASE_URL}/api/audio/synthesize`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, rate }),
  });
  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const j = await res.json();
      if (j.detail) detail = j.detail;
    } catch {}
    throw new Error(detail);
  }
  return await res.blob();
}

export async function transcribeAudioFile(file) {
  const formData = new FormData();
  formData.append('file', file);
  const res = await fetch(`${API_BASE_URL}/api/audio/transcribe`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const j = await res.json();
      if (j.detail) detail = j.detail;
    } catch {}
    throw new Error(detail);
  }
  return await res.json();
}

export async function fetchCurriculumTree() {
  const res = await fetch(`${API_BASE_URL}/api/curriculum/tree`);
  if (!res.ok) {
    throw new Error(`HTTP ${res.status}: ${res.statusText}`);
  }
  return await res.json();
}

export async function fetchSubtopics(topic) {
  const res = await fetch(`${API_BASE_URL}/api/curriculum/subtopics/${encodeURIComponent(topic)}`);
  if (!res.ok) {
    throw new Error(`HTTP ${res.status}: ${res.statusText}`);
  }
  return await res.json();
}

export async function fetchSubtopicProgress(studentId, topic) {
  const res = await fetch(`${API_BASE_URL}/api/subtopics/progress/${encodeURIComponent(studentId)}/${encodeURIComponent(topic)}`);
  if (!res.ok) {
    throw new Error(`HTTP ${res.status}: ${res.statusText}`);
  }
  return await res.json();
}

export async function fetchSubtopicRoadmap(studentId, topic) {
  const res = await fetch(`${API_BASE_URL}/api/subtopics/roadmap/${encodeURIComponent(studentId)}/${encodeURIComponent(topic)}`);
  if (!res.ok) {
    throw new Error(`HTTP ${res.status}: ${res.statusText}`);
  }
  return await res.json();
}

export async function markSubtopicReadingComplete(studentId, topic, subtopicId) {
  const res = await fetch(`${API_BASE_URL}/api/subtopics/reading/complete`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      student_id: studentId,
      topic: topic,
      subtopic_id: subtopicId,
    }),
  });
  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const j = await res.json();
      if (j.detail) detail = j.detail;
    } catch {}
    throw new Error(detail);
  }
  return await res.json();
}

export async function submitSubtopicMasteryCheck(
  studentId,
  topic,
  subtopicId,
  selectedOption,
  timeTakenSeconds = 25,
  customQuestion = null,
  isRemedial = false
) {
  const res = await fetch(`${API_BASE_URL}/api/subtopics/mastery-check/submit`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      student_id: studentId,
      topic: topic,
      subtopic_id: subtopicId,
      selected_option: selectedOption,
      time_taken_seconds: timeTakenSeconds,
      custom_question: customQuestion,
      is_remedial: isRemedial,
    }),
  });
  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const j = await res.json();
      if (j.detail) detail = j.detail;
    } catch {}
    throw new Error(detail);
  }
  return await res.json();
}

export async function resetSubtopicProgress(studentId, topic) {
  const res = await fetch(`${API_BASE_URL}/api/subtopics/reset`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      student_id: studentId,
      topic: topic,
    }),
  });
  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const j = await res.json();
      if (j.detail) detail = j.detail;
    } catch {}
    throw new Error(detail);
  }
  return await res.json();
}

export async function advanceSubtopicCycle(studentId, topic, subtopicId, score = 85.0, isCorrect = true, weakConcepts = []) {
  const res = await fetch(`${API_BASE_URL}/api/subtopics/cycle/advance`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      student_id: studentId,
      topic: topic,
      subtopic_id: subtopicId,
      score: Number(score),
      is_correct: Boolean(isCorrect),
      weak_concepts: weakConcepts,
    }),
  });
  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const j = await res.json();
      if (j.detail) detail = j.detail;
    } catch {}
    throw new Error(detail);
  }
  return await res.json();
}
