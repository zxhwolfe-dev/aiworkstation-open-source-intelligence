# Plugin Packaging and Distribution

The repository is a valid **Skills-only plugin package** and also contains the separately installable read-only MCP runtime. The first broad directory submission should remain Skills-only; the hosted MCP connection can be added later after public-hosting gates are complete.

## Public package identity

- Name: `aiworkstation-open-source-intelligence`
- Display name: `AI Open Source Intelligence`
- Version: `0.1.0`
- License: Apache-2.0
- Website: https://aiworkstation.cn/githubai/
- Repository: https://github.com/zxhwolfe-dev/aiworkstation-open-source-intelligence
- Privacy: `PRIVACY.md`
- Terms: `TERMS.md`
- Support: `SUPPORT.md`
- Security: `SECURITY.md`

The Apache-2.0 license covers this public repository, not private AI Workstation databases, unpublished datasets, private backend systems, or trademarks.

## Current plugin surface

```text
.
├── .codex-plugin/
│   └── plugin.json
├── .agents/
│   └── plugins/
│       └── marketplace.json
└── skills/
    ├── open-source-project-research/SKILL.md
    ├── open-source-project-comparison/SKILL.md
    └── open-source-stack-planner/SKILL.md
```

Only `plugin.json` belongs in `.codex-plugin/`.

## Why the first directory release is Skills-only

The repository also contains a local stdio MCP server, but a public plugin should not claim a bundled or registered live MCP connection until installation and hosting are portable and reviewed.

A Skills-only release is still useful: it gives ChatGPT/Codex the exact research, comparison, evidence, constraint, license, and architecture workflow. When live tools are absent, the Skills are explicitly required not to invent current project facts.

The live data layer remains available to developers who separately install/configure the read-only MCP runtime.

## Install from the repository marketplace

```bash
codex plugin marketplace add zxhwolfe-dev/aiworkstation-open-source-intelligence --ref main
codex plugin marketplace list
```

For a local clone:

```bash
codex plugin marketplace add /ABSOLUTE/PATH/TO/aiworkstation-open-source-intelligence
codex plugin marketplace list
```

## Validate the plugin package

```bash
python -m pip install -e ".[mcp]"
osi-validate-plugin --root .
```

The validator checks:

- stable plugin identity and semantic version;
- Skills paths and frontmatter;
- repository marketplace identity;
- read-only capabilities;
- public website/listing metadata;
- Apache-2.0 license declaration;
- public privacy and terms URLs;
- optional MCP/app mappings when declared.

`public_submission_ready=true` means the repository's **Skills metadata package** has the required local public fields; it does not mean that a platform has reviewed or published the plugin.

## Deterministic Skills bundle

```bash
osi-build-alpha --root . --output-dir dist/alpha
(
  cd dist/alpha
  sha256sum --check SHA256SUMS
)
```

The output contains:

```text
aiworkstation-open-source-intelligence-skills-0.1.0.zip
SHA256SUMS
bundle-report.json
```

The ZIP includes:

- plugin + marketplace manifests;
- all three Skills;
- English and Chinese README/quickstart documentation;
- License and Terms;
- Security, Privacy, and Support documents;
- FAQ, Roadmap, and alpha-tester guidance;
- an embedded per-file SHA-256 manifest.

It excludes:

- Python runtime implementation;
- MCP source;
- tests and GitHub Actions;
- editable-install assumptions;
- environment files and credentials;
- temporary validation artifacts.

Two builds from the same tree must be byte-identical.

## GitHub release

The guarded workflow `.github/workflows/release.yml`:

1. requires a semantic `vX.Y.Z` tag input;
2. verifies the tag equals plugin/package version;
3. runs the test and plugin gates;
4. builds the deterministic Skills bundle;
5. creates a GitHub release or pre-release;
6. attaches the Skills ZIP, `SHA256SUMS`, and bundle report.

The workflow requires an explicit manual dispatch and repository `contents: write` only for the release job.

## PyPI distribution

`.github/workflows/publish-pypi.yml` prepares the Python/CLI/MCP package for PyPI using Trusted Publishing.

Before the first run:

1. confirm the PyPI project name is available or create the project;
2. configure a GitHub environment named `pypi`;
3. configure PyPI Trusted Publishing for this repository/workflow/environment;
4. verify version uniqueness;
5. manually dispatch the workflow and type `PUBLISH`.

The workflow runs tests, builds wheel/sdist, runs `twine check`, uploads a build artifact, and then publishes through OIDC. It does not store a long-lived PyPI API token in the repository.

After publishing, intended installation is:

```bash
pip install "aiworkstation-open-source-intelligence[mcp]"
```

## GHCR container distribution

`.github/workflows/publish-ghcr.yml` builds and pushes the repository Docker image to:

```text
ghcr.io/zxhwolfe-dev/aiworkstation-open-source-intelligence
```

It runs on `v*` tags or explicit manual dispatch and uses `GITHUB_TOKEN` package permission.

Publishing an image does **not** mean the HTTP MCP endpoint is approved for unrestricted public hosting. The container remains subject to the authentication/gateway/quotas/abuse requirements documented in `docs/hosted-mcp.md`.

## OpenAI Skills-only submission

Use [`openai-plugin-submission.md`](openai-plugin-submission.md) for:

- store/listing copy;
- five starter prompts;
- five positive review cases;
- three negative/boundary cases;
- privacy/safety statements;
- release notes;
- final publisher checklist.

The directory release and the public MCP release are separate milestones.

## Add a hosted MCP connection later

Only after public-hosting gates are complete:

1. choose a canonical public HTTPS MCP hostname;
2. deploy behind reviewed identity/authentication controls;
3. add revocation, quotas, rate limiting, abuse controls, monitoring, and retention policy;
4. run bilingual remote MCP validation;
5. register/verify the connection with the target platform;
6. add the final registered MCP mapping to the plugin package;
7. re-run directory tests before publishing the combined Skills+MCP version.

See `docs/public-launch-decisions.md` and `ROADMAP.md`.
