# AI Open Source Intelligence

**Evidence-backed open-source AI research, Radar browsing, comparison, license verification and stack planning.**

[简体中文](README.zh-CN.md) · [AI Open Source Radar](https://aiworkstation.cn/githubai/) · [Quickstart](docs/QUICKSTART.md) · [Architecture](docs/ONE-INSTALL-PRODUCT.md)

AI Open Source Intelligence is the plugin/product layer for **AI Open Source Radar**. The final product is designed to be installed once: the user signs in once, then ChatGPT, Codex or another compatible MCP host can use live Radar data without manually cloning a repository, configuring a database, or copying API keys.

## Final product experience

```text
Install AI Open Source Intelligence once
            |
        OAuth sign-in
            |
   +--------+---------------------------+
   |                                    |
3 Skills                        Hosted MCP
workflow/reasoning            live AI Workstation Radar
                                        |
                     +------------------+------------------+
                     |                                     |
              9 Radar tools                        Premium AI research
           data/research/browse                  publisher model + credits
                                                        |
                                               first successful task free
```

The user should not need to understand the implementation split between Skills and MCP. Skills teach the host how to research safely; the hosted MCP supplies current Radar data, identity, rate limits and premium entitlements.

## What it can do

### Discover and verify projects

- search open-source AI projects from natural-language requirements;
- verify project identity, repository/public metadata and evidence freshness;
- verify direct public license evidence without treating a missing license as permission;
- find alternatives while preserving hard requirements;
- compare two to five projects in one decision context;
- compose a candidate open-source AI stack and expose integration unknowns.

### Browse almost the whole AI Open Source Radar

The live product adds three compact browsing tools instead of dozens of tiny endpoint-shaped tools:

- `get_radar_overview` — discover current rankings, collections, categories, scenarios and navigation/filter dimensions;
- `browse_radar_projects` — browse/search projects by ranking, collection, category, scenario, role, topic, deployment, license and other public filters;
- `browse_radar_skills` — browse/filter/search the Radar Skills library or open one Skill by ID.

This allows requests such as:

- “Show me today’s AI open-source ranking.”
- “What collections are available?”
- “Browse the RAG category.”
- “Show self-hosted projects with Docker.”
- “Find installable code-review Skills.”
- “Open this Skill and explain how to use it.”

### Optional Premium AI research

The hosted product also defines:

- `deep_research_ai_projects`

Ordinary Radar data tools do **not** consume publisher AI credits. Premium deep research first performs rules-first Radar retrieval, then sends only bounded public Radar context to the AI Workstation model for deeper synthesis.

Current product policy in the hosted candidate:

- first **successful** premium research task: free;
- failed model requests refund the reserved trial/credit;
- later premium tasks consume AI credits;
- no available credit: return an upgrade state and, for unsubscribed users, a checkout URL;
- an active paid subscription that exhausts its monthly credits must not silently create a duplicate subscription.

The premium narrative remains **model analysis**, not a new verified-fact source.

## Evidence model

Every standard tool result keeps four boundaries explicit:

1. **verified facts** — source-backed facts that crossed the evidence boundary;
2. **recommendations** — analysis or decision guidance;
3. **unknowns** — unavailable or unverified information;
4. **risks** — license, maintenance, deployment, security and integration limits.

A value in `data` is not automatically a verified fact. The hardened provider distinguishes fields such as:

```text
verified_public_metadata
verified_direct_evidence
public_projection_only
unknown
```

License is stricter still: a label is promoted to a verified license only when direct public `License` evidence and a public excerpt are available.

## Tools

### Nine standard live tools

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

These tools are read-only with respect to user data, AI Workstation content, GitHub and third-party repositories. They never execute or install third-party repository code.

### Hosted-only premium tool

```text
deep_research_ai_projects
```

It is non-destructive but intentionally not declared read-only/idempotent because a successful call consumes a one-time trial or AI credit.

See [`schemas/tool-manifest.json`](schemas/tool-manifest.json) and [`schemas/hosted-tool-manifest.json`](schemas/hosted-tool-manifest.json).

## Skills

- `open-source-project-research`
- `open-source-project-comparison`
- `open-source-stack-planner`

The Skills package remains useful in local/offline mode, but the **final public product is not intended to be Skills-only**. Live rankings, collections, categories, project facts, Skills-library data and premium entitlement all belong to the hosted MCP connection.

## Current installation modes

### Developer/local mode

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

This local mode exposes the **nine standard tools** and does not include hosted OAuth billing or the premium tool.

### Hosted one-install mode

The repository now contains the hosted candidate command:

```bash
osi-mcp-hosted --check-config
```

The public hosted mode requires, at minimum:

- live HTTP Radar provider;
- protected public HTTPS `/mcp` endpoint;
- standard OAuth resource-server configuration;
- stable OAuth issuer + subject identity;
- service-to-service backend authentication;
- per-user rate limits;
- premium entitlement storage;
- verified payment webhooks;
- final production privacy/terms/retention policy.

It intentionally fails closed when those controls are missing.

## Authentication and privacy

The hosted candidate uses standard OAuth resource-server semantics. A verified `(issuer, subject)` pair is transformed into a stable opaque entitlement ID before it is sent to AI Workstation billing/model services. Raw access tokens, raw OAuth subjects and payment-provider customer/subscription IDs are not part of public tool results.

The nine ordinary data tools are rate-limited by authenticated user identity. Premium AI has a stricter rate window in addition to trial/credit enforcement.

## Billing architecture

Billing is provider-neutral inside the product:

```text
OAuth user
   |
opaque entitlement ID
   |
free trial / plan / AI credits
   |
Payment adapter (Paddle first; replaceable later)
```

The private backend contains an entitlement ledger, idempotent payment-event processing and lifecycle ordering. The initial Paddle adapter creates a recurring Pro checkout, verifies signed webhook bodies, provisions credits only from recognized completed transactions, and prevents replayed/stale events from corrupting subscription state.

See [`docs/BILLING-AND-ENTITLEMENTS.md`](docs/BILLING-AND-ENTITLEMENTS.md).

## Live contract validation

Two independent workflow layers protect the release:

- evidence-critical live contract validation for project facts, selectors, license and privacy-safe captures;
- full Radar browse validation for EN/ZH overview, rankings, collections, categories, scenarios, Skills listing and Skill detail.

The browse probe is also available as:

```bash
python -m aiworkstation_osi.radar_browse_probe \
  --base-url https://aiworkstation.cn \
  --locale en
```

## Status

**Hosted public-product candidate — not yet a public hosted launch.**

The previously validated Skills/local release foundation remains intact, but the product scope is now intentionally larger. The new hosted candidate must still complete real execution gates before public release:

- full unit/CI validation of the nine-tool and hosted OAuth/Premium paths;
- EN/ZH live Radar browse validation;
- real OAuth provider configuration and login flow;
- public HTTPS hosted MCP deployment and remote tool discovery;
- Paddle sandbox checkout/webhook/renewal/cancel end-to-end test;
- one-free-premium-task and paid-credit end-to-end test;
- final public service privacy/terms/retention review;
- OpenAI Skills + MCP connection registration and platform review.

Do not describe the hosted MCP as publicly launched until those gates are observed.

## Documentation

- [`docs/ONE-INSTALL-PRODUCT.md`](docs/ONE-INSTALL-PRODUCT.md)
- [`docs/HOSTED-OAUTH.md`](docs/HOSTED-OAUTH.md)
- [`docs/BILLING-AND-ENTITLEMENTS.md`](docs/BILLING-AND-ENTITLEMENTS.md)
- [`docs/QUICKSTART.md`](docs/QUICKSTART.md)
- [`docs/FAQ.md`](docs/FAQ.md)
- [`docs/MODEL-AND-DATA-FLOW.md`](docs/MODEL-AND-DATA-FLOW.md)
- [`docs/architecture.md`](docs/architecture.md)
- [`docs/hosted-mcp.md`](docs/hosted-mcp.md)
- [`docs/release-readiness.md`](docs/release-readiness.md)
- [`SECURITY.md`](SECURITY.md)
- [`PRIVACY.md`](PRIVACY.md)
- [`TERMS.md`](TERMS.md)

## License

The public distribution repository is licensed under Apache-2.0. That does not grant rights to private AI Workstation databases, unpublished Radar production data, private backend systems, service credentials, payment accounts or AI Workstation trademarks.
