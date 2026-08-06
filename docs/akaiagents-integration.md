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
maximum of 200. Keyword project searches use a short public cache. Maintenance,
observability and refresh routes are protected and are outside this project's
read-only scope.

## Confirmed public projection shapes

### Project list

The release projection tests show a response containing:

- `items`
- `page_ids`
- `project_ids`
- `total`
- `offset`
- `limit`
- `has_more`
- `ready_total`
- `public_total`
- `snapshot_id`

Chinese list and keyword search read from the materialized public projection
instead of scanning the internal catalog.

### Project detail release artifact

`github_ai_radar_public_details.py` declares
`githubai.public_detail.v4`. Its immutable artifact contains:

- `project_id`
- `snapshot_id`
- locale-specific reviewed payloads in `locales`
- locale-specific public final project items in `items`

The materialized public item includes compact project facts, related public
cards and an `interpretation` payload. The reviewed detail includes a
`coverage_level` and public-safe `transparency` generated from the matching
publication.

This is the preferred source for `get_project_facts`; the adapter must still
select which individual fields qualify as verified facts.

### Selector

The retrieval evaluation invokes `POST /selector` with a natural-language
query, locale and optional retrieval diagnostics. The public smoke contract
allows high-level fields including:

- `result_kind`, `resource_kind`, `items` and `skills`
- `constraints`, `requirements`, `assumptions` and clarification questions
- `evidence_status`, `notice` and `no_match_reason`
- `verified_answer`
- `solution`, `solution_blueprint`, `project_roles` and `gaps`
- `comparison`, `guidance` and `ranking`
- `near_matches`, `relaxation_options` and `relaxation_context`
- `catalog_status`, `retrieval_status` and degradation indicators

Near matches must remain outside formal recommendations, have exactly one
blocking constraint, and never leak internal evidence IDs, source hashes or
publication versions. A no-result response is valid only when the evidence index
is available or partial and an explicit verified no-match reason is present.

## Production adapter mapping

| M0 tool | Existing source | Adapter responsibility |
| --- | --- | --- |
| `search_ai_projects` | `POST /selector`, public project list | Convert explicit constraints, preserve no-match reasons, stable IDs and near-match boundaries. |
| `get_project_facts` | `GET /projects/{project_id}` | Project only current detail fields into the unified fact/evidence envelope. |
| `get_license_evidence` | Project detail transparency and public evidence fields | Return observed license material and time; never infer a missing license. |
| `compare_ai_projects` | Multiple same-snapshot project-detail reads; selector comparison when suitable | Build a matrix while keeping recommendations separate from facts. |
| `find_alternatives` | Selector alternatives/near matches plus project details | Verify every alternative and expose any relaxed constraint. |
| `compose_ai_stack` | Selector solution and project-role results plus project details | Orchestrate reads; label architecture and compatibility as recommendations. |

## Required fail-closed checks

Before production use, the adapter must verify:

1. project list and detail responses expose a non-empty matching `snapshot_id`;
2. all project records come from one current healthy public release or an
   explicitly compatible snapshot;
3. project IDs are stable and resolve to public records;
4. evidence URLs and observation times are present for fields presented as
   verified facts;
5. selector `evidence_status` is `available` or explicitly `partial` with a
   public notice;
6. missing or conflicting evidence becomes `unknowns`, not a guessed value;
7. near matches never enter the formal recommendation list automatically;
8. archived or non-public projects are not silently substituted;
9. internal fields such as source hashes, evidence IDs and publication versions
   are not exposed;
10. upstream errors preserve the last healthy result only when the upstream
    contract explicitly marks that result as safe stale data.

## Remaining M1 confirmations

The six public product tool names do not yet exist as one dedicated external API
contract. M0 therefore keeps a provider protocol and deterministic mock instead
of coupling directly to private Python modules.

Before implementing the live provider, confirm from representative production
responses:

- the exact location and shape of public transparency/evidence URLs;
- the observation time for each fact and the project repository update time;
- how `coverage_level` should map to public confidence;
- the license source, ambiguity state and missing-license representation;
- whether project detail HTTP responses expose `snapshot_id` directly alongside
  the final `item`;
- stable handling of explicit project identity aliases;
- cache and timeout behavior expected for anonymous external clients.

If any field is unavailable, document the smallest additive public API change
needed in `akaiagents`; do not import its private modules or modify its main
branch from this repository.
