import React, { Fragment } from 'react';

export const Logo = () => (
  <div className="logo">
    <span className="logo-mark">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2.2" strokeLinejoin="round">
        <path d="M3 9l9-5 9 5-9 5-9-5z" />
        <path d="M7 11.5V16c0 1.6 2.2 3 5 3s5-1.4 5-3v-4.5" />
      </svg>
    </span>
    EduAdapt
  </div>
);

const P = {
  dash: "M3 12l9-8 9 8M5 10v10h14V10",
  book: "M4 5a2 2 0 012-2h13v16H6a2 2 0 00-2 2zM4 19V5",
  map: "M9 4l-6 2v14l6-2 6 2 6-2V4l-6 2-6-2zM9 4v14M15 6v14",
  chat: "M4 5h16v11H8l-4 4z",
  check: "M5 12l4 4 10-10",
  chart: "M4 20V10M10 20V4M16 20v-8M22 20H2",
  gear: "M12 9a3 3 0 100 6 3 3 0 000-6zM19 12a7 7 0 00-.1-1.2l2-1.6-2-3.4-2.4 1a7 7 0 00-2-1.2L14 3h-4l-.5 2.6a7 7 0 00-2 1.2l-2.4-1-2 3.4 2 1.6a7 7 0 000 2.4l-2 1.6 2 3.4 2.4-1a7 7 0 002 1.2L10 21h4l.5-2.6a7 7 0 002-1.2l2.4 1 2-3.4-2-1.6c.1-.4.1-.8.1-1.2z",
  mic: "M12 3a3 3 0 00-3 3v6a3 3 0 006 0V6a3 3 0 00-3-3zM5 11a7 7 0 0014 0M12 18v3",
  speaker: "M4 9v6h4l5 4V5L8 9zM16 9a4 4 0 010 6M18.5 6.5a8 8 0 010 11",
  send: "M4 12l16-8-6 16-2-7z",
  arrow: "M5 12h14M13 6l6 6-6 6",
  login: "M10 17l5-5-5-5M15 12H3M14 3h6v18h-6",
  phone: "M8 3h8v18H8zM11 18h2",
  lock: "M6 11h12v10H6zM8 11V8a4 4 0 018 0v3",
  spark: "M12 3v4M12 17v4M3 12h4M17 12h4M6 6l2.5 2.5M15.5 15.5L18 18M6 18l2.5-2.5M15.5 8.5L18 6",
  clock: "M12 7v5l3 2M12 3a9 9 0 100 18 9 9 0 000-18z",
  flame: "M12 3c1 4 5 5 5 10a5 5 0 01-10 0c0-3 2-4 2-6 2 1 3 2 3-4z",
  target: "M12 3a9 9 0 100 18 9 9 0 000-18zM12 8a4 4 0 100 8 4 4 0 000-8z",
  plus: "M12 5v14M5 12h14",
  out: "M15 17l5-5-5-5M20 12H9M9 3H4v18h5",
  shield: "M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z",
  code: "M16 18l6-6-6-6M8 6l-6 6 6 6",
  play: "M5 3l14 9-14 9V3z",
  user: "M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2M12 11a4 4 0 100-8 4 4 0 000 8z",
  refresh: "M23 4v6h-6M1 20v-6h6M3.51 9a9 9 0 0114.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0020.49 15",
  copy: "M8 4v12a2 2 0 002 2h8a2 2 0 002-2V4a2 2 0 00-2-2h-8a2 2 0 00-2 2zM4 8H2v12a2 2 0 002 2h12v-2",
  search: "M11 19a8 8 0 100-16 8 8 0 000 16zM21 21l-4.35-4.35",
  eye: "M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8zM12 9a3 3 0 100 6 3 3 0 000-6z",
  eyeOff: "M17.94 17.94A10.07 10.07 0 0112 20c-7 0-11-8-11-8a18.45 18.45 0 015.06-5.94M9.9 4.24A9.12 9.12 0 0112 4c7 0 11 8 11 8a18.5 18.5 0 01-2.16 3.19m-6.72-1.07a3 3 0 11-4.24-4.24M1 1l22 22",
  mail: "M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z",
  key: "M21 2l-2 2m-1.5 1.5L14 9l-1.5-1.5-2 2 1.5 1.5-4 4A6 6 0 115 13l4-4 1.5 1.5 2-2L11 7l3.5-3.5L16 2l5 0z",
};

export const Icon = ({ name, size = 18, ...rest }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="1.8"
    strokeLinecap="round"
    strokeLinejoin="round"
    aria-hidden="true"
    {...rest}
  >
    <path d={P[name] || P.spark} />
  </svg>
);

export const Bar = ({ value = 0, tone }) => {
  const v = Math.max(0, Math.min(100, Number(value) || 0));
  const t = tone || (v >= 85 ? "green" : v > 0 && v < 60 ? "amber" : "");
  return (
    <div className={`bar ${t}`}>
      <i style={{ width: `${v}%` }} />
    </div>
  );
};

