# Roadmap

AI Workstation Open Source Intelligence is developed in staged release layers so evidence quality, product simplicity, privacy and distribution can mature independently.

## Current product foundation

- [x] One unified user-facing Skill: `ai-open-source-intelligence`
- [x] Nine read-only MCP data/evidence tools
- [x] Offline mock provider
- [x] Hardened public AI Open Source Radar provider
- [x] Requirement selector fixed to `use_model=false`
- [x] AI Workstation server-model execution removed from the current Hosted product path
- [x] OAuth/Premium runtime switch fails closed
- [x] English and Chinese public-contract validation
- [x] License-evidence and snapshot boundaries
- [x] stdio MCP and guarded Streamable HTTP MCP
- [x] Deterministic one-Skill distribution bundle
- [x] Candidate-bound CI, Codex acceptance and release-readiness tooling
- [x] Public Hosted MCP endpoint at `https://mcp.aiworkstation.cn/mcp`
- [x] TLS, loopback-only upstream and candidate deployment identity
- [x] Anonymous gateway request/connection abuse controls
- [x] Canonical AI Workstation/Radar/repository links in MCP results

## Next: one-Skill data-only release validation

Every source candidate still needs its own evidence chain before production deployment.

- [ ] Fresh candidate-bound Python 3.10/3.12 CI
- [ ] Fresh EN/ZH live-contract validation
- [ ] Fresh Radar browse validation
- [ ] Fresh nine-tool Codex acceptance
- [ ] Named human artifact review
- [ ] Deploy exact candidate SHA
- [ ] Candidate-bound `hosted-public` remote smoke
- [ ] Confirm `server_model_enabled=false`, `oauth_enabled=false` and exactly nine tools remotely
- [ ] Confirm new short+sustained anonymous abuse controls in production
- [ ] Final Hosted readiness for the exact release candidate

## Public distribution and platform launch

- [x] Apache-2.0 public repository license
- [x] Public privacy, terms, support, security, contribution and conduct documents
- [x] English and Simplified Chinese README surfaces
- [x] One-Skill Quickstart and submission pack
- [ ] Final logo/social-preview assets
- [ ] Final service-specific privacy/retention review
- [ ] Production error/latency/429 monitoring baseline
- [ ] Real-user abuse-threshold tuning
- [ ] Publisher/developer verification in target platforms
- [ ] Register the real Hosted MCP connection identity
- [ ] Fresh-install one-Skill + MCP acceptance
- [ ] Platform/directory submission and staged rollout
- [ ] Publish a GitHub pre-release/release from the accepted candidate

## Developer distribution

- [ ] Verify package name availability on PyPI
- [ ] Configure PyPI Trusted Publishing
- [ ] Publish wheel/sdist
- [ ] Publish versioned container images to GHCR
- [ ] Document one-command local MCP installation

## Future product expansion

Potential work should be driven by real usage rather than feature count:

- richer project/category exploration;
- saved research and alerts;
- evidence freshness and project-change views;
- better cache efficiency for public Radar traffic;
- adaptive anonymous abuse controls based on observed traffic;
- enterprise evaluation/report packs.

## Future member/server-model capability — separate version only

The current product has no server-model/Premium route.

If a later version introduces explicit AI Workstation server inference, it must be designed as a new reviewed product version and should:

- safely link the caller to existing AI Workstation membership;
- reuse existing AI Workstation model usage/quota accounting;
- disclose server-side inference explicitly;
- prove active/expired/disabled membership behavior;
- receive a fresh privacy/cost/abuse/release evidence chain.

Do not reintroduce a hidden OAuth/Premium switch or a second OSI credit database into the current data-only product.

Write-capable tools and third-party repository execution remain outside the current product boundary.
