# BLACK Architecture

## Current State

BLACK is currently in **Phase 1** of development. The project is being rebuilt from the earlier Jarvis-style monolithic implementation into a more modular, maintainable architecture.

The current goal is not to redesign everything at once. The goal is to establish a stable core system that works locally, supports future expansion, and avoids unnecessary redundancy.

---

## Phase 1 Objective

Phase 1 focuses on building the core of BLACK as a **single-owner, local-first AI operating system** with the following capabilities:

- React/Vite frontend operator console
- FastAPI backend
- Persistent memory
- Approval-gated actions
- Audit logging
- Local-first model usage with cloud fallback
- Clean modular structure for future specialist agents

This phase is about creating a strong foundation before adding broader automation, integrations, or autonomy.

---

## Current Direction

The architecture is moving away from a monolithic design and toward a modular split between frontend, backend, and project documentation.

### Frontend
The frontend is evolving into an operator console with:
- Chat interface
- Memory management
- Approvals view
- Audit visibility
- System status view

The accepted frontend direction now includes:
- App-shell structure
- Modular views
- Centralized API handling
- Approval-count synchronization
- In-memory session handling for current Phase 1 usage

### Backend
The backend is responsible for:
- Chat orchestration
- Conversation persistence
- Memory storage and retrieval
- Approval workflows
- Audit trail generation
- Learning trace capture
- System health/status reporting

The backend should continue moving toward separated routers, services, models, and orchestration layers rather than returning to a single-file approach.

---

## System Shape

```text
BLACK
├── frontend/      # React/Vite operator console
├── backend/       # FastAPI backend and orchestration
├── docs/          # Project notes, ADRs, status, planning
├── README.md      # Project overview and setup
├── ARCHITECTURE.md
└── AGENTS.md
```

---

## Functional Flow

1. User interacts through the BLACK frontend operator console.
2. Frontend sends requests to the FastAPI backend.
3. Backend loads memory, conversation context, and current mode.
4. Backend routes inference through local-first execution, with cloud fallback if needed.
5. Backend stores conversation history, learning traces, and approval events.
6. Frontend reflects status, approvals, memory, and audit information back to the user.

---

## Current Priorities

The current priorities for Phase 1 are:

1. Stabilize backend runtime behavior.
2. Verify frontend and backend integration.
3. Confirm memory, approvals, audit, and chat flows work end to end.
4. Keep the codebase modular and migration-friendly.
5. Avoid premature expansion into Phase 2 features before the core is stable.

---

## Not Yet in Scope

The following are **not** the current focus of Phase 1:

- Multi-user support
- Public deployment
- Full autonomous action execution
- Broad external integrations
- Phase 2 specialist agents
- Commercial hardening

Those can come later after the core system is stable and trustworthy.

---

## Summary

BLACK is no longer being treated as an abstract concept or a greenfield prototype. It is an active Phase 1 build moving from an earlier monolithic base into a modular local-first AI operating system. The current architectural strategy is to stabilize the core first, then expand in controlled phases.