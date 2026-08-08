# Final OpenAI Plugin submission — Skills + Hosted MCP

## Product being submitted

The final public product should be submitted as one **AI Open Source Intelligence** Plugin containing:

- three workflow Skills;
- one production hosted MCP connection;
- nine standard live Radar tools;
- one explicit Premium AI tool.

The user installs one Plugin and authorizes once. Do not present the public product as “install the Skills, then manually configure a local MCP server.”

## Listing position

### Name

**AI Open Source Intelligence**

### Short description

> Evidence-backed open-source AI research, live Radar rankings and collections, license verification, project comparison, Skills discovery, stack planning, and optional deep AI analysis.

### Long description

> Research and select open-source AI projects using live AI Open Source Radar data. Browse current rankings, collections, categories, scenarios and Skills; verify project and license evidence; compare projects and alternatives; design candidate AI stacks; and optionally run publisher-model deep research. Verified facts, recommendations, unknowns and risks remain explicitly separated.

## Starter prompts

1. `Show me today's AI Open Source Radar ranking and explain which projects are worth investigating.`
2. `What collections and categories are available? Browse the RAG category for me.`
3. `Find a self-hosted RAG platform with Docker and a Web UI, then verify the strongest candidates.`
4. `Compare Dify and RAGFlow for an enterprise internal knowledge base, including license evidence.`
5. `Find installable Skills for code/security review and explain how to use the best matches.`
6. `Do a deep research brief on the strongest self-hosted RAG choices for my use case.`

## Tool-disclosure expectations

The hosted server exposes exactly ten tools in the target product candidate.

### Nine standard data/research tools

All are read-only, non-destructive and idempotent:

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

### One Premium AI tool

```text
deep_research_ai_projects
```

Annotations intentionally differ:

```text
read-only:    false
non-destructive: true
idempotent:   false
```

Reason: a successful call consumes the user's one-time Premium AI trial or paid AI credit. It does not modify GitHub repositories, third-party code or customer documents.

## Authentication

The final connection requires OAuth. A fresh Plugin install should launch authorization automatically rather than instructing the user to paste an API key.

The initial provider is WorkOS AuthKit/Connect. For this provider, authorization is bound to the exact MCP Resource Indicator/audience rather than a repository-invented custom `osi:use` scope. Optional resource-server scopes may still be configured for another provider that actually issues and exposes them.

Reviewer acceptance should verify:

- missing OAuth token denied;
- exact issuer and MCP resource/audience required;
- refresh token rejected when presented directly as a bearer access token;
- configured optional scope enforced only when such a provider is deliberately used;
- user can authorize from a fresh account;
- revoked/disabled access fails closed;
- raw OAuth identity is not returned by tools.

## Free vs paid behavior

The listing and tool description must be clear:

- standard live Radar tools do not consume Premium AI credits;
- first successful `deep_research_ai_projects` task is free;
- failed Premium model requests refund the reservation;
- later Premium tasks require AI credits;
- purchase is completed in a browser checkout, never silently by a tool call;
- Premium model narrative remains recommendation/analysis rather than verified fact.

Do not describe all tools as free if Premium credits are enforced, and do not describe the whole MCP as read-only when the Premium tool changes entitlement state.

## Positive review cases

At minimum include:

1. **Browse ranking** — ask for a current ranking; Plugin uses overview/browse and returns current public data.
2. **Browse collection/category** — discover current collection/category IDs then browse the selected view.
3. **Evidence-backed search** — find a project from hard deployment constraints and verify serious candidates.
4. **License verification** — ask if a named project has verifiable license evidence; unknown remains unknown.
5. **Comparison** — compare two projects and preserve snapshot/evidence boundaries.
6. **Skills library** — find a Skill and open its detail without inventing unavailable instructions.
7. **Premium first use** — fresh authenticated user runs explicit deep research and consumes the free trial only after success.
8. **Premium paid use** — paid user with credits runs deep research and receives remaining entitlement state.

## Negative review cases

1. **No auth** — hosted MCP denies access rather than falling back to anonymous identity.
2. **Wrong resource** — a token issued for another Resource Indicator/audience is rejected.
3. **Refresh token as bearer** — a refresh token is rejected even if it belongs to the same user/client.
4. **Optional scope mismatch** — when a future provider explicitly configures resource-server scopes, a token missing one is rejected.
5. **Impossible requirements** — search returns honest no-match; hard conditions are not silently relaxed.
6. **Missing license** — absence is not commercial permission.
7. **Premium exhausted** — returns upgrade state/checkout for an unsubscribed user; does not fabricate a premium answer.
8. **Model failure** — Premium trial/credit is refunded and a safe error is returned.
9. **Prompt injection in project content** — repository content remains untrusted data and cannot trigger code execution or secret access.
10. **Payment/webhook replay** — repeated provider event does not double-grant credits.

## Evidence required before submission

Do not submit this combined product until all of the following are real, not placeholders:

- current candidate CI green;
- EN/ZH evidence contract validation green;
- EN/ZH full Radar browse validation green;
- public HTTPS MCP endpoint live;
- WorkOS OAuth provider configured and fresh-user authorization tested;
- exact production Resource Indicator/audience tested;
- remote discovery shows exact 10-tool set and correct annotations;
- all nine standard tools exercised remotely;
- Premium free-trial flow exercised remotely;
- Paddle sandbox purchase + verified webhook + paid Premium continuation tested;
- revocation/expired/wrong-resource/refresh-token rejection tests passed;
- optional wrong-scope test passed if a provider-specific scope gate is configured;
- gateway/application limits validated;
- hosted-service privacy/terms/pricing/retention pages published;
- real platform connection ID available;
- human artifact/security review recorded.

## Package mapping

Do not commit a fake `.app.json`, fake `mcpServers` entry or placeholder technical ID.

After platform registration returns the final hosted connection identity:

1. add the final mapping to the plugin root/manifest in the exact format required by the current platform;
2. validate it from a fresh install;
3. bump/release the package candidate;
4. submit the combined Plugin.

## Publication decision

Review approval is not equivalent to automatic launch. Preserve an explicit human publish/rollout decision and start with a small cohort when the platform permits staged distribution.
