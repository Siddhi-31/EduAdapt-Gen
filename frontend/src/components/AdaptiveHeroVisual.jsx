import React from 'react';
import { Icon } from './ui';

export function AdaptiveHeroVisual() {
  return (
    <div className="adaptive-hero-card">
      <div className="hero-card-header">
        <div className="hero-card-tag">
          <span className="live-dot" />
          <span>PPS Adaptive Learning Twin</span>
        </div>
        <span className="hero-card-badge">C Programming</span>
      </div>

      <div className="adaptive-pipeline">
        <div className="pipeline-node done">
          <div className="node-icon"><Icon name="check" size={14} /></div>
          <div className="node-info">
            <strong>01. C Fundamentals</strong>
            <span>Variables & Memory</span>
          </div>
          <span className="node-status">Foundational</span>
        </div>

        <div className="pipeline-connector done" />

        <div className="pipeline-node current">
          <div className="node-icon"><Icon name="target" size={14} /></div>
          <div className="node-info">
            <strong>02. Control Structures</strong>
            <span>Conditionals & Loops</span>
          </div>
          <span className="node-status pulse">Active Focus</span>
        </div>

        <div className="pipeline-connector" />

        <div className="pipeline-node upcoming">
          <div className="node-icon"><Icon name="code" size={14} /></div>
          <div className="node-info">
            <strong>03. Pointers & Memory</strong>
            <span>Addressing & Heap</span>
          </div>
          <span className="node-status">Adaptive Next</span>
        </div>
      </div>

      <div className="hero-code-box">
        <div className="code-box-header">
          <div className="code-dots">
            <span className="dot red" />
            <span className="dot yellow" />
            <span className="dot green" />
          </div>
          <span className="code-filename">adaptive_engine.c</span>
        </div>
        <pre className="code-content">
          <code>
            <span className="c-kw">#include</span> <span className="c-str">&lt;stdio.h&gt;</span>{'\n'}
            <span className="c-type">int</span> <span className="c-fn">main</span>() {'{\n'}
            {'  '}<span className="c-type">int</span> mastery = <span className="c-num">100</span>;{'\n'}
            {'  '}<span className="c-type">int</span>* p_knowledge = &amp;mastery;{'\n'}
            {'  '}<span className="c-fn">printf</span>(<span className="c-str">"Ready to master C: %d%%\\n"</span>, *p_knowledge);{'\n'}
            {'  '}<span className="c-kw">return</span> <span className="c-num">0</span>;{'\n'}
            {'}'}
          </code>
        </pre>
      </div>

      <div className="hero-features-row">
        <div className="hero-feat-chip">
          <Icon name="spark" size={13} />
          <span>Tailored Pace</span>
        </div>
        <div className="hero-feat-chip">
          <Icon name="chat" size={13} />
          <span>AI Tutor Guided</span>
        </div>
        <div className="hero-feat-chip">
          <Icon name="shield" size={13} />
          <span>100% Real Progress</span>
        </div>
      </div>
    </div>
  );
}
