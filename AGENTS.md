# AGENTS.md

## Purpose

This repository is for building **BLACK**, a private, local-first AI operating system for a single owner.

BLACK is not being built as a generic chatbot. It is being built as a guided command system for:
- business and commerce intelligence
- market and investment analysis
- financial stewardship
- memory-aware workflow support
- approval-gated action execution

All work in this repository must support that direction.

---

## Project Reality

BLACK is currently in **Phase 1**.

Phase 1 means:
- single-owner only
- local-first development
- no unnecessary complexity
- modular architecture
- migration-friendly implementation
- stable working foundation before expansion

This repo is not a greenfield fantasy project. It is the continuation of earlier work that came from a more monolithic Jarvis-style codebase and is now being rebuilt in a cleaner, more modular form.

---

## Core Rules

### 1. Preserve the real objective
Every change should support BLACK as a serious operating system for the owner, not as a toy assistant or generic AI chat app.

### 2. Prefer modularity
Avoid large monolithic files when a cleaner split is reasonable.  
Prefer clear boundaries between:
- frontend views
- frontend hooks
- frontend API utilities
- backend routers
- backend services
- backend models
- backend orchestration logic

### 3. Do not over-engineer early
Phase 1 is about a strong working core.  
Do not add unnecessary abstraction, infrastructure, or enterprise complexity before the current foundation is stable.

### 4. Keep migration practical
When migrating from older code, extract useful logic carefully.  
Do not blindly copy over monolithic structure, dead code, naming drift, or unnecessary redundancy.

### 5. Preserve security mindset
BLACK is intended to become highly secure and eventually capable of stronger autonomy.  
Even in early phases, development should respect:
- approval gates
- owner control
- minimal exposure
- auditable actions
- future authentication and authorization
- safe handling of memory and sensitive data

### 6. Ask before assuming
When a major architectural choice is unclear, ask clarifying questions before implementing large changes.

---

## Current Phase 1 Priorities

The immediate priorities are:

1. Stabilize the backend runtime.
2. Keep the frontend moving toward a clean operator-console structure.
3. Verify memory, approvals, audit, and chat flows.
4. Reduce redundancy.
5. Maintain a structure that can support specialist agents later.
6. Avoid premature Phase 2 work before Phase 1 is trustworthy.

---

## Development Guidance

### Frontend guidance
The frontend should become a focused operator console, not a cluttered multi-purpose dashboard.

Prefer:
- an app-shell structure
- modular views
- reusable UI sections
- centralized API access
- minimal duplication
- clear status and approval visibility

Avoid:
- giant single-file React components
- scattered fetch logic
- duplicated state logic
- UI complexity that hides the core workflows

### Backend guidance
The backend should act as the system brain and control layer.

Prefer:
- slim entrypoints
- modular routers
- separated service logic
- clean persistence boundaries
- auditable action flow
- memory and approval handling as first-class system functions

Avoid:
- returning to one giant `main.py`
- mixing routing, persistence, inference, and scheduling logic in one place
- adding tools or integrations before the core flow is stable

---

## What Good Work Looks Like

Good work in this repo usually has these traits:
- small, clear, testable changes
- minimal redundancy
- practical architecture improvements
- copy-paste-ready implementation guidance
- stable incremental progress
- preservation of working behavior while improving structure

---

## What to Avoid

Avoid the following unless explicitly required:
- giant rewrites
- speculative abstractions
- placeholder architecture with no working path
- generic AI assistant patterns that do not fit BLACK
- adding broad integrations too early
- bloated frameworks or unnecessary dependencies
- mixing old Jarvis naming with BLACK naming without a clear migration reason

---

## Long-Term Direction

After Phase 1 is stable, BLACK may expand into:
- specialist agents
- external integrations
- stronger automation
- higher-trust execution paths
- more advanced security layers
- scalable production infrastructure

But none of that should compromise the current mission:
build a stable, modular, owner-controlled BLACK core first.

---

## Contributor Rule

Any assistant, developer, or future contributor working in this repo should:
- respect the current project phase
- optimize for clarity and maintainability
- reduce waste and redundancy
- keep recommendations practical
- prefer staged implementation over sweeping rewrites
- align every change with the real BLACK vision