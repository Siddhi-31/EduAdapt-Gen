import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { OnboardLayout } from "../components/Layouts";
import PreferencesForm from "../components/PreferencesForm";
import { Spinner, Loading, Icon } from "../components/ui";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";

export function OnbDetails() {
  const nav = useNavigate();
  const { profile, refresh } = useAuth();
  const [meta, setMeta] = useState(null);
  const [f, setF] = useState({ name: "", institution_id: "", program_id: "", semester: "3", preferred_language: "English", subject_ids: [] });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    api.get("/meta").then((m) => {
      setMeta(m);
      setF((x) => ({ ...x, name: profile?.user?.name || "", preferred_language: profile?.user?.preferred_language || "English", institution_id: profile?.profile?.institution_id || m.institutions[0]?.institution_id || "",
        program_id: profile?.profile?.program_id || m.programs[0]?.program_id || "", semester: profile?.profile?.semester || "3",
        subject_ids: profile?.subject_ids?.length ? profile.subject_ids : m.subjects.slice(0, 1).map((s) => s.subject_id) }));
    });
  }, [profile]);

  const toggleSub = (id) => setF((x) => ({ ...x, subject_ids: x.subject_ids.includes(id) ? x.subject_ids.filter((s) => s !== id) : [...x.subject_ids, id] }));

  const save = async (e) => {
    e.preventDefault();
    if (!f.name.trim()) return setError("Please tell us your name.");
    if (!f.subject_ids.length) return setError("Pick at least one subject.");
    setBusy(true);
    try {
      await api.put("/onboarding/details", f);
      await refresh();
      nav("/onboarding/preferences");
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  if (!meta) return <OnboardLayout step={0}><Loading /></OnboardLayout>;
  return (
    <OnboardLayout step={0}>
      <form className="col" style={{ gap: 20, maxWidth: 640 }} onSubmit={save}>
        <div><h1>Let's get to know you.</h1><p className="muted mt8">This helps us match your syllabus and course outcomes.</p></div>
        <div className="card col" style={{ gap: 16 }}>
          <h3>Student details</h3>
          <div className="grid g2">
            <label className="field">Full name<input className="input" value={f.name} onChange={(e) => setF({ ...f, name: e.target.value })} placeholder="Your name" /></label>
            <label className="field">Institution
              <select className="input" value={f.institution_id} onChange={(e) => setF({ ...f, institution_id: Number(e.target.value) })}>
                {meta.institutions.map((i) => <option key={i.institution_id} value={i.institution_id}>{i.name}</option>)}
              </select>
            </label>
            <label className="field">Program
              <select className="input" value={f.program_id} onChange={(e) => setF({ ...f, program_id: Number(e.target.value) })}>
                {meta.programs.map((p) => <option key={p.program_id} value={p.program_id}>{p.name}</option>)}
              </select>
            </label>
            <label className="field">Semester
              <select className="input" value={f.semester} onChange={(e) => setF({ ...f, semester: e.target.value })}>
                {[1, 2, 3, 4, 5, 6, 7, 8].map((s) => <option key={s} value={String(s)}>Semester {s}</option>)}
              </select>
            </label>
            <label className="field">Preferred language
              <select className="input" value={f.preferred_language} onChange={(e) => setF({ ...f, preferred_language: e.target.value })}>
                <option value="English">English</option><option value="Hindi">Hindi + English</option><option value="Tamil">Tamil + English</option>
              </select>
            </label>
          </div>
          <div className="field">Subjects this semester
            <div className="chip-select mt8">
              {meta.subjects.map((s) => (
                <button type="button" key={s.subject_id} className={f.subject_ids.includes(s.subject_id) ? "on" : ""}
                        aria-pressed={f.subject_ids.includes(s.subject_id)} onClick={() => toggleSub(s.subject_id)}>
                  {s.name} · {s.code}
                </button>
              ))}
            </div>
            <span className="hint mt8">Content is mapped to SRMIST Regulations 2021 units and CO1–CO5.</span>
          </div>
        </div>
        {error && <p className="error">{error}</p>}
        <div><button className="btn primary" disabled={busy}>{busy ? <Spinner /> : <>Continue <Icon name="arrow" size={16} /></>}</button></div>
      </form>
    </OnboardLayout>
  );
}

export function OnbPreferences() {
  const nav = useNavigate();
  const { profile, refresh } = useAuth();
  if (!profile) return <OnboardLayout step={1}><Loading /></OnboardLayout>;
  return (
    <OnboardLayout step={1}>
      <div className="col" style={{ gap: 20, maxWidth: 720 }}>
        <div><h1>Make learning your own.</h1><p className="muted mt8">Choose what helps you focus. Everything previews live.</p></div>
        <PreferencesForm initial={profile} submitLabel="Continue →" onSaved={async () => { await refresh(); nav("/onboarding/goal"); }} />
        <button className="btn ghost sm" style={{ alignSelf: "flex-start" }} onClick={() => nav("/onboarding/details")}>← Back</button>
      </div>
    </OnboardLayout>
  );
}

const QUICK = ["Master Data Structures for semester exams", "Prepare for CLA-1 unit test", "Get placement-ready in DSA", "Revise weak topics before finals"];

export function OnbGoal() {
  const nav = useNavigate();
  const { refresh } = useAuth();
  const [title, setTitle] = useState(QUICK[0]);
  const [date, setDate] = useState("");
  const [hours, setHours] = useState("5");
  const [diag, setDiag] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const save = async (e) => {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      await api.put("/onboarding/goal", { title, target_date: date || null, goal_type: "exam",
        description: `${hours} hours per week`, learning_goal: title });
      await refresh();
      if (diag) {
        const rm = await api.get("/roadmap");
        const first = rm.items.find((i) => i.status === "current") || rm.items[0];
        if (first) return nav(`/practice?topic=${first.topic_id}&purpose=diagnostic`);
      }
      nav("/dashboard");
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <OnboardLayout step={2}>
      <form className="col" style={{ gap: 20, maxWidth: 640 }} onSubmit={save}>
        <div><h1>Set a goal. Find your path.</h1><p className="muted mt8">We'll build a roadmap around it and adjust as you learn.</p></div>
        <div className="card col" style={{ gap: 16 }}>
          <label className="field">Your learning goal<input className="input" value={title} onChange={(e) => setTitle(e.target.value)} /></label>
          <div className="chip-select">
            {QUICK.map((q) => <button type="button" key={q} className={title === q ? "on" : ""} onClick={() => setTitle(q)}>{q}</button>)}
          </div>
          <div className="grid g2">
            <label className="field">Target date<input type="date" className="input" value={date} onChange={(e) => setDate(e.target.value)} /></label>
            <label className="field">Time per week
              <select className="input" value={hours} onChange={(e) => setHours(e.target.value)}>
                {["2", "5", "8", "12"].map((h) => <option key={h} value={h}>{h} hours</option>)}
              </select>
            </label>
          </div>
        </div>
        <div className="card soft row between">
          <div><strong className="small">Take a 5-question starting check</strong>
            <p className="hint">Finds your baseline so we don't make you repeat what you know. Not graded.</p></div>
          <input type="checkbox" checked={diag} onChange={(e) => setDiag(e.target.checked)} aria-label="Take diagnostic" style={{ width: 20, height: 20 }} />
        </div>
        {error && <p className="error">{error}</p>}
        <div className="row">
          <button type="button" className="btn ghost" onClick={() => nav("/onboarding/preferences")}>← Back</button>
          <button className="btn primary" disabled={busy}>{busy ? <Spinner /> : "Build my roadmap"}</button>
        </div>
      </form>
    </OnboardLayout>
  );
}
