import { NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import { Logo, Icon } from "./ui";
import { AdaptiveHeroVisual } from "./AdaptiveHeroVisual";
import { useAuth } from "../lib/auth";

export function AuthLayout({ children }) {
  return (
    <div className="auth-wrap">
      <header className="topbar">
        <Logo />
        <span className="small muted">Need help? <a href="mailto:support@eduadapt.app">Contact support ↗</a></span>
      </header>
      <main className="auth-main">
        <section className="auth-hero" aria-hidden="true">
          <span className="eyebrow plain">Tailored PPS Learning System</span>
          <h1>A learning path that understands you.</h1>
          <p className="muted">Build confidence one concept at a time. Personalized roadmaps, clear explanations, and C programming practice that meets you where you are.</p>
          <AdaptiveHeroVisual />
          <div className="steps3">
            <div><b>01</b>Understand</div><div><b>02</b>Practice</div><div><b>03</b>Master</div>
          </div>
          <p className="tiny muted">Continuous diagnostic calibration. Human pace. You stay in control.</p>
        </section>
        <section>{children}</section>
      </main>
      <footer className="footer">© 2026 EduAdapt · Personalized Adaptive Learning for PPS</footer>
    </div>
  );
}

const STEPS = ["Student details", "Preferences", "Your goal"];
export function OnboardLayout({ step, children }) {
  return (
    <div className="auth-wrap">
      <header className="topbar"><Logo /><span className="small muted">Step {step + 1} of 3</span></header>
      <main className="onb">
        <aside className="onb-side">
          <span className="eyebrow">Get started</span>
          <h2>Your learning, thoughtfully tailored.</h2>
          <div className="stepper">
            {STEPS.map((s, i) => (
              <div key={s} className={i < step ? "done" : i === step ? "active" : ""}>
                <i>{i < step ? <Icon name="check" size={12} /> : i + 1}</i>{s}
              </div>
            ))}
          </div>
          <div className="card tip small">
            <strong>There's no right way to learn.</strong>
            <p className="muted mt8">Your preferences shape explanations, pace and practice. You can change them any time in Settings.</p>
          </div>
        </aside>
        <section>{children}</section>
      </main>
    </div>
  );
}

const NAV = [
  ["Learn", [["/dashboard", "dash", "Dashboard"], ["/subjects", "book", "Subjects"], ["/roadmap", "map", "Roadmap"]]],
  ["Practice", [["/tutor", "chat", "Learning tutor"], ["/practice", "check", "Practice"], ["/progress", "chart", "Progress"]]],
  ["You", [["/settings", "gear", "Accessibility"]]],
];
const CRUMB = { dashboard: "Dashboard", subjects: "Subjects & topics", roadmap: "Roadmap", tutor: "Learning tutor",
  practice: "Practice & assessments", progress: "Progress", settings: "Accessibility", topics: "Topic", results: "Results" };

export function AppShell() {
  const { me, logout } = useAuth();
  const nav = useNavigate();
  const loc = useLocation();
  const name = me?.user?.name || "Student";
  const crumb = CRUMB[loc.pathname.split("/")[1]] || "";
  return (
    <div className="shell">
      <aside className="side">
        <Logo />
        <nav className="nav" aria-label="Main">
          {NAV.map(([label, items]) => (
            <div key={label} className="nav">
              <span className="label">{label}</span>
              {items.map(([to, icon, text]) => (
                <NavLink key={to} to={to}><Icon name={icon} />{text}</NavLink>
              ))}
            </div>
          ))}
        </nav>
        <div className="side-foot">
          <div className="card tip small" style={{ padding: 12 }}>
            <strong>Study tip</strong>
            <p className="muted">Short sessions beat long ones. Try one 5-minute step.</p>
          </div>
          <div className="row">
            <span className="avatar">{name.slice(0, 1).toUpperCase()}</span>
            <div className="grow small"><strong>{name}</strong><div className="muted tiny">Student</div></div>
            <button className="btn ghost sm" aria-label="Sign out" onClick={() => { logout(); nav("/login"); }}>
              <Icon name="out" size={16} />
            </button>
          </div>
        </div>
      </aside>
      <div className="main">
        <div className="main-top">
          <span>Workspace / <strong style={{ color: "var(--ink)" }}>{crumb}</strong></span>
          <span className="row small"><Icon name="shield" size={14} />Your data stays private</span>
        </div>
        <Outlet />
      </div>
    </div>
  );
}
