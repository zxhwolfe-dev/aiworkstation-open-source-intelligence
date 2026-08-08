# Skills, Hosted MCP, Online Data, and Model Usage

This document explains where reasoning happens, where live data comes from, and which component pays for model inference in the final one-install product.

## Final architecture

```text
User
  |
ChatGPT / Codex / compatible MCP host model
  |
  +--> 3 Skills: reusable workflow and decision rules
  |
  +--> Hosted MCP
          |
          +--> 9 standard live Radar tools
          |       -> public AI Workstation Radar data/retrieval
          |       -> no publisher-model credit
          |
          +--> deep_research_ai_projects
                  -> rules-first public Radar selection
                  -> AI Workstation publisher model
                  -> free trial / AI credit entitlement
```

The final user experience is one installation plus one OAuth sign-in. The implementation remains layered so data, reasoning, identity and billing are independently controllable.

## Skills

The three Skills contain research procedure, safety boundaries, output structure, and verification logic.

Skills answer **how to work**. They do not contain database credentials and should not rely on hidden network scripts as the production data connector.

When live tools are unavailable, a Skill can still:

- interpret requirements;
- preserve hard/preferred/not-required constraint polarity;
- create a search or verification plan;
- provide a blank decision matrix or role-level architecture;
- expose what current facts remain unavailable.

The final public product is nevertheless designed to install Skills together with the hosted MCP connection so users do not normally experience this degraded mode.

## Nine standard live Radar tools

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

These tools expose the useful machine-operable majority of AI Open Source Radar:

- natural-language project discovery;
- project/evidence/license verification;
- comparison, alternatives and stack planning;
- all discoverable ranking/collection/category/scenario dimensions;
- filtered/paginated project browsing;
- Skills-library browsing/search/detail.

They do not mirror every private website endpoint, user-account route or visual-only UI feature.

## Ordinary model usage

### Host model

ChatGPT, Codex, or another MCP host model:

- understands the user's natural-language request;
- chooses a Skill and tool-call sequence;
- converts user intent into structured tool inputs;
- interprets returned data/evidence;
- writes the final conversational answer.

This inference belongs to the host/user environment.

### AI Workstation standard data path

The standard Radar layer:

- resolves validated public releases;
- reads precomputed ranking/collection/filter structures;
- runs deterministic selector/filter/retrieval logic;
- returns project/detail/license/snapshot/evidence contracts;
- does **not** consume AI Workstation Premium AI credits.

The evidence-critical selector path continues to use rules-first retrieval with backend model assistance disabled for ordinary MCP search.

## Publisher-model premium usage

The only initial hosted tool that deliberately invokes the AI Workstation model is:

```text
deep_research_ai_projects
```

It is explicit because server inference has a real publisher cost and changes entitlement state.

Flow:

```text
query
 -> rules-first Radar selector (model disabled)
 -> bounded public context whitelist
 -> reserve free trial / paid credit
 -> publisher model
     success -> keep reservation consumed
     failure -> refund reservation
 -> analysis returned as recommendation
```

The model prompt may contain the user's premium research task plus bounded public Radar result context. It must not contain:

- OAuth bearer tokens;
- raw OAuth subject;
- backend service credentials;
- Paddle customer/subscription IDs;
- private selector continuation tokens;
- internal publication/source hashes;
- confidential project data not supplied as public Radar context.

## Why not enable the publisher model for every search?

Using a second model for every ordinary request would create hidden publisher cost while duplicating reasoning already performed by ChatGPT/Codex.

The scalable split is:

```text
Normal request
  host model + deterministic Radar data

Premium request
  host model + deterministic Radar data + explicit publisher model
```

This lets standard browsing remain fast and inexpensive while premium deep synthesis has a measurable unit of value.

## Entitlement and billing

```text
OAuth (issuer, subject)
   -> opaque entitlement ID
   -> free trial / plan / AI credits
```

Initial policy:

- first successful Premium AI research task is free;
- failed model calls refund the reservation;
- later Premium AI tasks consume credits;
- standard nine tools never consume AI credits;
- active paid users with exhausted credits should not be sold a duplicate recurring subscription.

See [`BILLING-AND-ENTITLEMENTS.md`](BILLING-AND-ENTITLEMENTS.md).

## Rate-limit boundary

Authenticated Hosted MCP calls are rate-limited by the opaque OAuth identity, not by raw access token, IP address or a client-supplied username.

Current configurable launch defaults:

```text
standard: 60/minute, 300/hour
premium:   5/minute
```

Premium access is also constrained by entitlement/credit state.

## Future premium capabilities

If user data proves demand, additional premium tools can reuse the same entitlement boundary, for example:

- long-form project due-diligence reports;
- change-over-time research briefs;
- larger multi-project procurement studies;
- enterprise stack architecture reports.

Do not turn every new data endpoint into a paid model call. Premium should correspond to material server-side synthesis value, not simple retrieval.
