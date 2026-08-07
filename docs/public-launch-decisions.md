# Public Launch Decisions

The repository can prepare and distribute a public Skills package without pretending that the hosted MCP service is already a production multi-user service. The decisions below are tracked separately by release layer.

## 1. Software license — RESOLVED for the public repository

The public `aiworkstation-open-source-intelligence` repository is licensed under **Apache-2.0**.

This decision covers the public repository only. It does not grant rights to:

- private AI Workstation databases;
- unpublished Radar datasets;
- private backend repositories or infrastructure;
- hosted-service accounts/data;
- AI Workstation trademarks.

The data-production and private backend layer can remain proprietary while the public plugin/client/integration layer is open source.

## 2. Public distribution legal URLs — PREPARED for Skills-only release

The repository now publishes:

- `PRIVACY.md`;
- `TERMS.md`;
- `SUPPORT.md`;
- `SECURITY.md`.

The Skills-only plugin manifest points to public GitHub URLs for these documents. These repository/pre-release documents are adequate for public package transparency, but a future paid or multi-user hosted service should publish **service-specific** privacy/terms/retention information on the final product domain and replace the manifest URLs when appropriate.

## 3. Publisher identity — PENDING PLATFORM VERIFICATION

Recommended publisher identity: **AI Workstation**.

Before directory submission, the publisher must complete whatever individual/business/developer verification the target platform currently requires and ensure that website, support, privacy, terms, logo, and listing ownership are consistent.

## 4. Public MCP hostname and deployment owner — PENDING

Decide:

- canonical MCP hostname (recommended pattern: `mcp.aiworkstation.cn`, subject to infrastructure review);
- cloud/server owner;
- deployment region;
- backup region, if any;
- TLS termination point;
- reverse proxy/load balancer;
- observability destination;
- rollback owner.

The repository's container example binds to host loopback only and is designed for a same-host proxy or private validation.

## 5. Authentication model — PENDING for broad hosted MCP

The current six tools are anonymous/read-only against the public Radar API in local/private testing. A broad public multi-user service must decide whether anonymous access is sufficient for a bounded free surface or whether per-user identity/OAuth is required.

If accounts, paid quotas, saved work, team features, private data, or user-specific access are introduced, use a per-user identity model with explicit scopes, token lifetime, refresh/revocation, and account deletion rather than a shared static secret.

Do not expose the current hosted-alpha endpoint directly to the Internet without an authenticated gateway, trusted private network, or reviewed native authorization model.

## 6. Quotas and commercial model — PENDING

Decide before broad public hosting:

- anonymous/free calls per day;
- authenticated free tier;
- paid unit: tasks, calls, seats, or monthly plan;
- per-tool cost ceilings;
- timeout and hydration limits;
- abuse thresholds;
- team/API policy.

The current live Open Source Intelligence path uses deterministic retrieval with `use_model=false`, which avoids a second publisher-funded LLM call for ordinary project search. If model-assisted backend features are added later, give them separate quotas and cost ceilings.

## 7. Logging and retention — PENDING for hosted service

Decide:

- whether complete prompts are ever stored;
- operational-log retention;
- security-log retention;
- IP-address handling;
- account identifier pseudonymization;
- deletion/export/correction channels;
- whether evaluation samples may be retained and under what consent.

Recommended default: data minimization. Preserve operational metadata needed for reliability/security without retaining credentials or complete confidential prompts.

## 8. Evidence freshness and service guarantees — PENDING

Define:

- maximum acceptable project-fact age;
- behavior during Radar degradation;
- whether safe stale results may be served;
- stale-result labeling;
- uptime/incident targets for any paid service;
- incident communication path.

Do not silently fall back from verified current facts to model guesses.

## 9. Public release sequence

### Skills-only public release

1. finish External Alpha cohort feedback;
2. run standard CI and bilingual live contract validation on the release candidate;
3. run real Codex Skills/MCP acceptance;
4. build deterministic Skills bundle and verify SHA-256;
5. publish GitHub pre-release;
6. complete publisher verification and listing assets;
7. submit the Skills-only plugin using `docs/openai-plugin-submission.md`;
8. publish only after platform review/approval.

### Developer distribution

1. verify the PyPI package name;
2. configure PyPI Trusted Publishing for `.github/workflows/publish-pypi.yml`;
3. publish wheel/sdist;
4. publish versioned Docker images to GHCR.

### Hosted MCP public release

1. choose canonical hostname and deployment owner;
2. deploy behind reviewed TLS/authentication controls;
3. implement identity/revocation as required by product scope;
4. implement quotas, rate limiting, and abuse controls;
5. publish service-specific privacy/terms/retention policy;
6. run remote English and Chinese MCP smoke tests;
7. register/verify the hosted MCP connection with target platforms;
8. update the plugin package only after the connection identity is stable;
9. publish to the MCP Registry when the endpoint/package meets its current requirements.

## Decisions that should not block the first Skills release

These can wait until real usage proves value:

- paid pricing;
- team workspaces;
- multi-region deployment;
- saved collections and alerts;
- write-capable tools;
- public hosted MCP;
- publisher-funded model-assisted search.
