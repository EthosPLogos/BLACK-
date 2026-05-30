# ADR 0001: BLACK Project Directive

- **Status:** Accepted
- **Date:** 2026-05-30

## Context

BLACK is being built as a private, local-first AI operating system for a single owner. The project is a continuation of earlier work that existed in a more monolithic Jarvis-style codebase.

That earlier implementation contained useful logic, working ideas, and real product direction, but it also carried structural problems:
- oversized files
- mixed responsibilities
- harder maintenance
- reduced clarity
- weaker long-term scalability

A fresh repository has been created so BLACK can continue in a cleaner and more disciplined form.

---

## Decision

BLACK will be developed as a **phased, modular, migration-friendly system**.

The project will not be rebuilt through one massive rewrite. It will move in controlled stages, preserving useful work while improving structure and reducing redundancy.

### The directive is:

1. Build BLACK as a **single-owner, local-first** system first.
2. Keep the implementation **modular** across frontend, backend, and documentation.
3. Extract useful logic from earlier work selectively rather than copying monolithic structure wholesale.
4. Prioritize a stable working foundation before advanced autonomy or broad integrations.
5. Preserve strong control features such as approvals, audit visibility, and owner authority from the beginning.
6. Use phased progress so the system can keep working while architecture improves.

---

## Phase 1 Meaning

Phase 1 is defined as the construction of the BLACK core.

This includes:
- React/Vite frontend
- FastAPI backend
- persistent memory
- approvals workflow
- audit visibility
- local-first inference with cloud fallback
- learning trace foundation
- modular project structure

This phase does **not** include:
- multi-user support
- open public deployment
- aggressive external integrations
- broad autonomous execution
- premature enterprise infrastructure
- Phase 2 specialist agent sprawl

---

## Consequences

### Positive consequences
- The codebase stays easier to maintain.
- Frontend and backend can evolve independently with cleaner boundaries.
- Migration from older work remains practical.
- The project is less likely to collapse under its own complexity early.
- The owner keeps clear authority over approvals, actions, and system direction.

### Tradeoffs
- Progress may feel slower than doing a giant rewrite.
- Some legacy ideas will need to be reworked rather than copied directly.
- Documentation and structure must be maintained intentionally.
- Certain advanced capabilities must wait until the core is stable.

---

## Implementation Notes

The repository should reflect this directive:
- `README.md` explains the project and current Phase 1 state.
- `ARCHITECTURE.md` explains the system structure and direction.
- `AGENTS.md` explains how contributors and assistants should operate within the repo.
- `docs/adr/` records important architectural decisions over time.

The frontend should move toward an operator-console structure.  
The backend should move toward modular routers, services, and orchestration layers.  
No major change should violate the rule of building a stable owner-controlled core first.

---

## Current Standing

As of this ADR, BLACK is in active Phase 1 development. The frontend direction has already moved toward a cleaner operator-console architecture, and the overall project direction remains modular, local-first, and owner-controlled.

This ADR establishes that direction as the official baseline for future work.