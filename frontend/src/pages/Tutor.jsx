import React, { useState, useRef, useEffect } from 'react';
import {
  askAiTutor,
  fetchTutorHistory,
  clearTutorHistory,
  transcribeAudioFile,
  synthesizeLessonAudio,
} from '../api/learningApi';
import MermaidDiagram from '../components/MermaidDiagram';
import { Icon, Spinner, StatusPill } from '../components/ui';

const getStorageKey = (sid, topic) => `eduadapt_tutor_${sid}_${topic}`;
const getDefaultGreeting = (topic) => [
  {
    role: 'assistant',
    text: `Hello! I am your EduAdapt Learning Tutor for Programming for Problem Solving. Ask me anything about ${topic}, memory layout, pointers, or C code implementation.`,
  },
];

const PPS_ALL_TOPICS = [
  'Variables and Data Types',
  'Operators and Expressions',
  'Conditionals',
  'Loops',
  'Arrays',
  'Strings',
  'Functions',
  'Pointers',
  'Structures',
  'Dynamic Memory Allocation',
];

function ChatMessageContent({ text, onCopyCode }) {
  if (!text) return null;

  const parts = [];
  const blockRegex = /```(c|C|mermaid)?\s*([\s\S]*?)```/g;
  let lastIndex = 0;
  let match;

  while ((match = blockRegex.exec(text)) !== null) {
    if (match.index > lastIndex) {
      const textChunk = text.substring(lastIndex, match.index).trim();
      if (textChunk) {
        parts.push({ type: 'text', content: textChunk });
      }
    }

    const lang = (match[1] || '').toLowerCase();
    const body = match[2].trim();

    if (lang === 'mermaid' || body.startsWith('flowchart') || body.startsWith('graph')) {
      parts.push({ type: 'diagram', content: body });
    } else {
      parts.push({ type: 'code', content: body });
    }

    lastIndex = blockRegex.lastIndex;
  }

  if (lastIndex < text.length) {
    const remaining = text.substring(lastIndex).trim();
    if (remaining) {
      parts.push({ type: 'text', content: remaining });
    }
  }

  if (parts.length === 0) {
    return <div className="md"><p>{text}</p></div>;
  }

  return (
    <div className="md">
      {parts.map((p, idx) => {
        if (p.type === 'code') {
          return (
            <div key={idx} className="code-container">
              <div className="code-header">
                <span>C Code (C99)</span>
                <button
                  type="button"
                  className="btn ghost sm"
                  style={{ color: '#cbd5e1', padding: '2px 8px' }}
                  onClick={() => onCopyCode && onCopyCode(p.content)}
                >
                  <Icon name="copy" size={14} /> Copy
                </button>
              </div>
              <pre className="code-block"><code>{p.content}</code></pre>
            </div>
          );
        }
        if (p.type === 'diagram') {
          return (
            <div key={idx} style={{ margin: '14px 0' }}>
              <MermaidDiagram code={p.content} title="Concept Diagram" />
            </div>
          );
        }
        return (
          <p key={idx} style={{ whiteSpace: 'pre-line' }}>
            {p.content}
          </p>
        );
      })}
    </div>
  );
}

