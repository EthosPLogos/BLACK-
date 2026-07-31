import React, { useCallback, useEffect, useRef, useState } from "react";

const BASE = window.location.port === "5173"
  ? `http://${window.location.hostname}:8001`
  : "";
const API_KEY = import.meta.env.VITE_BLACK_API_KEY || "";

function apiHeaders(extra = {}) {
  const h = { "Content-Type": "application/json", ...extra };
  if (API_KEY) h["X-BLACK-API-KEY"] = API_KEY;
  return h;
}

function fHeaders() {
  if (API_KEY) return { "X-BLACK-API-KEY": API_KEY };
  return {};
}

const VERDICT_LABEL = { pending_approval: "approval required", blocked: "blocked" };

// ─── Status Dot ────────────────────────────────────────────────────────────────

function StatusDot({ s }) {
  const c = s === "ok" ? "#22c55e" : s === "degraded" ? "#f59e0b" : "#ef4444";
  return (
    <span style={{ display: "inline-block", width: 7, height: 7, borderRadius: "50%", background: c, marginRight: 6, flexShrink: 0 }} />
  );
}

// ─── Approval Card ─────────────────────────────────────────────────────────────

function ApprovalCard({ record, onResolve }) {
  const [busy, setBusy] = useState(false);
  const [execResult, setExecResult] = useState(record.execution_result || null);
  const [showRaw, setShowRaw] = useState(false);

  async function act(action) {
    setBusy(true);
    try {
      const res = await fetch(`${BASE}/api/approvals/${record.id}/${action}`, {
        method: "POST",
        headers: fHeaders(),
      });
      if (action === "execute" && res.ok) {
        const data = await res.json();
        setExecResult(data.execution_result || null);
      }
      onResolve();
    } finally {
      setBusy(false);
    }
  }

  const isExecuted = execResult != null || record.status === "executed";
  const isApproved = record.status === "approved" && !isExecuted;
  const isRejected = record.status === "rejected";

  const headerColor = isExecuted ? "#16a34a" : isRejected ? "#52525b" : isApproved ? "#60a5fa" : "#a16207";
  const borderColor = isExecuted ? "#14532d" : isRejected ? "#27272a" : isApproved ? "#1d4ed8" : "#713f12";

  return (
    <div style={{ background: "#1c1a0d", border: `1px solid ${borderColor}`, borderRadius: 10, padding: "12px 14px", display: "flex", flexDirection: "column", gap: 6 }}>
      <div style={{ fontSize: 12, color: headerColor, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.05em" }}>
        {isExecuted ? "⚙ Executed" : isRejected ? "✕ Rejected" : isApproved ? "✓ Approved · Pending Execution" : "⚑ Approval Required"}
        {" · "}{record.domain}{" · "}{record.task_type}
      </div>
      <div style={{ fontSize: 14, color: "#e5e7eb", lineHeight: 1.5 }}>
        {record.user_input.length > 120 ? record.user_input.slice(0, 120) + "…" : record.user_input}
      </div>
      {!isExecuted && !isRejected && (
        <div style={{ fontSize: 12, color: "#71717a" }}>Reason: {record.policy_reason}</div>
      )}
      <div style={{ fontSize: 11, color: "#3f3f46", fontFamily: "monospace" }}>ID: {record.id}</div>

      {execResult && (
        <div style={{ background: execResult.success ? "#052e16" : "#1c0a0a", border: `1px solid ${execResult.success ? "#15803d" : "#7f1d1d"}`, borderRadius: 8, padding: "10px 12px", marginTop: 4, display: "flex", flexDirection: "column", gap: 4 }}>
          <div style={{ fontSize: 12, color: execResult.success ? "#22c55e" : "#ef4444", fontWeight: 600 }}>
            {execResult.success ? "✓ Success" : "✕ Failed"} · {execResult.action_type}
          </div>
          <div style={{ fontSize: 13, color: "#d4d4d8", lineHeight: 1.5, whiteSpace: "pre-wrap" }}>{execResult.summary}</div>
          {execResult.raw_output && (
            <>
              <button onClick={() => setShowRaw(v => !v)}
                style={{ background: "none", border: "none", color: "#52525b", cursor: "pointer", fontSize: 12, padding: "2px 0", textAlign: "left" }}>
                {showRaw ? "▾ Hide raw output" : "▸ Show raw output"}
              </button>
              {showRaw && (
                <pre style={{ fontSize: 11, color: "#71717a", background: "#0a0a0b", border: "1px solid #27272a", borderRadius: 6, padding: "8px 10px", overflowX: "auto", whiteSpace: "pre-wrap", wordBreak: "break-all", margin: 0 }}>
                  {execResult.raw_output}
                </pre>
              )}
            </>
          )}
          {execResult.verifier_verdict && execResult.verifier_verdict !== "N/A" && (
            <div style={{ fontSize: 11, color: "#52525b" }}>
              Verifier: {execResult.verifier_verdict.startsWith("PASS") ? "✓ PASS" : execResult.verifier_verdict.slice(0, 120)}
            </div>
          )}
        </div>
      )}

      {!isExecuted && !isRejected && (
        <div style={{ display: "flex", gap: 8, marginTop: 4 }}>
          <button onClick={() => act("execute")} disabled={busy}
            style={{ flex: 2, background: busy ? "#27272a" : "#15803d", color: busy ? "#52525b" : "#fff", border: "none", borderRadius: 8, padding: "8px 0", fontSize: 13, fontWeight: 600, cursor: busy ? "not-allowed" : "pointer" }}>
            {busy ? "Executing…" : isApproved ? "Execute" : "Approve & Execute"}
          </button>
          {!isApproved && (
            <button onClick={() => act("approve")} disabled={busy}
              style={{ flex: 1, background: "#1e3a5f", color: busy ? "#52525b" : "#93c5fd", border: "1px solid #1d4ed8", borderRadius: 8, padding: "8px 0", fontSize: 13, fontWeight: 600, cursor: busy ? "not-allowed" : "pointer" }}>
              Approve
            </button>
          )}
          <button onClick={() => act("reject")} disabled={busy}
            style={{ flex: 1, background: "#1c1d22", color: busy ? "#52525b" : "#d4d4d8", border: "1px solid #3f3f46", borderRadius: 8, padding: "8px 0", fontSize: 13, fontWeight: 600, cursor: busy ? "not-allowed" : "pointer" }}>
            Reject
          </button>
        </div>
      )}
    </div>
  );
}

// ─── Brief Panel ───────────────────────────────────────────────────────────────

function BriefPanel({ onClose }) {
  const [brief, setBrief] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [summary, setSummary] = useState(null);
  const [summaryLoading, setSummaryLoading] = useState(false);

  useEffect(() => {
    fetch(`${BASE}/api/brief`, { headers: fHeaders() })
      .then(r => r.ok ? r.json() : Promise.reject())
      .then(d => {
        setBrief(d);
        setLoading(false);
        // Kick off summary generation after data loads
        setSummaryLoading(true);
        return fetch(`${BASE}/api/brief/summary`, {
          method: "POST",
          headers: apiHeaders(),
          body: JSON.stringify(d),
        });
      })
      .then(r => r.ok ? r.json() : Promise.reject())
      .then(d => { setSummary(d.summary); setSummaryLoading(false); })
      .catch(() => { setError(prev => !brief ? true : prev); setSummaryLoading(false); setLoading(false); });
  }, []);

  return (
    <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.75)", zIndex: 100, display: "flex", justifyContent: "center", alignItems: "flex-start", padding: "40px 24px", overflowY: "auto" }}
      onClick={e => { if (e.target === e.currentTarget) onClose(); }}>
      <div style={{ background: "#111114", border: "1px solid #2a2a31", borderRadius: 18, width: "100%", maxWidth: 680, padding: "28px 32px", display: "flex", flexDirection: "column", gap: 20, boxShadow: "0 20px 60px rgba(0,0,0,0.6)" }}>

        {/* Header */}
        <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between" }}>
          <div>
            <h2 style={{ margin: 0, fontSize: 18, fontWeight: 700, letterSpacing: "0.06em" }}>Daily Brief</h2>
            {brief && <p style={{ margin: "4px 0 0", color: "#52525b", fontSize: 12 }}>{brief.date} · {brief.time}</p>}
          </div>
          <button onClick={onClose} style={{ background: "none", border: "none", color: "#52525b", fontSize: 20, cursor: "pointer", lineHeight: 1, padding: "0 4px" }}>✕</button>
        </div>

        {loading && (
          <div style={{ color: "#52525b", fontSize: 13, textAlign: "center", padding: "20px 0" }}>
            <span style={{ display: "inline-block", width: 8, height: 8, borderRadius: "50%", background: "#22c55e", animation: "blink 1.2s step-start infinite", marginRight: 8 }} />
            Assembling your brief…
          </div>
        )}

        {error && <div style={{ color: "#ef4444", fontSize: 13 }}>Could not load brief — check that the backend is running.</div>}

        {brief && (
          <>
            {/* Summary */}
            <div style={{ background: "#0f1117", border: "1px solid #1e2030", borderRadius: 12, padding: "14px 16px" }}>
              <div style={{ fontSize: 10, color: "#52525b", fontWeight: 700, letterSpacing: "0.1em", marginBottom: 8 }}>MR.BLACK SAYS</div>
              {summaryLoading
                ? <div style={{ fontSize: 13, color: "#3f3f46" }}>
                    <span style={{ display: "inline-block", width: 6, height: 6, borderRadius: "50%", background: "#22c55e", animation: "blink 1.2s step-start infinite", marginRight: 6 }} />
                    Generating summary…
                  </div>
                : <div style={{ fontSize: 14, color: "#d4d4d8", lineHeight: 1.7 }}>{summary || "Summary unavailable."}</div>
              }
            </div>

            {/* Weather */}
            {brief.weather && Object.keys(brief.weather).length > 0 && (
              <div>
                <div style={{ fontSize: 10, color: "#52525b", fontWeight: 700, letterSpacing: "0.1em", marginBottom: 8 }}>WEATHER</div>
                <div style={{ fontSize: 13, color: "#a1a1aa" }}>
                  {brief.weather.city && <span style={{ color: "#e5e7eb", marginRight: 8 }}>{brief.weather.city}</span>}
                  {brief.weather.description} · {brief.weather.temp_f}°F (feels {brief.weather.feels_like_f}°F) · High {brief.weather.high_f}°F / Low {brief.weather.low_f}°F
                </div>
              </div>
            )}

            {/* Calendar */}
            <div>
              <div style={{ fontSize: 10, color: "#52525b", fontWeight: 700, letterSpacing: "0.1em", marginBottom: 8 }}>TODAY'S CALENDAR ({brief.events.length})</div>
              {brief.events.length === 0
                ? <div style={{ fontSize: 12, color: "#3f3f46" }}>No events today.</div>
                : brief.events.map((e, i) => (
                  <div key={i} style={{ display: "flex", gap: 12, padding: "4px 0", borderBottom: "1px solid #1c1d22", fontSize: 13 }}>
                    <span style={{ color: "#52525b", fontFamily: "monospace", flexShrink: 0 }}>{e.start}</span>
                    <span style={{ color: "#e5e7eb" }}>{e.title}</span>
                    <span style={{ color: "#3f3f46", fontSize: 10, marginLeft: "auto", flexShrink: 0 }}>{e.calendar}</span>
                  </div>
                ))
              }
            </div>

            {/* Reminders */}
            <div>
              <div style={{ fontSize: 10, color: "#52525b", fontWeight: 700, letterSpacing: "0.1em", marginBottom: 8 }}>PENDING REMINDERS ({brief.reminders.length})</div>
              {brief.reminders.length === 0
                ? <div style={{ fontSize: 12, color: "#3f3f46" }}>No pending reminders.</div>
                : brief.reminders.map((r, i) => (
                  <div key={i} style={{ fontSize: 13, color: "#a1a1aa", padding: "3px 0", borderBottom: "1px solid #1c1d22" }}>
                    · {r.title}{r.due ? <span style={{ color: "#52525b", fontSize: 11, marginLeft: 8 }}>{r.due}</span> : ""}
                  </div>
                ))
              }
            </div>

            {/* News */}
            {brief.news && brief.news.length > 0 && (
              <div>
                <div style={{ fontSize: 10, color: "#52525b", fontWeight: 700, letterSpacing: "0.1em", marginBottom: 8 }}>TOP NEWS</div>
                {brief.news.map((n, i) => (
                  <div key={i} style={{ padding: "5px 0", borderBottom: "1px solid #1c1d22" }}>
                    <div style={{ fontSize: 13, color: "#e5e7eb", fontWeight: 600 }}>{n.title}</div>
                    <div style={{ fontSize: 11, color: "#71717a", marginTop: 2 }}>{n.snippet.slice(0, 160)}{n.snippet.length > 160 ? "…" : ""}</div>
                  </div>
                ))}
              </div>
            )}
          </>
        )}

        <div style={{ borderTop: "1px solid #1c1d22", paddingTop: 12, fontSize: 10, color: "#3f3f46", textAlign: "center" }}>
          Mr.Black Daily Brief · Refresh to regenerate
        </div>
      </div>
    </div>
  );
}

// ─── Guide Panel ───────────────────────────────────────────────────────────────

const GUIDE_SECTIONS = [
  {
    title: "Talking to Mr.Black",
    items: [
      "Type any message and press Enter (or click Send). Shift+Enter for a new line.",
      "Mr.Black automatically routes your message to the right agent — you don't pick it.",
      "Be specific. \"Research NVDA earnings Q1 2025\" beats \"tell me about NVDA\".",
      "The ⬡ local / ☁ cloud badge on each reply shows which inference engine responded.",
    ],
  },
  {
    title: "Agents — automatic routing",
    items: [
      "Researcher — questions, analysis, deep research on any topic.",
      "Builder — code generation, architecture, debugging, technical tasks.",
      "Finance — market data, stock quotes, news. Mention tickers like AAPL or $TSLA.",
      "Business — strategy, operations, decisions, planning.",
      "Execution — runs real shell commands (git, python, npm) after your approval.",
    ],
  },
  {
    title: "The Approval Gate",
    items: [
      "Any high-risk action (running commands, executing code) creates an approval record.",
      "You get a macOS notification with a Sosumi chime the instant it's created.",
      "Open the Approvals panel in the header to review it.",
      "Approve & Execute runs it immediately. Approve stages it. Reject discards it.",
      "Nothing executes without your explicit click — ever.",
    ],
  },
  {
    title: "Scheduled Tasks",
    items: [
      "Open System → Schedule tab to create recurring tasks.",
      "Each task has a name, a prompt Mr.Black will run, a cron schedule, and a domain.",
      "Cron quick reference: 0 9 * * 1-5 = weekdays 9am · */15 * * * * = every 15 min · 0 8 * * * = daily 8am.",
      "When a task fires, Mr.Black runs it and sends a Ping notification with the summary.",
      "Use Run now to test a task immediately. Pause/Resume to toggle without deleting.",
    ],
  },
  {
    title: "Memory",
    items: [
      "Mr.Black remembers conversations and facts between sessions automatically.",
      "System → Memory: edit your user profile (name, goals, businesses, projects).",
      "Add facts Mr.Black should always know — these are injected into every conversation.",
      "Clear History removes all stored conversations but keeps your profile and facts.",
      "Memory is encrypted at rest with your Fernet key.",
    ],
  },
  {
    title: "Operator Console (System panel)",
    items: [
      "Status tab: live health of Ollama, memory capacity, audit count, pending approvals.",
      "Memory tab: edit your profile, manage facts, clear conversation history.",
      "Audit tab: append-only log of every action Mr.Black has taken.",
      "Schedule tab: manage recurring tasks and run the watchdog manually.",
      "The watchdog runs every 5 minutes and fires a Basso alert if something needs attention.",
    ],
  },
  {
    title: "Finance Domain",
    items: [
      "Ask about any publicly traded ticker: \"What is AAPL doing?\" or \"Summarise $TSLA news\".",
      "Mr.Black fetches live quotes and recent news via Alpha Vantage before replying.",
      "Free tier limit: 25 API requests per day, 5 per minute. Mr.Black caches for 5 minutes.",
      "Without a key, Mr.Black uses its training knowledge only — still useful, just not live.",
    ],
  },
  {
    title: "Inference & Ollama",
    items: [
      "Mr.Black runs locally on Ollama (llama3.1:8b) by default — no internet required.",
      "If Ollama goes down, Mr.Black retries 3 times then shows a macOS dialog.",
      "The dialog asks: Stop or Use Haiku. Default is Stop — no cloud calls without your click.",
      "Set ANTHROPIC_API_KEY in backend/.env to enable the Haiku fallback option.",
    ],
  },
  {
    title: "Voice — STT & TTS",
    items: [
      "The 🎙 mic button appears in the input area when Whisper and ffmpeg are both installed.",
      "Click 🎙 to start recording — the button turns red and pulses. Click ⏹ to stop.",
      "Your speech is transcribed locally by Whisper (no cloud) and fills the input box.",
      "Review the text, then press Enter or Send — nothing is auto-sent without your action.",
      "Click 🔇 to enable TTS — Mr.Black will read its replies aloud using the macOS say command.",
      "Change the voice in backend/.env with TTS_VOICE (run `say -v ?` in Terminal to list voices).",
      "Change the Whisper model in backend/.env with WHISPER_MODEL: tiny (fast), base (default), small (most accurate).",
      "Whisper downloads the model on first use (~74MB for base). Subsequent uses are instant.",
    ],
  },
  {
    title: "Personal Integrations",
    items: [
      "Click ☀ Brief in the header for your full daily summary: weather, calendar, reminders, and top news — all in one view.",
      "Open System → Integrations tab for Calendar, Reminders, Files, Notes, Contacts, Web Search, and Weather.",
      "Calendar reads from macOS Calendar — no accounts needed. macOS asks permission on first use.",
      "Reminders reads your default list and lets you add new ones directly from the panel.",
      "File Search scans ~/Desktop, ~/Documents, and ~/Downloads. Add paths via FILE_SEARCH_PATHS in .env.",
      "Notes Search searches title and body of all your macOS Notes.",
      "Contacts Search looks up people by name and returns email, phone, and organization.",
      "Web Search uses DuckDuckGo — no API key, no account. Results appear in the panel or are injected into chat answers.",
      "Talk naturally: \"What do I have today?\" · \"Who is John Smith?\" · \"Search the web for…\" · \"Find that PDF from last week\".",
      "Calendar, Reminders, Notes, Contacts: all local via osascript — nothing leaves your Mac.",
    ],
  },
  {
    title: "Email (IMAP — read-only)",
    items: [
      "Mr.Black reads your inbox over IMAP — it cannot send, delete, or modify emails.",
      "Requires an App-Specific Password — not your Apple ID password.",
      "Generate one at appleid.apple.com → Sign-In and Security → App-Specific Passwords.",
      "Set EMAIL_HOST=imap.mail.me.com, EMAIL_USER, and EMAIL_PASSWORD in backend/.env, then restart.",
      "Other providers: Gmail=imap.gmail.com · Outlook=outlook.office365.com · Yahoo=imap.mail.yahoo.com",
      "Ask in chat: \"Check my email\" · \"Any unread messages?\" · \"Do I have anything from Sarah?\"",
      "Or open System → Integrations → Email to browse your inbox and search directly.",
    ],
  },
  {
    title: "Backup & Restore",
    items: [
      "Open System → Backup to download a complete snapshot of your Mr.Black data.",
      "The backup zip contains: memory, scheduled tasks, audit log, and approvals.",
      "Click 'Download mr_black_backup.zip' — save it somewhere secure (external drive, iCloud, etc.).",
      "To restore: upload any black_backup_*.zip file in the Restore section.",
      "Restore overwrites current data — download a fresh backup first if you want to preserve it.",
      "After restoring, restart the backend for changes to take effect.",
      "Important: your MEMORY_ENCRYPTION_KEY in backend/.env is NOT included in the backup — back it up separately or you will lose access to encrypted memory.",
    ],
  },
  {
    title: "Wake Word",
    items: [
      "Click ◎ Wake in the header to enable always-on wake word detection.",
      "Say \"Hey Mr.Black\" or \"Mr. Black\" — Mr.Black responds with a Jarvis-style greeting.",
      "Greeting is time-aware: different phrases for morning, afternoon, evening, and late night.",
      "If your name is set in System → Memory → Profile, Mr.Black will use it in the greeting.",
      "After the wake word triggers, the input box is focused and ready for your message.",
      "If TTS is also enabled (🔊), Mr.Black will speak the greeting aloud through your speakers.",
      "The gold pulsing dot next to ◎ Wake means it's actively listening.",
      "Wake word runs entirely in the browser via Web Speech API — no audio is sent to any server.",
      "Click ◎ Wake again to disable listening. Browser will ask for microphone permission on first use.",
    ],
  },
  {
    title: "Tips & shortcuts",
    items: [
      "Enter to send · Shift+Enter for a new line in your message.",
      "The ⊞ System and ⚑ Approvals panels are mutually exclusive — opening one closes the other.",
      "Restart the backend (uvicorn) from a terminal if you edit backend/.env — it hot-reloads code but not env vars.",
      "Generate a fresh memory encryption key: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\"",
      "Back up backend/black_memory.json and your MEMORY_ENCRYPTION_KEY together — losing the key means losing the memory.",
    ],
  },
];

function GuidePanel({ onClose }) {
  return (
    <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.7)", zIndex: 100, display: "flex", justifyContent: "center", alignItems: "flex-start", padding: "40px 24px", overflowY: "auto" }}
      onClick={e => { if (e.target === e.currentTarget) onClose(); }}>
      <div style={{ background: "#111114", border: "1px solid #2a2a31", borderRadius: 18, width: "100%", maxWidth: 720, padding: "28px 32px", display: "flex", flexDirection: "column", gap: 24, boxShadow: "0 20px 60px rgba(0,0,0,0.6)" }}>
        <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between" }}>
          <div>
            <h2 style={{ margin: 0, fontSize: 18, fontWeight: 700, letterSpacing: "0.06em" }}>How to use Mr.Black</h2>
            <p style={{ margin: "4px 0 0", color: "#52525b", fontSize: 12 }}>Your private AI operating system — single owner, local-first.</p>
          </div>
          <button onClick={onClose}
            style={{ background: "none", border: "none", color: "#52525b", fontSize: 20, cursor: "pointer", lineHeight: 1, padding: "0 4px", flexShrink: 0 }}>✕</button>
        </div>

        {GUIDE_SECTIONS.map(({ title, items }) => (
          <div key={title}>
            <div style={{ fontSize: 10, color: "#52525b", fontWeight: 700, letterSpacing: "0.12em", textTransform: "uppercase", marginBottom: 10, paddingBottom: 6, borderBottom: "1px solid #1c1d22" }}>
              {title}
            </div>
            <ul style={{ margin: 0, padding: "0 0 0 16px", display: "flex", flexDirection: "column", gap: 5 }}>
              {items.map((item, i) => (
                <li key={i} style={{ fontSize: 13, color: "#a1a1aa", lineHeight: 1.6 }}>{item}</li>
              ))}
            </ul>
          </div>
        ))}

        <div style={{ borderTop: "1px solid #1c1d22", paddingTop: 16, fontSize: 11, color: "#3f3f46", textAlign: "center" }}>
          Mr.Black v1.0 · Single-owner · Local-first
        </div>
      </div>
    </div>
  );
}

