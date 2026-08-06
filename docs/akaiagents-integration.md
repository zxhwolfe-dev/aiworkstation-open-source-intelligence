# akaiagents Read-Only Integration Map

This document records the M0 analysis of `zxhwolfe-dev/akaiagents`. It is an
integration plan, not a request to change that repository.

## Relevant current public surfaces

The existing Radar implementation already exposes read-oriented FastAPI
surfaces under `/api/v1/ai/githubai`, including:

- `GET /overview`
- `GET /projects`
- `GET /projects/{project_id}`
- `GET /skills`
- `GET /skills/{skill_id}`
- `GET /skill-sources/{source_id}`
- `POST /selector`

The public-contract tests require ETags for overview, project lists, project
details and Skills. The project-list contract defaults to 24 rows and accepts a
maximum of 200. Maintenance and refresh routes are protected and are outside
this project's read-only scope.

The retrieval evaluation script invokes `POST /selector` with a natural-language
query, locale and optional retrieval diagnostics. Its result extraction already
handles ranked projects, Skills, verified answers, primary solutions,
alternatives and complementary projects.

## Production adapter mapping

| M0 tool | Existing source | Adapter responsibility |
| --- | --- | --- |
| `search_ai_projects` | `POST /selector`, public project list | Convert explicit constraints, preserve no-match reasons and stable IDs. |
| `get_project_facts` | `GET /projects/{project_id}` | Project only current public fields into the unified fact/evidence envelope. |
| `get_license_evidence` | Project detail and public evidence fields | Return observed license material and timestamp; never infer missing licenses. |
| `compare_ai_projects` | Multiple project-detail reads | Build one same-snapshot matrix; keep recommendations separate from facts. |
| `find_alternatives` | Selector alternative results plus project details | Verify every returned alternative against current constraints. |
| `compose_ai_stack` | Selector solution results plus project details | Orchestrate reads, then label architecture choices as recommendations. |

## Required fail-closed checks

Before production use, the adapter must verify:

1. all project records come from one current healthy public release or an
   explicitly compatible snapshot;
2. project IDs are stable and resolve to public records;
3. evidence URLs and observation times are present for fields presented as
   verified facts;
4. missing or conflicting evidence becomes `unknowns`, not a guessed value;
5. archived or non-public projects are not silently substituted;
6. upstream errors preserve the last healthy result only when the upstream
   contract explicitly marks that result as safe stale data.

## M0 integration gaps

The six public product tool names do not yet exist as a dedicated external API
contract. M0 therefore keeps a provider protocol and deterministic mock instead
of coupling directly to private Python modules.

Before M1 production integration, confirm the exact public response fields for:

- publication/snapshot identity;
- fact-level evidence references;
- observation and project-update timestamps;
- confidence or evidence coverage;
- explicit no-match and relaxed-constraint states;
- license source material and ambiguity.

If any field is unavailable, document the smallest additive public API change
needed in `akaiagents`; do not import its private modules or modify its main
branch from this repository.
