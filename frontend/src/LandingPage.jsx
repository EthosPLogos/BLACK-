import React, { useEffect, useState } from "react";

const BASE = window.location.port === "5173"
  ? `http://${window.location.hostname}:8001`
  : "";

const FEATURES = [
  {
    icon: "◈",
    title: "Persistent Memory",
    desc: "Learns your context, goals, businesses, and preferences across every session. Encrypted at rest. Yours alone.",
  },
  {
    icon: "◎",
    title: "Voice Activated",
    desc: 'Say "Hey Mr.Black" — Whisper transcribes locally, Samantha responds. Full hands-free, no cloud.',
  },
  {
    icon: "⬡",
    title: "Multi-Tier Intelligence",
    desc: "Groq → OpenRouter → Ollama → Perplexity. Always the fastest free option. Paid only as a final fallback.",
  },
  {
    icon: "⊞",
    title: "Deep Integrations",
    desc: "Calendar, Reminders, Notes, Contacts, Files, Email. Mr.Black reads your world and answers from within it.",
  },
  {
    icon: "☀",
    title: "Daily Brief",
    desc: "Every morning: weather, schedule, pending tasks, market data, and headlines — before you say a word.",
  },
  {
    icon: "⚑",
    title: "Approval Gate",
    desc: "Every high-risk action requires your explicit confirmation. Nothing executes without your click. Always in control.",
  },
];

const PRINCIPLES = [
  {
    label: "PRIVATE",
    title: "Yours alone.",
    desc: "No accounts. No signup. No telemetry. Mr.Black exists on one machine for one person — you.",
  },
  {
    label: "LOCAL-FIRST",
    title: "Runs on your Mac.",
    desc: "Core intelligence runs entirely on-device. Cloud inference is an optional fallback, never the foundation.",
  },
  {
    label: "SINGULAR",
    title: "Built for one mind.",
    desc: "Most AI averages millions of users. Mr.Black is calibrated to one: your context, your goals, your world.",
  },
];

