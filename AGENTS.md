# AGENTS.md

## Project mission

AI Workstation Open Source Intelligence provides Skills, MCP tools, SDKs and evaluations for researching, verifying, comparing and composing open-source AI projects.

## Development rules

- Main branch is the source of truth.
- Keep commits small and focused.
- Do not modify `akaiagents`; use it only as a reference implementation.
- Prefer documentation and contracts before production integrations.
- First release is read-only.

## Product boundaries

Separate:

1. Verified facts from sources.
2. Model-generated analysis and recommendations.
3. Unknown or unverified information.
4. Risks and limitations.

## First product capabilities

- open-source-project-research
- open-source-project-comparison
- open-source-stack-planner

## MCP principles

- Explicit schemas.
- Read-only by default.
- Return evidence and timestamps where available.
- Never execute third-party repository code.
