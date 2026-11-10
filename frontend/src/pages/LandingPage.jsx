import React, { useState, useEffect, useRef } from 'react';
import { Icon } from '../components/ui';
import '../styles/landing.css';

const SHOWCASE_TABS = [
  { id: 'lessons', label: 'Interactive Lessons', icon: 'book' },
  { id: 'tutor', label: 'Learning Tutor', icon: 'chat' },
  { id: 'practice', label: 'Coding Practice', icon: 'code' },
  { id: 'assessments', label: 'Progress & Insights', icon: 'chart' },
];

export default function LandingPage({ onNavigate, studentProfile, isAuthenticated = false }) {
  const activeStudentId = studentProfile?.student_code || studentProfile?.student_id || 'S001';

  // Intro Sequence Stages: 'initial' -> 'typing' -> 'reveal' -> 'transitioning' -> 'completed'
  const [introStage, setIntroStage] = useState(() => {
    try {
      const seen = sessionStorage.getItem('eduadapt_landing_intro_seen');
      const prefersReduced = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
      if (seen || prefersReduced) return 'completed';
    } catch {}
    return 'initial';
  });

  const [typedText, setTypedText] = useState('');
  const [motionStyles, setMotionStyles] = useState(null);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [activeShowcaseTab, setActiveShowcaseTab] = useState('lessons');

  const dockAnchorRef = useRef(null);
  const brandRef = useRef(null);
  const fullText = 'EduAdapt';

  // Coordinate Intro Animation Sequence
  useEffect(() => {
    if (introStage === 'completed') return;

    let timer;
    if (introStage === 'initial') {
      timer = setTimeout(() => {
        setIntroStage('typing');
      }, 450);
    } else if (introStage === 'typing') {
      if (typedText.length < fullText.length) {
        timer = setTimeout(() => {
          setTypedText(fullText.slice(0, typedText.length + 1));
        }, 85);
      } else {
        // Typing done, hold for brand reveal
        timer = setTimeout(() => {
          setIntroStage('reveal');
        }, 320);
      }
    } else if (introStage === 'reveal') {
      // Hold brand reveal, measure dock anchor, and begin physical transition to top-left
      timer = setTimeout(() => {
        if (dockAnchorRef.current && brandRef.current) {
          const dockRect = dockAnchorRef.current.getBoundingClientRect();
          const brandRect = brandRef.current.getBoundingClientRect();
          const scale = 36 / brandRect.height;

          setMotionStyles({
            top: `${dockRect.top + (dockRect.height - 36) / 2}px`,
            left: `${dockRect.left}px`,
            transform: `scale(${scale})`,
          });
        }
        setIntroStage('transitioning');
      }, 700);
    } else if (introStage === 'transitioning') {
      // Complete transition into header after motion completes
      timer = setTimeout(() => {
        setIntroStage('completed');
        try {
          sessionStorage.setItem('eduadapt_landing_intro_seen', 'true');
        } catch {}
      }, 980);
    }

    return () => clearTimeout(timer);
  }, [introStage, typedText]);

  const handleSkipIntro = () => {
    setIntroStage('completed');
    try {
      sessionStorage.setItem('eduadapt_landing_intro_seen', 'true');
    } catch {}
  };

  const handleStartLearning = () => {
    if (onNavigate) {
      onNavigate('home');
    }
  };

  const scrollToSection = (id) => {
    setMobileMenuOpen(false);
    const el = document.getElementById(id);
    if (el) {
      el.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <div className="landing-root">
      {/* Background Atmosphere Accent */}
      <div className="landing-bg-decor" aria-hidden="true" />

      {/* PHASE 1: Full-Screen Intro Animation Overlay & Animated Brand Element */}
      {introStage !== 'completed' && (
        <div className={`landing-intro-overlay ${introStage === 'transitioning' ? 'fade-out' : ''}`}>
          <button
            type="button"
            className="landing-intro-skip-btn"
            onClick={handleSkipIntro}
          >
            Skip Intro →
          </button>
        </div>
      )}

      {/* Physical Brand Element that animates from Center to Top-Left */}
      {introStage !== 'completed' && (
        <div
          ref={brandRef}
          className={`brand-group-animated ${
            introStage === 'initial' || introStage === 'typing'
              ? 'state-center'
              : introStage === 'reveal'
              ? 'state-center glowing'
              : 'state-moving'
          }`}
          style={introStage === 'transitioning' && motionStyles ? motionStyles : undefined}
        >
          {introStage === 'reveal' && <div className="brand-aura" />}
          <div className={`landing-logo-mark ${introStage === 'transitioning' ? 'docked' : 'large'}`}>
            <svg
              width={introStage === 'transitioning' ? '20' : '32'}
              height={introStage === 'transitioning' ? '20' : '32'}
              viewBox="0 0 24 24"
              fill="none"
              stroke="#ffffff"
              strokeWidth="2.3"
              strokeLinejoin="round"
            >
              <path d="M3 9l9-5 9 5-9 5-9-5z" />
              <path d="M7 11.5V16c0 1.6 2.2 3 5 3s5-1.4 5-3v-4.5" />
            </svg>
          </div>
          <span className={`landing-logo-text ${introStage === 'transitioning' ? 'docked' : 'large'}`}>
            {introStage === 'initial' ? '' : typedText}
            {introStage === 'typing' && <span className="typing-caret" />}
          </span>
        </div>
      )}

      {/* Landing Sticky Header Navbar */}
      <header className={`landing-header ${introStage === 'completed' ? 'revealed' : ''}`}>
        <div className="landing-header-inner">
          {/* Logo Dock Target: Where the logo docks seamlessly */}
          <div
            ref={dockAnchorRef}
            className="landing-logo-dock-anchor"
            onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
          >
            {introStage === 'completed' && (
              <>
                <div className="landing-logo-mark docked">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#ffffff" strokeWidth="2.3" strokeLinejoin="round">
                    <path d="M3 9l9-5 9 5-9 5-9-5z" />
                    <path d="M7 11.5V16c0 1.6 2.2 3 5 3s5-1.4 5-3v-4.5" />
                  </svg>
                </div>
                <span className="landing-logo-text docked">EduAdapt</span>
              </>
            )}
          </div>

          {/* Desktop Navigation Links */}
          <nav className="landing-nav-links" aria-label="Main Navigation">
            <span className="landing-nav-link" onClick={() => scrollToSection('features')}>
              Personalized Learning
            </span>
            <span className="landing-nav-link" onClick={() => scrollToSection('how-it-works')}>
              How It Works
            </span>
            <span className="landing-nav-link" onClick={() => scrollToSection('showcase')}>
              Showcase
            </span>
            <span className="landing-nav-link" onClick={() => scrollToSection('adaptive')}>
              Adaptive Learning
            </span>
            <span className="landing-nav-link" onClick={() => scrollToSection('practice')}>
              Coding Practice
            </span>
          </nav>

          {/* Header Action Buttons */}
          <div className="landing-header-actions">
            {isAuthenticated ? (
              <>
                <button
                  type="button"
                  className="btn sm ghost"
                  onClick={() => onNavigate('home')}
                >
                  Dashboard ({studentProfile?.full_name ? studentProfile.full_name.split(' ')[0] : activeStudentId})
                </button>
                <button
                  type="button"
                  className="btn sm primary"
                  onClick={() => onNavigate('home')}
                >
                  Go to Dashboard →
                </button>
              </>
            ) : (
              <>
                <button
                  type="button"
                  className="btn sm ghost"
                  onClick={() => onNavigate('login')}
                >
                  Sign In
                </button>
                <button
                  type="button"
                  className="btn sm primary"
                  onClick={() => onNavigate('login')}
                >
                  Get Started →
                </button>
              </>
            )}
            <button
              type="button"
              className="landing-mobile-toggle"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              aria-label="Toggle navigation menu"
            >
              <Icon name="dash" size={18} />
            </button>
          </div>
        </div>

        {/* Mobile Navigation Dropdown */}
        {mobileMenuOpen && (
          <div className="landing-mobile-menu">
            <button type="button" className="landing-nav-link" onClick={() => scrollToSection('features')}>
              Personalized Learning
            </button>
            <button type="button" className="landing-nav-link" onClick={() => scrollToSection('how-it-works')}>
              How It Works
            </button>
            <button type="button" className="landing-nav-link" onClick={() => scrollToSection('showcase')}>
              Showcase
            </button>
            <button type="button" className="landing-nav-link" onClick={() => scrollToSection('adaptive')}>
              Adaptive Learning
            </button>
            <button type="button" className="landing-nav-link" onClick={() => scrollToSection('practice')}>
              Coding Practice
            </button>
            <div className="row mt8">
              <button type="button" className="btn sm primary block" onClick={handleStartLearning}>
                Start Learning Now →
              </button>
            </div>
          </div>
        )}
      </header>

      {/* PHASE 2 & 3: Hero Section with 3D Educational Visual Composition */}
      <section className="landing-hero">
        <div className="landing-hero-grid">
          {/* Left Hero Content */}
          <div className="hero-content">
            <div className="hero-badge-wrap">
              <span className="pill violet">PPS Curriculum Aligned</span>
              <span className="pill green">Adaptive Learning</span>
            </div>

            <h1 className="hero-headline">
              Learn at Your Pace.<br />
              Master Every Concept.
            </h1>

            <p className="hero-description">
              Your learning journey, designed around you. Build strong foundations, strengthen your understanding, and progress confidently through every concept.
            </p>

            <div className="hero-cta-group">
              <button
                type="button"
                className="btn primary"
                style={{ padding: '12px 24px', fontSize: '1.02em', fontWeight: 600 }}
                onClick={handleStartLearning}
              >
                Start Learning <Icon name="arrow" size={16} />
              </button>
              <button
                type="button"
                className="btn"
                style={{ padding: '12px 22px', fontSize: '1.02em' }}
                onClick={() => scrollToSection('how-it-works')}
              >
                Explore How It Works
              </button>
            </div>

            <div className="hero-trust-row">
              <div className="trust-item">
                <span className="trust-check"><Icon name="check" size={14} /></span>
                <span>Personalized Lesson Pace</span>
              </div>
              <div className="trust-item">
                <span className="trust-check"><Icon name="check" size={14} /></span>
                <span>Interactive C99 Practice</span>
              </div>
              <div className="trust-item">
                <span className="trust-check"><Icon name="check" size={14} /></span>
                <span>Real-Time Feedback</span>
              </div>
            </div>
          </div>

          {/* Right Hero: 3D Educational Visual Composition */}
          <div className="hero-visual-container" aria-label="Interactive 3D learning visual composition">
            {/* Central Isometric Floating Code Folio */}
            <div className="hero-3d-book">
              <div className="book-spine-accent" />
              <div className="book-header">
                <span className="book-title">pointers_memory.c</span>
                <span className="book-badge">C99 Standard</span>
              </div>
              <div className="book-body">
                <div>
                  <span className="code-comment">// 1. Stack memory allocation</span><br />
                  <span className="code-type">int</span> value = <span className="code-num">42</span>;
                </div>
                <div>
                  <span className="code-comment">// 2. Address referencing with &</span><br />
                  <span className="code-type">int</span> *ptr = &value;
                </div>
                <div>
                  <span className="code-comment">// 3. Dereference to update</span><br />
                  *ptr = <span className="code-num">100</span>;
                </div>
                <div>
                  <span className="code-fn">printf</span>(<span className="code-str">"Updated: %d\n"</span>, value);
                </div>
              </div>
            </div>

            {/* Floating 3D Concept Node: Pointers & Memory */}
            <div className="floating-node node-1">
              <span className="icon-chip" style={{ width: 28, height: 28 }}>
                <Icon name="code" size={14} />
              </span>
              <div>
                <div>Pointers & Memory</div>
                <div className="tiny muted">Address: 0x7ffee4</div>
              </div>
            </div>

            {/* Floating 3D Concept Node: Control Flow */}
            <div className="floating-node node-2">
              <span className="icon-chip" style={{ width: 28, height: 28 }}>
                <Icon name="map" size={14} />
              </span>
              <div>
                <div>Structured Roadmaps</div>
                <div className="tiny muted">Prerequisite Sequence</div>
              </div>
            </div>

            {/* Floating 3D Concept Node: Dynamic Memory */}
            <div className="floating-node node-3">
              <span className="icon-chip" style={{ width: 28, height: 28 }}>
                <Icon name="spark" size={14} />
              </span>
              <div>
                <div>Heap Allocation</div>
                <div className="tiny muted">malloc & free</div>
              </div>
            </div>

            {/* Floating Live Metric Card */}
            <div className="floating-metric-card">
              <div className="row between">
                <span className="tiny muted">Topic Mastery</span>
                <span className="pill green" style={{ fontSize: '0.7em' }}>Verified</span>
              </div>
              <div style={{ fontSize: '1.4em', fontWeight: 700, color: 'var(--ink)' }}>
                94%
              </div>
              <div className="tiny muted">5 of 5 Units Progressing</div>
            </div>
          </div>
        </div>
      </section>

      {/* PHASE 4: SECTION 2 — Personalized Learning */}
      <section id="features" className="landing-section soft-bg">
        <div className="landing-section-content">
          <div className="section-head">
            <span className="eyebrow">Personalized Learning</span>
            <h2 className="section-headline">A Learning Experience That Understands You.</h2>
            <p className="section-subhead">
              Everyone learns differently. EduAdapt adjusts the way concepts are explained and practiced to match your understanding and pace.
            </p>
          </div>

          <div className="features-grid">
            {/* Card 1 */}
            <div className="feature-card">
              <div className="feature-icon-box">
                <Icon name="book" size={24} />
              </div>
              <h3 className="feature-title">Build Strong Foundations</h3>
              <p className="feature-desc">
                Understand the basics through clear explanations and guided examples. Break complex C programming logic into manageable, intuitive steps.
              </p>
              <button
                type="button"
                className="feature-link"
                onClick={() => onNavigate('learn')}
              >
                Explore interactive lessons →
              </button>
            </div>

            {/* Card 2 */}
            <div className="feature-card">
              <div className="feature-icon-box">
                <Icon name="target" size={24} />
              </div>
              <h3 className="feature-title">Learn at Your Level</h3>
              <p className="feature-desc">
                Explore concepts at the right level of depth for your current understanding. Move forward smoothly without feeling overwhelmed or held back.
              </p>
              <button
                type="button"
                className="feature-link"
                onClick={() => onNavigate('roadmap')}
              >
                View customized roadmap →
              </button>
            </div>

            {/* Card 3 */}
            <div className="feature-card">
              <div className="feature-icon-box">
                <Icon name="check" size={24} />
              </div>
              <h3 className="feature-title">Progress with Confidence</h3>
              <p className="feature-desc">
                Strengthen your skills through practice and meaningful feedback. Each concept check validates your mental model before advancing to new topics.
              </p>
              <button
                type="button"
                className="feature-link"
                onClick={() => onNavigate('practice')}
              >
                Try practice problems →
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* PHASE 4: SECTION 3 — How It Works */}
      <section id="how-it-works" className="landing-section">
        <div className="section-head">
          <span className="eyebrow">How It Works</span>
          <h2 className="section-headline">Your Journey to Mastery, Step by Step.</h2>
          <p className="section-subhead">
            A structured, confidence-building pathway that guides you from core basics to verified programming fluency.
          </p>
        </div>

        <div className="how-it-works-grid">
          <div className="step-card">
            <div className="step-number-badge">1</div>
            <h3 className="step-title">Discover Your Learning Level</h3>
            <p className="step-desc">
              Take an initial self-check to assess your familiarity with variables, memory layout, and control flow.
            </p>
          </div>

          <div className="step-card">
            <div className="step-number-badge">2</div>
            <h3 className="step-title">Learn Concepts Your Way</h3>
            <p className="step-desc">
              Receive structured lessons with visual memory diagrams, step-by-step code walkthroughs, and audio narration.
            </p>
          </div>

          <div className="step-card">
            <div className="step-number-badge">3</div>
            <h3 className="step-title">Practice and Strengthen</h3>
            <p className="step-desc">
              Write C code in an interactive workspace with instant compiler feedback and progressive multi-tier hints.
            </p>
          </div>

          <div className="step-card">
            <div className="step-number-badge">4</div>
            <h3 className="step-title">Progress to New Concepts</h3>
            <p className="step-desc">
              Demonstrate topic mastery on checkpoint evaluations to unlock advanced topics along your learning roadmap.
            </p>
          </div>
        </div>
      </section>

      {/* PHASE 4: SECTION 4 — Learning Experience Showcase */}
      <section id="showcase" className="landing-section soft-bg">
        <div className="landing-section-content">
          <div className="section-head">
            <span className="eyebrow">Product Experience</span>
            <h2 className="section-headline">Built for Real Student Success.</h2>
            <p className="section-subhead">
              Explore the actual tools inside EduAdapt designed to support your programming journey from day one.
            </p>
          </div>

          <div className="showcase-container">
            {/* Showcase Tab Navigation */}
            <div className="showcase-tabs-nav">
              {SHOWCASE_TABS.map((tab) => (
                <button
                  key={tab.id}
                  type="button"
                  className={`showcase-tab-btn ${activeShowcaseTab === tab.id ? 'active' : ''}`}
                  onClick={() => setActiveShowcaseTab(tab.id)}
                >
                  <Icon name={tab.icon} size={16} />
                  <span>{tab.label}</span>
                </button>
              ))}
            </div>

            {/* Showcase Tab Content */}
            <div className="showcase-tab-panel">
              {activeShowcaseTab === 'lessons' && (
                <div className="showcase-content-layout">
                  <div className="col" style={{ gap: 16 }}>
                    <span className="pill violet">Interactive Lessons</span>
                    <h3>Structured, Step-by-Step Explanations</h3>
                    <p className="small muted" style={{ lineHeight: 1.6 }}>
                      Every lesson provides a clear learning objective, conceptual overview, memory architecture diagram, verified C99 implementation, and common pitfalls to avoid.
                    </p>
                    <div className="row mt8">
                      <button type="button" className="btn primary sm" onClick={() => onNavigate('learn')}>
                        Open Sample Lesson →
                      </button>
                    </div>
                  </div>
                  <div className="card" style={{ padding: 20 }}>
                    <div className="row between" style={{ marginBottom: 12 }}>
                      <strong className="small">Pointers & Memory Addresses</strong>
                      <span className="pill green">Curriculum Aligned</span>
                    </div>
                    <div className="code-container" style={{ margin: 0 }}>
                      <pre className="code-block" style={{ fontSize: 12 }}>
                        <code>{`int value = 42;
int *ptr = &value; // Stores address of value
printf("Address: %p\\n", (void *)ptr);
*ptr = 100; // Directly updates memory location`}</code>
                      </pre>
                    </div>
                  </div>
                </div>
              )}

              {activeShowcaseTab === 'tutor' && (
                <div className="showcase-content-layout">
                  <div className="col" style={{ gap: 16 }}>
                    <span className="pill violet">Learning Tutor</span>
                    <h3>Ask Questions Whenever You Need Guidance</h3>
                    <p className="small muted" style={{ lineHeight: 1.6 }}>
                      Need help deciphering a compiler error, tracing a pointer address, or understanding array indexing? The Learning Tutor provides calm, grounded guidance with helpful memory diagrams.
                    </p>
                    <div className="row mt8">
                      <button type="button" className="btn primary sm" onClick={() => onNavigate('tutor')}>
                        Chat with Learning Tutor →
                      </button>
                    </div>
                  </div>
                  <div className="card col" style={{ padding: 20, gap: 12 }}>
                    <div className="msg user" style={{ alignSelf: 'flex-end', fontSize: '0.85em' }}>
                      How does dereferencing work when accessing arrays with pointers?
                    </div>
                    <div className="msg ai" style={{ alignSelf: 'flex-start', fontSize: '0.85em' }}>
                      In C, an array name acts like a pointer to its first element. <code>*(arr + i)</code> evaluates to exactly the same memory cell as <code>arr[i]</code>.
                    </div>
                  </div>
                </div>
              )}

              {activeShowcaseTab === 'practice' && (
                <div className="showcase-content-layout">
                  <div className="col" style={{ gap: 16 }}>
                    <span className="pill violet">Coding Practice</span>
                    <h3>Safe C99 Code Practice with Progressive Hints</h3>
                    <p className="small muted" style={{ lineHeight: 1.6 }}>
                      Write real C99 programs, supply custom inputs, run test cases, and reveal progressive 4-tier hints only when you want help—without spoiling the answer.
                    </p>
                    <div className="row mt8">
                      <button type="button" className="btn primary sm" onClick={() => onNavigate('practice')}>
                        Open Coding Practice →
                      </button>
                    </div>
                  </div>
                  <div className="card col" style={{ padding: 20, gap: 10 }}>
                    <div className="row between">
                      <strong className="small">Dynamic Array Accumulation</strong>
                      <span className="pill green">All Tests Passed</span>
                    </div>
                    <div className="terminal-box" style={{ margin: 0, fontSize: 12 }}>
                      Output (stdout):<br />
                      Total Elements: 5<br />
                      Sum: 150 · Average: 30.00<br />
                      Execution time: 0.04s
                    </div>
                  </div>
                </div>
              )}

              {activeShowcaseTab === 'assessments' && (
                <div className="showcase-content-layout">
                  <div className="col" style={{ gap: 16 }}>
                    <span className="pill violet">Progress & Insights</span>
                    <h3>Track Your Growth Across All 5 Units</h3>
                    <p className="small muted" style={{ lineHeight: 1.6 }}>
                      View verified topic mastery, practice accuracy, and diagnostic breakdowns across syntax, memory models, and problem-solving application.
                    </p>
                    <div className="row mt8">
                      <button type="button" className="btn primary sm" onClick={() => onNavigate('progress')}>
                        View Your Progress →
                      </button>
                    </div>
                  </div>
                  <div className="grid g2">
                    <div className="card stat" style={{ padding: 16 }}>
                      <span className="muted tiny">Topic Mastery</span>
                      <div className="num" style={{ fontSize: '1.4em' }}>88%</div>
                    </div>
                    <div className="card stat" style={{ padding: 16 }}>
                      <span className="muted tiny">Practice Accuracy</span>
                      <div className="num" style={{ fontSize: '1.4em' }}>92%</div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </section>

      {/* PHASE 4: SECTION 5 — Adaptive Learning Comparison */}
      <section id="adaptive" className="landing-section">
        <div className="section-head">
          <span className="eyebrow">Adaptive Learning</span>
          <h2 className="section-headline">
            Not Everyone Learns the Same Way.<br />
            Neither Should Their Lessons.
          </h2>
          <p className="section-subhead">
            EduAdapt tailors explanation depth, examples, and practice pace based on individual understanding.
          </p>
        </div>

        <div className="comparison-grid">
          {/* Pathway A: Foundational Learner */}
          <div className="comparison-column">
            <div className="comparison-header">
              <div className="comparison-persona">
                <span className="persona-avatar">A</span>
                <div>
                  <strong>Foundational Pathway</strong>
                  <div className="tiny muted">For students building core concepts</div>
                </div>
              </div>
              <span className="pill violet">Step-by-Step</span>
            </div>

            <div className="comparison-list">
              <div className="comparison-item">
                <span className="trust-check"><Icon name="check" size={14} /></span>
                <span><strong>Micro-chunk explanations</strong> focused on foundational memory concepts and variable sizing.</span>
              </div>
              <div className="comparison-item">
                <span className="trust-check"><Icon name="check" size={14} /></span>
                <span><strong>Visual address analogies</strong> illustrating stack slots before introducing pointer arithmetic.</span>
              </div>
              <div className="comparison-item">
                <span className="trust-check"><Icon name="check" size={14} /></span>
                <span><strong>Frequent concept checks</strong> with immediate clarification when misconceptions occur.</span>
              </div>
              <div className="comparison-item">
                <span className="trust-check"><Icon name="check" size={14} /></span>
                <span><strong>Targeted reinforcement</strong> reinforcing prerequisite topics before introducing advanced heap allocation.</span>
              </div>
            </div>
          </div>

          {/* Pathway B: Advanced Learner */}
          <div className="comparison-column highlighted">
            <div className="comparison-header">
              <div className="comparison-persona">
                <span className="persona-avatar">B</span>
                <div>
                  <strong>Accelerated Pathway</strong>
                  <div className="tiny muted">For students ready for deeper challenges</div>
                </div>
              </div>
              <span className="pill green">Deep & Rapid</span>
            </div>

            <div className="comparison-list">
              <div className="comparison-item">
                <span className="trust-check"><Icon name="check" size={14} /></span>
                <span><strong>Streamlined explanations</strong> that progress straight into practical implementation and pointer arithmetic.</span>
              </div>
              <div className="comparison-item">
                <span className="trust-check"><Icon name="check" size={14} /></span>
                <span><strong>Edge-case problem solving</strong> covering memory leaks, dangling pointers, and struct alignments.</span>
              </div>
              <div className="comparison-item">
                <span className="trust-check"><Icon name="check" size={14} /></span>
                <span><strong>Advanced coding exercises</strong> with custom inputs and multi-case compiler test suites.</span>
              </div>
              <div className="comparison-item">
                <span className="trust-check"><Icon name="check" size={14} /></span>
                <span><strong>Immediate milestone advancement</strong> unlocking subsequent curriculum units upon demonstrating mastery.</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* PHASE 4: SECTION 6 — Programming Practice Showcase */}
      <section id="practice" className="landing-section soft-bg">
        <div className="landing-section-content">
          <div className="section-head">
            <span className="eyebrow">Interactive Practice</span>
            <h2 className="section-headline">Turn Understanding into Real Programming Skills.</h2>
            <p className="section-subhead">
              Write C code, run programs, inspect runtime outputs, and learn from instant diagnostic guidance.
            </p>
          </div>

          <div className="practice-showcase-box">
            <div className="practice-showcase-header">
              <div className="row" style={{ gap: 8 }}>
                <Icon name="code" size={14} />
                <span>workspace/solution.c (C99 Standard)</span>
              </div>
              <span className="pill green" style={{ fontSize: '0.75em' }}>Protected Execution</span>
            </div>

            <div className="practice-showcase-body">
              <div className="practice-code-area">
                <span className="code-comment">// Exercise: Reverse an integer array in place</span><br />
                <span className="code-keyword">#include</span> &lt;<span className="code-str">stdio.h</span>&gt;<br /><br />
                <span className="code-type">void</span> <span className="code-fn">reverseArray</span>(<span className="code-type">int</span> *arr, <span className="code-type">int</span> size) &#123;<br />
                &nbsp;&nbsp;&nbsp;&nbsp;<span className="code-type">int</span> *start = arr;<br />
                &nbsp;&nbsp;&nbsp;&nbsp;<span className="code-type">int</span> *end = arr + size - <span className="code-num">1</span>;<br />
                &nbsp;&nbsp;&nbsp;&nbsp;<span className="code-keyword">while</span> (start &lt; end) &#123;<br />
                &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span className="code-type">int</span> temp = *start;<br />
                &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;*start = *end;<br />
                &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;*end = temp;<br />
                &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;start++;<br />
                &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;end--;<br />
                &nbsp;&nbsp;&nbsp;&nbsp;&#125;<br />
                &#125;
              </div>

              <div className="practice-output-area">
                <div>
                  <span className="tiny muted" style={{ color: '#94a3b8' }}>Program Output:</span>
                  <div className="terminal-box" style={{ color: '#4ade80', marginTop: 6 }}>
                    Original: [ 10, 20, 30, 40, 50 ]<br />
                    Reversed: [ 50, 40, 30, 20, 10 ]<br />
                    Result: PASSED (All 3 test cases satisfied)
                  </div>
                </div>

                <div className="col" style={{ gap: 6 }}>
                  <span className="tiny muted" style={{ color: '#94a3b8' }}>Progressive Hint Ladder:</span>
                  <div className="choice" style={{ padding: '8px 12px', background: '#1e243b', borderColor: '#2f3650', color: '#e2e8f0' }}>
                    <div className="small"><strong>Hint 1:</strong> Use two pointers starting at opposite ends.</div>
                  </div>
                </div>

                <div className="row mt8">
                  <button type="button" className="btn primary sm" onClick={() => onNavigate('practice')}>
                    Try Coding Workspace →
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* PHASE 4: SECTION 7 — Progress and Mastery */}
      <section className="landing-section">
        <div className="section-head">
          <span className="eyebrow">Continuous Mastery</span>
          <h2 className="section-headline">Every Concept You Master Is a Step Forward.</h2>
          <p className="section-subhead">
            Track your progress across all 5 syllabus units with clear milestone roadmaps.
          </p>
        </div>

        <div className="progress-showcase-grid">
          <div className="card col" style={{ gap: 14 }}>
            <h3>Syllabus Unit Mastery</h3>
            <div className="col" style={{ gap: 12 }}>
              <div>
                <div className="row between small">
                  <strong>Unit 1: Fundamentals of Computing & C</strong>
                  <span className="pill green">95%</span>
                </div>
                <div className="bar green mt8"><i style={{ width: '95%' }} /></div>
              </div>
              <div>
                <div className="row between small">
                  <strong>Unit 2: Control Structures & Loops</strong>
                  <span className="pill green">90%</span>
                </div>
                <div className="bar green mt8"><i style={{ width: '90%' }} /></div>
              </div>
              <div>
                <div className="row between small">
                  <strong>Unit 3: Arrays & Strings</strong>
                  <span className="pill green">82%</span>
                </div>
                <div className="bar green mt8"><i style={{ width: '82%' }} /></div>
              </div>
              <div>
                <div className="row between small">
                  <strong>Unit 4: Functions & Pointers</strong>
                  <span className="pill violet">78%</span>
                </div>
                <div className="bar mt8"><i style={{ width: '78%' }} /></div>
              </div>
              <div>
                <div className="row between small">
                  <strong>Unit 5: Structures & Dynamic Memory</strong>
                  <span className="pill">Upcoming</span>
                </div>
                <div className="bar mt8"><i style={{ width: '40%' }} /></div>
              </div>
            </div>
          </div>

          <div className="card col" style={{ gap: 14 }}>
            <h3>Your Milestone Learning Roadmap</h3>
            <div className="timeline">
              <div className="tl-item completed">
                <div className="tl-rail">
                  <span className="node"><Icon name="check" size={12} /></span>
                  <span className="line" />
                </div>
                <div className="tl-body">
                  <strong>1. Variable Scope & Stack Frame Representation</strong>
                  <p className="hint">Mastered · Foundations verified</p>
                </div>
              </div>
              <div className="tl-item current">
                <div className="tl-rail">
                  <span className="node">2</span>
                  <span className="line" />
                </div>
                <div className="tl-body">
                  <strong>2. Pointer Dereferencing and Address-Of Operations</strong>
                  <p className="hint">In progress · Active learning focus</p>
                </div>
              </div>
              <div className="tl-item">
                <div className="tl-rail">
                  <span className="node">3</span>
                </div>
                <div className="tl-body">
                  <strong>3. Heap Memory Allocation (malloc, calloc, and free)</strong>
                  <p className="hint">Next in sequence</p>
                </div>
              </div>
            </div>
            <div className="row mt8">
              <button type="button" className="btn sm" onClick={() => onNavigate('roadmap')}>
                Explore Full Roadmap →
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* PHASE 4: SECTION 8 — Final Call to Action */}
      <section className="landing-section" style={{ paddingTop: 0 }}>
        <div className="landing-final-cta">
          <h2>Your Learning Journey Starts Here.</h2>
          <p>
            Build your understanding, strengthen your skills, and move forward with confidence. Start learning PPS and C programming at your pace.
          </p>
          <div className="row center" style={{ gap: 16 }}>
            <button
              type="button"
              className="btn primary"
              style={{ padding: '14px 32px', fontSize: '1.08em', fontWeight: 600 }}
              onClick={handleStartLearning}
            >
              Start Learning Now <Icon name="arrow" size={16} />
            </button>
            <button
              type="button"
              className="btn"
              style={{ background: 'transparent', color: '#fff', borderColor: 'rgba(255,255,255,0.3)' }}
              onClick={() => onNavigate('curriculum')}
            >
              Explore Course Curriculum
            </button>
          </div>
        </div>
      </section>

      {/* PHASE 4: SECTION 9 — Minimal Product Footer */}
      <footer className="landing-footer">
        <div className="landing-footer-inner">
          <div className="footer-brand-col">
            <div className="row" style={{ gap: 8 }}>
              <div className="landing-logo-mark docked">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#ffffff" strokeWidth="2.3" strokeLinejoin="round">
                  <path d="M3 9l9-5 9 5-9 5-9-5z" />
                  <path d="M7 11.5V16c0 1.6 2.2 3 5 3s5-1.4 5-3v-4.5" />
                </svg>
              </div>
              <strong style={{ fontSize: '1.1em', color: 'var(--ink)' }}>EduAdapt</strong>
            </div>
            <p className="footer-desc">
              A personalized adaptive learning platform designed to help students master Programming for Problem Solving (PPS) and C programming step by step.
            </p>
          </div>

          <div>
            <div className="footer-heading">Learning</div>
            <div className="footer-links-list">
              <button type="button" className="footer-link-btn" onClick={() => onNavigate('home')}>Dashboard</button>
              <button type="button" className="footer-link-btn" onClick={() => onNavigate('curriculum')}>Curriculum</button>
              <button type="button" className="footer-link-btn" onClick={() => onNavigate('learn')}>Interactive Lessons</button>
              <button type="button" className="footer-link-btn" onClick={() => onNavigate('roadmap')}>Learning Roadmap</button>
            </div>
          </div>

          <div>
            <div className="footer-heading">Practice</div>
            <div className="footer-links-list">
              <button type="button" className="footer-link-btn" onClick={() => onNavigate('tutor')}>Learning Tutor</button>
              <button type="button" className="footer-link-btn" onClick={() => onNavigate('practice')}>Coding Workspace</button>
              <button type="button" className="footer-link-btn" onClick={() => onNavigate('tests')}>Assessments</button>
              <button type="button" className="footer-link-btn" onClick={() => onNavigate('progress')}>Your Progress</button>
            </div>
          </div>

          <div>
            <div className="footer-heading">Preferences</div>
            <div className="footer-links-list">
              <button type="button" className="footer-link-btn" onClick={() => onNavigate('settings')}>Accessibility</button>
              <button type="button" className="footer-link-btn" onClick={() => onNavigate('profile')}>Student Profile</button>
              <button type="button" className="footer-link-btn" onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}>Back to Top</button>
            </div>
          </div>
        </div>

        <div className="footer-bottom">
          <span>&copy; 2026 EduAdapt. All rights reserved.</span>
          <span>Programming for Problem Solving (PPS) · C99 Standard</span>
        </div>
      </footer>
    </div>
  );
}
