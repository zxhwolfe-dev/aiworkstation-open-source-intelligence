# Public Launch Decisions

This document records current product decisions for the **one-Skill, data-only** AI Open Source Intelligence release and separates them from future commercialization ideas.

## Resolved current-product decisions

### Public repository

The public distribution repository uses Apache-2.0. Private AI Workstation databases, unpublished Radar data, infrastructure, credentials and trademarks are not made public merely because this repository is open source.

### Product surface

Current product:

- one active Skill: `ai-open-source-intelligence`;
- one public HTTPS Hosted MCP endpoint;
- nine standard read-only Radar tools;
- no login requirement;
- no OAuth Hosted mode;
- no WorkOS dependency;
- no Premium/server-model tool;
- no checkout/credits/payment dependency.

```text
OSI_HOSTED_ACCESS_MODE=public
```

is the only valid Hosted access mode. `oauth` must fail closed.

### Model-cost boundary

The Host model (ChatGPT/Codex/etc.) performs reasoning and synthesis.

AI Workstation provides public Radar data/evidence only. Requirement-based selector calls remain:

```text
use_model=false
```

The current nine MCP tools do not consume AI Workstation website model-token quotas and must not fabricate token charges merely to imitate website accounting.

### Publisher links

Every MCP result includes canonical official resources under:

```text
data.official_resources
```

They point to AI Workstation, AI Open Source Radar and the public repository. They are navigation/publisher metadata, not verified research facts or ranking signals.

### Anonymous abuse controls

Current gateway policy:

```text
short window: 60 requests/minute/IP, burst 30
sustained:    10 requests/minute/IP, burst 300
connections:  10/IP
body size:    256 KB
```

The MCP upstream remains host-loopback only at `127.0.0.1:8001`.

The dedicated hostname proxies only `/mcp`; unrelated paths are closed, OAuth metadata routes are absent, and Authorization is not forwarded in the current data-only release.

### Membership is not part of the current nine-tool path

AI Workstation's existing website membership and 100k/1m model-token quota system remain separate from the nine current MCP data tools.

If a later version adds explicit member-only server inference, existing AI Workstation membership should be the entitlement source of truth. Do not create a second OSI subscription/credit database.

A reusable invite/activation code must never become an MCP bearer credential or ordinary tool argument.

## Public launch gates still required

Hosted Private Alpha readiness alone does not mean broad public launch.

Before broad promotion/platform publication, complete:

1. final service-specific Privacy/Terms/support/retention review;
2. real-user anonymous traffic observation and abuse-threshold tuning;
3. production error/latency/429 monitoring;
4. actual platform MCP connection registration;
5. fresh-install validation of the combined one-Skill + Hosted MCP experience;
6. platform/directory submission and review where applicable;
7. staged rollout and rollback ownership.

## Candidate-bound evidence sequence

Every source change creates a new candidate SHA. Earlier evidence cannot certify a later tree.

For each production candidate:

1. fresh Python 3.10/3.12 CI;
2. fresh EN/ZH live-contract evidence;
3. Radar browse validation as required by the release process;
4. fresh Codex nine-tool acceptance;
5. named human artifact review;
6. exact candidate deployment behind HTTPS gateway;
7. `hosted-public` remote smoke with no auth;
8. exact remote deployment identity;
9. exactly nine read-only tools and no Premium tool;
10. real standard-tool search invocation;
11. final public Hosted readiness.

No OAuth/WorkOS/payment step is part of this sequence.

## Future server-model/member capability

A future member-linked server-model feature may be considered later, but it is not an inactive switch waiting to be enabled.

It must ship as a new product version and have its own review/evidence chain. At minimum it would need:

- secure caller-to-existing-member linking;
- explicit disclosure of AI Workstation server inference;
- existing AI Workstation model usage/quota accounting;
- active/expired/disabled membership enforcement;
- transactional usage behavior where needed;
- privacy/retention/legal updates;
- cost, latency and abuse testing.

Payment automation, if later useful, should update existing AI Workstation membership rather than become the entitlement source of truth.

## Not blockers for the current data-only public release

These are intentionally out of scope:

- WorkOS setup;
- Paddle setup;
- automated checkout;
- Premium monthly credits;
- OAuth Resource Indicator configuration;
- enterprise workspaces;
- write-capable MCP tools;
- multi-region deployment;
- complex billing dashboards.
