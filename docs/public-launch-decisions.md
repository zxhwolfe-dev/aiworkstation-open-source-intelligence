# Public Launch Decisions

The codebase can prepare a private alpha without making business, legal or
infrastructure decisions on behalf of the publisher. The following decisions
must be made explicitly before a broad public release.

## 1. Software license

Current state: no open-source license is granted.

Choose one of these product strategies before adding a `license` field to the
plugin manifest:

- open-source distribution under a recognized license;
- source-available distribution under custom terms;
- proprietary hosted product with only the Skills package publicly inspectable.

The choice affects reuse, forks, commercial redistribution and marketplace
expectations. Do not infer permission from the repository being publicly
readable.

## 2. Public legal URLs

Publish final URLs for:

- privacy policy;
- terms of service;
- support/contact;
- security reporting, when separate from the repository policy.

The existing `PRIVACY.md`, `SECURITY.md` and `SUPPORT.md` describe the current
repository and alpha posture. They are not automatically a substitute for legal
review of a hosted paid service.

## 3. MCP hostname and deployment owner

Decide:

- canonical MCP hostname;
- cloud/server owner;
- deployment region;
- backup region, if any;
- TLS termination point;
- reverse proxy/load balancer;
- observability destination;
- rollback owner.

The repository's container example binds to host loopback only and is designed
for a same-host proxy or private validation.

## 4. Authentication model

For public ChatGPT/plugin use, prefer per-user OAuth-style authorization over a
shared static token.

Decide:

- authorization server;
- user/account identity source;
- scopes;
- token lifetime and refresh policy;
- revocation path;
- anonymous trial policy, if any;
- service-to-service access policy.

Do not expose the current hosted alpha endpoint directly to the Internet without
an authenticated gateway or native MCP authorization.

## 5. Quotas and commercial model

Decide before adding billing code:

- anonymous/free calls per day;
- authenticated free tier;
- paid plan unit: calls, successful research tasks, seats or monthly package;
- per-tool cost ceilings;
- timeout and hydration limits;
- abuse thresholds;
- team or API access policy.

Prefer measuring successful user tasks over raw calls when evaluating product
value, while infrastructure rate limits still operate on requests.

## 6. Logging and retention

Decide:

- whether complete prompts are ever stored;
- default log retention;
- security-log retention;
- IP-address handling;
- account identifier pseudonymization;
- deletion and export process;
- whether evaluation samples may be retained and under what consent.

The recommended default is data minimization: operational metadata and stable
request IDs without complete prompts or credentials.

## 7. Evidence freshness and service guarantees

Define:

- maximum acceptable project-fact age;
- behavior during Radar degradation;
- whether safe stale results are served;
- how stale data is labeled;
- uptime target for a paid service;
- incident communication path.

Do not silently fall back from verified current facts to model guesses.

## 8. Public launch sequence

Recommended order:

1. pass normal CI;
2. run bilingual live contract validation;
3. test the local Skills package;
4. test stdio MCP from Codex;
5. deploy the guarded Streamable HTTP server behind a private/authenticated
   gateway;
6. run `osi-remote-smoke` against that endpoint;
7. complete OAuth, quotas and abuse controls;
8. publish legal/support URLs;
9. register the hosted MCP connection with the target platform;
10. update the plugin package with the real hosted connection only after the
    connection identifier and endpoint are stable;
11. invite a small external alpha cohort;
12. expand distribution only after repeated-use and reliability metrics justify
    it.

## Decisions that should not block private testing

The following can wait until the private alpha proves value:

- paid plan pricing;
- team workspace design;
- broad public directory submission;
- screenshots and marketing assets;
- multi-region deployment;
- saved collections and alerts;
- write-capable MCP tools.