// ─── System Panel ──────────────────────────────────────────────────────────────

function SystemPanel() {
  const [tab, setTab] = useState("status");
  const [sysStatus, setSysStatus] = useState(null);
  const [memData, setMemData] = useState(null);
  const [auditLog, setAuditLog] = useState([]);
  const [tasks, setTasks] = useState([]);
  const [newTask, setNewTask] = useState({ name: "", prompt: "", cron: "*/15 * * * *", domain: "general" });
  const [userFields, setUserFields] = useState({});
  const [newFact, setNewFact] = useState("");
  const [savingField, setSavingField] = useState(null);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState(null);
  const [patterns, setPatterns] = useState(null);
  const [weatherData, setWeatherData] = useState(null);
  const [calEvents, setCalEvents] = useState(null);
  const [calUpcoming, setCalUpcoming] = useState(null);
  const [reminders, setReminders] = useState(null);
  const [newReminder, setNewReminder] = useState("");
  const [fileQuery, setFileQuery] = useState("");
  const [fileResults, setFileResults] = useState(null);
  const [notesQuery, setNotesQuery] = useState("");
  const [notesResults, setNotesResults] = useState(null);
  const [contactsQuery, setContactsQuery] = useState("");
  const [contactsResults, setContactsResults] = useState(null);
  const [webQuery, setWebQuery] = useState("");
  const [webResults, setWebResults] = useState(null);
  const [webSearching, setWebSearching] = useState(false);
  const [backupInfo, setBackupInfo] = useState(null);
  const [restoring, setRestoring] = useState(false);
  const [restoreResult, setRestoreResult] = useState(null);
  const [emailStatus, setEmailStatus] = useState(null);
  const [emailInbox, setEmailInbox] = useState(null);
  const [emailSearchQuery, setEmailSearchQuery] = useState("");
  const [emailSearchResults, setEmailSearchResults] = useState(null);
  const [emailLoading, setEmailLoading] = useState(false);

  const load = useCallback(async (t) => {
    setLoading(true);
    try {
      if (t === "status") {
        const r = await fetch(`${BASE}/api/status`, { headers: fHeaders() });
        if (r.ok) setSysStatus(await r.json());
      } else if (t === "memory") {
        const [r, p] = await Promise.all([
          fetch(`${BASE}/api/memory`, { headers: fHeaders() }),
          fetch(`${BASE}/api/memory/patterns`, { headers: fHeaders() }),
        ]);
        if (r.ok) {
          const d = await r.json();
          setMemData(d);
          setUserFields({
            name: d.user?.name || "",
            identity: d.user?.identity || "",
            goals: (d.user?.goals || []).join(", "),
            businesses: (d.user?.businesses || []).join(", "),
            projects: (d.user?.projects || []).join(", "),
            values: (d.user?.values || []).join(", "),
          });
        }
        if (p.ok) setPatterns(await p.json());
      } else if (t === "audit") {
        const r = await fetch(`${BASE}/api/audit?limit=30`, { headers: fHeaders() });
        if (r.ok) {
          const d = await r.json();
          setAuditLog([...d.records].reverse());
        }
      } else if (t === "schedule") {
        const r = await fetch(`${BASE}/api/scheduler`, { headers: fHeaders() });
        if (r.ok) { const d = await r.json(); setTasks(d.tasks || []); }
      } else if (t === "backup") {
        const r = await fetch(`${BASE}/api/backup/info`, { headers: fHeaders() });
        if (r.ok) setBackupInfo(await r.json());
      } else if (t === "integrations") {
        const [cal, rem, wx, em] = await Promise.all([
          fetch(`${BASE}/api/integrations/calendar/today`, { headers: fHeaders() }),
          fetch(`${BASE}/api/integrations/reminders`, { headers: fHeaders() }),
          fetch(`${BASE}/api/brief`, { headers: fHeaders() }),
          fetch(`${BASE}/api/email/status`, { headers: fHeaders() }),
        ]);
        if (cal.ok) { const d = await cal.json(); setCalEvents(d.events || []); }
        if (rem.ok) { const d = await rem.json(); setReminders(d.reminders || []); }
        if (wx.ok) { const d = await wx.json(); setWeatherData(d.weather || null); }
        if (em.ok) setEmailStatus(await em.json());
      }
    } catch {} finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(tab); }, [tab, load]);

  async function saveField(field) {
    setSavingField(field);
    const lists = ["goals", "businesses", "projects", "values"];
    const value = lists.includes(field)
      ? userFields[field].split(",").map(s => s.trim()).filter(Boolean)
      : userFields[field];
    try {
      await fetch(`${BASE}/api/memory/user`, {
        method: "PATCH",
        headers: apiHeaders(),
        body: JSON.stringify({ field, value }),
      });
    } finally {
      setSavingField(null);
    }
  }

  async function addFact() {
    if (!newFact.trim()) return;
    await fetch(`${BASE}/api/memory/facts`, {
      method: "POST",
      headers: apiHeaders(),
      body: JSON.stringify({ fact: newFact.trim() }),
    });
    setNewFact("");
    load("memory");
  }

  async function clearHistory() {
    if (!confirm("Clear all conversation history? This cannot be undone.")) return;
    await fetch(`${BASE}/api/memory/conversations`, { method: "DELETE", headers: fHeaders() });
    load("memory");
  }

  const TAB = (t) => ({
    background: "none", border: "none",
    color: tab === t ? "#f5f5f5" : "#52525b",
    borderBottom: tab === t ? "2px solid #f5f5f5" : "2px solid transparent",
    fontSize: 11, fontWeight: 600, padding: "7px 12px", cursor: "pointer",
    textTransform: "uppercase", letterSpacing: "0.07em",
  });

  return (
    <div style={{ borderBottom: "1px solid #2a2a31", background: "#0c0d0f", flexShrink: 0, maxHeight: 360, display: "flex", flexDirection: "column" }}>
      <div style={{ display: "flex", alignItems: "center", borderBottom: "1px solid #1c1d22", padding: "0 14px" }}>
        {["status", "memory", "audit", "schedule", "integrations", "backup"].map(t => (
          <button key={t} onClick={() => setTab(t)} style={TAB(t)}>{t}</button>
        ))}
        <div style={{ flex: 1 }} />
        {loading && <span style={{ fontSize: 10, color: "#3f3f46" }}>loading…</span>}
        <button onClick={() => load(tab)}
          style={{ background: "none", border: "none", color: "#3f3f46", cursor: "pointer", fontSize: 14, padding: "4px 8px" }}>↻</button>
      </div>

      <div style={{ overflowY: "auto", padding: "12px 16px", flex: 1 }}>

        {/* STATUS */}
        {tab === "status" && (
          sysStatus ? (
            <div style={{ display: "flex", flexDirection: "column", gap: 7 }}>
              {[
                sysStatus.groq?.configured ? {
                  label: "GROQ",
                  dot: "ok",
                  detail: `${sysStatus.groq.model} · primary · free · fast`,
                } : null,
                sysStatus.openrouter?.configured ? {
                  label: "OPENROUTER",
                  dot: sysStatus.groq?.configured ? "degraded" : "ok",
                  detail: `${sysStatus.openrouter.model} · ${sysStatus.groq?.configured ? "fallback 2 · free" : "primary · free"}`,
                } : null,
                {
                  label: "OLLAMA",
                  dot: (sysStatus.openrouter?.configured || sysStatus.groq?.configured) ? "degraded" : sysStatus.ollama?.status,
                  detail: (sysStatus.openrouter?.configured || sysStatus.groq?.configured)
                    ? `${sysStatus.ollama?.model} · fallback 3 · offline`
                    : [
                        sysStatus.ollama?.latency_ms != null ? `${sysStatus.ollama.latency_ms}ms` : null,
                        sysStatus.ollama?.model,
                        sysStatus.ollama?.error ? sysStatus.ollama.error.slice(0, 60) : null,
                      ].filter(Boolean).join(" · "),
                },
                sysStatus.perplexity?.configured ? {
                  label: "PERPLEXITY",
                  dot: "degraded",
                  detail: `${sysStatus.perplexity.model} · last resort · paid · live web search`,
                } : null,
                {
                  label: "MEMORY",
                  dot: "ok",
                  detail: `${sysStatus.memory?.fact_count ?? 0} facts · ${sysStatus.memory?.conversation_count ?? 0} conversations · profile ${sysStatus.memory?.profile_fields_filled ?? "0/6"}${sysStatus.memory?.encrypted ? " · encrypted" : ""}`,
                },
                {
                  label: "AUDIT",
                  dot: "ok",
                  detail: `${sysStatus.audit?.total_records ?? 0} records`,
                },
                {
                  label: "APPROVALS",
                  dot: sysStatus.approvals?.pending > 0 ? "degraded" : "ok",
                  detail: `${sysStatus.approvals?.pending ?? 0} pending`,
                },
              ].filter(Boolean).map(({ label, dot, detail }) => (
                <div key={label} style={{ display: "flex", alignItems: "center", gap: 6 }}>
                  <StatusDot s={dot} />
                  <span style={{ fontSize: 11, color: "#52525b", fontFamily: "monospace", width: 82, flexShrink: 0 }}>{label}</span>
                  <span style={{ fontSize: 12, color: "#a1a1aa" }}>{detail}</span>
                </div>
              ))}
              <div style={{ marginTop: 6, paddingTop: 8, borderTop: "1px solid #1c1d22", fontSize: 10, color: "#3f3f46", fontFamily: "monospace" }}>
                {sysStatus.version} · {sysStatus.phase} · {sysStatus.mode}
              </div>
            </div>
          ) : (
            <div style={{ color: "#3f3f46", fontSize: 12 }}>Loading…</div>
          )
        )}

        {/* MEMORY */}
        {tab === "memory" && (
          <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
            <div>
              <div style={{ fontSize: 10, color: "#52525b", fontWeight: 700, letterSpacing: "0.1em", marginBottom: 8 }}>USER PROFILE</div>
              {[
                { key: "name",       label: "Name",       ph: "Your name" },
                { key: "identity",   label: "Identity",   ph: "Your role or description" },
                { key: "goals",      label: "Goals",      ph: "goal1, goal2" },
                { key: "businesses", label: "Businesses", ph: "biz1, biz2" },
                { key: "projects",   label: "Projects",   ph: "project1, project2" },
                { key: "values",     label: "Values",     ph: "integrity, clarity" },
              ].map(({ key, label, ph }) => (
                <div key={key} style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 5 }}>
                  <span style={{ fontSize: 11, color: "#52525b", width: 78, flexShrink: 0 }}>{label}</span>
                  <input
                    value={userFields[key] || ""} placeholder={ph}
                    onChange={e => setUserFields(p => ({ ...p, [key]: e.target.value }))}
                    onKeyDown={e => e.key === "Enter" && saveField(key)}
                    style={{ flex: 1, background: "#18191e", color: "#f5f5f5", border: "1px solid #2d2f36", borderRadius: 6, padding: "4px 8px", fontSize: 12, outline: "none", fontFamily: "inherit" }}
                  />
                  <button onClick={() => saveField(key)} disabled={savingField === key}
                    style={{ background: savingField === key ? "#27272a" : "#1d4ed8", color: "#fff", border: "none", borderRadius: 6, padding: "4px 9px", fontSize: 11, cursor: "pointer", flexShrink: 0 }}>
                    {savingField === key ? "…" : "Save"}
                  </button>
                </div>
              ))}
            </div>

            <div>
              <div style={{ fontSize: 10, color: "#52525b", fontWeight: 700, letterSpacing: "0.1em", marginBottom: 8 }}>
                FACTS ({memData?.facts?.length ?? 0})
              </div>
              <div style={{ display: "flex", gap: 6, marginBottom: 8 }}>
                <input
                  value={newFact} placeholder="Add a fact Mr.Black should know…"
                  onChange={e => setNewFact(e.target.value)}
                  onKeyDown={e => e.key === "Enter" && addFact()}
                  style={{ flex: 1, background: "#18191e", color: "#f5f5f5", border: "1px solid #2d2f36", borderRadius: 6, padding: "4px 8px", fontSize: 12, outline: "none", fontFamily: "inherit" }}
                />
                <button onClick={addFact}
                  style={{ background: "#1d4ed8", color: "#fff", border: "none", borderRadius: 6, padding: "4px 9px", fontSize: 11, cursor: "pointer" }}>Add</button>
              </div>
              {(memData?.facts || []).slice().reverse().map((f, i) => (
                <div key={i} style={{ fontSize: 12, color: "#a1a1aa", padding: "3px 0", borderBottom: "1px solid #111213" }}>
                  · {f.fact}
                  {f.timestamp && (
                    <span style={{ color: "#3f3f46", marginLeft: 6, fontSize: 10 }}>
                      {new Date(f.timestamp).toLocaleDateString()}
                    </span>
                  )}
                </div>
              ))}
            </div>

            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", paddingTop: 4 }}>
              <span style={{ fontSize: 12, color: "#52525b" }}>
                Conversations: <span style={{ color: "#a1a1aa" }}>{memData?.conversation_count ?? 0}</span> stored
              </span>
              <button onClick={clearHistory}
                style={{ background: "none", border: "1px solid #3f3f46", color: "#71717a", borderRadius: 6, padding: "3px 10px", fontSize: 11, cursor: "pointer" }}>
                Clear History
              </button>
            </div>

            {/* SEARCH */}
            <div>
              <div style={{ fontSize: 10, color: "#52525b", fontWeight: 700, letterSpacing: "0.1em", marginBottom: 8 }}>MEMORY SEARCH</div>
              <div style={{ display: "flex", gap: 6, marginBottom: 8 }}>
                <input value={searchQuery} placeholder="Search facts and conversations…"
                  onChange={e => setSearchQuery(e.target.value)}
                  onKeyDown={async e => {
                    if (e.key !== "Enter" || !searchQuery.trim()) return;
                    const r = await fetch(`${BASE}/api/memory/search?q=${encodeURIComponent(searchQuery)}&limit=8`, { headers: fHeaders() });
                    if (r.ok) setSearchResults((await r.json()).results);
                  }}
                  style={{ flex: 1, background: "#18191e", color: "#f5f5f5", border: "1px solid #2d2f36", borderRadius: 6, padding: "4px 8px", fontSize: 12, outline: "none", fontFamily: "inherit" }}
                />
                <button onClick={async () => {
                  if (!searchQuery.trim()) return;
                  const r = await fetch(`${BASE}/api/memory/search?q=${encodeURIComponent(searchQuery)}&limit=8`, { headers: fHeaders() });
                  if (r.ok) setSearchResults((await r.json()).results);
                }} style={{ background: "#1d4ed8", color: "#fff", border: "none", borderRadius: 6, padding: "4px 9px", fontSize: 11, cursor: "pointer" }}>Search</button>
                {searchResults && <button onClick={() => setSearchResults(null)}
                  style={{ background: "none", border: "1px solid #3f3f46", color: "#71717a", borderRadius: 6, padding: "4px 9px", fontSize: 11, cursor: "pointer" }}>Clear</button>}
              </div>
              {searchResults && (
                searchResults.length === 0
                  ? <div style={{ fontSize: 12, color: "#3f3f46" }}>No results found.</div>
                  : searchResults.map((r, i) => (
                    <div key={i} style={{ borderBottom: "1px solid #111213", padding: "6px 0", display: "flex", flexDirection: "column", gap: 3 }}>
                      <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                        <span style={{ fontSize: 10, color: r.type === "fact" ? "#60a5fa" : "#a16207", fontFamily: "monospace", fontWeight: 700 }}>{r.type}</span>
                        <span style={{ fontSize: 10, color: "#3f3f46", fontFamily: "monospace" }}>score: {r.score}</span>
                        {r.timestamp && <span style={{ fontSize: 10, color: "#27272a" }}>{new Date(r.timestamp).toLocaleDateString()}</span>}
                      </div>
                      {r.type === "fact"
                        ? <div style={{ fontSize: 12, color: "#d4d4d8" }}>{r.content}</div>
                        : <>
                            <div style={{ fontSize: 12, color: "#a1a1aa" }}>You: {r.user}</div>
                            <div style={{ fontSize: 12, color: "#71717a" }}>Mr.Black: {r.assistant}</div>
                          </>
                      }
                    </div>
                  ))
              )}
            </div>

            {/* PATTERNS */}
            {patterns && patterns.top_domains?.length > 0 && (
              <div>
                <div style={{ fontSize: 10, color: "#52525b", fontWeight: 700, letterSpacing: "0.1em", marginBottom: 8 }}>USAGE PATTERNS</div>
                <div style={{ display: "flex", gap: 16, flexWrap: "wrap" }}>
                  <div>
                    <div style={{ fontSize: 10, color: "#3f3f46", marginBottom: 4 }}>TOP DOMAINS</div>
                    {patterns.top_domains.map(d => (
                      <div key={d.domain} style={{ fontSize: 12, color: "#a1a1aa" }}>{d.domain} <span style={{ color: "#52525b" }}>×{d.count}</span></div>
                    ))}
                  </div>
                  <div>
                    <div style={{ fontSize: 10, color: "#3f3f46", marginBottom: 4 }}>APPROVALS</div>
                    <div style={{ fontSize: 12, color: "#a1a1aa" }}>approved: <span style={{ color: "#22c55e" }}>{patterns.approvals.approved}</span></div>
                    <div style={{ fontSize: 12, color: "#a1a1aa" }}>rejected: <span style={{ color: "#ef4444" }}>{patterns.approvals.rejected}</span></div>
                    {patterns.approvals.approval_rate_pct != null && (
                      <div style={{ fontSize: 12, color: "#a1a1aa" }}>rate: <span style={{ color: "#60a5fa" }}>{patterns.approvals.approval_rate_pct}%</span></div>
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* AUDIT */}
        {tab === "audit" && (
          auditLog.length === 0
            ? <div style={{ color: "#3f3f46", fontSize: 12, textAlign: "center", padding: 16 }}>No audit records</div>
            : auditLog.map((ev, i) => (
              <div key={i} style={{ display: "flex", gap: 8, padding: "3px 0", borderBottom: "1px solid #111213", fontSize: 11, fontFamily: "monospace" }}>
                <span style={{ color: "#3f3f46", flexShrink: 0 }}>{new Date(ev.timestamp).toLocaleTimeString()}</span>
                <span style={{ color: "#a16207", width: 180, flexShrink: 0, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{ev.event_type}</span>
                <span style={{ color: "#52525b", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                  {ev.session_id ? `[${ev.session_id}] ` : ""}{JSON.stringify(ev.details || {}).slice(0, 80)}
                </span>
              </div>
            ))
        )}

        {/* SCHEDULE */}
        {tab === "schedule" && (
          <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
            {/* Add task form */}
            <div>
              <div style={{ fontSize: 10, color: "#52525b", fontWeight: 700, letterSpacing: "0.1em", marginBottom: 8 }}>NEW TASK</div>
              <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                {[
                  { key: "name",   ph: "Task name (e.g. Morning AAPL check)" },
                  { key: "prompt", ph: "Prompt to run (e.g. Check AAPL and summarize)" },
                  { key: "cron",   ph: "Cron (e.g. 0 9 * * 1-5 = weekdays 9am)" },
                ].map(({ key, ph }) => (
                  <input key={key} value={newTask[key]} placeholder={ph}
                    onChange={e => setNewTask(p => ({ ...p, [key]: e.target.value }))}
                    style={{ background: "#18191e", color: "#f5f5f5", border: "1px solid #2d2f36", borderRadius: 6, padding: "5px 8px", fontSize: 12, outline: "none", fontFamily: "inherit" }}
                  />
                ))}
                <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
                  <select value={newTask.domain} onChange={e => setNewTask(p => ({ ...p, domain: e.target.value }))}
                    style={{ background: "#18191e", color: "#a1a1aa", border: "1px solid #2d2f36", borderRadius: 6, padding: "5px 8px", fontSize: 12, outline: "none", flex: 1 }}>
                    {["general","finance","research","business","builder"].map(d => <option key={d} value={d}>{d}</option>)}
                  </select>
                  <button
                    onClick={async () => {
                      if (!newTask.name.trim() || !newTask.prompt.trim()) return;
                      await fetch(`${BASE}/api/scheduler`, { method: "POST", headers: apiHeaders(), body: JSON.stringify(newTask) });
                      setNewTask({ name: "", prompt: "", cron: "*/15 * * * *", domain: "general" });
                      load("schedule");
                    }}
                    style={{ background: "#1d4ed8", color: "#fff", border: "none", borderRadius: 6, padding: "5px 14px", fontSize: 12, fontWeight: 600, cursor: "pointer", flexShrink: 0 }}>
                    Add
                  </button>
                </div>
              </div>
            </div>

            {/* Task list */}
            <div>
              <div style={{ fontSize: 10, color: "#52525b", fontWeight: 700, letterSpacing: "0.1em", marginBottom: 8, marginTop: 4 }}>
                SCHEDULED TASKS ({tasks.length})
              </div>
              {tasks.length === 0
                ? <div style={{ color: "#3f3f46", fontSize: 12 }}>No tasks scheduled yet.</div>
                : tasks.map(t => (
                  <div key={t.id} style={{ borderBottom: "1px solid #1c1d22", padding: "8px 0", display: "flex", flexDirection: "column", gap: 3 }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                      <StatusDot s={t.enabled ? "ok" : "error"} />
                      <span style={{ fontSize: 13, color: "#e5e7eb", fontWeight: 600, flex: 1 }}>{t.name}</span>
                      <span style={{ fontSize: 10, color: "#52525b", fontFamily: "monospace" }}>{t.cron}</span>
                      <span style={{ fontSize: 10, color: "#3f3f46" }}>{t.domain}</span>
                    </div>
                    <div style={{ fontSize: 11, color: "#52525b", paddingLeft: 13 }}>{t.prompt.slice(0, 80)}{t.prompt.length > 80 ? "…" : ""}</div>
                    {t.last_run && (
                      <div style={{ fontSize: 10, color: "#3f3f46", paddingLeft: 13, fontFamily: "monospace" }}>
                        last run: {new Date(t.last_run).toLocaleString()} · {t.last_result?.slice(0, 60)}
                      </div>
                    )}
                    <div style={{ display: "flex", gap: 6, paddingLeft: 13, marginTop: 2 }}>
                      <button onClick={async () => {
                        await fetch(`${BASE}/api/scheduler/${t.id}`, { method: "PATCH", headers: apiHeaders(), body: JSON.stringify({ enabled: !t.enabled }) });
                        load("schedule");
                      }} style={{ background: "none", border: "1px solid #2d2f36", color: t.enabled ? "#52525b" : "#22c55e", borderRadius: 5, padding: "2px 8px", fontSize: 11, cursor: "pointer" }}>
                        {t.enabled ? "Pause" : "Resume"}
                      </button>
                      <button onClick={async () => {
                        await fetch(`${BASE}/api/scheduler/${t.id}/run`, { method: "POST", headers: fHeaders() });
                        setTimeout(() => load("schedule"), 2000);
                      }} style={{ background: "none", border: "1px solid #2d2f36", color: "#60a5fa", borderRadius: 5, padding: "2px 8px", fontSize: 11, cursor: "pointer" }}>
                        Run now
                      </button>
                      <button onClick={async () => {
                        if (!confirm(`Delete "${t.name}"?`)) return;
                        await fetch(`${BASE}/api/scheduler/${t.id}`, { method: "DELETE", headers: fHeaders() });
                        load("schedule");
                      }} style={{ background: "none", border: "1px solid #3f3f46", color: "#71717a", borderRadius: 5, padding: "2px 8px", fontSize: 11, cursor: "pointer" }}>
                        Delete
                      </button>
                    </div>
                  </div>
                ))
              }
            </div>
          </div>
        )}

        {/* BACKUP */}
        {tab === "backup" && (
          <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>

            {/* What's included */}
            <div>
              <div style={{ fontSize: 10, color: "#52525b", fontWeight: 700, letterSpacing: "0.1em", marginBottom: 8 }}>WHAT GETS BACKED UP</div>
              {backupInfo ? (
                backupInfo.files.length === 0
                  ? <div style={{ fontSize: 12, color: "#3f3f46" }}>No data files found yet.</div>
                  : backupInfo.files.map(f => (
                    <div key={f.name} style={{ display: "flex", gap: 10, padding: "4px 0", borderBottom: "1px solid #111213", fontSize: 12 }}>
                      <span style={{ color: "#e5e7eb", fontFamily: "monospace", flex: 1 }}>{f.name}</span>
                      <span style={{ color: "#52525b" }}>{f.size_kb} KB</span>
                      <span style={{ color: "#3f3f46", fontSize: 10 }}>{new Date(f.modified).toLocaleDateString()}</span>
                    </div>
                  ))
              ) : (
                <div style={{ fontSize: 12, color: "#3f3f46" }}>Loading…</div>
              )}
              <div style={{ fontSize: 10, color: "#27272a", marginTop: 6 }}>Memory · Schedule · Audit log · Approvals — packaged as a single .zip</div>
            </div>

            {/* Download */}
            <div>
              <div style={{ fontSize: 10, color: "#52525b", fontWeight: 700, letterSpacing: "0.1em", marginBottom: 10 }}>DOWNLOAD BACKUP</div>
              <a href={`${BASE}/api/backup/download`}
                style={{ display: "inline-block", background: "#15803d", color: "#fff", borderRadius: 8, padding: "9px 20px", fontSize: 13, fontWeight: 600, textDecoration: "none", letterSpacing: "0.04em" }}
                onClick={() => setRestoreResult(null)}>
                ↓ Download black_backup.zip
              </a>
              <div style={{ fontSize: 11, color: "#3f3f46", marginTop: 8 }}>
                Keep this file somewhere safe — it contains your full memory and history.
                If you use memory encryption, back up your <span style={{ fontFamily: "monospace", color: "#52525b" }}>MEMORY_ENCRYPTION_KEY</span> from .env separately.
              </div>
            </div>

            {/* Restore */}
            <div>
              <div style={{ fontSize: 10, color: "#52525b", fontWeight: 700, letterSpacing: "0.1em", marginBottom: 10 }}>RESTORE FROM BACKUP</div>
              <div style={{ fontSize: 12, color: "#71717a", marginBottom: 10, lineHeight: 1.6 }}>
                Upload a <span style={{ fontFamily: "monospace", color: "#a1a1aa" }}>black_backup_*.zip</span> file to overwrite current data.
                This cannot be undone — download a fresh backup first if you want to preserve current state.
              </div>
              <label style={{ display: "inline-block", background: restoring ? "#27272a" : "#1c1d22", color: restoring ? "#52525b" : "#a1a1aa", border: "1px solid #2d2f36", borderRadius: 8, padding: "8px 16px", fontSize: 12, fontWeight: 600, cursor: restoring ? "not-allowed" : "pointer" }}>
                {restoring ? "Restoring…" : "↑ Choose backup file"}
                <input type="file" accept=".zip" disabled={restoring} style={{ display: "none" }}
                  onChange={async e => {
                    const file = e.target.files?.[0];
                    if (!file) return;
                    setRestoring(true);
                    setRestoreResult(null);
                    const form = new FormData();
                    form.append("file", file);
                    try {
                      const headers = API_KEY ? { "X-BLACK-API-KEY": API_KEY } : {};
                      const r = await fetch(`${BASE}/api/backup/restore`, { method: "POST", headers, body: form });
                      const d = await r.json();
                      setRestoreResult({ ok: r.ok, ...d });
                      if (r.ok) load("backup");
                    } catch {
                      setRestoreResult({ ok: false, detail: "Upload failed — check backend is running." });
                    } finally {
                      setRestoring(false);
                      e.target.value = "";
                    }
                  }}
                />
              </label>

              {restoreResult && (
                <div style={{ marginTop: 12, background: restoreResult.ok ? "#052e16" : "#1c0a0a", border: `1px solid ${restoreResult.ok ? "#15803d" : "#991b1b"}`, borderRadius: 8, padding: "10px 14px", fontSize: 12 }}>
                  {restoreResult.ok ? (
                    <>
                      <div style={{ color: "#22c55e", fontWeight: 600, marginBottom: 4 }}>✓ Restore complete</div>
                      <div style={{ color: "#a1a1aa" }}>Files restored: {restoreResult.restored?.join(", ")}</div>
                      <div style={{ color: "#52525b", marginTop: 4 }}>Backup from: {restoreResult.backup_created?.slice(0, 16)} · v{restoreResult.backup_version}</div>
                      <div style={{ color: "#f59e0b", marginTop: 6, fontWeight: 600 }}>Restart the backend to apply changes.</div>
                    </>
                  ) : (
                    <div style={{ color: "#f87171" }}>✕ {restoreResult.detail || "Restore failed."}</div>
                  )}
                </div>
              )}
            </div>

          </div>
        )}

        {/* INTEGRATIONS */}
        {tab === "integrations" && (
          <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>

            {/* Weather */}
            <div>
              <div style={{ fontSize: 10, color: "#52525b", fontWeight: 700, letterSpacing: "0.1em", marginBottom: 8 }}>WEATHER</div>
              {weatherData && Object.keys(weatherData).length > 0 ? (
                <div style={{ fontSize: 13, color: "#a1a1aa" }}>
                  {weatherData.city && <span style={{ color: "#e5e7eb", marginRight: 8 }}>{weatherData.city}</span>}
                  <span>{weatherData.description} · {weatherData.temp_f}°F (feels {weatherData.feels_like_f}°F)</span>
                  <span style={{ color: "#52525b", marginLeft: 10 }}>High {weatherData.high_f}°F / Low {weatherData.low_f}°F · Humidity {weatherData.humidity}%</span>
                </div>
              ) : (
                <div style={{ fontSize: 12, color: "#3f3f46" }}>{weatherData === null ? "Loading…" : "Weather unavailable."}</div>
              )}
              <div style={{ fontSize: 10, color: "#27272a", marginTop: 4 }}>Set your city in WEATHER_LOCATION in .env for accurate results. Or click ☀ Brief in the header for a full morning summary.</div>
            </div>

            {/* Calendar */}
            <div>
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 8 }}>
                <div style={{ fontSize: 10, color: "#52525b", fontWeight: 700, letterSpacing: "0.1em" }}>CALENDAR — TODAY</div>
                <button onClick={async () => {
                  const r = await fetch(`${BASE}/api/integrations/calendar/upcoming?days=7`, { headers: fHeaders() });
                  if (r.ok) { const d = await r.json(); setCalUpcoming(d.events || []); }
                }} style={{ background: "none", border: "1px solid #2d2f36", color: "#52525b", borderRadius: 5, padding: "2px 8px", fontSize: 10, cursor: "pointer" }}>
                  Show week ↓
                </button>
              </div>
              {calEvents === null
                ? <div style={{ fontSize: 12, color: "#3f3f46" }}>Loading…</div>
                : calEvents.length === 0
                  ? <div style={{ fontSize: 12, color: "#3f3f46" }}>No events today.</div>
                  : calEvents.map((e, i) => (
                    <div key={i} style={{ fontSize: 12, color: "#a1a1aa", borderBottom: "1px solid #111213", padding: "4px 0", display: "flex", gap: 10 }}>
                      <span style={{ color: "#52525b", fontFamily: "monospace", flexShrink: 0 }}>{e.start}–{e.end}</span>
                      <span>{e.title}</span>
                      <span style={{ color: "#3f3f46", fontSize: 10, marginLeft: "auto", flexShrink: 0 }}>{e.calendar}</span>
                    </div>
                  ))
              }
              {calUpcoming && calUpcoming.length > 0 && (
                <div style={{ marginTop: 10 }}>
                  <div style={{ fontSize: 10, color: "#52525b", fontWeight: 700, letterSpacing: "0.1em", marginBottom: 6 }}>UPCOMING (7 DAYS)</div>
                  {calUpcoming.map((e, i) => (
                    <div key={i} style={{ fontSize: 12, color: "#a1a1aa", borderBottom: "1px solid #111213", padding: "4px 0", display: "flex", gap: 10 }}>
                      <span style={{ color: "#52525b", fontFamily: "monospace", flexShrink: 0 }}>{e.date} {e.start}</span>
                      <span>{e.title}</span>
                      <span style={{ color: "#3f3f46", fontSize: 10, marginLeft: "auto", flexShrink: 0 }}>{e.calendar}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Reminders */}
            <div>
              <div style={{ fontSize: 10, color: "#52525b", fontWeight: 700, letterSpacing: "0.1em", marginBottom: 8 }}>REMINDERS</div>
              <div style={{ display: "flex", gap: 6, marginBottom: 8 }}>
                <input value={newReminder} placeholder="Add a reminder…"
                  onChange={e => setNewReminder(e.target.value)}
                  onKeyDown={async e => {
                    if (e.key !== "Enter" || !newReminder.trim()) return;
                    await fetch(`${BASE}/api/integrations/reminders`, { method: "POST", headers: apiHeaders(), body: JSON.stringify({ title: newReminder.trim() }) });
                    setNewReminder("");
                    const r = await fetch(`${BASE}/api/integrations/reminders`, { headers: fHeaders() });
                    if (r.ok) { const d = await r.json(); setReminders(d.reminders || []); }
                  }}
                  style={{ flex: 1, background: "#18191e", color: "#f5f5f5", border: "1px solid #2d2f36", borderRadius: 6, padding: "4px 8px", fontSize: 12, outline: "none", fontFamily: "inherit" }}
                />
                <button onClick={async () => {
                  if (!newReminder.trim()) return;
                  await fetch(`${BASE}/api/integrations/reminders`, { method: "POST", headers: apiHeaders(), body: JSON.stringify({ title: newReminder.trim() }) });
                  setNewReminder("");
                  const r = await fetch(`${BASE}/api/integrations/reminders`, { headers: fHeaders() });
                  if (r.ok) { const d = await r.json(); setReminders(d.reminders || []); }
                }} style={{ background: "#1d4ed8", color: "#fff", border: "none", borderRadius: 6, padding: "4px 9px", fontSize: 11, cursor: "pointer" }}>Add</button>
              </div>
              {reminders === null
                ? <div style={{ fontSize: 12, color: "#3f3f46" }}>Loading…</div>
                : reminders.length === 0
                  ? <div style={{ fontSize: 12, color: "#3f3f46" }}>No pending reminders.</div>
                  : reminders.map((r, i) => (
                    <div key={i} style={{ fontSize: 12, color: "#a1a1aa", borderBottom: "1px solid #111213", padding: "4px 0", display: "flex", gap: 8 }}>
                      <span>· {r.title}</span>
                      {r.due && <span style={{ color: "#52525b", fontSize: 10, marginLeft: "auto" }}>{r.due}</span>}
                    </div>
                  ))
              }
            </div>

            {/* Files */}
            <div>
              <div style={{ fontSize: 10, color: "#52525b", fontWeight: 700, letterSpacing: "0.1em", marginBottom: 8 }}>FILE SEARCH</div>
              <div style={{ display: "flex", gap: 6, marginBottom: 8 }}>
                <input value={fileQuery} placeholder="Search Desktop, Documents, Downloads…"
                  onChange={e => setFileQuery(e.target.value)}
                  onKeyDown={async e => {
                    if (e.key !== "Enter" || !fileQuery.trim()) return;
                    const r = await fetch(`${BASE}/api/integrations/files/search?q=${encodeURIComponent(fileQuery)}&limit=20`, { headers: fHeaders() });
                    if (r.ok) { const d = await r.json(); setFileResults(d.results || []); }
                  }}
                  style={{ flex: 1, background: "#18191e", color: "#f5f5f5", border: "1px solid #2d2f36", borderRadius: 6, padding: "4px 8px", fontSize: 12, outline: "none", fontFamily: "inherit" }}
                />
                <button onClick={async () => {
                  if (!fileQuery.trim()) return;
                  const r = await fetch(`${BASE}/api/integrations/files/search?q=${encodeURIComponent(fileQuery)}&limit=20`, { headers: fHeaders() });
                  if (r.ok) { const d = await r.json(); setFileResults(d.results || []); }
                }} style={{ background: "#1d4ed8", color: "#fff", border: "none", borderRadius: 6, padding: "4px 9px", fontSize: 11, cursor: "pointer" }}>Search</button>
                {fileResults && <button onClick={() => setFileResults(null)}
                  style={{ background: "none", border: "1px solid #3f3f46", color: "#71717a", borderRadius: 6, padding: "4px 9px", fontSize: 11, cursor: "pointer" }}>Clear</button>}
              </div>
              {fileResults && (
                fileResults.length === 0
                  ? <div style={{ fontSize: 12, color: "#3f3f46" }}>No files found.</div>
                  : fileResults.map((f, i) => (
                    <div key={i} style={{ fontSize: 12, color: "#a1a1aa", borderBottom: "1px solid #111213", padding: "4px 0" }}>
                      <span style={{ color: "#e5e7eb" }}>{f.name}</span>
                      <span style={{ color: "#3f3f46", fontSize: 10, marginLeft: 8 }}>{(f.size / 1024).toFixed(1)} KB</span>
                      <div style={{ fontSize: 10, color: "#27272a", fontFamily: "monospace", marginTop: 2 }}>{f.path}</div>
                    </div>
                  ))
              )}
              <div style={{ fontSize: 10, color: "#27272a", marginTop: 6 }}>Searches: ~/Desktop · ~/Documents · ~/Downloads · Configurable via FILE_SEARCH_PATHS in .env</div>
            </div>

            {/* Notes */}
            <div>
              <div style={{ fontSize: 10, color: "#52525b", fontWeight: 700, letterSpacing: "0.1em", marginBottom: 8 }}>NOTES SEARCH</div>
              <div style={{ display: "flex", gap: 6, marginBottom: 8 }}>
                <input value={notesQuery} placeholder="Search your notes…"
                  onChange={e => setNotesQuery(e.target.value)}
                  onKeyDown={async e => {
                    if (e.key !== "Enter" || !notesQuery.trim()) return;
                    const r = await fetch(`${BASE}/api/integrations/notes/search?q=${encodeURIComponent(notesQuery)}&limit=10`, { headers: fHeaders() });
                    if (r.ok) { const d = await r.json(); setNotesResults(d.results || []); }
                  }}
                  style={{ flex: 1, background: "#18191e", color: "#f5f5f5", border: "1px solid #2d2f36", borderRadius: 6, padding: "4px 8px", fontSize: 12, outline: "none", fontFamily: "inherit" }}
                />
                <button onClick={async () => {
                  if (!notesQuery.trim()) return;
                  const r = await fetch(`${BASE}/api/integrations/notes/search?q=${encodeURIComponent(notesQuery)}&limit=10`, { headers: fHeaders() });
                  if (r.ok) { const d = await r.json(); setNotesResults(d.results || []); }
                }} style={{ background: "#1d4ed8", color: "#fff", border: "none", borderRadius: 6, padding: "4px 9px", fontSize: 11, cursor: "pointer" }}>Search</button>
                {notesResults && <button onClick={() => setNotesResults(null)}
                  style={{ background: "none", border: "1px solid #3f3f46", color: "#71717a", borderRadius: 6, padding: "4px 9px", fontSize: 11, cursor: "pointer" }}>Clear</button>}
              </div>
              {notesResults && (
                notesResults.length === 0
                  ? <div style={{ fontSize: 12, color: "#3f3f46" }}>No notes found.</div>
                  : notesResults.map((n, i) => (
                    <div key={i} style={{ borderBottom: "1px solid #111213", padding: "6px 0" }}>
                      <div style={{ fontSize: 12, color: "#e5e7eb", fontWeight: 600 }}>{n.title}</div>
                      <div style={{ fontSize: 11, color: "#71717a", marginTop: 2, whiteSpace: "pre-wrap" }}>{n.body.slice(0, 200)}{n.body.length > 200 ? "…" : ""}</div>
                    </div>
                  ))
              )}
            </div>

            {/* Contacts */}
            <div>
              <div style={{ fontSize: 10, color: "#52525b", fontWeight: 700, letterSpacing: "0.1em", marginBottom: 8 }}>CONTACTS SEARCH</div>
              <div style={{ display: "flex", gap: 6, marginBottom: 8 }}>
                <input value={contactsQuery} placeholder="Search by name…"
                  onChange={e => setContactsQuery(e.target.value)}
                  onKeyDown={async e => {
                    if (e.key !== "Enter" || !contactsQuery.trim()) return;
                    const r = await fetch(`${BASE}/api/integrations/contacts/search?q=${encodeURIComponent(contactsQuery)}`, { headers: fHeaders() });
                    if (r.ok) { const d = await r.json(); setContactsResults(d.results || []); }
                  }}
                  style={{ flex: 1, background: "#18191e", color: "#f5f5f5", border: "1px solid #2d2f36", borderRadius: 6, padding: "4px 8px", fontSize: 12, outline: "none", fontFamily: "inherit" }}
                />
                <button onClick={async () => {
                  if (!contactsQuery.trim()) return;
                  const r = await fetch(`${BASE}/api/integrations/contacts/search?q=${encodeURIComponent(contactsQuery)}`, { headers: fHeaders() });
                  if (r.ok) { const d = await r.json(); setContactsResults(d.results || []); }
                }} style={{ background: "#1d4ed8", color: "#fff", border: "none", borderRadius: 6, padding: "4px 9px", fontSize: 11, cursor: "pointer" }}>Search</button>
                {contactsResults && <button onClick={() => setContactsResults(null)}
                  style={{ background: "none", border: "1px solid #3f3f46", color: "#71717a", borderRadius: 6, padding: "4px 9px", fontSize: 11, cursor: "pointer" }}>Clear</button>}
              </div>
              {contactsResults && (
                contactsResults.length === 0
                  ? <div style={{ fontSize: 12, color: "#3f3f46" }}>No contacts found.</div>
                  : contactsResults.map((c, i) => (
                    <div key={i} style={{ fontSize: 12, color: "#a1a1aa", borderBottom: "1px solid #111213", padding: "5px 0", display: "flex", flexDirection: "column", gap: 2 }}>
                      <span style={{ color: "#e5e7eb", fontWeight: 600 }}>{c.name}</span>
                      <div style={{ display: "flex", gap: 12, fontSize: 11, color: "#52525b" }}>
                        {c.email && <span>✉ {c.email}</span>}
                        {c.phone && <span>✆ {c.phone}</span>}
                        {c.org && <span>🏢 {c.org}</span>}
                      </div>
                    </div>
                  ))
              )}
            </div>

            {/* Web Search */}
            <div>
              <div style={{ fontSize: 10, color: "#52525b", fontWeight: 700, letterSpacing: "0.1em", marginBottom: 8 }}>WEB SEARCH</div>
              <div style={{ display: "flex", gap: 6, marginBottom: 8 }}>
                <input value={webQuery} placeholder="Search the web via DuckDuckGo…"
                  onChange={e => setWebQuery(e.target.value)}
                  onKeyDown={async e => {
                    if (e.key !== "Enter" || !webQuery.trim() || webSearching) return;
                    setWebSearching(true);
                    try {
                      const r = await fetch(`${BASE}/api/integrations/web/search?q=${encodeURIComponent(webQuery)}&max_results=5`, { headers: fHeaders() });
                      if (r.ok) { const d = await r.json(); setWebResults(d.results || []); }
                    } finally { setWebSearching(false); }
                  }}
                  style={{ flex: 1, background: "#18191e", color: "#f5f5f5", border: "1px solid #2d2f36", borderRadius: 6, padding: "4px 8px", fontSize: 12, outline: "none", fontFamily: "inherit" }}
                />
                <button onClick={async () => {
                  if (!webQuery.trim() || webSearching) return;
                  setWebSearching(true);
                  try {
                    const r = await fetch(`${BASE}/api/integrations/web/search?q=${encodeURIComponent(webQuery)}&max_results=5`, { headers: fHeaders() });
                    if (r.ok) { const d = await r.json(); setWebResults(d.results || []); }
                  } finally { setWebSearching(false); }
                }} disabled={webSearching} style={{ background: webSearching ? "#27272a" : "#1d4ed8", color: "#fff", border: "none", borderRadius: 6, padding: "4px 9px", fontSize: 11, cursor: webSearching ? "not-allowed" : "pointer" }}>
                  {webSearching ? "…" : "Search"}
                </button>
                {webResults && <button onClick={() => setWebResults(null)}
                  style={{ background: "none", border: "1px solid #3f3f46", color: "#71717a", borderRadius: 6, padding: "4px 9px", fontSize: 11, cursor: "pointer" }}>Clear</button>}
              </div>
              {webResults && (
                webResults.length === 0
                  ? <div style={{ fontSize: 12, color: "#3f3f46" }}>No results found.</div>
                  : webResults.map((r, i) => (
                    <div key={i} style={{ borderBottom: "1px solid #111213", padding: "6px 0", display: "flex", flexDirection: "column", gap: 3 }}>
                      <div style={{ fontSize: 12, color: "#60a5fa", fontWeight: 600 }}>{r.title}</div>
                      <div style={{ fontSize: 11, color: "#a1a1aa" }}>{r.snippet.slice(0, 180)}{r.snippet.length > 180 ? "…" : ""}</div>
                      <div style={{ fontSize: 10, color: "#3f3f46", fontFamily: "monospace" }}>{r.url.slice(0, 70)}</div>
                    </div>
                  ))
              )}
              <div style={{ fontSize: 10, color: "#27272a", marginTop: 6 }}>Results via DuckDuckGo — no account or API key required. Or ask Mr.Black in chat: "search the web for…"</div>
            </div>

            {/* Email */}
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
                <div style={{ fontSize: 10, color: "#52525b", fontWeight: 700, letterSpacing: "0.1em" }}>EMAIL (IMAP)</div>
                {emailStatus && (
                  <span style={{ fontSize: 10, padding: "1px 7px", borderRadius: 100, background: emailStatus.configured ? "#052e16" : "#1c0a0a", color: emailStatus.configured ? "#22c55e" : "#f87171", border: `1px solid ${emailStatus.configured ? "#15803d" : "#991b1b"}` }}>
                    {emailStatus.configured ? `connected · ${emailStatus.unread ?? 0} unread` : "not configured"}
                  </span>
                )}
              </div>

              {emailStatus && !emailStatus.configured && (
                <div style={{ fontSize: 12, color: "#52525b", background: "#0f1012", border: "1px solid #1c1d22", borderRadius: 8, padding: "10px 12px", marginBottom: 8, lineHeight: 1.7 }}>
                  <div style={{ color: "#a1a1aa", fontWeight: 600, marginBottom: 4 }}>Setup — iCloud App-Specific Password</div>
                  <div>1. Go to <span style={{ color: "#60a5fa", fontFamily: "monospace" }}>appleid.apple.com</span></div>
                  <div>2. Sign-In and Security → App-Specific Passwords → Generate</div>
                  <div>3. Copy the generated password (xxxx-xxxx-xxxx-xxxx format)</div>
                  <div style={{ marginTop: 6 }}>Then set in <span style={{ fontFamily: "monospace", color: "#d4d4d8" }}>backend/.env</span>:</div>
                  <pre style={{ fontSize: 11, color: "#71717a", margin: "4px 0 0", lineHeight: 1.6 }}>{`EMAIL_HOST=imap.mail.me.com
EMAIL_USER=you@icloud.com
EMAIL_PASSWORD=xxxx-xxxx-xxxx-xxxx`}</pre>
                  <div style={{ marginTop: 6, color: "#52525b", fontSize: 11 }}>Restart the backend after saving .env</div>
                </div>
              )}

              {emailStatus?.configured && (
                <>
                  <div style={{ display: "flex", gap: 6, marginBottom: 8 }}>
                    <button onClick={async () => {
                      setEmailLoading(true);
                      try {
                        const r = await fetch(`${BASE}/api/email/inbox?limit=10&unread_only=false`, { headers: fHeaders() });
                        if (r.ok) { const d = await r.json(); setEmailInbox(d.emails || []); }
                      } finally { setEmailLoading(false); }
                    }} disabled={emailLoading} style={{ background: emailLoading ? "#27272a" : "#1d4ed8", color: "#fff", border: "none", borderRadius: 6, padding: "4px 10px", fontSize: 11, cursor: emailLoading ? "not-allowed" : "pointer" }}>
                      {emailLoading ? "Loading…" : "Load inbox"}
                    </button>
                    <button onClick={async () => {
                      setEmailLoading(true);
                      try {
                        const r = await fetch(`${BASE}/api/email/inbox?limit=10&unread_only=true`, { headers: fHeaders() });
                        if (r.ok) { const d = await r.json(); setEmailInbox(d.emails || []); }
                      } finally { setEmailLoading(false); }
                    }} disabled={emailLoading} style={{ background: "none", border: "1px solid #2d2f36", color: "#52525b", borderRadius: 6, padding: "4px 10px", fontSize: 11, cursor: emailLoading ? "not-allowed" : "pointer" }}>
                      Unread only
                    </button>
                    {emailInbox && <button onClick={() => setEmailInbox(null)}
                      style={{ background: "none", border: "1px solid #3f3f46", color: "#71717a", borderRadius: 6, padding: "4px 9px", fontSize: 11, cursor: "pointer" }}>Clear</button>}
                  </div>

                  <div style={{ display: "flex", gap: 6, marginBottom: 8 }}>
                    <input value={emailSearchQuery} placeholder="Search by sender or subject…"
                      onChange={e => setEmailSearchQuery(e.target.value)}
                      onKeyDown={async e => {
                        if (e.key !== "Enter" || !emailSearchQuery.trim()) return;
                        setEmailLoading(true);
                        try {
                          const r = await fetch(`${BASE}/api/email/search?q=${encodeURIComponent(emailSearchQuery)}&limit=10`, { headers: fHeaders() });
                          if (r.ok) { const d = await r.json(); setEmailSearchResults(d.emails || []); }
                        } finally { setEmailLoading(false); }
                      }}
                      style={{ flex: 1, background: "#18191e", color: "#f5f5f5", border: "1px solid #2d2f36", borderRadius: 6, padding: "4px 8px", fontSize: 12, outline: "none", fontFamily: "inherit" }}
                    />
                    <button onClick={async () => {
                      if (!emailSearchQuery.trim()) return;
                      setEmailLoading(true);
                      try {
                        const r = await fetch(`${BASE}/api/email/search?q=${encodeURIComponent(emailSearchQuery)}&limit=10`, { headers: fHeaders() });
                        if (r.ok) { const d = await r.json(); setEmailSearchResults(d.emails || []); }
                      } finally { setEmailLoading(false); }
                    }} disabled={emailLoading} style={{ background: emailLoading ? "#27272a" : "#1d4ed8", color: "#fff", border: "none", borderRadius: 6, padding: "4px 9px", fontSize: 11, cursor: emailLoading ? "not-allowed" : "pointer" }}>
                      Search
                    </button>
                    {emailSearchResults && <button onClick={() => setEmailSearchResults(null)}
                      style={{ background: "none", border: "1px solid #3f3f46", color: "#71717a", borderRadius: 6, padding: "4px 9px", fontSize: 11, cursor: "pointer" }}>Clear</button>}
                  </div>

                  {(emailInbox || emailSearchResults)?.map((e, i) => (
                    <div key={i} style={{ borderBottom: "1px solid #111213", padding: "7px 0", display: "flex", flexDirection: "column", gap: 2 }}>
                      <div style={{ display: "flex", gap: 8, alignItems: "flex-start" }}>
                        <span style={{ fontSize: 12, color: "#e5e7eb", fontWeight: 600, flex: 1 }}>{e.subject}</span>
                        <span style={{ fontSize: 10, color: "#3f3f46", fontFamily: "monospace", flexShrink: 0, marginTop: 1 }}>{e.date?.slice(0, 16)}</span>
                      </div>
                      <div style={{ fontSize: 11, color: "#52525b" }}>From: {e.from}</div>
                      {e.body && <div style={{ fontSize: 11, color: "#71717a", marginTop: 2, lineHeight: 1.5 }}>{e.body.slice(0, 180)}{e.body.length > 180 ? "…" : ""}</div>}
                    </div>
                  ))}
                </>
              )}

              <div style={{ fontSize: 10, color: "#27272a", marginTop: 6 }}>Read-only IMAP — no emails are sent. Or ask Mr.Black in chat: "check my email" or "any emails from John?"</div>
            </div>

          </div>
        )}

      </div>
    </div>
  );
}

// ─── Main App ──────────────────────────────────────────────────────────────────

export default function App() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content: "Mr.Black v1.0 online. Say \"Hey Mr.Black\" or click ◎ Wake to activate voice.",
      streaming: false,
      meta: { agent: "system", task_type: "startup", memory_used: false, policy_verdict: "auto_approved" },
    },
  ]);
  const [loading, setLoading] = useState(false);
  const [approvals, setApprovals] = useState([]);
  const [showApprovals, setShowApprovals] = useState(false);
  const [showSystem, setShowSystem] = useState(false);
  const [showGuide, setShowGuide] = useState(false);
  const [showBrief, setShowBrief] = useState(false);
  const [recording, setRecording] = useState(false);
  const [transcribing, setTranscribing] = useState(false);
  const [ttsEnabled, setTtsEnabled] = useState(false);
  const [voiceReady, setVoiceReady] = useState(false);
  const [wakeWordEnabled, setWakeWordEnabled] = useState(false);
  const [wakeWordListening, setWakeWordListening] = useState(false);
  const [commandListening, setCommandListening] = useState(false);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const recognitionRef = useRef(null);
  const commandRecRef = useRef(null);
  const lastWakeRef = useRef(0);
  const bottomRef = useRef(null);
  const inputRef = useRef(null);

  const fetchApprovals = useCallback(async () => {
    try {
      const res = await fetch(`${BASE}/api/approvals?pending_only=false`, { headers: fHeaders() });
      if (!res.ok) return;
      const data = await res.json();
      setApprovals((data.records || []).filter(r => r.status === "pending" || r.status === "approved"));
    } catch {}
  }, []);

  useEffect(() => { fetchApprovals(); }, [fetchApprovals]);

  useEffect(() => {
    fetch(`${BASE}/api/voice/status`, { headers: fHeaders() })
      .then(r => r.ok ? r.json() : null)
      .then(d => { if (d) setVoiceReady(d.ready); })
      .catch(() => {});
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Wake word listener — Web Speech API
  useEffect(() => {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR || !wakeWordEnabled) {
      setWakeWordListening(false);
      return;
    }

    const recognition = new SR();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = "en-US";
    recognitionRef.current = recognition;

    const WAKE_WORDS = ["hey black", "hey, black", "mr. black", "mr black"];
    const KILL_PHRASES = ["chibuike kill mr black", "chibuike kill mr. black", "chibuike kill black"];

    recognition.onresult = (event) => {
      const transcript = Array.from(event.results)
        .map(r => r[0].transcript)
        .join("")
        .toLowerCase()
        .trim();

      // ── Kill switch ──────────────────────────────────────────
      if (KILL_PHRASES.some(p => transcript.includes(p))) {
        setMessages(prev => [...prev, {
          role: "assistant",
          content: "Kill switch activated. Mr. Black going offline. Goodbye.",
          streaming: false,
          meta: { agent: "black", task_type: "shutdown", memory_used: false, policy_verdict: "auto_approved" },
        }]);
        fetch(`${BASE}/api/shutdown`, { method: "POST", headers: apiHeaders() }).catch(() => {});
        setWakeWordEnabled(false);
        return;
      }

      const now = Date.now();
      const hit = WAKE_WORDS.some(w => transcript.includes(w)) ||
        /\bblack\b/.test(transcript);

      if (hit && now - lastWakeRef.current > 4000) {
        lastWakeRef.current = now;
        fetch(`${BASE}/api/voice/greet`, { headers: fHeaders() })
          .then(r => r.ok ? r.json() : null)
          .then(d => {
            if (!d) return;
            const greeting = d.greeting;
            setMessages(prev => [...prev, {
              role: "assistant",
              content: greeting,
              streaming: false,
              meta: { agent: "black", task_type: "wake", memory_used: false, policy_verdict: "auto_approved" },
            }]);

            // Estimate how long TTS takes so we don't record over it
            const ttsDelay = ttsEnabled
              ? Math.max(1500, greeting.split(" ").length * 210)
              : 400;

            if (ttsEnabled) {
              fetch(`${BASE}/api/voice/speak`, {
                method: "POST",
                headers: apiHeaders(),
                body: JSON.stringify({ text: greeting }),
              }).catch(() => {});
            }

            // After greeting, auto-open mic for command
            setTimeout(() => {
              const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
              if (!SR) { inputRef.current?.focus(); return; }

              try { commandRecRef.current?.stop(); } catch {}

              const cmd = new SR();
              cmd.continuous = false;
              cmd.interimResults = false;
              cmd.lang = "en-US";
              commandRecRef.current = cmd;
              setCommandListening(true);

              cmd.onresult = (e) => {
                const text = e.results[0]?.[0]?.transcript?.trim();
                if (!text) return;
                setCommandListening(false);
                setInput(text);
                // Auto-send after a short tick so state updates flush
                setTimeout(() => {
                  const trimmed = text.trim();
                  if (!trimmed) return;
                  setMessages(prev => [...prev, { role: "user", content: trimmed, streaming: false, meta: null }]);
                  setInput("");
                  setLoading(true);
                  setMessages(prev => [...prev, { role: "assistant", content: "", streaming: true, meta: null }]);
                  fetch(`${BASE}/api/chat/stream`, {
                    method: "POST",
                    headers: apiHeaders(),
                    body: JSON.stringify({ message: trimmed }),
                  }).then(async (response) => {
                    if (!response.ok) throw new Error(`HTTP ${response.status}`);
                    const reader = response.body.getReader();
                    const decoder = new TextDecoder();
                    let fullReply = "";
                    while (true) {
                      const { done, value } = await reader.read();
                      if (done) break;
                      const chunk = decoder.decode(value, { stream: true });
                      for (const line of chunk.split("\n")) {
                        if (!line.startsWith("data: ")) continue;
                        const data = line.slice(6).trim();
                        if (data === "[DONE]") break;
                        try {
                          const parsed = JSON.parse(data);
                          if (parsed.token) {
                            fullReply += parsed.token;
                            setMessages(prev => {
                              const updated = [...prev];
                              updated[updated.length - 1] = { ...updated[updated.length - 1], content: fullReply };
                              return updated;
                            });
                          }
                          if (parsed.done) {
                            setMessages(prev => {
                              const updated = [...prev];
                              updated[updated.length - 1] = { ...updated[updated.length - 1], streaming: false, meta: parsed.meta || null };
                              return updated;
                            });
                            if (ttsEnabled && fullReply) {
                              fetch(`${BASE}/api/voice/speak`, {
                                method: "POST", headers: apiHeaders(),
                                body: JSON.stringify({ text: fullReply.slice(0, 300) }),
                              }).catch(() => {});
                            }
                          }
                        } catch {}
                      }
                    }
                  }).catch((err) => {
                    setMessages(prev => {
                      const updated = [...prev];
                      updated[updated.length - 1] = { ...updated[updated.length - 1], content: `Error: ${err.message}`, streaming: false };
                      return updated;
                    });
                  }).finally(() => setLoading(false));
                }, 50);
              };

              cmd.onerror = () => setCommandListening(false);
              cmd.onend = () => setCommandListening(false);

              try { cmd.start(); } catch { setCommandListening(false); }
            }, ttsDelay);
          })
          .catch(() => {});
      }
    };

    recognition.onend = () => {
      // Auto-restart so it keeps listening
      if (recognitionRef.current === recognition) {
        try { recognition.start(); } catch {}
      }
    };

    recognition.onerror = (e) => {
      if (e.error === "not-allowed") {
        setWakeWordEnabled(false);
        setWakeWordListening(false);
      }
    };

    try {
      recognition.start();
      setWakeWordListening(true);
    } catch {}

    return () => {
      recognitionRef.current = null;
      recognition.onend = null;
      try { recognition.stop(); } catch {}
      setWakeWordListening(false);
    };
  }, [wakeWordEnabled, ttsEnabled]);

  async function sendMessage() {
    const trimmed = input.trim();
    if (!trimmed || loading) return;

    // ── Kill switch ──────────────────────────────────────────
    const lower = trimmed.toLowerCase();
    if (["chibuike kill mr black", "chibuike kill mr. black", "chibuike kill black"].some(p => lower.includes(p))) {
      setMessages(prev => [...prev,
        { role: "user", content: trimmed, streaming: false, meta: null },
        { role: "assistant", content: "Kill switch activated. Mr. Black going offline. Goodbye.", streaming: false,
          meta: { agent: "black", task_type: "shutdown", memory_used: false, policy_verdict: "auto_approved" } },
      ]);
      setInput("");
      setWakeWordEnabled(false);
      fetch(`${BASE}/api/shutdown`, { method: "POST", headers: apiHeaders() }).catch(() => {});
      return;
    }

    setMessages(prev => [...prev, { role: "user", content: trimmed, streaming: false, meta: null }]);
    setInput("");
    setLoading(true);
    setMessages(prev => [...prev, { role: "assistant", content: "", streaming: true, meta: null }]);

    try {
      const response = await fetch(`${BASE}/api/chat/stream`, {
        method: "POST",
        headers: apiHeaders(),
        body: JSON.stringify({ message: trimmed }),
      });

      if (!response.ok) throw new Error(`HTTP ${response.status}`);

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const parts = buffer.split("\n\n");

        for (let i = 0; i < parts.length - 1; i++) {
          const part = parts[i].trim();
          if (!part.startsWith("data: ")) continue;
          let event;
          try { event = JSON.parse(part.slice(6)); } catch { continue; }

          if (event.type === "token") {
            setMessages(prev => {
              const msgs = [...prev];
              const last = msgs[msgs.length - 1];
              if (last?.streaming) msgs[msgs.length - 1] = { ...last, content: last.content + event.content };
              return msgs;
            });
          } else if (event.type === "done") {
            setMessages(prev => {
              const msgs = [...prev];
              const last = msgs[msgs.length - 1];
              if (last?.streaming) {
                if (ttsEnabled && last.content) {
                  fetch(`${BASE}/api/voice/speak`, {
                    method: "POST", headers: apiHeaders(),
                    body: JSON.stringify({ text: last.content.slice(0, 600) }),
                  }).catch(() => {});
                }
                msgs[msgs.length - 1] = {
                  ...last, streaming: false,
                  meta: { agent: event.agent, task_type: event.task_type, memory_used: event.memory_used, policy_verdict: event.policy_verdict, inference_provider: event.inference_provider },
                };
              }
              return msgs;
            });
          } else if (event.type === "fact_check") {
            setMessages(prev => {
              const msgs = [...prev];
              const last = msgs[msgs.length - 1];
              if (last?.role === "assistant") {
                msgs[msgs.length - 1] = { ...last, factCheck: { verdict: event.verdict, flags: event.flags || [], confidence: event.confidence } };
              }
              return msgs;
            });
          } else if (["blocked", "pending_approval", "error"].includes(event.type)) {
            setMessages(prev => {
              const msgs = [...prev];
              const last = msgs[msgs.length - 1];
              if (last?.streaming) msgs[msgs.length - 1] = {
                ...last,
                content: event.reply || event.content || "Unknown error",
                streaming: false,
                meta: { agent: event.agent || "black", task_type: event.task_type || event.type, memory_used: false, policy_verdict: event.policy_verdict || event.type },
              };
              return msgs;
            });
            if (event.type === "pending_approval") fetchApprovals();
          }
        }
        buffer = parts[parts.length - 1];
      }
    } catch (error) {
      setMessages(prev => {
        const msgs = [...prev];
        const last = msgs[msgs.length - 1];
        if (last?.streaming) msgs[msgs.length - 1] = {
          ...last,
          content: `Request failed: ${error.message}`,
          streaming: false,
          meta: { agent: "error", task_type: "error", memory_used: false, policy_verdict: null },
        };
        return msgs;
      });
    } finally {
      setLoading(false);
    }
  }

  function handleKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(); }
  }

  function togglePanel(panel) {
    if (panel === "system") {
      setShowSystem(v => !v);
      setShowApprovals(false);
    } else {
      setShowApprovals(v => !v);
      setShowSystem(false);
    }
  }

  function openGuide() { setShowGuide(true); }

  async function startRecording() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      audioChunksRef.current = [];
      const mr = new MediaRecorder(stream);
      mr.ondataavailable = e => { if (e.data.size > 0) audioChunksRef.current.push(e.data); };
      mr.start();
      mediaRecorderRef.current = mr;
      setRecording(true);
    } catch {
      alert("Microphone access denied.");
    }
  }

  async function stopRecording() {
    const mr = mediaRecorderRef.current;
    if (!mr) return;
    setRecording(false);
    setTranscribing(true);
    await new Promise(resolve => {
      mr.onstop = resolve;
      mr.stop();
      mr.stream.getTracks().forEach(t => t.stop());
    });
    try {
      const blob = new Blob(audioChunksRef.current, { type: "audio/webm" });
      const form = new FormData();
      form.append("audio", blob, "recording.webm");
      const headers = API_KEY ? { "X-BLACK-API-KEY": API_KEY } : {};
      const res = await fetch(`${BASE}/api/voice/transcribe`, { method: "POST", headers, body: form });
      if (res.ok) {
        const { text } = await res.json();
        if (text) setInput(text);
      }
    } catch {}
    setTranscribing(false);
  }

  const pendingCount = approvals.filter(r => r.status === "pending").length;

  return (
    <>
      <style>{`
        @keyframes blink { 0%,100%{opacity:1}50%{opacity:0} }
        @keyframes pulse-red { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:0.5;transform:scale(1.4)} }
        .cursor{display:inline-block;width:2px;height:1em;background:#a1a1aa;margin-left:2px;vertical-align:text-bottom;animation:blink 1s step-start infinite}
        *{box-sizing:border-box} body{margin:0}
        ::-webkit-scrollbar{width:5px} ::-webkit-scrollbar-track{background:transparent} ::-webkit-scrollbar-thumb{background:#2d2f36;border-radius:3px}
      `}</style>

      <div style={{ minHeight: "100vh", background: "#0b0b0c", color: "#f5f5f5", fontFamily: "'Inter',Arial,sans-serif", display: "flex", justifyContent: "center", padding: 24 }}>
        <div style={{ width: "100%", maxWidth: 960, display: "flex", flexDirection: "column", height: "92vh", background: "#151518", border: "1px solid #2a2a31", borderRadius: 18, overflow: "hidden", boxShadow: "0 10px 30px rgba(0,0,0,0.4)" }}>

          {/* Header */}
          <div style={{ padding: "16px 22px", borderBottom: "1px solid #2a2a31", background: "#111114", display: "flex", alignItems: "center", justifyContent: "space-between", flexShrink: 0 }}>
            <div>
              <h1 style={{ margin: 0, fontSize: 19, fontWeight: 700, letterSpacing: "0.08em" }}>Mr.Black</h1>
              <p style={{ margin: "3px 0 0", color: "#52525b", fontSize: 12 }}>v1.0 · Local-first · Single-owner</p>
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
              {loading && (
                <div style={{ display: "flex", alignItems: "center", gap: 6, color: "#52525b", fontSize: 12 }}>
                  <span style={{ width: 6, height: 6, borderRadius: "50%", background: "#22c55e", display: "inline-block", animation: "blink 1.2s step-start infinite" }} />
                  processing
                </div>
              )}
              {commandListening && (
                <span style={{ fontSize: 11, color: "#ef4444", fontWeight: 600, display: "flex", alignItems: "center", gap: 5, padding: "4px 10px", border: "1px solid #7f1d1d", borderRadius: 8, background: "rgba(239,68,68,0.08)" }}>
                  <span style={{ width: 6, height: 6, borderRadius: "50%", background: "#ef4444", display: "inline-block", animation: "pulse-red 1s ease-in-out infinite", flexShrink: 0 }} />
                  Listening…
                </span>
              )}
              <button
                onClick={() => setWakeWordEnabled(v => !v)}
                title={wakeWordEnabled ? "Wake word active — click to disable" : "Enable wake word (Hey Mr.Black)"}
                style={{ background: wakeWordEnabled ? "rgba(200,160,40,0.12)" : "none", color: wakeWordEnabled ? "#c8a028" : "#52525b", border: `1px solid ${wakeWordEnabled ? "rgba(200,160,40,0.4)" : "#2d2f36"}`, borderRadius: 8, padding: "6px 12px", fontSize: 12, fontWeight: 600, cursor: "pointer", display: "flex", alignItems: "center", gap: 6, transition: "all 0.2s" }}>
                {wakeWordListening && (
                  <span style={{ width: 6, height: 6, borderRadius: "50%", background: "#c8a028", display: "inline-block", animation: "blink 1.4s step-start infinite", flexShrink: 0 }} />
                )}
                ◎ Wake
              </button>
              <button onClick={() => setShowBrief(true)}
                style={{ background: "none", color: "#52525b", border: "1px solid #2d2f36", borderRadius: 8, padding: "6px 12px", fontSize: 12, fontWeight: 600, cursor: "pointer" }}
                title="Daily Brief">☀ Brief</button>
              <button onClick={openGuide}
                style={{ background: "none", color: "#52525b", border: "1px solid #2d2f36", borderRadius: 8, padding: "6px 11px", fontSize: 13, fontWeight: 700, cursor: "pointer", lineHeight: 1 }}
                title="How to use Mr.Black">?</button>
              <button
                onClick={() => togglePanel("system")}
                style={{ background: showSystem ? "#1c1d22" : "none", color: showSystem ? "#f5f5f5" : "#52525b", border: "1px solid #2d2f36", borderRadius: 8, padding: "6px 12px", fontSize: 12, fontWeight: 600, cursor: "pointer" }}>
                ⊞ System
              </button>
              <button
                onClick={() => { togglePanel("approvals"); if (!showApprovals) fetchApprovals(); }}
                style={{ background: pendingCount > 0 ? "#713f12" : "#1c1d22", color: pendingCount > 0 ? "#fbbf24" : "#52525b", border: `1px solid ${pendingCount > 0 ? "#92400e" : "#2d2f36"}`, borderRadius: 8, padding: "6px 12px", fontSize: 12, fontWeight: 600, cursor: "pointer", display: "flex", alignItems: "center", gap: 6 }}>
                ⚑ Approvals{pendingCount > 0 ? ` (${pendingCount})` : ""}
              </button>
            </div>
          </div>

          {/* System Panel */}
          {showSystem && <SystemPanel />}

          {/* Approvals Panel */}
          {showApprovals && (
            <div style={{ borderBottom: "1px solid #2a2a31", background: "#0f1012", padding: "12px 16px", flexShrink: 0, maxHeight: 300, overflowY: "auto" }}>
              <div style={{ fontSize: 11, color: "#52525b", marginBottom: 10, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <span style={{ fontWeight: 600, letterSpacing: "0.08em" }}>ACTIVE APPROVALS</span>
                <button onClick={fetchApprovals} style={{ background: "none", border: "none", color: "#52525b", cursor: "pointer", fontSize: 12 }}>↻ refresh</button>
              </div>
              {approvals.length === 0 ? (
                <div style={{ color: "#3f3f46", fontSize: 13, textAlign: "center", padding: "14px 0" }}>No active approvals</div>
              ) : (
                <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                  {approvals.map(a => (
                    <ApprovalCard key={a.id} record={a} onResolve={fetchApprovals} />
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Messages */}
          <div style={{ flex: 1, overflowY: "auto", padding: 18, display: "flex", flexDirection: "column", gap: 12, background: "#0f1012" }}>
            {messages.map((msg, i) => {
              const isUser = msg.role === "user";
              const verdict = msg.meta?.policy_verdict;
              const isBlocked = verdict === "blocked";
              const isPending = verdict === "pending_approval";

              return (
                <div key={i} style={{ display: "flex", justifyContent: isUser ? "flex-end" : "flex-start" }}>
                  <div style={{
                    maxWidth: "78%",
                    background: isUser ? "#1d4ed8" : isBlocked ? "#2d1212" : isPending ? "#1c1a0d" : "#1c1d22",
                    color: "#fff",
                    padding: "12px 15px",
                    borderRadius: isUser ? "16px 16px 4px 16px" : "16px 16px 16px 4px",
                    whiteSpace: "pre-wrap",
                    lineHeight: 1.6,
                    border: isUser ? "none" : isBlocked ? "1px solid #7f1d1d" : isPending ? "1px solid #713f12" : "1px solid #2d2f36",
                    wordBreak: "break-word",
                  }}>
                    <div style={{ fontSize: 15 }}>
                      {msg.streaming && !msg.content
                        ? <span style={{ color: "#52525b", fontStyle: "italic" }}>thinking…</span>
                        : msg.content}
                      {msg.streaming && msg.content && <span className="cursor" />}
                    </div>
                    {msg.meta && (
                      <div style={{ marginTop: 9, paddingTop: 7, borderTop: "1px solid rgba(255,255,255,0.06)", fontSize: 11, color: "#3f3f46", display: "flex", gap: 10, flexWrap: "wrap" }}>
                        <span>agent: <span style={{ color: "#52525b" }}>{msg.meta.agent}</span></span>
                        <span>task: <span style={{ color: "#52525b" }}>{msg.meta.task_type}</span></span>
                        <span>memory: <span style={{ color: "#52525b" }}>{msg.meta.memory_used ? "active" : "none"}</span></span>
                        {msg.meta.inference_provider && msg.meta.inference_provider !== "none" && (
                          <span style={{ color: msg.meta.inference_provider === "openrouter" ? "#22c55e" : msg.meta.inference_provider === "groq" ? "#60a5fa" : msg.meta.inference_provider === "perplexity" ? "#c8a028" : msg.meta.inference_provider === "cloud" ? "#818cf8" : "#3f3f46" }}>
                            {msg.meta.inference_provider === "openrouter" ? "◉ openrouter" : msg.meta.inference_provider === "groq" ? "◉ groq" : msg.meta.inference_provider === "perplexity" ? "◉ perplexity" : msg.meta.inference_provider === "cloud" ? "☁ cloud" : "⬡ local"}
                          </span>
                        )}
                        {msg.factCheck && (
                          <span title={msg.factCheck.flags?.length ? msg.factCheck.flags.join("\n") : "No issues detected"} style={{
                            color: msg.factCheck.verdict === "CLEAN" ? "#22c55e" : msg.factCheck.verdict === "SUSPECT" ? "#f59e0b" : "#ef4444",
                            fontWeight: 600, cursor: msg.factCheck.flags?.length ? "help" : "default",
                          }}>
                            {msg.factCheck.verdict === "CLEAN" ? "● verified" : msg.factCheck.verdict === "SUSPECT" ? "◐ suspect" : "○ flagged"}
                          </span>
                        )}
                        {VERDICT_LABEL[verdict] && (
                          <span style={{ color: isBlocked ? "#ef4444" : "#f59e0b", fontWeight: 600 }}>⚑ {VERDICT_LABEL[verdict]}</span>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
            <div ref={bottomRef} />
          </div>

          {/* Input */}
          <div style={{ borderTop: "1px solid #2a2a31", background: "#111114", padding: "14px 18px", flexShrink: 0 }}>
            <div style={{ display: "flex", gap: 10, alignItems: "flex-end" }}>
              <textarea
                ref={inputRef}
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder={transcribing ? "Transcribing…" : "Message Mr.Black…"}
                rows={3}
                disabled={loading || transcribing}
                style={{ flex: 1, background: "#18191e", color: "#f5f5f5", border: "1px solid #2d2f36", borderRadius: 12, padding: "12px 14px", fontSize: 15, resize: "none", outline: "none", fontFamily: "inherit", lineHeight: 1.5, opacity: (loading || transcribing) ? 0.6 : 1 }}
              />
              <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                {voiceReady && (
                  <button
                    onClick={recording ? stopRecording : startRecording}
                    disabled={loading || transcribing}
                    title={recording ? "Stop recording" : "Start voice input"}
                    style={{ background: recording ? "#7f1d1d" : "#1c1d22", color: recording ? "#fca5a5" : "#52525b", border: `1px solid ${recording ? "#dc2626" : "#2d2f36"}`, borderRadius: 10, padding: "8px 12px", fontSize: 16, cursor: "pointer", animation: recording ? "blink 1.2s step-start infinite" : "none" }}>
                    {transcribing ? "⌛" : recording ? "⏹" : "🎙"}
                  </button>
                )}
                <button
                  onClick={() => setTtsEnabled(v => !v)}
                  title={ttsEnabled ? "TTS on — click to disable" : "TTS off — click to enable"}
                  style={{ background: ttsEnabled ? "#14532d" : "#1c1d22", color: ttsEnabled ? "#86efac" : "#3f3f46", border: `1px solid ${ttsEnabled ? "#15803d" : "#2d2f36"}`, borderRadius: 10, padding: "8px 12px", fontSize: 14, cursor: "pointer" }}>
                  {ttsEnabled ? "🔊" : "🔇"}
                </button>
                <button
                  onClick={sendMessage}
                  disabled={loading}
                  style={{ background: loading ? "#27272a" : "#f5f5f5", color: loading ? "#52525b" : "#111114", border: "none", borderRadius: 10, padding: "10px 16px", fontSize: 15, fontWeight: 600, cursor: loading ? "not-allowed" : "pointer", whiteSpace: "nowrap" }}>
                  {loading ? "…" : "Send"}
                </button>
              </div>
            </div>
            <p style={{ margin: "7px 0 0", fontSize: 11, color: "#27272a", textAlign: "center" }}>Enter to send · Shift+Enter for new line{voiceReady ? " · 🎙 voice ready" : ""}</p>
          </div>

        </div>
      </div>
      {showGuide && <GuidePanel onClose={() => setShowGuide(false)} />}
      {showBrief && <BriefPanel onClose={() => setShowBrief(false)} />}
    </>
  );
}