export const Toggle = ({ on, onChange, label }) => (
  <button
    type="button"
    role="switch"
    aria-checked={!!on}
    aria-label={label}
    className={`toggle ${on ? "on" : ""}`}
    onClick={() => onChange(!on)}
  />
);

export const Spinner = () => <div className="spinner" role="status" aria-label="Loading" />;
export const Loading = () => (
  <div className="center">
    <Spinner />
  </div>
);

const STATUS = {
  not_started: ["", "Not started"],
  not_assessed: ["", "Not Assessed"],
  locked: ["", "Locked"],
  learning: ["violet", "Learning"],
  in_progress: ["violet", "In Progress"],
  needs_practice: ["amber", "Needs practice"],
  mastered: ["green", "Mastered"],
  upcoming: ["", "Upcoming"],
  current: ["violet", "Current"],
  completed: ["green", "Completed"],
  reinforcement: ["amber", "Reinforce"],
};

export const DONE = ["completed", "mastered"];

export const StatusPill = ({ status }) => {
  const normalized = (status || "").toLowerCase().replace(/\s+/g, "_");
  const [tone, label] = STATUS[normalized] || ["", status || "Pending"];
  return <span className={`pill ${tone}`}>{label}</span>;
};

// Safe Markdown parser
function inline(text, key) {
  const parts = text.split(/(\*\*[^*]+\*\*|`[^`]+`|\[S\d+\])/g);
  return parts.map((p, i) => {
    if (/^\*\*.+\*\*$/.test(p)) return <strong key={`${key}-${i}`}>{p.slice(2, -2)}</strong>;
    if (/^`.+`$/.test(p)) return <code key={`${key}-${i}`}>{p.slice(1, -1)}</code>;
    if (/^\[S\d+\]$/.test(p)) return <sup key={`${key}-${i}`} className="pill violet" style={{ padding: "0 5px" }}>{p.slice(1, -1)}</sup>;
    return <Fragment key={`${key}-${i}`}>{p}</Fragment>;
  });
}

export function Markdown({ text = "" }) {
  if (!text) return null;
  const out = [];
  const blocks = text.split(/(```[\s\S]*?```)/g);
  blocks.forEach((b, bi) => {
    if (b.startsWith("```")) {
      const body = b.replace(/^```\w*\n?/, "").replace(/```$/, "");
      out.push(
        <pre key={bi}>
          <code>{body}</code>
        </pre>
      );
      return;
    }
    let list = null;
    b.split("\n").forEach((line, li) => {
      const k = `${bi}-${li}`;
      const m = line.match(/^\s*(?:[-*]|\d+\.)\s+(.*)/);
      if (m) {
        list = list || [];
        list.push(<li key={k}>{inline(m[1], k)}</li>);
        return;
      }
      if (list) {
        out.push(<ul key={`${k}u`}>{list}</ul>);
        list = null;
      }
      const h = line.match(/^#{1,4}\s+(.*)/);
      if (h) out.push(<p key={k}><strong>{inline(h[1], k)}</strong></p>);
      else if (line.trim()) out.push(<p key={k}>{inline(line, k)}</p>);
    });
    if (list) out.push(<ul key={`${bi}-end`}>{list}</ul>);
  });
  return <div className="md">{out}</div>;
}

export const fmtTime = (s = 0) => {
  const h = Math.floor(s / 3600), m = Math.floor((s % 3600) / 60);
  return h ? `${h}h ${String(m).padStart(2, "0")}m` : `${m}m`;
};

export const TreeArt = () => {
  const n = [
    [50, 160, 26],
    [30, 80, 80],
    [70, 240, 80],
    [20, 40, 134],
    [40, 120, 134],
    [60, 200, 134],
    [80, 280, 134]
  ];
  const e = [
    [0, 1], [0, 2], [1, 3], [1, 4], [2, 5], [2, 6]
  ];
  return (
    <svg viewBox="0 0 320 160" width="100%" role="img" aria-label="Binary search tree with root 50">
      {e.map(([a, b]) => (
        <line
          key={`${a}${b}`}
          x1={n[a][1]}
          y1={n[a][2]}
          x2={n[b][1]}
          y2={n[b][2]}
          stroke="#c9cbe0"
          strokeWidth="1.5"
        />
      ))}
      {n.map(([v, x, y], i) => (
        <g key={v}>
          <circle
            cx={x}
            cy={y}
            r="16"
            fill={i === 0 ? "#4f46e5" : "#fff"}
            stroke={i === 0 ? "#4f46e5" : "#c9cbe0"}
            strokeWidth="1.5"
          />
          <text
            x={x}
            y={y + 4}
            textAnchor="middle"
            fontSize="11"
            fontWeight="600"
            fill={i === 0 ? "#fff" : "#1d2235"}
          >
            {v}
          </text>
        </g>
      ))}
    </svg>
  );
};
