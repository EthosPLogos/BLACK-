import React, { useCallback, useEffect, useRef, useState } from "react";

const BASE = "http://127.0.0.1:8001";
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

// ─── System Panel ──────────────────────────────────────────────────────────────

function SystemPanel() {
  const [tab, setTab] = useState("status");
  const [sysStatus, setSysStatus] = useState(null);
  const [memData, setMemData] = useState(null);
  const [auditLog, setAuditLog] = useState([]);
  const [userFields, setUserFields] = useState({});
  const [newFact, setNewFact] = useState("");
  const [savingField, setSavingField] = useState(null);
  const [loading, setLoading] = useState(false);

  const load = useCallback(async (t) => {
    setLoading(true);
    try {
      if (t === "status") {
        const r = await fetch(`${BASE}/api/status`, { headers: fHeaders() });
        if (r.ok) setSysStatus(await r.json());
      } else if (t === "memory") {
        const r = await fetch(`${BASE}/api/memory`, { headers: fHeaders() });
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
      } else if (t === "audit") {
        const r = await fetch(`${BASE}/api/audit?limit=30`, { headers: fHeaders() });
        if (r.ok) {
          const d = await r.json();
          setAuditLog([...d.records].reverse());
        }
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
        {["status", "memory", "audit"].map(t => (
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
                {
                  label: "OLLAMA",
                  dot: sysStatus.ollama?.status,
                  detail: [
                    sysStatus.ollama?.latency_ms != null ? `${sysStatus.ollama.latency_ms}ms` : null,
                    sysStatus.ollama?.model,
                    sysStatus.ollama?.error ? sysStatus.ollama.error.slice(0, 60) : null,
                  ].filter(Boolean).join(" · "),
                },
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
              ].map(({ label, dot, detail }) => (
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
                  value={newFact} placeholder="Add a fact BLACK should know…"
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
      content: "BLACK online. Phase 2 active.",
      streaming: false,
      meta: { agent: "system", task_type: "startup", memory_used: false, policy_verdict: "auto_approved" },
    },
  ]);
  const [loading, setLoading] = useState(false);
  const [approvals, setApprovals] = useState([]);
  const [showApprovals, setShowApprovals] = useState(false);
  const [showSystem, setShowSystem] = useState(false);
  const bottomRef = useRef(null);

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
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function sendMessage() {
    const trimmed = input.trim();
    if (!trimmed || loading) return;

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
              if (last?.streaming) msgs[msgs.length - 1] = {
                ...last, streaming: false,
                meta: { agent: event.agent, task_type: event.task_type, memory_used: event.memory_used, policy_verdict: event.policy_verdict, inference_provider: event.inference_provider },
              };
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

  const pendingCount = approvals.filter(r => r.status === "pending").length;

  return (
    <>
      <style>{`
        @keyframes blink { 0%,100%{opacity:1}50%{opacity:0} }
        .cursor{display:inline-block;width:2px;height:1em;background:#a1a1aa;margin-left:2px;vertical-align:text-bottom;animation:blink 1s step-start infinite}
        *{box-sizing:border-box} body{margin:0}
        ::-webkit-scrollbar{width:5px} ::-webkit-scrollbar-track{background:transparent} ::-webkit-scrollbar-thumb{background:#2d2f36;border-radius:3px}
      `}</style>

      <div style={{ minHeight: "100vh", background: "#0b0b0c", color: "#f5f5f5", fontFamily: "'Inter',Arial,sans-serif", display: "flex", justifyContent: "center", padding: 24 }}>
        <div style={{ width: "100%", maxWidth: 960, display: "flex", flexDirection: "column", height: "92vh", background: "#151518", border: "1px solid #2a2a31", borderRadius: 18, overflow: "hidden", boxShadow: "0 10px 30px rgba(0,0,0,0.4)" }}>

          {/* Header */}
          <div style={{ padding: "16px 22px", borderBottom: "1px solid #2a2a31", background: "#111114", display: "flex", alignItems: "center", justifyContent: "space-between", flexShrink: 0 }}>
            <div>
              <h1 style={{ margin: 0, fontSize: 19, fontWeight: 700, letterSpacing: "0.08em" }}>BLACK</h1>
              <p style={{ margin: "3px 0 0", color: "#52525b", fontSize: 12 }}>Local-first · Phase 2 · Single-owner</p>
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
              {loading && (
                <div style={{ display: "flex", alignItems: "center", gap: 6, color: "#52525b", fontSize: 12 }}>
                  <span style={{ width: 6, height: 6, borderRadius: "50%", background: "#22c55e", display: "inline-block", animation: "blink 1.2s step-start infinite" }} />
                  processing
                </div>
              )}
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
                      {msg.content}
                      {msg.streaming && <span className="cursor" />}
                    </div>
                    {msg.meta && (
                      <div style={{ marginTop: 9, paddingTop: 7, borderTop: "1px solid rgba(255,255,255,0.06)", fontSize: 11, color: "#3f3f46", display: "flex", gap: 10, flexWrap: "wrap" }}>
                        <span>agent: <span style={{ color: "#52525b" }}>{msg.meta.agent}</span></span>
                        <span>task: <span style={{ color: "#52525b" }}>{msg.meta.task_type}</span></span>
                        <span>memory: <span style={{ color: "#52525b" }}>{msg.meta.memory_used ? "active" : "none"}</span></span>
                        {msg.meta.inference_provider && msg.meta.inference_provider !== "none" && (
                          <span style={{ color: msg.meta.inference_provider === "cloud" ? "#818cf8" : "#3f3f46" }}>
                            {msg.meta.inference_provider === "cloud" ? "☁ cloud" : "⬡ local"}
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
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Message BLACK…"
                rows={3}
                disabled={loading}
                style={{ flex: 1, background: "#18191e", color: "#f5f5f5", border: "1px solid #2d2f36", borderRadius: 12, padding: "12px 14px", fontSize: 15, resize: "none", outline: "none", fontFamily: "inherit", lineHeight: 1.5, opacity: loading ? 0.6 : 1 }}
              />
              <button
                onClick={sendMessage}
                disabled={loading}
                style={{ background: loading ? "#27272a" : "#f5f5f5", color: loading ? "#52525b" : "#111114", border: "none", borderRadius: 12, padding: "12px 18px", fontSize: 15, fontWeight: 600, cursor: loading ? "not-allowed" : "pointer", whiteSpace: "nowrap" }}>
                {loading ? "…" : "Send"}
              </button>
            </div>
            <p style={{ margin: "7px 0 0", fontSize: 11, color: "#27272a", textAlign: "center" }}>Enter to send · Shift+Enter for new line</p>
          </div>

        </div>
      </div>
    </>
  );
}
