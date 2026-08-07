# M1 Alpha

M1 connects the public Skills to AI Workstation's Open Source Radar through six read-only tools, exposes those tools over stdio and guarded Streamable HTTP MCP transports, and packages the research workflows as a portable Skills-only plugin.

## Delivered

### Skills-only plugin package

The repository contains:

- `.codex-plugin/plugin.json` with stable identity, Apache-2.0, public legal/support URLs and five starter prompts;
- `.agents/plugins/marketplace.json` for repo-scoped installation;
- three complete Skill workflows;
- English and Simplified Chinese onboarding;
- safe no-tool fallback behavior.

The first public directory package remains Skills-only. It does not claim a bundled/registered live MCP connection. Developers can configure the companion MCP separately.

### Three Skills

- `open-source-project-research`
- `open-source-project-comparison`
- `open-source-stack-planner`

Without live MCP tools, Skills may structure requirements and verification plans but must not invent current project facts or license status.

### Six read-only tools

- `search_ai_projects`
- `get_project_facts`
- `get_license_evidence`
- `compare_ai_projects`
- `find_alternatives`
- `compose_ai_stack`

All six are read-only, non-destructive, idempotent with respect to caller-visible writes, and prohibited from installing/executing third-party repository code.

### Evidence boundaries

The live provider protects:

- project/snapshot identity;
- field-level fact vs analysis separation;
- direct License evidence requirements;
- missing/ambiguous license unknown states;
- near-match separation;
- explicit no-match;
- mixed-snapshot comparison failure;
- sanitized contract-capture artifacts.

### Live data path

`AIWorkstationHttpProvider` reads the public Radar API and never imports the private `akaiagents` repository.

Current selector requests use `use_model=false`, so ordinary six-tool retrieval does not require an additional publisher-funded backend LLM call. The host model (ChatGPT, Codex, or another MCP client) still interprets the user request and synthesizes the answer.

See `docs/MODEL-AND-DATA-FLOW.md`.

### MCP transports

`osi-mcp` provides stdio MCP.

`osi-mcp-http` provides guarded stateless Streamable HTTP with loopback/mock defaults. Non-loopback deployment requires explicit acknowledgement and Host/origin restrictions. The acknowledgement is not authentication.

The repository also contains:

- non-root Docker image;
- localhost-only Compose example;
- remote MCP smoke tooling;
- transport/container policy tests.

### Public contract validation

`osi-probe`, `osi-capture-contracts`, `osi-validate-contracts` and `osi-replay-contracts` form the bilingual validation chain.

`live-contract-validation` runs on relevant `main` changes and can also be dispatched manually. Artifacts are uploaded only after probe, capture, validation, replay and forbidden-key gates succeed.

### Evidence-first readiness

`osi-readiness` and `osi-evidence-readiness` distinguish:

- `code_ready`;
- `external_alpha_ready`;
- `hosted_private_alpha_ready`;
- `public_launch_ready`.

CI, live validation, and real Codex acceptance can generate candidate-bound evidence rather than relying only on operator assertions.

## External Alpha status

A prior release candidate (`71ec1dd055f0d4143cc32966e5792b953b24ccc8`) completed:

- Python 3.10 CI;
- Python 3.12 CI;
- English/Chinese live probes;
- English/Chinese contract replay;
- artifact SHA-256 and privacy review;
- real Codex six-tool live acceptance;
- named human reviewer approval.

That candidate received External Alpha GO and Cohort 1 tracking was opened. Subsequent public-release packaging/documentation changes create a **new candidate** and must be revalidated once as a batch before the first GitHub/platform release.

## Public release preparation delivered after Alpha GO

- Apache-2.0 public repository license;
- Terms, Privacy, Support, Security and contribution/community documents;
- product-first English README and Simplified Chinese README;
- Quickstart, FAQ, Roadmap and model/data-flow documentation;
- structured issue intake;
- Skills-only platform submission copy and 5 positive + 3 negative review cases;
- guarded GitHub release workflow;
- PyPI Trusted Publishing workflow preparation;
- GHCR container publishing workflow.

## Deterministic Skills bundle

`osi-build-alpha` creates a reproducible ZIP containing:

- plugin manifests;
- all three Skills;
- English/Chinese onboarding;
- License and Terms;
- Security, Privacy and Support;
- FAQ/Roadmap/tester guidance;
- embedded per-file SHA-256 manifest.

It excludes runtime MCP source, tests, CI and local configuration.

## Current release layers

### Skills-only public package

Code/metadata preparation is substantially complete. Remaining real-world gates are:

- finish/triage External Alpha cohort feedback;
- re-run candidate CI/live/Codex evidence after the release-prep batch;
- final logo/social preview;
- publisher/developer verification;
- platform submission/review/publish;
- first GitHub pre-release.

### Developer distribution

Prepared but not yet externally published:

- PyPI wheel/sdist through Trusted Publishing;
- GHCR Docker image on version tag.

### Broad hosted MCP

Still separate and not public-launch-ready. Remaining gates include:

- canonical public hostname/deployment owner;
- identity/authentication/revocation as required by product scope;
- quotas, rate limits and abuse controls;
- monitoring and incident response;
- service-specific privacy/terms/retention;
- remote bilingual MCP validation;
- target-platform connection verification/review.

## Local commands

```bash
python -m pip install -e ".[mcp]"
python -m compileall -q src tests
python -m unittest discover -s tests -v
osi-validate-plugin --root .
osi-readiness --root .

OSI_PROVIDER=mock osi-mcp

OSI_PROVIDER=http \
AIWORKSTATION_RADAR_BASE_URL=https://aiworkstation.cn \
osi-mcp

osi-probe --base-url https://aiworkstation.cn --locale en
osi-probe --base-url https://aiworkstation.cn --locale zh

osi-build-alpha --root . --output-dir dist/alpha
```

## Next milestone

Do **not** expand feature count before release feedback. The next milestone is the first public Skills release:

1. finish Cohort 1 feedback triage;
2. run one batched release-candidate validation;
3. upload final logo/social preview and repository About/Topics;
4. create `v0.1.0` GitHub pre-release;
5. configure/publish PyPI and GHCR as desired;
6. complete publisher verification and submit the Skills-only plugin;
7. develop the public hosted MCP as a separate product/release gate.
