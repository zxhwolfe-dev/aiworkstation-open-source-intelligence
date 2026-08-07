# v0.1.0 — Initial Public Pre-release

AI Workstation Open Source Intelligence provides evidence-backed workflows and read-only tools for researching, verifying, comparing, and composing open-source AI projects.

## Highlights

- 3 reusable Skills for project research, comparison, and stack planning
- 6 read-only MCP tools for live project intelligence
- English and Simplified Chinese workflows
- explicit separation of verified facts, recommendations, unknowns, and risks
- snapshot-consistent project comparison
- direct-evidence boundary for license verification
- honest no-match and near-match handling
- stdio and guarded Streamable HTTP MCP transports
- deterministic Skills-only distribution bundle with SHA-256 manifests
- Apache-2.0 public repository license

## Install — Skills-only

```bash
codex plugin marketplace add zxhwolfe-dev/aiworkstation-open-source-intelligence --ref v0.1.0
codex plugin marketplace list
```

Skills-only mode provides the research workflows but does not provide live AI Workstation database access by itself.

## Install — local MCP development

```bash
git clone --branch v0.1.0 https://github.com/zxhwolfe-dev/aiworkstation-open-source-intelligence.git
cd aiworkstation-open-source-intelligence
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[mcp]"
```

Run offline:

```bash
OSI_PROVIDER=mock osi-mcp
```

Run with the public read-only Radar provider:

```bash
OSI_PROVIDER=http \
AIWORKSTATION_RADAR_BASE_URL=https://aiworkstation.cn \
osi-mcp
```

## Distribution assets

A release should attach:

- `aiworkstation-open-source-intelligence-skills-0.1.0.zip`
- `SHA256SUMS`
- optionally `bundle-report.json`

## Known limitations

- Skills-only installation does not include a live MCP connection.
- Broad public hosted MCP is not yet approved; local/private-alpha HTTP deployment remains guarded.
- Public hosted identity/authentication, revocation, quotas, rate limiting, abuse controls, and service-specific retention/incident policies remain future gates.
- License evidence is technical evidence, not legal advice.
- Cross-project compatibility is not considered verified until separately tested.

## Security

Do not submit real secrets, customer records, private source code, or confidential documents. Research tools do not install or execute third-party repository code. See `SECURITY.md` and `PRIVACY.md`.

## Upgrade policy

`0.x` releases may refine schemas and packaging as external-alpha evidence accumulates. Breaking tool-contract changes should be called out explicitly in release notes and tested against the bilingual contract/eval suite.
