# Security Policy

## Supported versions

This repository is M1 Alpha / pre-release. Only the latest commit on `main` is
considered for security fixes.

A guarded Streamable HTTP transport and container scaffold are available for
local/private-alpha testing, but no broad public MCP service is approved or
supported yet. Native end-user OAuth, production quota/rate-limit/abuse controls
and final public-service policies remain release blockers.

## Reporting a vulnerability

Do not open a public issue for a vulnerability involving:

- credentials, tokens or private data;
- authentication, Host/origin or gateway bypass;
- prompt injection that crosses a trust boundary;
- remote code execution or third-party repository execution;
- unsafe write behavior;
- data leakage from Radar/public-contract responses;
- false promotion of analysis or indirect evidence into verified facts;
- container or hosted MCP isolation failures.

Until a dedicated security mailbox is published, use the private contact method
listed on the AI Workstation website and include:

- affected commit or version;
- reproduction steps;
- expected and observed behavior;
- impact and required preconditions;
- deployment mode: mock, live stdio, local HTTP or hosted private alpha;
- suggested mitigation, when available.

Do not include real secrets, customer data or weaponized payloads that could harm
third parties.

## Current security guarantees

- all six product tools are read-only;
- the default provider performs no network access;
- third-party repository code is never executed or installed;
- mock data is explicitly marked and cannot be presented as verified live facts;
- live Radar integration fails closed on required identity/evidence contracts;
- public Radar redirects are rejected rather than followed to another origin;
- repository/public metadata is separated from editorial/analysis projection
  fields before values enter `verified_facts`;
- a license is verified only with direct public `License` transparency evidence;
- Streamable HTTP defaults to loopback and mock data;
- non-loopback binds require explicit private-network/reverse-proxy
  acknowledgement, the live provider and explicit MCP Host allowlists;
- non-loopback mode passes Host/origin allowlists into MCP transport security for
  DNS-rebinding/Host-header protection;
- MCP request bodies have a bounded alpha default;
- the bind acknowledgement is not authentication;
- remote MCP smoke URLs reject embedded credentials, require HTTPS outside
  localhost and require the canonical `/mcp` path;
- runtime telemetry writes to stderr and does not accept query text, constraints,
  project IDs or raw request IDs as event fields;
- the example container runs non-root, drops capabilities and maps only to host
  loopback;
- Skills-only alpha bundles exclude runtime MCP source and scan for common
  credential-like material.

## Not a public-hosting guarantee

The repository does not currently guarantee that an Internet-exposed deployment
is secure merely because `osi-mcp-http` starts successfully. Public hosting also
requires real per-user identity/authentication, revocation, TLS gateway controls,
rate limits, abuse blocking, production logging/monitoring, secret management
and incident response.

See `docs/security-and-privacy.md`, `docs/hosted-mcp.md` and
`docs/public-launch-decisions.md` before any hosted rollout.
