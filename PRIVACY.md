# Privacy

_Last updated: 2026-08-12_

## Current 0.3 product

AI Workstation Open Source Intelligence exposes one Skill and nine anonymous,
read-only, data/evidence MCP tools. The current release has no account login,
OAuth, subscription, payment, checkout, credit ledger, or publisher-model tool.

The tools receive only the request fields declared in `schemas/tool-manifest.json`:
project queries and identifiers, typed selection constraints, locale, browsing
filters, and an optional caller-generated request ID. The service uses these
values to query the public AI Open Source Radar. It does not install or execute
third-party repository code.

Operational tool telemetry records tool name, outcome, duration, safe counts,
error code, and a one-way request-ID fingerprint. It does not record raw
queries, constraints, project payloads, authorization headers, cookies, or
credentials. The application does not create a database of MCP inputs or
results. The reviewed production Compose configuration bounds future container
recreations to five 10 MiB log files. The current v0.3.0 container still uses
the host's existing Docker logging configuration; this candidate limit is not
active until it is applied and verified.

The MCP service receives only the fields sent to a selected tool. It does not
receive a user's complete ChatGPT/Codex conversation history unless the host
explicitly places that text into a declared tool argument.

The public gateway necessarily processes IP addresses in memory for TLS,
connection control and anonymous abuse prevention. Its dedicated MCP access log
stores only timestamp, HTTP status and request/upstream duration; it omits IP,
request URI and query, referrer, User-Agent and request body. Nginx error and
security logs may contain network metadata, including IP addresses. Nginx logs
rotate daily and retain 14 rotations on the production host.

Because the Hosted MCP has no account identity, an anonymous request cannot be
looked up by account. For a privacy or deletion request concerning identifiable
gateway log data, email `zxhwolfe@gmail.com` with the relevant IP address and a
narrow timestamp range. The operator will verify and process the request where
the record can be located, subject to security, recovery and legal retention
needs. Do not send prompt text or credentials in the request.

Local stdio mode does not contact AI Workstation unless the user explicitly
selects the live HTTP provider. Local process logs remain under the user's or
self-hosted operator's control.

Public policy pages:

- Privacy: https://useaistation.com/githubai/privacy/
- Terms: https://useaistation.com/terms/

Tool results contain public source URLs and observation timestamps. They keep
source-backed facts separate from recommendations, unknowns, and risks.

Future identity, billing, or model-execution features are outside this release
and require a new privacy review and product version before implementation.
