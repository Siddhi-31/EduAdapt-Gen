import React from 'react';
import { Logo, Icon } from '../ui';

const NAV_GROUPS = [
  {
    label: 'Learn',
    items: [
      { id: 'home', icon: 'dash', label: 'Dashboard' },
      { id: 'curriculum', icon: 'book', label: 'Curriculum' },
      { id: 'learn', icon: 'spark', label: 'Personalized Lesson' },
      { id: 'roadmap', icon: 'map', label: 'Learning Roadmap' },
    ],
  },
  {
    label: 'Practice',
    items: [
      { id: 'tutor', icon: 'chat', label: 'Learning Tutor' },
      { id: 'practice', icon: 'code', label: 'Practice & Coding' },
      { id: 'tests', icon: 'check', label: 'Assessments' },
      { id: 'results', icon: 'chart', label: 'Your Results' },
    ],
  },
  {
    label: 'You',
    items: [
      { id: 'progress', icon: 'chart', label: 'Your Progress' },
      { id: 'profile', icon: 'user', label: 'Your Profile' },
      { id: 'settings', icon: 'gear', label: 'Accessibility' },
    ],
  },
];

export default function Sidebar({
  activePage,
  onNavigate,
  studentId = 'S001',
  studentProfile,
  onReset,
  onLogout,
  onOpenProfileManager,
}) {
  const displayName = studentProfile?.full_name || studentId || 'Student';
  const avatarLetter = (displayName || 'S').slice(0, 1).toUpperCase();
  const difficulty = studentProfile?.recommended_difficulty || 'Beginner';

  return (
    <aside className="side" aria-label="Main Navigation">
      <div
        onClick={() => { if (onNavigate) onNavigate('landing'); }}
        style={{ cursor: 'pointer' }}
        title="View EduAdapt Landing Page"
        role="button"
        tabIndex={0}
        onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { if (onNavigate) onNavigate('landing'); } }}
      >
        <Logo />
      </div>

      <nav className="nav" aria-label="Sidebar Menu">
        {!studentProfile?.has_completed_diagnostic && (
          <div className="nav" style={{ marginBottom: 12 }}>
            <span className="label" style={{ color: '#f59e0b' }}>Required Step</span>
            <button
              type="button"
              className={`nav-btn ${activePage === 'diagnostic' ? 'active' : ''}`}
              style={{ background: activePage === 'diagnostic' ? undefined : 'rgba(245, 158, 11, 0.1)', color: '#b45309' }}
              onClick={() => onNavigate('diagnostic')}
            >
              <Icon name="spark" size={18} />
              <span>Initial Diagnostic</span>
            </button>
          </div>
        )}

        {NAV_GROUPS.map((group) => (
          <div key={group.label} className="nav">
            <span className="label">{group.label}</span>
            {group.items.map((item) => (
              <button
                key={item.id}
                type="button"
                className={`nav-btn ${activePage === item.id ? 'active' : ''}`}
                onClick={() => onNavigate(item.id)}
              >
                <Icon name={item.icon} size={18} />
                <span>{item.label}</span>
              </button>
            ))}
          </div>
        ))}
      </nav>

      <div className="side-foot">
        <button
          type="button"
          className="btn sm"
          style={{ width: '100%', marginBottom: 10, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6, background: '#f1f5f9', color: '#334155', border: '1px solid #cbd5e1' }}
          onClick={onOpenProfileManager}
          title="Switch between 5 local student accounts"
        >
          <Icon name="user" size={14} />
          <span>Switch Profile (5 Slots)</span>
        </button>

        <div className="card tip small" style={{ padding: 12 }}>
          <strong>Study Tip</strong>
          <p className="muted" style={{ marginTop: 4 }}>
            Short, focused sessions beat long ones. Take one concept at a time.
          </p>
        </div>

        <div className="row" style={{ padding: '6px 4px' }}>
          <span className="avatar">{avatarLetter}</span>
          <div className="grow small" style={{ minWidth: 0, overflow: 'hidden' }}>
            <strong style={{ display: 'block', textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap' }}>
              {displayName}
            </strong>
            <div className="muted tiny">{studentId} · {difficulty}</div>
          </div>
          {onLogout && (
            <button
              type="button"
              className="btn ghost sm"
              style={{ padding: 4 }}
              title="Sign out of student account"
              onClick={onLogout}
              aria-label="Sign out"
            >
              <Icon name="out" size={15} />
            </button>
          )}
          {onReset && (
            <button
              type="button"
              className="btn ghost sm"
              style={{ padding: 4 }}
              title="Reset progress to start fresh"
              onClick={onReset}
              aria-label="Reset progress"
            >
              <Icon name="refresh" size={15} />
            </button>
          )}
        </div>
      </div>
    </aside>
  );
}