export default function Tutor({
  studentId = 'S001',
  currentTopic = 'Pointers',
  initialContextCode = '',
  initialContextQuestion = null,
}) {
  const [selectedTopic, setSelectedTopic] = useState(currentTopic);
  const activeTopicRef = useRef(selectedTopic);
  const activeStudentRef = useRef(studentId);

  const [messages, setMessages] = useState(() => {
    try {
      const cached = localStorage.getItem(getStorageKey(studentId, currentTopic));
      if (cached) {
        const parsed = JSON.parse(cached);
        if (Array.isArray(parsed) && parsed.length > 0) return parsed;
      }
    } catch {}
    return getDefaultGreeting(currentTopic);
  });
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [copiedNotice, setCopiedNotice] = useState(false);

  // Audio Recording & TTS State
  const [isRecording, setIsRecording] = useState(false);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const [recordingError, setRecordingError] = useState(null);
  const [speakingIdx, setSpeakingIdx] = useState(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const audioPlayerRef = useRef(null);
  const chatEndRef = useRef(null);

  useEffect(() => {
    setSelectedTopic(currentTopic);
  }, [currentTopic]);

  useEffect(() => {
    activeTopicRef.current = selectedTopic;
    activeStudentRef.current = studentId;

    let hasLocal = false;
    try {
      const cached = localStorage.getItem(getStorageKey(studentId, selectedTopic));
      if (cached) {
        const parsed = JSON.parse(cached);
        if (Array.isArray(parsed) && parsed.length > 0) {
          setMessages(parsed);
          hasLocal = true;
        }
      }
    } catch {}

    if (!hasLocal) {
      setMessages(getDefaultGreeting(selectedTopic));
    }

    let isCancelled = false;
    fetchTutorHistory(studentId, selectedTopic)
      .then((res) => {
        if (isCancelled || activeTopicRef.current !== selectedTopic || activeStudentRef.current !== studentId) {
          return;
        }
        if (res && Array.isArray(res.messages) && res.messages.length > 0) {
          setMessages(res.messages);
          try {
            localStorage.setItem(getStorageKey(studentId, selectedTopic), JSON.stringify(res.messages));
          } catch {}
        }
      })
      .catch(() => {});

    return () => {
      isCancelled = true;
    };
  }, [studentId, selectedTopic]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const handleCopyCode = (code) => {
    if (navigator.clipboard) {
      navigator.clipboard.writeText(code);
      setCopiedNotice(true);
      setTimeout(() => setCopiedNotice(false), 2000);
    }
  };

  const handleSendMessage = async (textToSend = inputMessage, promptVariation = null) => {
    const q = (textToSend || '').trim();
    if (!q || isLoading) return;

    setError(null);
    setInputMessage('');

    const newMessages = [...messages, { role: 'user', text: q }];
    setMessages(newMessages);
    setIsLoading(true);

    try {
      const response = await askAiTutor(studentId, selectedTopic, q, promptVariation);
      const answerText = response.answer || response.response || 'I have analyzed your query.';
      const updated = [
        ...newMessages,
        {
          role: 'assistant',
          text: answerText,
          sources: response.sources || [],
          verification: response.verification,
        },
      ];
      setMessages(updated);
      try {
        localStorage.setItem(getStorageKey(studentId, selectedTopic), JSON.stringify(updated));
      } catch {}
    } catch (err) {
      setError('The learning tutor is temporarily unavailable. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleClearChat = async () => {
    try {
      await clearTutorHistory(studentId, selectedTopic);
    } catch {}
    const defaultMsg = getDefaultGreeting(selectedTopic);
    setMessages(defaultMsg);
    try {
      localStorage.removeItem(getStorageKey(studentId, selectedTopic));
    } catch {}
  };

  // Audio Speech To Text
  const startVoiceRecording = async () => {
    setRecordingError(null);
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      setRecordingError('Microphone not supported in this browser.');
      return;
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      audioChunksRef.current = [];
      const recorder = new MediaRecorder(stream);
      mediaRecorderRef.current = recorder;

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) audioChunksRef.current.push(e.data);
      };

      recorder.onstop = async () => {
        stream.getTracks().forEach((track) => track.stop());
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
        if (audioBlob.size === 0) return;

        setIsTranscribing(true);
        try {
          const res = await transcribeAudioFile(audioBlob, 'tutor_query.wav');
          if (res && res.transcription) {
            setInputMessage((prev) => (prev ? `${prev} ${res.transcription}` : res.transcription));
          }
        } catch (err) {
          setRecordingError(`Speech-to-text error: ${err.message}`);
        } finally {
          setIsTranscribing(false);
        }
      };

      recorder.start();
      setIsRecording(true);
    } catch (err) {
      setRecordingError(`Microphone access denied: ${err.message}`);
    }
  };

  const stopVoiceRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  // Read message aloud
  const handleSpeakMessage = async (idx, text) => {
    if (speakingIdx === idx) {
      if (audioPlayerRef.current) audioPlayerRef.current.pause();
      if (window.speechSynthesis) window.speechSynthesis.cancel();
      setSpeakingIdx(null);
      return;
    }

    setSpeakingIdx(idx);
    try {
      const blob = await synthesizeLessonAudio(text.slice(0, 400), 170);
      const url = URL.createObjectURL(blob);
      if (!audioPlayerRef.current) audioPlayerRef.current = new Audio();
      audioPlayerRef.current.src = url;
      audioPlayerRef.current.onended = () => setSpeakingIdx(null);
      audioPlayerRef.current.play();
    } catch {
      if (window.speechSynthesis) {
        window.speechSynthesis.cancel();
        const u = new SpeechSynthesisUtterance(text.slice(0, 400));
        u.onend = () => setSpeakingIdx(null);
        u.onerror = () => setSpeakingIdx(null);
        window.speechSynthesis.speak(u);
      } else {
        setSpeakingIdx(null);
      }
    }
  };

  return (
    <div className="page" style={{ paddingBottom: 24 }}>
      <div className="page-head">
        <div>
          <span className="eyebrow plain">Concept Support</span>
          <h1>Learning Tutor</h1>
          <p className="muted">
            Clear explanations, memory diagrams, and C code guidance tailored to your learning pace.
          </p>
        </div>
        <div className="row">
          <span className="pill violet">{selectedTopic}</span>
          <span className="pill">Student: {studentId}</span>
        </div>
      </div>

      {copiedNotice && (
        <div className="pill green" style={{ alignSelf: 'flex-start' }}>
          Code copied to clipboard
        </div>
      )}

      {/* Main Chat Layout */}
      <div className="chat">
        {/* Left Sidebar: Topic Selector & History */}
        <div className="chat-col" style={{ padding: 14, gap: 14 }}>
          <div className="col" style={{ gap: 8 }}>
            <span className="eyebrow plain">Current Topic</span>
            <select
              className="input"
              value={selectedTopic}
              onChange={(e) => setSelectedTopic(e.target.value)}
            >
              {PPS_ALL_TOPICS.map((top) => (
                <option key={top} value={top}>
                  {top}
                </option>
              ))}
            </select>
          </div>

          <button
            type="button"
            className="btn primary block"
            onClick={handleClearChat}
          >
            <Icon name="plus" size={16} /> New Conversation
          </button>

          {/* Context Card if opened with code or question */}
          {initialContextCode && (
            <div className="card soft col" style={{ padding: 12, gap: 6 }}>
              <strong className="tiny">Code Context Attached</strong>
              <div className="hint" style={{ maxHeight: 60, overflow: 'hidden' }}>
                <code>{initialContextCode.slice(0, 100)}...</code>
              </div>
              <button
                type="button"
                className="btn sm"
                onClick={() => setInputMessage(`Please explain this code and point out potential bugs:\n\`\`\`c\n${initialContextCode}\n\`\`\``)}
              >
                Ask about code
              </button>
            </div>
          )}

          {initialContextQuestion && (
            <div className="card soft col" style={{ padding: 12, gap: 6 }}>
              <strong className="tiny">Practice Question Context</strong>
              <div className="hint">{initialContextQuestion.question || initialContextQuestion.title}</div>
              <button
                type="button"
                className="btn sm"
                onClick={() => setInputMessage(`I'm stuck on this question: "${initialContextQuestion.question}". Can you explain the core concept without giving away the direct answer?`)}
              >
                Ask for hint
              </button>
            </div>
          )}

          <div className="col" style={{ marginTop: 'auto', gap: 6 }}>
            <span className="tiny muted">Suggested Questions:</span>
            <button
              type="button"
              className="btn ghost sm"
              style={{ textAlign: 'left', justifyContent: 'flex-start' }}
              onClick={() => handleSendMessage(`Explain ${selectedTopic} simply with a short example.`)}
            >
              • Explain simply with example
            </button>
            <button
              type="button"
              className="btn ghost sm"
              style={{ textAlign: 'left', justifyContent: 'flex-start' }}
              onClick={() => handleSendMessage(`Show a memory diagram for ${selectedTopic}.`)}
            >
              • Memory layout diagram
            </button>
            <button
              type="button"
              className="btn ghost sm"
              style={{ textAlign: 'left', justifyContent: 'flex-start' }}
              onClick={() => handleSendMessage(`What are the most common compilation and runtime mistakes in ${selectedTopic}?`)}
            >
              • Common runtime bugs
            </button>
          </div>
        </div>

        {/* Right Main Column: Message Stream and Composer */}
        <div className="chat-col">
          <div className="msgs">
            {messages.map((msg, idx) => {
              const isUser = msg.role === 'user';
              return (
                <div key={idx} className={`msg ${isUser ? 'user' : 'ai'}`}>
                  <div className="row between" style={{ marginBottom: 6 }}>
                    <strong className="tiny" style={{ color: isUser ? '#fff' : 'var(--muted)' }}>
                      {isUser ? studentId : 'EduAdapt Learning Tutor'}
                    </strong>
                    {!isUser && (
                      <button
                        type="button"
                        className="btn ghost sm"
                        style={{ padding: 2 }}
                        title="Read response aloud"
                        onClick={() => handleSpeakMessage(idx, msg.text)}
                      >
                        <Icon name="speaker" size={15} />
                      </button>
                    )}
                  </div>

                  <ChatMessageContent text={msg.text} onCopyCode={handleCopyCode} />

                  {msg.sources && msg.sources.length > 0 && (
                    <div className="col mt8" style={{ gap: 4 }}>
                      <span className="tiny muted">Course References:</span>
                      {msg.sources.map((s, si) => (
                        <div key={si} className="src">
                          <strong>S{si + 1}</strong> · {s.topic || selectedTopic} {s.slide ? `· Slide ${s.slide}` : ''}
                          <div className="muted tiny">{s.text || s.preview || 'Course curriculum reference'}</div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              );
            })}

            {isLoading && (
              <div className="msg ai">
                <div className="row" style={{ gap: 8 }}>
                  <Spinner />
                  <span className="small muted">Preparing your explanation...</span>
                </div>
              </div>
            )}
            <div ref={chatEndRef} />
          </div>

          {error && <p className="error" style={{ padding: '8px 16px' }}>{error}</p>}
          {recordingError && <p className="error" style={{ padding: '8px 16px' }}>{recordingError}</p>}

          {/* Chat Composer */}
          <form
            className="composer"
            onSubmit={(e) => {
              e.preventDefault();
              handleSendMessage();
            }}
          >
            <button
              type="button"
              className={`btn sm ${isRecording ? 'mic rec' : ''}`}
              title={isRecording ? 'Stop recording voice' : 'Record voice query'}
              onClick={isRecording ? stopVoiceRecording : startVoiceRecording}
            >
              <Icon name="mic" size={16} />
              {isTranscribing ? 'Transcribing...' : isRecording ? 'Listening...' : ''}
            </button>

            <textarea
              className="input grow"
              placeholder={`Ask a question about ${selectedTopic}...`}
              rows={1}
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSendMessage();
                }
              }}
            />

            <button
              type="submit"
              className="btn primary sm"
              disabled={isLoading || !inputMessage.trim()}
            >
              <Icon name="send" size={16} /> Send
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
