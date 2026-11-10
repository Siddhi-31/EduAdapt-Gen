import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../lib/api";
import { Bar, DONE, Icon, Loading, StatusPill } from "../components/ui";

const FILTERS = [["all", "All"], ["done", "Done"], ["current", "Current"], ["reinforcement", "Reinforce"], ["upcoming", "Upcoming"]];

export default function Roadmap() {
  const [d, setD] = useState(null);
  const [f, setF] = useState("all");
  const [busy, setBusy] = useState(false);
  const nav = useNavigate();
  useEffect(() => { api.get("/roadmap").then(setD); }, []);
  if (!d) return <Loading />;
  const tr = d.tracker || {};
  const twin = tr.learning_twin || {};
  const show = d.items.filter((i) => f === "all" || (f === "done" ? DONE.includes(i.status) : i.status === f));

  return (
    <div className="page">
      <div className="page-head">
        <div><span className="eyebrow plain">Your plan</span><h1>Your learning roadmap</h1>
          <p className="muted">Milestone path adapted to your pace and topic mastery.</p></div>
        <button className="btn" disabled={busy} onClick={async () => { setBusy(true); setD(await api.post("/roadmap/rebuild")); setBusy(false); }}>
          <Icon name="spark" size={16} />Refresh plan
        </button>
      </div>
      <div className="grid" style={{ gridTemplateColumns: "2fr 1fr" }}>
        <div className="card">
          <span className="muted small">Goal</span>
          <h3>{d.goal?.title || d.roadmap.title}</h3>
          {d.goal?.target_date && <p className="hint">Target: {new Date(d.goal.target_date).toLocaleDateString()}</p>}
          <div className="mt16"><Bar value={tr.overall_progress} tone="green" /></div>
          <p className="hint mt8">{Math.round(tr.overall_progress || 0)}% of topics mastered</p>
        </div>
        <div className="card"><span className="muted small">Overall mastery</span><div className="stat"><div className="num">{Math.round(tr.overall_mastery || 0)}%</div></div><p className="hint">Average across topics you've attempted.</p></div>
      </div>
      <div className="grid" style={{ gridTemplateColumns: "2fr 1fr", alignItems: "start" }}>
        <div className="col">
          <div className="chip-select">
            {FILTERS.map(([k, l]) => <button key={k} className={f === k ? "on" : ""} onClick={() => setF(k)}>{l}</button>)}
          </div>
          <div className="timeline">
            {show.map((it, idx) => (
              <div key={it.roadmap_item_id} className={`tl-item ${it.status}`}>
                <div className="tl-rail"><span className="node">{DONE.includes(it.status) ? <Icon name="check" size={12} /> : it.sequence_no}</span>{idx < show.length - 1 && <span className="line" />}</div>
                <div className="tl-body">
                  <div className="card" style={{ padding: 16 }}>
                    <div className="row between"><strong>{it.topic.title}</strong><StatusPill status={it.status} /></div>
                    <p className="hint">~{it.topic.estimated_minutes} min · recommended level: {it.recommended_difficulty}
                      {it.topic.mastery != null && ` · mastery ${Math.round(it.topic.mastery)}%`}</p>
                    {it.topic.mastery != null && <div className="mt8"><Bar value={it.topic.mastery} /></div>}
                    {it.status !== "upcoming" && (
                      <div className="row mt16">
                        <button className="btn sm primary" onClick={() => nav(`/topics/${it.topic_id}`)}>{DONE.includes(it.status) ? "Review" : "Open lesson"}</button>
                        <button className="btn sm" onClick={() => nav(`/practice?topic=${it.topic_id}`)}>Practice</button>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
        <div className="col">
          <div className="card">
            <h3>Why this path?</h3>
            <p className="small muted mt8">Topics follow their prerequisites. Mastered topics advance automatically, while topics needing reinforcement provide focused practice.</p>
            {twin.weak_topics?.length > 0 && <p className="small mt8"><strong>Reinforcing:</strong> {twin.weak_topics.join(", ")}</p>}
            {twin.strong_topics?.length > 0 && <p className="small mt8"><strong>Strong in:</strong> {twin.strong_topics.join(", ")}</p>}
          </div>
          <div className="card">
            <h3>Next steps</h3>
            {d.recommendations.map((r) => (
              <div key={r.recommendation_id} className="list-item">
                <div className="grow small"><strong>{r.title}</strong><div className="hint">{r.reason}</div></div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
