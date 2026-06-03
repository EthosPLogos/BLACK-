# Black

Black is a secure, scalable, Christ-centered AI operating system and command hub focused on investment and market intelligence, online commerce execution, and disciplined decision support.

## Purpose

This repository is the clean restart of the previous Jarvis-era project. It is being built with an orchestrator-first architecture so the core assistant remains strong, modular, and maintainable before any specialist agent expansion.

## Mission

Black is being designed to support:
- Investment and market intelligence
- Online commerce execution and optimization
- Long-term decision support grounded in biblical stewardship, honesty, diligence, integrity, generosity, wisdom, and accountability

## Current status

This repository is the new Black baseline. The prior project existed as a Jarvis-era monolithic FastAPI backend and oversized React frontend, and this repo starts the migration into a cleaner architecture with stronger boundaries between backend, frontend, providers, orchestration, and documentation.

## Core principles

- Orchestrator-first before multi-agent expansion
- Modular architecture over monolithic growth
- Low redundancy between frontend and backend
- Provider abstraction instead of hard-wired model logic
- Production-minded design: logging, auditability, security, and maintainability
- OpenJarvis integration readiness where appropriate
- Local-first and on-device capability where appropriate

## Repository structure

```text
black/
├── backend/
├── frontend/
├── docs/
│   └── adr/
├── README.md
├── ARCHITECTURE.md
└── AGENTS.md
```

## Immediate goals

1. Define architecture clearly before feature expansion
2. Build a modular FastAPI backend structure
3. Build a cleaner React frontend structure
4. Reduce Jarvis-era duplication and tight coupling
5. Create a stable foundation for future provider and agent expansion

## Notes

This is not a greenfield product concept in the abstract. It is the intentional rebuild and migration path for a real project moving from Jarvis to Black.

## Project Update 

2026-05-30 — Phase 1 Project Update

BLACK remains in Phase 1 as a single-owner, local-first AI operating system focused on the core stack: React/Vite frontend, FastAPI backend, persistent memory, approvals, audit logging, and local/cloud inference routing.

Current project status:
- The new BLACK repository has replaced the old Jarvis-era working direction.
- The architecture is being rebuilt in a more modular form rather than continuing as a monolithic codebase.
- Phase 1 is active and focused on establishing a stable owner-console foundation before expanding features.

Completed progress so far:
- New BLACK repository initialized and connected to GitHub.
- Core project structure established for backend, frontend, and architecture documents.
- Project directive and architecture baseline created.
- Phase 1 direction confirmed as local-first, single-owner, and modular.
- Frontend refactor accepted into the Phase 1 project direction.
- Frontend structure now moves toward an app-shell/operator-console model with modular views, centralized API handling, approval-count synchronization, and in-memory session handling aligned with the current backend conversation model.

Current Phase 1 scope:
- React/Vite frontend for the operator console
- FastAPI backend with modular router direction
- Persistent memory system
- Approval-gated actions
- Audit visibility
- Learning trace foundation
- Local-first inference with cloud fallback when needed

What remains in Phase 1:
- Backend validation and cleanup
- End-to-end boot testing
- Runtime stabilization across frontend, backend, and inference services
- Verification that merged frontend behavior works cleanly against live backend endpoints

Summary:
BLACK has progressed from repo initialization into active Phase 1 system construction. The project now has a clearer modular direction, and the frontend merge improves the operator-console architecture. The next milestone is stabilization and validation, not expansion.