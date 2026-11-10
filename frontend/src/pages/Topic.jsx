import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";
import { speak, stopSpeaking } from "../lib/speech";
import { Bar, Icon, Loading, Markdown, Spinner, StatusPill } from "../components/ui";

// Break lesson text into micro-steps (3-5 min reads). Smaller steps when micro-chunks are on.
function toSteps(lessons, micro) {
  const paras = lessons.flatMap((l) => l.text.split(/(?<=[.!?])\s+(?=[A-Z])/));
  const size = micro ? 2 : 4;
  const steps = [];
  for (let i = 0; i < paras.length; i += size) steps.push(paras.slice(i, i + size).join(" "));
  return steps;
}

export default function TopicPage() {
  const { id } = useParams();
  const { profile } = useAuth();
  const nav = useNavigate();
  const [d, setD] = useState(null);
  const [step, setStep] = useState(0);
  const [done, setDone] = useState(new Set());
  const [ai, setAi] = useState(null);
  const [aiBusy, setAiBusy] = useState(false);
  const micro = profile?.profile?.accessibility?.chunk_size === "micro";
  const speed = profile?.profile?.accessibility?.audio_speed || 1;

  useEffect(() => {
    setD(null); setStep(0); setDone(new Set()); setAi(null);
    api.get(`/topics/${id}`).then(setD);
    api.post("/tutor/sessions", { topic_id: Number(id) }).catch(() => {}); // logs study time
    return stopSpeaking;
  }, [id]);
  const steps = useMemo(() => (d ? toSteps(d.lessons, micro) : []), [d, micro]);
  if (!d) return <Loading />;
  const t = d.topic;

  const explain = async () => {
    setAiBusy(true);
    try {
      setAi(await api.post("/tutor/ask", { query: `Explain ${t.title} simply with one small example.`, topic_id: t.topic_id, interaction_type: "simplify" }));
    } catch (e) {
      setAi({ answer: `Couldn't reach the tutor: ${e.message}`, sources: [] });
    } finally {
      setAiBusy(false);
    }
  };
  const markDone = () => {
    setDone(new Set([...done, step]));
    if (step < steps.length - 1) setStep(step + 1);
  };

  return (
    <div className="page">
      <div className="page-head">
        <div>
          <span className="muted small"><Link to="/subjects">{d.subject.name}</Link> › {d.module.title}</span>
          <h1 className="mt8">{t.title}</h1>
          <div className="row mt8 wrap">
            <span className="pill violet">{d.co}</span><span className="pill">~{t.estimated_minutes} min</span>
            <span className="pill">Level: {d.difficulty}</span><StatusPill status={t.status} />
          </div>
        </div>
        <div className="row">
          <button className="btn" onClick={() => nav(`/tutor?topic=${t.topic_id}`)}><Icon name="chat" size={16} />Ask tutor</button>
          <button className="btn primary" onClick={() => nav(`/practice?topic=${t.topic_id}`)}>Practice <Icon name="arrow" size={16} /></button>
        </div>
      </div>

      {d.prerequisites.some((p) => p.status !== "mastered") && (
        <p className="notice">Builds on: {d.prerequisites.map((p) => p.title).join(", ")}. A quick look back may help.</p>
      )}

      <div className="grid" style={{ gridTemplateColumns: "2fr 1fr", alignItems: "start" }}>
        <div className="col">
          <div className="card">
            {steps.length === 0 ? <p className="empty">No notes indexed for this topic yet. Ask the tutor instead.</p> : (
              <>
                <div className="row between">
                  <span className="eyebrow">Step {step + 1} of {steps.length}</span>
                  <button className="btn sm" onClick={() => speak(steps[step], { speed })}><Icon name="speaker" size={14} />Read aloud</button>
                </div>
                <p className="mt16" style={{ fontSize: "1.08em", lineHeight: 1.8, maxWidth: "68ch" }}>{steps[step]}</p>
                <div className="row between mt24">
                  <button className="btn" disabled={step === 0} onClick={() => setStep(step - 1)}>← Back</button>
                  <button className="btn primary" onClick={markDone}>{step === steps.length - 1 ? "Complete Lesson" : "Got it, next →"}</button>
                </div>
              </>
            )}
          </div>
          <div className="card">
            <div className="row between"><h3>Alternative Explanation</h3>
              <button className="btn sm" onClick={explain} disabled={aiBusy}>{aiBusy ? <Spinner /> : <><Icon name="refresh" size={14} /> Explain</>}</button></div>
            {ai && (
              <div className="mt16">
                <Markdown text={ai.answer} />
                {ai.verification && (
                  <p className="hint mt8">Aligned with {ai.sources.length} course reference materials · {ai.verification.passed ? "Verified" : "Reference notes"}</p>
                )}
              </div>
            )}
          </div>
        </div>
        <div className="col">
          <div className="card">
            <h3>In this lesson</h3>
            <div className="mt8"><Bar value={(100 * done.size) / Math.max(1, steps.length)} tone="green" /></div>
            <p className="hint mt8">{done.size} of {steps.length} steps done</p>
            {steps.map((s, i) => (
              <button key={i} className="list-item" style={{ width: "100%", background: "none", border: "none", cursor: "pointer", textAlign: "left" }} onClick={() => setStep(i)}>
                <span className={`dot ${done.has(i) ? "done" : i === step ? "now" : ""}`} />
                <span className="small grow" style={{ fontWeight: i === step ? 600 : 400 }}>{s.split(" ").slice(0, 6).join(" ")}…</span>
              </button>
            ))}
          </div>
          <div className="card">
            <h3>In this unit</h3>
            {d.siblings.map((s) => (
              <Link key={s.topic_id} to={`/topics/${s.topic_id}`} className="list-item" style={{ color: "inherit" }}>
                <span className="small grow" style={{ fontWeight: s.topic_id === t.topic_id ? 600 : 400 }}>{s.title}</span><StatusPill status={s.status} />
              </Link>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
