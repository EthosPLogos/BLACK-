# ADR 0001: Black project migration directive

## Status

Accepted

## Date

2026-05-29

## Context

The prior application existed in a Jarvis-era state with a monolithic FastAPI backend and a large React frontend containing mixed concerns. The old codebase included Jarvis branding, tightly coupled logic, duplicated state and command behavior across frontend and backend, and server-side proxy behavior tied to a specific provider approach.

A new direction has been chosen for the project under the name Black.

## Decision

The project will move forward as Black, a secure, scalable, Christ-centered AI operating system and command hub.

The migration direction is defined by the following decisions:

1. The project is treated as a refactor and migration effort, not as an imagined completed platform
2. Black begins as one orchestrator-first system
3. Specialist agents are deferred until clearly justified
4. Provider abstraction is a core architectural requirement
5. Backend and frontend concerns should be more cleanly separated
6. Redundant command/state logic should be reduced
7. OpenJarvis readiness is a desired architectural direction
8. Claude is allowed as part of the provider strategy
9. Architecture should be production-minded, secure, modular, and maintainable

## Consequences

### Positive

- clearer architecture decisions from the start
- less confusion about present state versus future goals
- better maintainability
- stronger alignment between naming, mission, and implementation
- lower risk of premature overengineering

### Trade-offs

- migration may take more disciplined incremental work
- some short-term feature velocity may be traded for cleaner structure
- specialist capabilities may arrive later than they would in a less disciplined architecture

## Implementation guidance

Near-term work should focus on:
- repository structure
- architecture documentation
- backend modularization
- frontend modularization
- provider abstraction
- logging and auditability
- clean naming and boundary decisions

The project should avoid:
- pretending the current system is already fully modular
- premature multi-agent expansion
- feature sprawl before architecture stabilization