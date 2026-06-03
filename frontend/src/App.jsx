import React, { useState } from "react";

export default function App() {
  const [input, setInput] = useState("");
  const [reply, setReply] = useState("");
  const [meta, setMeta] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function sendMessage() {
    if (!input.trim()) return;

    setLoading(true);
    setError("");
    setReply("");
    setMeta(null);

    try {
      const response = await fetch("http://127.0.0.1:8001/api/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          message: input
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const json = await response.json();
      setReply(json.reply);
      setMeta({
        agent: json.agent,
        task_type: json.task_type,
        memory_used: json.memory_used
      });
    } catch (err) {
      setError(`Request failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  }

  function handleKeyDown(event) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      sendMessage();
    }
  }

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "#f8f8f8",
        color: "#111",
        fontFamily: "Arial, sans-serif",
        padding: "40px"
      }}
    >
      <div
        style={{
          maxWidth: "900px",
          margin: "0 auto"
        }}
      >
        <h1 style={{ marginBottom: "8px" }}>BLACK</h1>
        <p style={{ marginTop: 0, color: "#444", marginBottom: "24px" }}>
          Local Phase 1 chat interface
        </p>

        <div
          style={{
            background: "#fff",
            border: "1px solid #ddd",
            borderRadius: "12px",
            padding: "20px",
            marginBottom: "20px"
          }}
        >
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Send a message to BLACK..."
            rows={5}
            style={{
              width: "100%",
              padding: "14px",
              fontSize: "16px",
              borderRadius: "8px",
              border: "1px solid #ccc",
              resize: "vertical",
              boxSizing: "border-box"
            }}
          />

          <button
            onClick={sendMessage}
            disabled={loading}
            style={{
              marginTop: "14px",
              background: loading ? "#999" : "#111",
              color: "#fff",
              border: "none",
              padding: "12px 18px",
              borderRadius: "8px",
              cursor: loading ? "not-allowed" : "pointer",
              fontSize: "15px"
            }}
          >
            {loading ? "Thinking..." : "Send"}
          </button>

          {error && (
            <p style={{ color: "crimson", marginTop: "14px" }}>
              {error}
            </p>
          )}
        </div>

        <div
          style={{
            background: "#fff",
            border: "1px solid #ddd",
            borderRadius: "12px",
            padding: "20px"
          }}
        >
          <h2 style={{ marginTop: 0 }}>Response</h2>

          {!reply && !loading && (
            <p style={{ color: "#666" }}>
              No response yet.
            </p>
          )}

          {loading && (
            <p style={{ color: "#666" }}>
              BLACK is thinking...
            </p>
          )}

          {reply && (
            <div
              style={{
                whiteSpace: "pre-wrap",
                lineHeight: "1.6",
                marginBottom: meta ? "20px" : 0
              }}
            >
              {reply}
            </div>
          )}

          {meta && (
            <pre
              style={{
                background: "#f4f4f4",
                padding: "16px",
                borderRadius: "8px",
                overflowX: "auto",
                marginBottom: 0
              }}
            >
              {JSON.stringify(meta, null, 2)}
            </pre>
          )}
        </div>
      </div>
    </div>
  );
}