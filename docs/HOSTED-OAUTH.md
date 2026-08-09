# Hosted OAuth — Disabled in the current product

## Current status

AI Workstation Open Source Intelligence `0.2.x` does **not** expose an OAuth Hosted mode.

The current product invariant is:

```text
OSI_HOSTED_ACCESS_MODE=public
9 anonymous read-only Radar tools
server_model_execution=false
OAuth=false
Premium=false
```

Setting:

```text
OSI_HOSTED_ACCESS_MODE=oauth
```

must fail closed.

The current public Compose file contains no `OSI_OAUTH_*`, Premium or private backend service credentials, and the dedicated Nginx configuration does not expose OAuth protected-resource metadata routes.

## Why this file still exists

Older alpha candidates explored a standards-based OAuth identity boundary and a publisher-model Premium tool. Those designs are retained only as repository history and must not be treated as an operational runbook for the current product.

The product decision for `0.2.x` is simpler:

```text
ChatGPT / Codex host model
          |
          | chooses tools / performs reasoning
          v
AI Workstation Hosted MCP
          |
          | public data/evidence only
          v
AI Open Source Radar
```

AI Workstation must not perform a second server-side model call on the standard Skill/MCP path.

Requirement-based selection uses the public Radar selector with:

```text
use_model=false
```

## Future identity or paid capabilities

If member-linked server-model capabilities are introduced later, they must ship as a **new reviewed product version** with a new candidate/evidence chain. They must not be activated by restoring an environment-variable switch in the current release.

Any future identity bridge should map to the existing AI Workstation membership source of truth rather than creating a second independent subscriber/credit database. Invite or activation codes must never be used directly as MCP bearer tokens or normal tool arguments.

## Current deployment identity

Candidate-bound deployment identity remains mandatory and unrelated to OAuth:

```text
OSI_RELEASE_COMMIT=<exact-40-character-hosted-candidate-sha>
OSI_IMAGE_COMMIT=<same-exact-candidate-sha>
```

The Hosted runtime fails closed when image/release identity does not match.
