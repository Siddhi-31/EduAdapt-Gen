import React, { useState, useEffect } from 'react';
import {
  MAX_PROFILE_SLOTS,
  getProfileSlots,
  getActiveSlotIndex,
  setActiveSlotIndex,
  recordAuthenticatedSession,
  clearSlot,
  purgeStudentSpecificCaches,
} from '../lib/profileSlots';
import { api, token } from '../lib/api';
import { Icon, Spinner } from './ui';

export default function ProfileManagerModal({
  isOpen,
  onClose,
  onProfileSwitched,
  currentStudent,
}) {
  const [slots, setSlots] = useState([]);
  const [activeSlotIdx, setActiveSlotIdx] = useState(1);
  const [addingSlotIndex, setAddingSlotIndex] = useState(null); // which slot number is being added
  const [emailInput, setEmailInput] = useState('');
  const [passwordInput, setPasswordInput] = useState('');
  const [loginLoading, setLoginLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState(null);
  const [successMessage, setSuccessMessage] = useState(null);

  const reloadSlots = () => {
    setSlots(getProfileSlots());
    setActiveSlotIdx(getActiveSlotIndex());
  };

  useEffect(() => {
    if (isOpen) {
      reloadSlots();
      setErrorMessage(null);
      setSuccessMessage(null);
      setAddingSlotIndex(null);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleSwitchToSlot = async (slot) => {
    if (slot.is_empty || !slot.token) return;
    if (slot.slot_index === activeSlotIdx) {
      onClose();
      return;
    }

    setErrorMessage(null);
    try {
      // 1. Set active slot index & token
      setActiveSlotIndex(slot.slot_index);
      token.set(slot.token);

      // 2. Purge caches
      purgeStudentSpecificCaches();

      // 3. Fetch newly authenticated student profile from backend authoritatively
      const meData = await api.get('/auth/me');

      // 4. Update parent state
      if (onProfileSwitched) {
        onProfileSwitched(meData);
      }
      onClose();
    } catch (err) {
      setErrorMessage(
        'Unable to switch to this profile session: ' +
          (err.message || 'Session may have expired. Please re-authenticate.')
      );
    }
  };

  const handleAddAccount = async (e) => {
    if (e) e.preventDefault();
    if (!emailInput.trim() || !passwordInput) {
      setErrorMessage('Please enter both email and password.');
      return;
    }

    setLoginLoading(true);
    setErrorMessage(null);
    try {
      const res = await api.post('/auth/login', {
        email: emailInput.trim(),
        password: passwordInput,
      });

      if (!res.access_token) {
        throw new Error('Authentication succeeded but no access token was returned.');
      }

      // Record in the chosen slot
      const targetSlot = addingSlotIndex || slots.findIndex((s) => s.is_empty) + 1;
      recordAuthenticatedSession(res.access_token, res.user, res.student, targetSlot);

      // Set active
      setActiveSlotIndex(targetSlot);
      token.set(res.access_token);
      purgeStudentSpecificCaches();

      const meData = await api.get('/auth/me');
      setSuccessMessage(`Account ${res.student?.full_name || emailInput} successfully added to Profile ${targetSlot}!`);
      reloadSlots();
      setAddingSlotIndex(null);
      setEmailInput('');
      setPasswordInput('');

      if (onProfileSwitched) {
        onProfileSwitched(meData);
      }
      setTimeout(() => {
        onClose();
      }, 700);
    } catch (err) {
      setErrorMessage('Failed to authenticate student: ' + (err.message || 'Invalid credentials.'));
    } finally {
      setLoginLoading(false);
    }
  };

  const handleRemoveSlot = (slotIndex) => {
    if (window.confirm(`Are you sure you want to remove Profile ${slotIndex}? You will need to log in again to restore it.`)) {
      clearSlot(slotIndex);
      reloadSlots();
      // If removed slot was active, trigger refresh
      if (slotIndex === activeSlotIdx) {
        window.location.reload();
      }
    }
  };

  return (
    <div
      className="modal-overlay"
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        background: 'rgba(15, 23, 42, 0.65)',
        backdropFilter: 'blur(4px)',
        zIndex: 9999,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: 16,
      }}
      onClick={onClose}
    >
      <div
        className="card"
        style={{
          width: '100%',
          maxWidth: 680,
          maxHeight: '90vh',
          overflowY: 'auto',
          background: '#ffffff',
          borderRadius: 16,
          boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
          padding: 24,
          position: 'relative',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="row between" style={{ borderBottom: '1px solid #f1f5f9', paddingBottom: 16 }}>
          <div>
            <span className="eyebrow plain">Local Profile Switcher</span>
            <h2 style={{ fontSize: '1.4em', marginTop: 4 }}>5-Student Account Manager</h2>
            <p className="tiny muted mt4">
              Switch seamlessly between five independently authenticated student accounts in this browser.
            </p>
          </div>
          <button
            type="button"
            className="btn ghost sm"
            onClick={onClose}
            aria-label="Close Profile Manager"
          >
            ✕
          </button>
        </div>

        {errorMessage && (
          <div className="notice mt16" role="alert" style={{ background: '#fef2f2', borderColor: '#f87171', color: '#991b1b' }}>
            {errorMessage}
          </div>
        )}

        {successMessage && (
          <div className="pill green mt16" style={{ width: '100%', justifyContent: 'center' }}>
            {successMessage}
          </div>
        )}

        {/* 5 Profile Slots List */}
        <div className="col mt16" style={{ gap: 12 }}>
          {slots.map((slot) => {
            const isActive = slot.slot_index === activeSlotIdx && !slot.is_empty;
            const isDiagDone = Boolean(slot.has_completed_diagnostic);

            if (slot.is_empty) {
              return (
                <div
                  key={slot.slot_index}
                  className="card soft row between"
                  style={{
                    padding: '14px 18px',
                    borderStyle: 'dashed',
                    borderColor: '#cbd5e1',
                    background: '#f8fafc',
                  }}
                >
                  <div className="row" style={{ gap: 12, alignItems: 'center' }}>
                    <span
                      style={{
                        width: 38,
                        height: 38,
                        borderRadius: '50%',
                        background: '#e2e8f0',
                        color: '#64748b',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontWeight: 700,
                        fontSize: '0.9em',
                      }}
                    >
                      P{slot.slot_index}
                    </span>
                    <div>
                      <strong className="small" style={{ color: '#64748b' }}>
                        Profile {slot.slot_index} — Empty Slot
                      </strong>
                      <div className="tiny muted">No authenticated student assigned</div>
                    </div>
                  </div>

                  <button
                    type="button"
                    className="btn sm"
                    onClick={() => {
                      setAddingSlotIndex(slot.slot_index);
                      setErrorMessage(null);
                    }}
                  >
                    + Add Account
                  </button>
                </div>
              );
            }

            return (
              <div
                key={slot.slot_index}
                className="card row between"
                style={{
                  padding: '14px 18px',
                  borderColor: isActive ? '#6366f1' : '#e2e8f0',
                  background: isActive ? '#f5f3ff' : '#ffffff',
                  boxShadow: isActive ? '0 0 0 2px rgba(99, 102, 241, 0.2)' : undefined,
                  transition: 'all 0.15s ease',
                }}
              >
                <div className="row" style={{ gap: 14, alignItems: 'center' }}>
                  <span
                    style={{
                      width: 42,
                      height: 42,
                      borderRadius: '50%',
                      background: isActive ? '#6366f1' : '#475569',
                      color: '#ffffff',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontWeight: 700,
                      fontSize: '1em',
                    }}
                  >
                    {slot.avatar_initials || 'S'}
                  </span>

                  <div>
                    <div className="row" style={{ gap: 8, alignItems: 'center' }}>
                      <strong style={{ fontSize: '1em' }}>{slot.full_name}</strong>
                      <span className="tiny muted">({slot.student_code || slot.student_id})</span>
                      {isActive && <span className="pill green" style={{ padding: '2px 8px', fontSize: '0.75em' }}>ACTIVE</span>}
                    </div>

                    <div className="row mt4" style={{ gap: 6, fontSize: '0.8em' }}>
                      <span className={`pill ${isDiagDone ? 'green' : 'amber'}`} style={{ padding: '2px 8px', fontSize: '0.85em' }}>
                        {isDiagDone ? 'Diagnostic Completed' : 'Diagnostic Pending'}
                      </span>
                      {isDiagDone && slot.current_skill_level && (
                        <span className="pill violet" style={{ padding: '2px 8px', fontSize: '0.85em' }}>
                          {slot.current_skill_level}
                        </span>
                      )}
                      {isDiagDone && slot.learning_pace && (
                        <span className="pill" style={{ padding: '2px 8px', fontSize: '0.85em' }}>
                          {slot.learning_pace} Pace
                        </span>
                      )}
                    </div>
                  </div>
                </div>

                <div className="row" style={{ gap: 8, alignItems: 'center' }}>
                  {!isActive ? (
                    <button
                      type="button"
                      className="btn sm primary"
                      onClick={() => handleSwitchToSlot(slot)}
                    >
                      Switch to Profile
                    </button>
                  ) : (
                    <span className="tiny muted" style={{ fontStyle: 'italic', paddingRight: 4 }}>
                      Current session
                    </span>
                  )}

                  <button
                    type="button"
                    className="btn ghost sm"
                    style={{ color: '#ef4444', padding: '4px 8px' }}
                    title="Remove profile from slot"
                    onClick={() => handleRemoveSlot(slot.slot_index)}
                  >
                    Remove
                  </button>
                </div>
              </div>
            );
          })}
        </div>

        {/* Inline Add Account Form if selected */}
        {addingSlotIndex && (
          <div
            className="card col mt16"
            style={{
              padding: 18,
              background: '#f8fafc',
              border: '1px solid #cbd5e1',
              borderRadius: 12,
              gap: 12,
            }}
          >
            <div className="row between">
              <strong>Add Account to Profile Slot {addingSlotIndex}</strong>
              <button
                type="button"
                className="btn ghost sm"
                onClick={() => setAddingSlotIndex(null)}
              >
                Cancel
              </button>
            </div>
            <p className="tiny muted">
              Sign in with a real registered student's credentials. The authenticated session will be saved to Slot {addingSlotIndex}.
            </p>

            <form onSubmit={handleAddAccount} className="col" style={{ gap: 10 }}>
              <input
                type="email"
                className="input"
                placeholder="Student Email (e.g. student@example.com)"
                value={emailInput}
                onChange={(e) => setEmailInput(e.target.value)}
                required
                disabled={loginLoading}
              />
              <input
                type="password"
                className="input"
                placeholder="Password"
                value={passwordInput}
                onChange={(e) => setPasswordInput(e.target.value)}
                required
                disabled={loginLoading}
              />
              <div className="row end" style={{ gap: 8 }}>
                <button
                  type="button"
                  className="btn ghost sm"
                  onClick={() => setAddingSlotIndex(null)}
                  disabled={loginLoading}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn sm primary"
                  disabled={loginLoading}
                >
                  {loginLoading ? <Spinner /> : `Sign In & Save to Slot ${addingSlotIndex}`}
                </button>
              </div>
            </form>
          </div>
        )}

        {/* Footer Note */}
        <div className="mt16" style={{ borderTop: '1px solid #f1f5f9', paddingTop: 14 }}>
          <p className="tiny muted" style={{ lineHeight: 1.5 }}>
            <strong>Localhost Multi-Account Isolation:</strong> When switching between profiles, previous student data,
            tutor histories, lesson caches, and in-memory states are immediately purged and re-fetched from the
            backend session. Passwords are never stored in the browser.
          </p>
        </div>
      </div>
    </div>
  );
}