function SystemStatusPanel({ status, emailStatus }) {
  const groqOk = status?.groq?.configured;
  const openrouterOk = status?.openrouter?.configured;
  const perplexityOk = status?.perplexity?.configured;
  const ollamaOk = status?.ollama?.status === "ok";
  const emailConnected = emailStatus?.configured;
  const unreadCount = emailStatus?.unread_count ?? 0;
  const memCount = status?.memory?.conversation_count ?? 0;

  const cells = [
    {
      label: "GROQ",
      sublabel: "Primary Inference",
      value: groqOk ? "ONLINE" : "STANDBY",
      detail: groqOk ? "FREE · FAST" : "—",
      ok: groqOk,
    },
    {
      label: "OPENROUTER",
      sublabel: "Secondary",
      value: openrouterOk ? "READY" : "STANDBY",
      detail: openrouterOk ? "FREE TIER" : "—",
      ok: openrouterOk,
    },
    {
      label: "PERPLEXITY",
      sublabel: "Last Resort",
      value: perplexityOk ? "CONFIGURED" : "STANDBY",
      detail: perplexityOk ? "WEB SEARCH" : "—",
      ok: perplexityOk,
    },
    {
      label: "LOCAL",
      sublabel: "Offline Fallback",
      value: ollamaOk ? `${status.ollama.latency_ms}ms` : "OFFLINE",
      detail: ollamaOk ? status.ollama.model : "OLLAMA",
      ok: ollamaOk,
    },
    {
      label: "MEMORY",
      sublabel: "Encrypted Sessions",
      value: `${memCount}`,
      detail: "CONVERSATIONS",
      ok: true,
    },
    emailStatus
      ? {
          label: "EMAIL",
          sublabel: "iCloud IMAP",
          value: emailConnected ? `${unreadCount}` : "STANDBY",
          detail: emailConnected ? "UNREAD" : "NOT CONFIGURED",
          ok: emailConnected,
        }
      : null,
  ].filter(Boolean);

  return (
    <div style={{ border: "1px solid rgba(255,255,255,0.06)", borderRadius: 18, background: "#0b0c0e", overflow: "hidden" }}>
      <div style={{ padding: "16px 28px", borderBottom: "1px solid rgba(255,255,255,0.05)", display: "flex", alignItems: "center", gap: 10 }}>
        <span style={{ width: 6, height: 6, borderRadius: "50%", background: "#22c55e", display: "inline-block", animation: "blink-dot 2s ease-in-out infinite" }} />
        <span style={{ fontSize: 10, color: "#52525b", fontWeight: 700, letterSpacing: "0.18em" }}>LIVE SYSTEM STATUS</span>
        <span style={{ marginLeft: "auto", fontSize: 10, color: "#27272a", letterSpacing: "0.1em" }}>v{status.version}</span>
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))" }}>
        {cells.map(({ label, sublabel, value, detail, ok }, i) => (
          <div key={label} style={{ padding: "22px 24px", borderRight: i < cells.length - 1 ? "1px solid rgba(255,255,255,0.04)" : "none" }}>
            <div style={{ fontSize: 9, color: "#3f3f46", fontWeight: 700, letterSpacing: "0.2em", marginBottom: 12 }}>{label}</div>
            <div style={{ display: "flex", alignItems: "center", gap: 7, marginBottom: 6 }}>
              <span style={{ width: 5, height: 5, borderRadius: "50%", background: ok ? "#22c55e" : "#27272a", display: "inline-block", flexShrink: 0 }} />
              <span style={{ fontSize: 17, fontWeight: 700, color: ok ? "#f0f0e8" : "#3f3f46", letterSpacing: "-0.01em" }}>{value}</span>
            </div>
            <div style={{ fontSize: 10, color: "#2a2a30", letterSpacing: "0.1em", fontWeight: 600 }}>{detail}</div>
            <div style={{ fontSize: 9, color: "#1c1c22", marginTop: 8, letterSpacing: "0.08em" }}>{sublabel}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function LandingPage({ onLaunch }) {
  const [status, setStatus] = useState(null);
  const [emailStatus, setEmailStatus] = useState(null);

  useEffect(() => {
    fetch(`${BASE}/api/status`)
      .then(r => (r.ok ? r.json() : null))
      .then(d => setStatus(d))
      .catch(() => {});
    fetch(`${BASE}/api/email/status`)
      .then(r => (r.ok ? r.json() : null))
      .then(d => setEmailStatus(d))
      .catch(() => {});
  }, []);

  const groqOk = status?.groq?.configured;
  const ollamaOk = status?.ollama?.status === "ok";
  const emailConnected = emailStatus?.configured;
  const unreadCount = emailStatus?.unread_count ?? 0;
  const memCount = status?.memory?.conversation_count ?? 0;

  const chips = status
    ? [
        { label: groqOk ? "GROQ ONLINE" : "GROQ STANDBY", active: groqOk },
        { label: status.openrouter?.configured ? "OPENROUTER READY" : "OPENROUTER STANDBY", active: status.openrouter?.configured },
        emailStatus != null
          ? { label: emailConnected ? `EMAIL · ${unreadCount} UNREAD` : "EMAIL STANDBY", active: emailConnected }
          : null,
        { label: `MEMORY · ${memCount} SESSIONS`, active: true },
      ].filter(Boolean)
    : [];

  return (
    <div style={{ minHeight: "100vh", background: "#08090a", color: "#f5f5f5", fontFamily: "Inter, -apple-system, Arial, sans-serif", display: "flex", flexDirection: "column" }}>

      {/* ── NAV ────────────────────────────────── */}
      <nav style={{ position: "fixed", top: 0, left: 0, right: 0, zIndex: 50, padding: "0 48px", height: 58, display: "flex", alignItems: "center", justifyContent: "space-between", background: "rgba(8,9,10,0.94)", borderBottom: "1px solid rgba(255,255,255,0.04)", backdropFilter: "blur(16px)" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <div style={{ width: 28, height: 28, borderRadius: "50%", border: "1.5px solid rgba(200,160,40,0.7)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 11, color: "#c8a028", fontWeight: 900 }}>B</div>
          <span style={{ fontSize: 13, fontWeight: 800, letterSpacing: "0.24em", color: "#eeede8" }}>MR.BLACK</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 20 }}>
          {status && (
            <div style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 10, color: "#3f3f46", letterSpacing: "0.12em", fontWeight: 600 }}>
              <span style={{ width: 5, height: 5, borderRadius: "50%", background: groqOk ? "#22c55e" : "#f59e0b", display: "inline-block", animation: "blink-dot 2.5s ease-in-out infinite" }} />
              {groqOk ? "ONLINE" : "STANDBY"} · v{status.version}
            </div>
          )}
          <button
            onClick={onLaunch}
            style={{ background: "transparent", color: "#c8a028", border: "1px solid rgba(200,160,40,0.45)", borderRadius: 8, padding: "7px 20px", fontSize: 11, fontWeight: 700, letterSpacing: "0.12em", cursor: "pointer", textTransform: "uppercase", transition: "all 0.18s" }}
            onMouseEnter={e => { e.currentTarget.style.background = "rgba(200,160,40,0.1)"; e.currentTarget.style.borderColor = "rgba(200,160,40,0.8)"; }}
            onMouseLeave={e => { e.currentTarget.style.background = "transparent"; e.currentTarget.style.borderColor = "rgba(200,160,40,0.45)"; }}
          >
            Launch
          </button>
        </div>
      </nav>

      {/* ── HERO ───────────────────────────────── */}
      <section style={{ position: "relative", minHeight: "100vh", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", textAlign: "center", padding: "120px 24px 80px", overflow: "hidden" }}>

        {/* Subtle grid */}
        <div style={{ position: "absolute", inset: 0, backgroundImage: "linear-gradient(rgba(200,160,40,0.022) 1px, transparent 1px), linear-gradient(90deg, rgba(200,160,40,0.022) 1px, transparent 1px)", backgroundSize: "72px 72px", maskImage: "radial-gradient(ellipse 85% 85% at 50% 50%, black 25%, transparent)", WebkitMaskImage: "radial-gradient(ellipse 85% 85% at 50% 50%, black 25%, transparent)" }} />

        {/* Ambient center glow */}
        <div style={{ position: "absolute", top: "46%", left: "50%", transform: "translate(-50%, -50%)", width: 700, height: 700, borderRadius: "50%", background: "radial-gradient(circle, rgba(200,160,40,0.045) 0%, transparent 65%)", pointerEvents: "none" }} />

        {/* Ring */}
        <div style={{ position: "relative", width: 260, height: 260, marginBottom: 52 }}>
          {/* Outermost — faint, 3 accent marks */}
          <div style={{ position: "absolute", inset: 0, borderRadius: "50%", border: "1px solid rgba(200,160,40,0.07)", animation: "spin-slow 30s linear infinite" }}>
            {[0, 120, 240].map(deg => (
              <div key={deg} style={{ position: "absolute", width: 3, height: 3, borderRadius: "50%", background: "rgba(200,160,40,0.3)", top: "50%", left: "50%", transform: `rotate(${deg}deg) translateY(-128px) translate(-50%,-50%)` }} />
            ))}
          </div>
          {/* Main orbit — 6 dots, clockwise */}
          <div style={{ position: "absolute", inset: 20, borderRadius: "50%", border: "1px solid rgba(200,160,40,0.17)", animation: "spin-slow 18s linear infinite" }}>
            {[0, 60, 120, 180, 240, 300].map(deg => (
              <div key={deg} style={{ position: "absolute", width: 5, height: 5, borderRadius: "50%", background: deg === 0 ? "rgba(200,160,40,0.9)" : "rgba(200,160,40,0.55)", top: "50%", left: "50%", transform: `rotate(${deg}deg) translateY(-108px) translate(-50%,-50%)` }} />
            ))}
          </div>
          {/* Dashed counter-clockwise */}
          <div style={{ position: "absolute", inset: 44, borderRadius: "50%", border: "1px dashed rgba(200,160,40,0.17)", animation: "spin-slow-rev 14s linear infinite" }} />
          {/* Core pulsing ring */}
          <div style={{ position: "absolute", inset: 66, borderRadius: "50%", border: "1.5px solid rgba(200,160,40,0.5)", boxShadow: "0 0 48px rgba(200,160,40,0.13), inset 0 0 48px rgba(200,160,40,0.06)", animation: "pulse-ring 3s ease-in-out infinite" }}>
            <div style={{ position: "absolute", inset: 0, display: "flex", alignItems: "center", justifyContent: "center" }}>
              <span style={{ fontSize: 58, fontWeight: 900, color: "#c8a028", letterSpacing: "-0.02em", animation: "glow-flicker 3s ease-in-out infinite" }}>B</span>
            </div>
          </div>
        </div>

        <h1 style={{ fontSize: "clamp(44px, 9vw, 88px)", fontWeight: 900, letterSpacing: "0.18em", color: "#f5f5f0", lineHeight: 1, animation: "fade-up 0.8s ease 0.15s both", textShadow: "0 0 100px rgba(200,160,40,0.07)" }}>
          MR.BLACK
        </h1>
        <p style={{ marginTop: 22, fontSize: "clamp(14px, 2vw, 18px)", color: "#5a5a66", fontWeight: 300, letterSpacing: "0.04em", animation: "fade-up 0.8s ease 0.3s both" }}>
          Your private intelligence.
        </p>
        <p style={{ marginTop: 8, fontSize: 11, color: "#333338", fontWeight: 600, letterSpacing: "0.16em", textTransform: "uppercase", animation: "fade-up 0.8s ease 0.4s both" }}>
          Built for one person. Built for you.
        </p>

        {/* Live status chips */}
        {chips.length > 0 && (
          <div style={{ marginTop: 36, display: "flex", flexWrap: "wrap", justifyContent: "center", gap: 8, animation: "fade-up 0.8s ease 0.5s both" }}>
            {chips.map(({ label, active }) => (
              <div key={label} style={{ display: "flex", alignItems: "center", gap: 6, background: active ? "rgba(200,160,40,0.07)" : "rgba(255,255,255,0.025)", border: `1px solid ${active ? "rgba(200,160,40,0.22)" : "rgba(255,255,255,0.05)"}`, borderRadius: 100, padding: "5px 14px", fontSize: 10, color: active ? "#b89420" : "#33333a", letterSpacing: "0.1em", fontWeight: 600 }}>
                <span style={{ width: 5, height: 5, borderRadius: "50%", background: active ? "#c8a028" : "#222228", display: "inline-block" }} />
                {label}
              </div>
            ))}
          </div>
        )}

        {/* CTA */}
        <div style={{ marginTop: 48, animation: "fade-up 0.8s ease 0.6s both" }}>
          <button
            onClick={onLaunch}
            style={{ background: "#c8a028", color: "#07080a", border: "none", borderRadius: 12, padding: "17px 56px", fontSize: 13, fontWeight: 800, letterSpacing: "0.14em", cursor: "pointer", textTransform: "uppercase", boxShadow: "0 0 64px rgba(200,160,40,0.28), 0 12px 36px rgba(0,0,0,0.55)", transition: "all 0.22s" }}
            onMouseEnter={e => { e.currentTarget.style.transform = "translateY(-3px)"; e.currentTarget.style.boxShadow = "0 0 100px rgba(200,160,40,0.44), 0 18px 48px rgba(0,0,0,0.65)"; }}
            onMouseLeave={e => { e.currentTarget.style.transform = "translateY(0)"; e.currentTarget.style.boxShadow = "0 0 64px rgba(200,160,40,0.28), 0 12px 36px rgba(0,0,0,0.55)"; }}
          >
            Launch Mr.Black
          </button>
        </div>

        {/* Vertical accent line at bottom */}
        <div style={{ position: "absolute", bottom: 36, left: "50%", transform: "translateX(-50%)", width: 1, height: 44, background: "linear-gradient(to bottom, transparent, rgba(200,160,40,0.35), transparent)", animation: "fade-up 1s ease 1.4s both" }} />
      </section>

      {/* ── PHILOSOPHY ─────────────────────────── */}
      <section style={{ padding: "108px 48px", background: "#07080a", borderTop: "1px solid rgba(255,255,255,0.04)" }}>
        <div style={{ maxWidth: 980, margin: "0 auto" }}>
          <div style={{ marginBottom: 14, fontSize: 10, color: "#c8a028", fontWeight: 700, letterSpacing: "0.22em", textTransform: "uppercase" }}>The Philosophy</div>
          <h2 style={{ fontSize: "clamp(30px, 5vw, 50px)", fontWeight: 800, color: "#f0f0e8", lineHeight: 1.12, maxWidth: 560, marginBottom: 18 }}>
            Not for everyone.<br />By design.
          </h2>
          <p style={{ fontSize: 14, color: "#46464f", lineHeight: 1.85, maxWidth: 500, marginBottom: 72 }}>
            Most AI products learn from millions of users, average their answers, and sell the aggregate back to you.
            Mr.Black learns only from you. Answers only for you. Runs only on your machine.
          </p>

          {/* Principle cards — grid separator trick */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: 1, background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.05)", borderRadius: 20, overflow: "hidden" }}>
            {PRINCIPLES.map(({ label, title, desc }) => (
              <div key={label} style={{ background: "#0d0e12", padding: "40px 34px" }}>
                <div style={{ fontSize: 9, color: "#c8a028", fontWeight: 800, letterSpacing: "0.28em", marginBottom: 18 }}>{label}</div>
                <div style={{ fontSize: 19, fontWeight: 700, color: "#f0f0e8", marginBottom: 14, lineHeight: 1.15 }}>{title}</div>
                <div style={{ fontSize: 13, color: "#46464f", lineHeight: 1.8 }}>{desc}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── CAPABILITIES ────────────────────────── */}
      <section style={{ padding: "108px 48px 80px", background: "#08090a" }}>
        <div style={{ maxWidth: 1100, margin: "0 auto" }}>
          <div style={{ marginBottom: 60 }}>
            <div style={{ fontSize: 10, color: "#c8a028", fontWeight: 700, letterSpacing: "0.22em", marginBottom: 16 }}>CAPABILITIES</div>
            <h2 style={{ fontSize: "clamp(26px, 4vw, 38px)", fontWeight: 700, color: "#f0f0e8" }}>Everything, in context.</h2>
            <p style={{ marginTop: 12, color: "#38383f", fontSize: 14, maxWidth: 400, lineHeight: 1.7 }}>
              Calendar, inbox, files, voice, and memory — orchestrated as one private system on your Mac.
            </p>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))", gap: 12 }}>
            {FEATURES.map(({ icon, title, desc }) => (
              <div
                key={title}
                style={{ background: "#0b0c0f", border: "1px solid rgba(255,255,255,0.055)", borderLeft: "2px solid rgba(200,160,40,0.22)", borderRadius: 14, padding: "30px 28px", display: "flex", flexDirection: "column", gap: 12, transition: "all 0.22s", cursor: "default" }}
                onMouseEnter={e => { e.currentTarget.style.borderLeftColor = "rgba(200,160,40,0.75)"; e.currentTarget.style.background = "#0f1014"; e.currentTarget.style.transform = "translateY(-2px)"; }}
                onMouseLeave={e => { e.currentTarget.style.borderLeftColor = "rgba(200,160,40,0.22)"; e.currentTarget.style.background = "#0b0c0f"; e.currentTarget.style.transform = "translateY(0)"; }}
              >
                <div style={{ fontSize: 22, color: "#c8a028", opacity: 0.85 }}>{icon}</div>
                <div style={{ fontSize: 14, fontWeight: 700, color: "#eeede8", letterSpacing: "0.01em" }}>{title}</div>
                <div style={{ fontSize: 13, color: "#46464f", lineHeight: 1.78 }}>{desc}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── LIVE SYSTEM STATUS ──────────────────── */}
      {status && (
        <section style={{ padding: "0 48px 80px", background: "#08090a" }}>
          <div style={{ maxWidth: 1100, margin: "0 auto" }}>
            <SystemStatusPanel status={status} emailStatus={emailStatus} />
          </div>
        </section>
      )}

      {/* ── CLOSING CTA ─────────────────────────── */}
      <section style={{ padding: "116px 48px 128px", background: "linear-gradient(to bottom, #08090a 0%, #060708 100%)", borderTop: "1px solid rgba(200,160,40,0.07)", textAlign: "center", position: "relative", overflow: "hidden" }}>
        {/* Ambient glow */}
        <div style={{ position: "absolute", top: "50%", left: "50%", transform: "translate(-50%, -50%)", width: 900, height: 500, borderRadius: "50%", background: "radial-gradient(ellipse, rgba(200,160,40,0.04) 0%, transparent 60%)", pointerEvents: "none" }} />
        <div style={{ position: "relative" }}>
          <div style={{ fontSize: 10, color: "#c8a028", fontWeight: 700, letterSpacing: "0.22em", marginBottom: 22, textTransform: "uppercase" }}>Ready</div>
          <h2 style={{ fontSize: "clamp(30px, 6vw, 56px)", fontWeight: 800, color: "#f0f0e8", lineHeight: 1.08, marginBottom: 16 }}>
            Meet your intelligence.
          </h2>
          <p style={{ fontSize: 14, color: "#33333a", letterSpacing: "0.04em", marginBottom: 52 }}>
            Private. Local. Always on.
          </p>
          <button
            onClick={onLaunch}
            style={{ background: "#c8a028", color: "#07080a", border: "none", borderRadius: 14, padding: "20px 72px", fontSize: 14, fontWeight: 800, letterSpacing: "0.14em", cursor: "pointer", textTransform: "uppercase", boxShadow: "0 0 88px rgba(200,160,40,0.3), 0 18px 52px rgba(0,0,0,0.6)", transition: "all 0.22s" }}
            onMouseEnter={e => { e.currentTarget.style.transform = "translateY(-3px) scale(1.02)"; e.currentTarget.style.boxShadow = "0 0 130px rgba(200,160,40,0.48), 0 24px 60px rgba(0,0,0,0.7)"; }}
            onMouseLeave={e => { e.currentTarget.style.transform = "translateY(0) scale(1)"; e.currentTarget.style.boxShadow = "0 0 88px rgba(200,160,40,0.3), 0 18px 52px rgba(0,0,0,0.6)"; }}
          >
            Launch Mr.Black
          </button>
          <p style={{ marginTop: 28, fontSize: 11, color: "#1e1e24", letterSpacing: "0.14em" }}>
            v{status?.version ?? "1.0.0"} · Single-owner · Never shared
          </p>
        </div>
      </section>

      {/* ── FOOTER ──────────────────────────────── */}
      <footer style={{ borderTop: "1px solid rgba(255,255,255,0.035)", padding: "26px 48px", display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: 12, background: "#06070a" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <div style={{ width: 22, height: 22, borderRadius: "50%", border: "1px solid rgba(200,160,40,0.3)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 9, color: "#c8a028", fontWeight: 900 }}>B</div>
          <span style={{ fontSize: 11, fontWeight: 800, letterSpacing: "0.22em", color: "#222228" }}>MR.BLACK</span>
        </div>
        <div style={{ fontSize: 11, color: "#1c1c22", letterSpacing: "0.07em" }}>Single-owner · Local-first · Private by design</div>
        <div style={{ fontSize: 11, color: "#17171c", letterSpacing: "0.07em" }}>No cloud · No accounts · No data collection</div>
      </footer>

    </div>
  );
}
