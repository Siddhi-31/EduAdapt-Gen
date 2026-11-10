import React, { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { AuthLayout } from "../components/Layouts";
import { Icon, Spinner } from "../components/ui";
import { useAuth } from "../lib/auth";
import { api } from "../lib/api";

export default function Login({ onLoginSuccess, onNavigate }) {
  // Modes: 'login' | 'register' | 'otp'
  const [mode, setMode] = useState("login");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  // Form Fields
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [phone, setPhone] = useState("");
  const [college, setCollege] = useState("");
  const [department, setDepartment] = useState("");

  // States
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [successMsg, setSuccessMsg] = useState("");

  const { login, register, refresh } = useAuth();
  const nav = useNavigate();

  const handleSuccessRedirect = (authResult) => {
    if (onLoginSuccess) {
      onLoginSuccess(authResult);
    } else if (onNavigate) {
      onNavigate("home");
    } else if (nav) {
      nav("/dashboard");
    }
  };

  const handleLoginSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSuccessMsg("");

    const cleanEmail = email.trim().toLowerCase();
    if (!cleanEmail || !cleanEmail.includes("@")) {
      return setError("Please enter a valid email address.");
    }
    if (!password) {
      return setError("Please enter your account password.");
    }

    setBusy(true);
    try {
      const res = await login(cleanEmail, password);
      handleSuccessRedirect(res);
    } catch (err) {
      setError(err.message || "Failed to sign in. Please verify your email and password.");
    } finally {
      setBusy(false);
    }
  };

  const handleRegisterSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSuccessMsg("");

    const cleanName = fullName.trim();
    const cleanEmail = email.trim().toLowerCase();

    if (!cleanName || cleanName.length < 2) {
      return setError("Please provide your full name (minimum 2 characters).");
    }
    if (!cleanEmail || !cleanEmail.includes("@")) {
      return setError("Please provide a valid email address.");
    }
    if (!password || password.length < 8) {
      return setError("Password must be at least 8 characters long.");
    }
    if (!/[0-9]/.test(password) || !/[a-zA-Z]/.test(password)) {
      return setError("Password must contain at least one letter and one number.");
    }
    if (password !== confirmPassword) {
      return setError("Password and Confirm Password do not match.");
    }

    setBusy(true);
    try {
      const payload = {
        full_name: cleanName,
        email: cleanEmail,
        password,
        confirm_password: confirmPassword,
        college: college.trim() || undefined,
        department: department.trim() || undefined,
      };
      const res = await register(payload);
      setSuccessMsg("Account created successfully! Redirecting...");
      setTimeout(() => {
        handleSuccessRedirect(res);
      }, 400);
    } catch (err) {
      setError(err.message || "Unable to create account. Please try again.");
    } finally {
      setBusy(false);
    }
  };

  const handleOtpSendSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSuccessMsg("");

    const digits = phone.replace(/\D/g, "");
    if (digits.length !== 10) {
      return setError("Please enter your 10-digit mobile number.");
    }

    setBusy(true);
    try {
      const r = await api.post("/auth/send-otp", { phone: digits, country_code: "+91" });
      sessionStorage.setItem("ea_phone", digits);
      if (r.dev_code) sessionStorage.setItem("ea_dev_code", r.dev_code);
      else sessionStorage.removeItem("ea_dev_code");

      if (onNavigate) {
        onNavigate("verify");
      } else if (nav) {
        nav("/verify");
      }
    } catch (err) {
      setError(err.message || "Unable to send verification code. Please try again.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <AuthLayout>
      <div className="auth-form-container">
        {/* Auth Mode Tabs */}
        <div className="auth-tabs" role="tablist">
          <button
            type="button"
            role="tab"
            aria-selected={mode === "login"}
            className={`auth-tab-btn ${mode === "login" ? "active" : ""}`}
            onClick={() => { setMode("login"); setError(""); }}
          >
            Sign In
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={mode === "register"}
            className={`auth-tab-btn ${mode === "register" ? "active" : ""}`}
            onClick={() => { setMode("register"); setError(""); }}
          >
            Create Account
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={mode === "otp"}
            className={`auth-tab-btn ${mode === "otp" ? "active" : ""}`}
            onClick={() => { setMode("otp"); setError(""); }}
          >
            Phone / OTP
          </button>
        </div>

        {/* ----------------- 1. SIGN IN MODE ----------------- */}
        {mode === "login" && (
          <form className="auth-form" onSubmit={handleLoginSubmit}>
            <span className="icon-chip"><Icon name="login" /></span>
            <span className="eyebrow" style={{ alignSelf: "flex-start" }}>Welcome Back</span>
            <h1>Sign in to EduAdapt</h1>
            <p className="muted small">Continue your personalized PPS learning journey.</p>

            <label className="field">
              <span>Email Address</span>
              <div className="field-input-icon-wrap">
                <span className="field-icon"><Icon name="mail" size={16} /></span>
                <input
                  type="email"
                  required
                  autoComplete="email"
                  placeholder="student@college.edu"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  disabled={busy}
                />
              </div>
            </label>

            <label className="field">
              <span>Password</span>
              <div className="field-input-icon-wrap">
                <span className="field-icon"><Icon name="lock" size={16} /></span>
                <input
                  type={showPassword ? "text" : "password"}
                  required
                  autoComplete="current-password"
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  disabled={busy}
                />
                <button
                  type="button"
                  className="field-password-toggle"
                  onClick={() => setShowPassword(!showPassword)}
                  aria-label={showPassword ? "Hide password" : "Show password"}
                >
                  <Icon name={showPassword ? "eyeOff" : "eye"} size={16} />
                </button>
              </div>
            </label>

            {error && <p className="error" role="alert">{error}</p>}
            {successMsg && <p className="notice" role="status">{successMsg}</p>}

            <button type="submit" className="btn primary block" disabled={busy}>
              {busy ? <Spinner /> : <><Icon name="arrow" size={16} />Sign in to continue</>}
            </button>

            <div className="row between small mt8">
              <button
                type="button"
                className="btn ghost sm"
                onClick={() => { setMode("register"); setError(""); }}
              >
                Need an account? Register here
              </button>
              <button
                type="button"
                className="btn ghost sm"
                onClick={() => { setMode("otp"); setError(""); }}
              >
                Sign in with OTP →
              </button>
            </div>

            <hr style={{ border: "none", borderTop: "1px solid var(--line)", width: "100%", margin: "8px 0" }} />
            <p className="row tiny muted">
              <Icon name="lock" size={14} style={{ color: "var(--green)" }} />
              Encrypted credentials stored securely in PostgreSQL.
            </p>
          </form>
        )}

        {/* ----------------- 2. CREATE ACCOUNT (REGISTER) MODE ----------------- */}
        {mode === "register" && (
          <form className="auth-form" onSubmit={handleRegisterSubmit}>
            <span className="icon-chip"><Icon name="user" /></span>
            <span className="eyebrow" style={{ alignSelf: "flex-start" }}>New Student Account</span>
            <h1>Create your profile</h1>
            <p className="muted small">Set up your adaptive PPS learning profile in seconds.</p>

            <label className="field">
              <span>Full Name</span>
              <div className="field-input-icon-wrap">
                <span className="field-icon"><Icon name="user" size={16} /></span>
                <input
                  type="text"
                  required
                  placeholder="Alex Chen"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  disabled={busy}
                />
              </div>
            </label>

            <label className="field">
              <span>College Email</span>
              <div className="field-input-icon-wrap">
                <span className="field-icon"><Icon name="mail" size={16} /></span>
                <input
                  type="email"
                  required
                  autoComplete="email"
                  placeholder="alex.chen@college.edu"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  disabled={busy}
                />
              </div>
            </label>

            <div className="row" style={{ gap: 10 }}>
              <label className="field grow">
                <span>College / Institution (Optional)</span>
                <input
                  type="text"
                  placeholder="Engineering College"
                  value={college}
                  onChange={(e) => setCollege(e.target.value)}
                  disabled={busy}
                />
              </label>
              <label className="field grow">
                <span>Department (Optional)</span>
                <input
                  type="text"
                  placeholder="CSE / IT"
                  value={department}
                  onChange={(e) => setDepartment(e.target.value)}
                  disabled={busy}
                />
              </label>
            </div>

            <label className="field">
              <span>Password</span>
              <div className="field-input-icon-wrap">
                <span className="field-icon"><Icon name="lock" size={16} /></span>
                <input
                  type={showPassword ? "text" : "password"}
                  required
                  autoComplete="new-password"
                  placeholder="At least 8 chars with 1 number"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  disabled={busy}
                />
                <button
                  type="button"
                  className="field-password-toggle"
                  onClick={() => setShowPassword(!showPassword)}
                  aria-label={showPassword ? "Hide password" : "Show password"}
                >
                  <Icon name={showPassword ? "eyeOff" : "eye"} size={16} />
                </button>
              </div>
              <span className="hint">Min. 8 characters with at least one letter and one number.</span>
            </label>

            <label className="field">
              <span>Confirm Password</span>
              <div className="field-input-icon-wrap">
                <span className="field-icon"><Icon name="lock" size={16} /></span>
                <input
                  type={showConfirmPassword ? "text" : "password"}
                  required
                  autoComplete="new-password"
                  placeholder="Re-enter your password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  disabled={busy}
                />
                <button
                  type="button"
                  className="field-password-toggle"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  aria-label={showConfirmPassword ? "Hide password" : "Show password"}
                >
                  <Icon name={showConfirmPassword ? "eyeOff" : "eye"} size={16} />
                </button>
              </div>
            </label>

            {error && <p className="error" role="alert">{error}</p>}
            {successMsg && <p className="notice" role="status">{successMsg}</p>}

            <button type="submit" className="btn primary block" disabled={busy}>
              {busy ? <Spinner /> : <><Icon name="arrow" size={16} />Create Account</>}
            </button>

            <div className="row center small mt8">
              <span className="muted">Already have an account?</span>
              <button
                type="button"
                className="btn ghost sm"
                onClick={() => { setMode("login"); setError(""); }}
              >
                Sign In
              </button>
            </div>
          </form>
        )}

        {/* ----------------- 3. PHONE / OTP MODE ----------------- */}
        {mode === "otp" && (
          <form className="auth-form" onSubmit={handleOtpSendSubmit}>
            <span className="icon-chip"><Icon name="phone" /></span>
            <span className="eyebrow" style={{ alignSelf: "flex-start" }}>Passwordless Sign In</span>
            <h1>Verify with Phone</h1>
            <p className="muted small">We will send a one-time secure verification code.</p>

            <label className="field">
              Mobile Phone Number
              <div className="phone">
                <span>+91</span>
                <input
                  type="tel"
                  inputMode="numeric"
                  autoComplete="tel-national"
                  placeholder="98765 43210"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  disabled={busy}
                  aria-label="Phone number"
                />
                <Icon name="phone" size={16} style={{ marginRight: 12, color: "var(--muted)" }} />
              </div>
              <span className="hint">10-digit mobile number.</span>
            </label>

            {error && <p className="error" role="alert">{error}</p>}

            <button type="submit" className="btn primary block" disabled={busy}>
              {busy ? <Spinner /> : <><Icon name="arrow" size={16} />Send verification code</>}
            </button>

            <div className="row center small mt8">
              <button
                type="button"
                className="btn ghost sm"
                onClick={() => { setMode("login"); setError(""); }}
              >
                ← Return to Email / Password Sign In
              </button>
            </div>
          </form>
        )}
      </div>
    </AuthLayout>
  );
}
