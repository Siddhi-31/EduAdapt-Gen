import React, { useEffect, useState } from 'react';
import { updateStudentProfile } from '../api/learningApi';
import { Bar, Icon, Loading, Spinner, StatusPill } from '../components/ui';

export default function ProfilePage({
  currentStudentId = 'S001',
  studentProfile,
  onNavigate,
}) {
  const [isEditing, setIsEditing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState(null);
  const [errorMessage, setErrorMessage] = useState(null);

  const isDiagComplete = Boolean(studentProfile?.has_completed_diagnostic);

  const [formData, setFormData] = useState({
    full_name: studentProfile?.full_name || '',
    college: studentProfile?.college || '',
    department: studentProfile?.department || '',
  });

  useEffect(() => {
    if (studentProfile) {
      setFormData({
        full_name: studentProfile.full_name || '',
        college: studentProfile.college || '',
        department: studentProfile.department || '',
      });
    }
  }, [studentProfile]);

  const handleSave = async (e) => {
    if (e) e.preventDefault();
    setIsSaving(true);
    setSaveMessage(null);
    setErrorMessage(null);
    try {
      await updateStudentProfile(formData);
      setSaveMessage('Profile information saved successfully.');
      setIsEditing(false);
      setTimeout(() => setSaveMessage(null), 3500);
    } catch (err) {
      setErrorMessage('Failed to save profile: ' + (err.message || 'Please try again.'));
    } finally {
      setIsSaving(false);
    }
  };

  const masteryVal = isDiagComplete && studentProfile?.mastery !== undefined ? Math.round(studentProfile.mastery * 100) : 0;
  const accuracyVal = isDiagComplete && studentProfile?.accuracy !== undefined ? Math.round(studentProfile.accuracy * 100) : 0;
  const pace = isDiagComplete ? (studentProfile?.learning_pace || 'Moderate') : 'Not determined';
  const difficulty = isDiagComplete ? (studentProfile?.recommended_difficulty || 'Beginner') : 'Not determined';
  const testsCount = isDiagComplete ? (studentProfile?.tests_completed || 0) : 0;
  const studentName = studentProfile?.full_name || 'Student';

  return (
    <div className="page" style={{ maxWidth: 920, margin: '0 auto', gap: 20 }}>
      <div className="page-head">
        <div>
          <span className="eyebrow plain">Student Identity</span>
          <h1>{studentName}</h1>
          <p className="muted">
            {formData.college ? `${formData.college} · ` : ''}
            {formData.department ? `${formData.department} · ` : ''}
            Student ID: <strong>{currentStudentId}</strong>
          </p>
        </div>
        <div className="row">
          <span className={`pill ${isDiagComplete ? 'green' : 'amber'}`}>
            {isDiagComplete ? 'Diagnostic Completed' : 'Diagnostic Pending'}
          </span>
          <span className="pill violet">{difficulty} Tier</span>
        </div>
      </div>

      {saveMessage && <div className="pill green" style={{ alignSelf: 'flex-start' }}>{saveMessage}</div>}
      {errorMessage && <div className="notice" role="alert">{errorMessage}</div>}

      {/* Profile Overview Card */}
      <div className="card col" style={{ gap: 16 }}>
        <div className="row between">
          <h3>Academic Information</h3>
          {!isEditing ? (
            <button
              type="button"
              className="btn sm"
              onClick={() => setIsEditing(true)}
            >
              <Icon name="gear" size={14} /> Edit Information
            </button>
          ) : (
            <button
              type="button"
              className="btn sm ghost"
              onClick={() => setIsEditing(false)}
            >
              Cancel
            </button>
          )}
        </div>

        {!isEditing ? (
          <div className="grid g3">
            <div className="card soft col" style={{ padding: 14 }}>
              <span className="tiny muted">Full Name</span>
              <strong className="mt4">{studentName}</strong>
            </div>
            <div className="card soft col" style={{ padding: 14 }}>
              <span className="tiny muted">College / Institution</span>
              <strong className="mt4">{formData.college || 'Not specified'}</strong>
            </div>
            <div className="card soft col" style={{ padding: 14 }}>
              <span className="tiny muted">Department / Major</span>
              <strong className="mt4">{formData.department || 'Not specified'}</strong>
            </div>
          </div>
        ) : (
          <form className="col" style={{ gap: 14 }} onSubmit={handleSave}>
            <div className="grid g3">
              <label className="col" style={{ gap: 6 }}>
                <span className="small muted">Full Name</span>
                <input
                  type="text"
                  className="input"
                  value={formData.full_name}
                  onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                  required
                />
              </label>
              <label className="col" style={{ gap: 6 }}>
                <span className="small muted">College</span>
                <input
                  type="text"
                  className="input"
                  value={formData.college}
                  onChange={(e) => setFormData({ ...formData, college: e.target.value })}
                />
              </label>
              <label className="col" style={{ gap: 6 }}>
                <span className="small muted">Department</span>
                <input
                  type="text"
                  className="input"
                  value={formData.department}
                  onChange={(e) => setFormData({ ...formData, department: e.target.value })}
                />
              </label>
            </div>
            <div className="row end mt8">
              <button
                type="submit"
                className="btn primary sm"
                disabled={isSaving}
              >
                {isSaving ? <Spinner /> : 'Save Profile Changes'}
              </button>
            </div>
          </form>
        )}
      </div>

      {/* Diagnostic & Mastery Metrics */}
      <div className="grid g4">
        <div className="card stat">
          <span className="muted small">Topic Mastery</span>
          <div className="num">{masteryVal}%</div>
          <div className="mt8">
            <Bar value={masteryVal} />
          </div>
          <span className="tiny muted mt8">Earned from practice</span>
        </div>
        <div className="card stat">
          <span className="muted small">Practice Accuracy</span>
          <div className="num">{accuracyVal}%</div>
          <div className="mt8">
            <Bar value={accuracyVal} tone="green" />
          </div>
          <span className="tiny muted mt8">Across verified attempts</span>
        </div>
        <div className="card stat">
          <span className="muted small">Learning Level</span>
          <div className="num" style={{ fontSize: '1.4em' }}>{difficulty}</div>
          <span className="tiny muted mt8">
            {isDiagComplete ? 'Calibrated from diagnostic' : 'Pending diagnostic'}
          </span>
        </div>
        <div className="card stat">
          <span className="muted small">Assessments Completed</span>
          <div className="num">{testsCount}</div>
          <span className="tiny muted mt8">Verified tests</span>
        </div>
      </div>

      {/* Personalization Parameters */}
      <div className="card col" style={{ gap: 14 }}>
        <h3>Active Personalization Parameters</h3>
        <p className="hint">
          Parameters aligned with your diagnostic performance, learning pace, and preferences.
        </p>

        <div className="grid g2 mt8">
          <div className="card soft col" style={{ padding: 14, gap: 6 }}>
            <span className="tiny muted">Initial Diagnostic Status</span>
            <strong>{isDiagComplete ? 'Completed & Verified' : 'Action Required'}</strong>
            <p className="tiny muted">
              {isDiagComplete
                ? 'Your baseline reasoning, numerical, and verbal skills have been recorded.'
                : 'You must complete the diagnostic assessment to unlock personalized recommendations.'}
            </p>
            {!isDiagComplete && (
              <button
                type="button"
                className="btn sm primary mt8"
                style={{ alignSelf: 'flex-start' }}
                onClick={() => onNavigate('diagnostic')}
              >
                Start Diagnostic Now →
              </button>
            )}
          </div>

          <div className="card soft col" style={{ padding: 14, gap: 6 }}>
            <span className="tiny muted">Learning Pace Optimization</span>
            <strong>{pace} Pace</strong>
            <p className="tiny muted">
              {isDiagComplete
                ? 'Adjusts lesson detail and scaffolding based on response velocity.'
                : 'Calibrated automatically after the diagnostic assessment.'}
            </p>
          </div>

          <div className="card soft col" style={{ padding: 14, gap: 6 }}>
            <span className="tiny muted">Curriculum Course</span>
            <strong>Programming for Problem Solving (PPS C99)</strong>
            <p className="tiny muted">Structured university curriculum across 5 units and 10 topics.</p>
          </div>

          <div className="card soft col" style={{ padding: 14, gap: 6 }}>
            <span className="tiny muted">Explanation Style Preference</span>
            <strong>{studentProfile?.explanation_style || 'Step by Step'}</strong>
            <p className="tiny muted">
              Can be customized anytime in{' '}
              <button
                type="button"
                className="btn ghost sm"
                style={{ padding: '0 4px', textDecoration: 'underline' }}
                onClick={() => onNavigate('settings')}
              >
                Accessibility & Learning Style
              </button>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
