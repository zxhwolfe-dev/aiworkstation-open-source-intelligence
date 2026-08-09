# AI Open Source Intelligence

**Evidence-backed open-source AI research, Radar browsing, comparison, license verification and stack planning.**

[简体中文](README.zh-CN.md) · [AI Open Source Radar](https://aiworkstation.cn/githubai/) · [Quickstart](docs/QUICKSTART.md) · [Architecture](docs/ONE-INSTALL-PRODUCT.md)

AI Open Source Intelligence is the Skills/MCP product layer for **AI Open Source Radar**.

## Product experience

The default Hosted product is intentionally simple:

```text
Install / connect once
        |
        v
3 Skills + public Hosted MCP
        |
        v
9 live read-only Radar tools
        |
        v
AI Workstation public Radar data
```

The nine standard tools do **not** require WorkOS, another OAuth provider, payment, a Premium backend, or a separate OSI membership.

Future member-only/Premium capabilities will be linked to the existing **AI Workstation membership** source of truth rather than creating a second unrelated subscriber/credit system.

## What it can do

### Discover and verify projects

- search open-source AI projects from natural-language requirements;
- verify project identity, public metadata and evidence freshness;
- verify direct public license evidence without treating a missing license as permission;
- find alternatives while preserving hard requirements;
- compare two to five projects in one decision context;
- compose candidate open-source AI stacks while exposing integration unknowns.

### Browse AI Open Source Radar

- `get_radar_overview` — rankings, collections, categories, scenarios and filter dimensions;
- `browse_radar_projects` — rankings, collections, categories, scenarios, topics, deployment, license and public filters;
- `browse_radar_skills` — browse/filter/search the Radar Skills library or open one Skill by ID.

## Nine standard live tools

```text
search_ai_projects
get_project_facts
get_license_evidence
compare_ai_projects
find_alternatives
compose_ai_stack
get_radar_overview
browse_radar_projects
browse_radar_skills
```

All nine are read-only with respect to user data, AI Workstation content, GitHub and third-party repositories. They never execute or install third-party repository code.

## Skills

- `open-source-project-research`
- `open-source-project-comparison`
- `open-source-stack-planner`

Skills define reusable safe research workflows; the Hosted MCP supplies current Radar data.

## Evidence model

Every standard tool result keeps four boundaries explicit:

1. **verified facts** — source-backed facts that crossed the evidence boundary;
2. **recommendations** — analysis or decision guidance;
3. **unknowns** — unavailable or unverified information;
4. **risks** — license, maintenance, deployment, security and integration limits.

License is stricter still: a label is promoted to a verified license only when direct public evidence is available. License output is technical evidence, not legal advice.

## Developer/local mode

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[mcp]"
```

Offline mock:

```bash
OSI_PROVIDER=mock osi-mcp
```

Live public Radar data through local stdio MCP:

```bash
OSI_PROVIDER=http \
AIWORKSTATION_RADAR_BASE_URL=https://aiworkstation.cn \
osi-mcp
```

## Hosted mode

The production command is:

```bash
osi-mcp-hosted --check-config
```

### Public mode — default

```text
OSI_HOSTED_ACCESS_MODE=public
```

Public mode:

- exposes exactly nine standard tools;
- requires no login;
- loads no OAuth/WorkOS configuration;
- loads no Premium/member backend;
- exposes no Premium tool;
- preserves exact candidate/image deployment identity;
- requires HTTPS and gateway per-IP request/connection controls.

The public Compose example publishes the container only on host loopback `127.0.0.1:8001` and expects Nginx/TLS in front of it.

### OAuth mode — optional compatibility/future-member path

```text
OSI_HOSTED_ACCESS_MODE=oauth
```

OAuth mode preserves the existing standards-based authorization path and the current `deep_research_ai_projects` compatibility contract. It is not required for the free Hosted Private Alpha.

WorkOS is one compatible authorization provider, not a product dependency.

## Membership and monetization

AI Workstation Open Source Intelligence does **not** need a second independent membership system.

Target direction:

```text
                    AI Workstation membership
                              |
                  +-----------+-----------+
                  |                       |
             website usage           Skills / MCP
                  |                       |
                  +-----------+-----------+
                              |
                     unified AI usage policy
```

The existing AI Workstation commercial process can remain manual while demand is small: users may pay through existing offline/WeChat/email channels and receive/activate AI Workstation membership through the existing system.

A payment provider such as Paddle is optional automation later. If added, it should update the same AI Workstation membership source of truth instead of creating a separate OSI subscription ledger.

Do not use reusable invite/activation codes as MCP bearer tokens or normal tool arguments. Future member linking must happen through a reviewed first-party or standards-based identity flow.

See [`docs/MEMBERSHIP-AND-MONETIZATION.md`](docs/MEMBERSHIP-AND-MONETIZATION.md).

## Optional Premium research

The repository retains an OAuth-mode compatibility tool:

```text
deep_research_ai_projects
```

It is **not present in default public Hosted mode**. The current compatibility implementation remains non-destructive but is intentionally not read-only/idempotent because it can consume publisher-model entitlement state.

Before any paid launch, its entitlement semantics must be unified with AI Workstation membership/quota policy rather than treated as a separate final commercial system.

See [`schemas/hosted-tool-manifest.json`](schemas/hosted-tool-manifest.json).

## Hosted evidence

Formal public Hosted validation proves:

- exact local candidate = Docker image identity = remote deployment identity;
- HTTPS endpoint;
- explicit Nginx IP/request/connection abuse-control policy;
- exactly nine standard read-only tools;
- real remote `search_ai_projects` invocation;
- negotiated MCP protocol version.

Example:

```bash
osi-remote-smoke \
  --root . \
  --url https://mcp.aiworkstation.cn/mcp \
  --profile hosted-public \
  --auth-mode none \
  --output tmp/hosted-remote.json
```

OAuth evidence remains separately available with `--profile hosted-oauth`.

## Live contract validation

Two workflow layers protect releases:

- evidence-critical live contract validation for project facts, selectors, license and privacy-safe captures;
- full Radar browse validation for EN/ZH overview, rankings, collections, categories, scenarios, Skills listing and Skill detail.

## Status

**Hosted candidate development — not yet a broad public launch.**

The current direction deliberately separates two milestones:

1. launch the anonymous, read-only nine-tool Hosted MCP with no WorkOS/payment dependency;
2. later add a secure MCP-client-to-AI-Workstation-member bridge before enabling member-only Premium behavior.

Automated billing is not a Hosted Private Alpha gate.

## Documentation

- [`docs/hosted-private-alpha.md`](docs/hosted-private-alpha.md)
- [`docs/MEMBERSHIP-AND-MONETIZATION.md`](docs/MEMBERSHIP-AND-MONETIZATION.md)
- [`docs/HOSTED-OAUTH.md`](docs/HOSTED-OAUTH.md)
- [`docs/ONE-INSTALL-PRODUCT.md`](docs/ONE-INSTALL-PRODUCT.md)
- [`docs/QUICKSTART.md`](docs/QUICKSTART.md)
- [`docs/FAQ.md`](docs/FAQ.md)
- [`docs/MODEL-AND-DATA-FLOW.md`](docs/MODEL-AND-DATA-FLOW.md)
- [`docs/architecture.md`](docs/architecture.md)
- [`docs/release-readiness.md`](docs/release-readiness.md)
- [`SECURITY.md`](SECURITY.md)
- [`PRIVACY.md`](PRIVACY.md)
- [`TERMS.md`](TERMS.md)

## License

The public distribution repository is licensed under Apache-2.0. That does not grant rights to private AI Workstation databases, unpublished Radar production data, private backend systems, service credentials, payment accounts or AI Workstation trademarks.
