import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../lib/api";
import { Bar, Loading, StatusPill } from "../components/ui";

export default function Subjects() {
  const [data, setData] = useState(null);
  const [active, setActive] = useState(null);
  const [q, setQ] = useState("");
  const load = () => api.get("/subjects").then((d) => {
    setData(d);
    setActive((a) => a ?? (d.subjects.find((s) => s.enrolled) || d.subjects[0])?.subject_id);
  });
  useEffect(() => { load(); }, []);
  if (!data) return <Loading />;
  const subj = data.subjects.find((s) => s.subject_id === active);
  const match = (t) => !q || t.title.toLowerCase().includes(q.toLowerCase());

  return (
    <div className="page">
      <div className="page-head">
        <div><span className="eyebrow plain">Your courses</span><h1>Subjects & topics</h1>
          <p className="muted">Every topic is mapped to its unit and course outcome (CO1–CO5).</p></div>
      </div>
      <div className="grid g3">
        {data.subjects.map((s) => (
          <button key={s.subject_id} className={`card choice ${s.subject_id === active ? "on" : ""}`} onClick={() => setActive(s.subject_id)}>
            <div className="row between"><strong>{s.name}</strong>{s.enrolled ? <span className="pill green">Enrolled</span> : <span className="pill">Not enrolled</span>}</div>
            <div className="hint">{s.code} · {s.modules.length} units</div>
            <div className="mt16 row small"><span className="muted grow">Mastery</span>{Math.round(s.mastery)}%</div>
            <div className="mt8"><Bar value={s.mastery} /></div>
          </button>
        ))}
      </div>
      {subj && (
        <>
          <div className="row between wrap">
            <h2>Units in {subj.name}</h2>
            <div className="row">
              <input className="input" style={{ width: 240 }} placeholder="Search topics…" value={q} onChange={(e) => setQ(e.target.value)} aria-label="Search topics" />
              {!subj.enrolled && <button className="btn primary" onClick={() => api.post(`/subjects/${subj.subject_id}/enroll`).then(load)}>Enroll</button>}
            </div>
          </div>
          <div className="grid g2">
            {subj.modules.map((m) => (
              <div key={m.module_id} className="card">
                <div className="row between"><div><strong>{m.title}</strong><div className="hint">{m.topics.length} topics</div></div><span className="pill violet">{m.co}</span></div>
                <div className="mt8"><Bar value={m.mastery} /></div>
                <div className="mt8">
                  {m.topics.filter(match).map((t) => (
                    <Link key={t.topic_id} to={`/topics/${t.topic_id}`} className="list-item" style={{ color: "inherit" }}>
                      <div className="grow small"><strong>{t.title}</strong><div className="hint">~{t.estimated_minutes} min{t.mastery != null ? ` · ${Math.round(t.mastery)}% mastery` : ""}</div></div>
                      <StatusPill status={t.status} />
                    </Link>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
