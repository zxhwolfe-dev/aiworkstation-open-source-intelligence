# akaiagents Read-Only Integration Map

This document records the current integration contract with
`zxhwolfe-dev/akaiagents`. That repository remains read-only from this project.

## Relevant public surfaces

The Radar implementation exposes read-oriented FastAPI surfaces under
`/api/v1/ai/githubai`, including:

- `GET /overview`
- `GET /projects`
- `GET /projects/{project_id}`
- `GET /skills`
- `GET /skills/{skill_id}`
- `GET /skill-sources/{source_id}`
- `POST /selector`

Maintenance, observability and refresh routes are outside this project's scope.

## Confirmed public projection shapes

### Project list

The public list/release projection includes fields such as:

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

The M1 provider requires non-empty snapshot identity before project facts can be
promoted to the verified result boundary.

### Project detail release artifact

`github_ai_radar_public_details.py` currently declares
`githubai.public_detail.v4`. Its immutable artifact contains:

- `project_id`
- `snapshot_id`
- locale-specific reviewed payloads in `locales`
- locale-specific public final project items in `items`

The final public item contains compact project facts plus `interpretation`. The
reviewed interpretation includes `coverage_level` and a public-safe
`transparency` object built from the matching validated publication.

The current public transparency implementation exposes:

- `content_level`
- `published_at`
- `source_updated_at`
- `quality_label`
- up to five direct `sources`

Each source currently exposes:

- `source_label`
- `source_path`
- `section_heading`
- `excerpt`

The public evidence builder validates source/evidence/quality artifacts against
the same source hash before producing this transparency projection. Direct
source labels include README, Release, License, repository metadata, project
manifest and manually verified material.

### Direct license evidence boundary

The distribution provider no longer treats a project-level `license` label by
itself as sufficient verified evidence.

For `get_license_evidence`:

1. the project/detail snapshot must pass the normal public-release checks;
2. the license value must not be an unknown sentinel;
3. `transparency.sources` must contain a direct `License` source with a public
   excerpt;
4. the adapter derives the corresponding official GitHub URL from stable
   `owner/repository` identity and the already-sanitized `source_path`;
5. only then is `license` emitted in `verified_facts`.

If the project has a license label but no direct public License source, the label
is removed from the verified project projection and the result becomes an
explicit `LICENSE_UNVERIFIED` unknown/risk state.

This is intentionally stricter than simply trusting repository metadata. It
prevents the product's strongest legal-adjacent fact from outrunning the public
evidence contract.

### Selector

`POST /selector` supports the high-level public contract needed by this project,
including:

- `result_kind`, `resource_kind`, `items` and `skills`
- `constraints`, `requirements`, `assumptions` and clarification questions
- `evidence_status`, `notice` and `no_match_reason`
- `verified_answer`
- `solution`, `solution_blueprint`, `project_roles` and `gaps`
- `comparison`, `guidance` and `ranking`
- `near_matches`, `relaxation_options` and `relaxation_context`
- `catalog_status`, `retrieval_status` and degradation indicators

Near matches must remain outside formal recommendations, contain exactly one
blocking constraint and never expose internal evidence IDs, source hashes or
publication versions. A no-result response is accepted only when the evidence
index is available/explicitly partial and a public no-match reason is present.

## Production adapter mapping

| Tool | Existing Radar source | Adapter responsibility |
| --- | --- | --- |
| `search_ai_projects` | `POST /selector`, public project list/detail | Preserve hard constraints, no-match reasons, stable IDs, evidence state and near-match boundaries; hydrate current facts. |
| `get_project_facts` | `GET /projects/{project_id}` | Project only current same-snapshot public fields into the fact/evidence envelope. |
| `get_license_evidence` | Project detail + direct `transparency.sources` License evidence | Require direct public License evidence; never infer permission from a label or missing license. |
| `compare_ai_projects` | Multiple same-snapshot project-detail reads | Keep factual comparisons separate from scenario-specific recommendations. |
| `find_alternatives` | Selector candidates plus project details | Resolve source aliases, exclude the source project and verify current alternatives. |
| `compose_ai_stack` | Selector solution/project-role results plus project details | Verify individual components; label architecture and compatibility as recommendations. |

## Required fail-closed checks

The current adapter enforces or is designed to validate:

1. non-empty compatible public snapshot identity;
2. stable project identity;
3. selector evidence status and partial-evidence notice;
4. direct license evidence before verified license output;
5. missing/conflicting evidence as `unknowns`, not guessed values;
6. formal recommendation / near-match separation;
7. maximum near-match count and one-blocker rule;
8. no internal source hashes, evidence IDs or publication versions in selector
   output;
9. archived and missing projects explicitly;
10. retryable upstream unavailability separately from contract errors;
11. malformed or oversized JSON rejected;
12. upstream HTTP redirects rejected before they can leave the configured Radar
    origin.

## Small additive upstream improvement worth considering later

The current `build_public_transparency()` source rows intentionally expose
`source_label`, `source_path`, `section_heading` and `excerpt`, but not the
already-computable official `source_url` or stable `source_type`.

`github_ai_radar_public_evidence.py` already computes official evidence URLs for
the selector evidence index. Therefore a useful additive API improvement would
be to expose these two public-safe fields on each detail transparency source:

```json
{
  "source_type": "license",
  "source_label": "License",
  "source_path": "LICENSE",
  "source_url": "https://github.com/owner/repo/blob/HEAD/LICENSE",
  "section_heading": "...",
  "excerpt": "..."
}
```

Benefits:

- no label-based inference in downstream clients;
- no need for this repository to derive a GitHub URL from `source_path`;
- stronger field-level provenance for license/deployment facts;
- easier compatibility for non-GitHub evidence sources later.

This is **not required for the current v0.3 product** because the public
transparency is sufficient for conservative License verification. If implemented,
it should be an additive public-contract change in `akaiagents`; this repository
must not import its private evidence artifacts to obtain the missing fields.

## Live-validation rule

Any future upstream change is justified only by representative production
captures showing that a required public field cannot be safely obtained through
the existing routes. First document the smallest additive public API change,
then modify `akaiagents` separately. Do not weaken the distribution adapter to
make an incomplete production response appear verified.
