# Mr. Black

Mr. Black is a secure, local-first, Christ-centered AI operating system and command hub — built for one owner. Focused on investment and market intelligence, online commerce execution, and disciplined decision support grounded in biblical stewardship.

## Purpose

This repository is the clean rebuild of the previous Jarvis-era project. Mr. Black is built with an orchestrator-first architecture so the core assistant remains strong, modular, and maintainable before any specialist agent expansion.

## Mission

Mr. Black is designed to support:
- Investment and market intelligence
- Online commerce execution and optimization
- Long-term decision support grounded in biblical stewardship, honesty, diligence, integrity, generosity, wisdom, and accountability

## Current Status

Mr. Black is in **Phase 1** — active and operational as a single-owner, local-first AI operating system.

Phase 1 is complete and running:
- React/Vite operator console (chat, approvals, memory, audit, scheduler, integrations, backup)
- FastAPI backend with modular routers, services, and orchestration
- 14 specialist agents (Finance, Business, Researcher, Builder, Execution, Security, GRE, Science, Email, Job Search, Job Apply, Ecommerce, World Intel, Fact Checker/Verifier)
- Persistent memory system with encryption
- Approval-gated action execution
- Audit logging
- Local-first inference (Ollama) with cloud fallback (Groq, OpenRouter, Anthropic, Perplexity)
- Scheduled tasks with macOS notifications
- Personal integrations: Calendar, Reminders, Notes, Contacts, Files, Email (IMAP), Weather, Web Search
- Voice: Whisper STT + macOS TTS, wake word detection ("Hey Mr. Black")
- Kill switch: "Chibuike kill Mr. Black" — voice, chat, or `stop-black.command`

## Core Principles

- Orchestrator-first before multi-agent expansion
- Modular architecture over monolithic growth
- Low redundancy between frontend and backend
- Provider abstraction instead of hard-wired model logic
- Production-minded design: logging, auditability, security, and maintainability
- Local-first and on-device capability where appropriate
- Single-owner: no multi-user, no public deployment, no unnecessary exposure

## Repository Structure

```text
black/
├── backend/
│   ├── app/
│   │   ├── agents/          # 14 specialist agents
│   │   ├── api/             # Modular routers
│   │   ├── approvals/       # Approval gate
│   │   ├── audit/           # Audit logging
│   │   ├── execution/       # Sandboxed execution
│   │   ├── integrations/    # Calendar, email, weather, etc.
│   │   ├── memory/          # Persistent encrypted memory
│   │   ├── middleware/       # Auth, rate limiting, security headers
│   │   ├── orchestrator/    # Engine, router, context, chain
│   │   ├── policy/          # Policy engine and rules
│   │   ├── scheduler/       # Task scheduling and watchdog
│   │   ├── services/        # Inference clients and utilities
│   │   └── main.py
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── App.jsx          # Operator console
│       └── LandingPage.jsx
├── docs/
├── start-black.command      # Launch everything (Ollama + backend + frontend)
├── stop-black.command       # Kill switch
├── README.md
├── ARCHITECTURE.md
└── AGENTS.md
```

## Launch

Double-click **`start-black.command`** or click the **Mr. Black** app icon on your Desktop.

This starts Ollama, the FastAPI backend on `:8001`, and the Vite frontend on `:5173`, then opens the operator console in your browser.

**Kill switch:** Say or type `"Chibuike kill Mr. Black"`, or double-click `stop-black.command`.

## Phase 2 (Future)

After Phase 1 is stable and trustworthy, Mr. Black may expand into:
- Specialist agent expansion
- External service integrations
- Stronger automation and higher-trust execution
- Scalable production infrastructure

None of that compromises the current mission: a stable, modular, owner-controlled core first.

## Project Update

2026-07-30 — Phase 1 Complete

Mr. Black is fully operational as a local-first AI operating system. The system boots cleanly, all 14 agents route correctly, memory and approvals work end to end, and the operator console is live. The next milestone is Phase 1 stabilization — end-to-end testing, portability hardening, and runtime validation before any Phase 2 expansion.
