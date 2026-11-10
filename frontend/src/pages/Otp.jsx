import { useRef, useState, useEffect } from "react";
import { useNavigate, Link } from "react-router-dom";
import { AuthLayout } from "../components/Layouts";
import { Icon, Spinner } from "../components/ui";
import { api, token } from "../lib/api";
import { useAuth } from "../lib/auth";

export default function Otp({ onNavigate, onVerifySuccess }) {
  const phone = sessionStorage.getItem("ea_phone") || "";
  const devCode = sessionStorage.getItem("ea_dev_code");
  const [digits, setDigits] = useState(Array(6).fill(""));
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [cooldown, setCooldown] = useState(30);
  const refs = useRef([]);
  const nav = useNavigate();
  const { refresh } = useAuth();

  useEffect(() => {
    if (!phone) {
      if (onNavigate) onNavigate("login");
      else if (nav) nav("/login");
    }
    refs.current[0]?.focus();
  }, [phone, nav, onNavigate]);

  useEffect(() => {
    if (cooldown <= 0) return;
    const t = setTimeout(() => setCooldown((c) => c - 1), 1000);
    return () => clearTimeout(t);
  }, [cooldown]);

  const setAt = (i, v) => {
    const clean = v.replace(/\D/g, "");
    if (clean.length > 1) { // pasted full code
      const arr = clean.slice(0, 6).split("");
      setDigits([...arr, ...Array(6 - arr.length).fill("")]);
      refs.current[Math.min(arr.length, 5)]?.focus();
      return;
    }
    const next = [...digits];
    next[i] = clean;
    setDigits(next);
    if (clean && i < 5) refs.current[i + 1]?.focus();
  };

  const verify = async (e) => {
    e?.preventDefault();
    const code = digits.join("");
    if (code.length !== 6) return setError("Enter all 6 digits.");
    setBusy(true);
    setError("");
    try {
      const r = await api.post("/auth/verify-otp", { phone, code });
      token.set(r.token);
      sessionStorage.removeItem("ea_dev_code");
      const me = await refresh();
      if (onVerifySuccess) {
        onVerifySuccess(me);
      } else if (onNavigate) {
        onNavigate("home");
      } else if (nav) {
        nav(me?.onboarding_complete ? "/dashboard" : "/onboarding/details");
      }
    } catch (err) {
      setError(err.message || "Failed to verify code. Please try again.");
    } finally {
      setBusy(false);
    }
  };

  const resend = async () => {
    setCooldown(30);
    try {
      const r = await api.post("/auth/send-otp", { phone });
      if (r.dev_code) sessionStorage.setItem("ea_dev_code", r.dev_code);
    } catch (err) {
      setError(err.message || "Failed to resend code.");
    }
  };

  const handleChangePhone = () => {
    if (onNavigate) onNavigate("login");
    else if (nav) nav("/login");
  };

  return (
    <AuthLayout>
      <form className="auth-form" onSubmit={verify}>
        <span className="icon-chip"><Icon name="phone" /></span>
        <span className="eyebrow" style={{ alignSelf: "flex-start" }}>Verify your number</span>
        <h1>Check your phone</h1>
        <p className="muted small">Enter the 6-digit code we sent to +91 {phone.replace(/(\d{5})(\d+)/, "$1 $2")}. It expires in 5 minutes.</p>
        {devCode && <p className="notice">Dev mode (no SMS provider): your code is <strong>{devCode}</strong></p>}
        <div className="otp" role="group" aria-label="One-time code">
          {digits.map((d, i) => (
            <input key={i} ref={(el) => (refs.current[i] = el)} value={d} inputMode="numeric" maxLength={6}
                   aria-label={`Digit ${i + 1}`} onChange={(e) => setAt(i, e.target.value)}
                   onKeyDown={(e) => e.key === "Backspace" && !d && i > 0 && refs.current[i - 1]?.focus()} />
          ))}
        </div>
        {error && <p className="error" role="alert">{error}</p>}
        <button className="btn primary block" disabled={busy}>{busy ? <Spinner /> : "Verify and continue"}</button>
        <div className="row between small">
          <button type="button" className="btn ghost sm" onClick={handleChangePhone}>Change phone number</button>
          <button type="button" className="btn ghost sm" disabled={cooldown > 0} onClick={resend}>
            {cooldown > 0 ? `Resend in ${cooldown}s` : "Resend code"}
          </button>
        </div>
        <p className="row tiny muted"><Icon name="lock" size={14} style={{ color: "var(--green)" }} />We never share your number.</p>
      </form>
    </AuthLayout>
  );
}
