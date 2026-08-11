# Privacy

_Last updated: 2026-08-11_

## Current 0.3 product

AI Workstation Open Source Intelligence exposes one Skill and nine anonymous,
read-only, data/evidence MCP tools. The current release has no account login,
OAuth, subscription, payment, checkout, credit ledger, or publisher-model tool.

The tools receive only the request fields declared in `schemas/tool-manifest.json`:
project queries and identifiers, typed selection constraints, locale, browsing
filters, and an optional caller-generated request ID. The service uses these
values to query the public AI Open Source Radar. It does not install or execute
third-party repository code.

Operational telemetry records tool name, outcome, duration, safe counts, error
code, and a one-way request-ID fingerprint. It must not record raw queries,
constraints, project payloads, authorization headers, cookies, or credentials.

The MCP service receives only the fields sent to a selected tool. It does not
receive a user's complete ChatGPT/Codex conversation history unless the host
explicitly places that text into a declared tool argument.

The public gateway may process IP addresses for TLS, connection control, abuse
prevention, and ordinary access logging. Retention and deletion for the hosted
service follow the policy published on the product website. Local stdio mode
does not send telemetry to AI Workstation unless the user explicitly selects the
live HTTP provider.

Public policy pages:

- Privacy: https://useaistation.com/githubai/privacy/
- Terms: https://useaistation.com/terms/

Tool results contain public source URLs and observation timestamps. They keep
source-backed facts separate from recommendations, unknowns, and risks.

Future identity, billing, or model-execution features are outside this release
and require a new privacy review and product version before implementation.
