# Plugin Packaging and Distribution

The repository is a valid **Skills-only Codex plugin package** for local
installation and invited alpha testing. It is not yet a public-directory
submission and does not bundle or reference the live MCP connection.

## Current package

```text
.
├── .codex-plugin/
│   └── plugin.json
├── .agents/
│   └── plugins/
│       └── marketplace.json
└── skills/
    ├── open-source-project-research/
    │   └── SKILL.md
    ├── open-source-project-comparison/
    │   └── SKILL.md
    └── open-source-stack-planner/
        └── SKILL.md
```

Only `plugin.json` belongs in `.codex-plugin/`. Skills, future MCP mappings and
future visual assets remain at the plugin root.

## Why the package is Skills-only today

The repository contains a local stdio MCP server, but the plugin manifest does
not declare `mcpServers` or `apps` yet.

A bundled `.mcp.json` needs a portable command guaranteed to exist after plugin
installation. The current `osi-mcp` command belongs to a project-specific Python
environment and cannot be assumed to exist on an arbitrary user's machine.

An `.app.json` mapping requires a registered MCP connection technical ID. That
ID should be committed only after the publishing organization and endpoint are
final. A broad hosted release also needs a production-grade public MCP endpoint,
authentication and abuse controls.

Publishing a broken MCP reference would be worse than publishing a clear
Skills-only alpha. The current package exposes the three workflows, while
developers can connect the local MCP server separately through
[`codex-setup.md`](codex-setup.md).

## Manifest decisions

`.codex-plugin/plugin.json` includes:

- stable kebab-case identity;
- semantic version;
- publisher, repository and product links;
- the `./skills/` package path;
- install-surface descriptions;
- read/research/compare capabilities;
- starter prompts;
- brand color;
- an explicit statement that live project facts require a separately configured
  MCP connection.

It intentionally omits:

- `license`, because no open-source license has been granted;
- public legal URLs, because plugin-specific legal pages are not final;
- `mcpServers`, because there is no portable bundled MCP command yet;
- `apps`, because there is no final registered hosted MCP technical ID;
- image paths, because final icon, logo and screenshots are not ready.

Do not add placeholder or inaccurate legal, license, asset or MCP fields merely
to make the manifest look complete.

## Repo-scoped marketplace

`.agents/plugins/marketplace.json` exposes the repository-root plugin as a local
entry. Codex can register the repository marketplace:

```bash
codex plugin marketplace add zxhwolfe-dev/aiworkstation-open-source-intelligence --ref main
codex plugin marketplace list
```

For a local clone:

```bash
codex plugin marketplace add /ABSOLUTE/PATH/TO/aiworkstation-open-source-intelligence
codex plugin marketplace list
```

Local marketplace installation tests only the packaged Skills. Configure the
stdio MCP server separately until the plugin receives a valid MCP mapping.

## Offline package validation

Run:

```bash
python -m pip install -e ".[mcp]"
osi-validate-plugin --root .
```

The validator checks:

- manifest identity and semantic version;
- package paths that remain inside the plugin root;
- the rule that `.codex-plugin/` contains only `plugin.json`;
- Skill directory presence, frontmatter names and descriptions;
- install-surface descriptions, prompts, color and read-only capabilities;
- optional `.mcp.json` and `.app.json` targets when declared;
- marketplace identity, local source path, policy and category;
- intentional public-release blockers such as missing license and legal URLs.

The command exits successfully when the local Skills package is structurally
ready. Its report keeps `public_submission_ready=false` while legal or
publication gates remain unresolved.

Low-level checks:

```bash
python -m json.tool .codex-plugin/plugin.json >/dev/null
python -m json.tool .agents/plugins/marketplace.json >/dev/null
python -m unittest tests.test_plugin_package -v
python -m unittest tests.test_plugin_validation -v
```

Then verify locally:

- the marketplace appears as `AI Workstation Local Plugins`;
- the plugin appears as `AI Open Source Intelligence`;
- all three Skills are available;
- starter prompts cover project research, comparison and stack planning;
- the package does not claim write access or a live MCP connection;
- a Skill without MCP access discloses that current facts are unavailable.

## Deterministic alpha ZIP

Build a reviewable Skills-only archive:

```bash
osi-build-alpha --root . --output-dir dist/alpha
```

The output directory contains:

```text
aiworkstation-open-source-intelligence-skills-0.1.0.zip
SHA256SUMS
bundle-report.json
```

Verify the archive:

```bash
(
  cd dist/alpha
  sha256sum --check SHA256SUMS
)
```

The builder:

- reads the package name and version from `plugin.json`;
- includes only the two distribution manifests, three Skill directories and a
  reviewed documentation/security/privacy allowlist;
- rejects symlinks, non-UTF-8 files, oversized files and credential-like text;
- writes fixed timestamps and permissions for reproducible ZIP bytes;
- embeds `BUNDLE-MANIFEST.json` with per-file size and SHA-256 values;
- emits an external archive checksum and machine-readable report;
- explicitly declares `distribution_mode=skills-only` and
  `live_mcp_bundled=false`.

It excludes:

- `src/` and the local MCP implementation;
- `tests/` and `.github/`;
- `pyproject.toml` and editable-install assumptions;
- temporary captures and validation artifacts;
- credentials, local configuration and environment files.

Two builds from the same source tree must produce identical archive bytes. The
unit suite checks reproducibility, package contents and checksums.

## Manual packaging workflow

The repository includes:

```text
.github/workflows/alpha-package.yml
```

This workflow is manually triggered and read-only. It:

1. installs the reviewed source tree;
2. runs the full unit suite;
3. validates the plugin package;
4. builds the deterministic archive;
5. verifies `SHA256SUMS`;
6. inspects the ZIP for required and forbidden paths;
7. uploads the package only if all gates pass.

The workflow never creates a release or tag and has no repository write
permission. A human still decides whether the resulting artifact is fit for an
invited alpha.

## Add the MCP connection later

Choose exactly one packaging route after live validation.

### Route A: registered MCP connection

Use this for hosted ChatGPT/plugin testing:

1. deploy a hardened MCP endpoint;
2. validate authentication, host checks, rate limits and logging;
3. register the endpoint with the intended publishing organization;
4. copy the final technical ID;
5. add a root `.app.json` mapping;
6. add the matching manifest field;
7. test the installed combined plugin in a new chat.

Do not commit an organization-specific technical ID until the publisher and
endpoint are final.

### Route B: bundled MCP server

Use this only when installation supplies a portable executable without manual
project setup:

1. define a root `.mcp.json` server map;
2. ensure the command works from the installed plugin cache;
3. avoid hard-coded developer paths;
4. add the matching manifest field;
5. test enable/disable and approval policy from a clean install.

The current editable Python installation does not satisfy this portability gate.

## External-alpha gates

Use [`external-alpha-checklist.md`](external-alpha-checklist.md). At minimum:

- standard CI succeeds on supported Python versions;
- the manual live contract workflow passes in Chinese and English;
- captured fixtures pass validation, replay and manual sanitization review;
- the Skills-only package validates and its checksum is verified;
- the archive is tested in a clean environment;
- critical and high-severity findings are closed or block the release;
- testers receive [`alpha-tester-guide.md`](alpha-tester-guide.md).

## Public submission gates

Do not enter a broad public submission flow until:

- the intended publisher identity is verified;
- public website, support contact, privacy policy and terms are ready;
- English and Chinese evaluation cases pass;
- GitHub Actions and public Radar validation pass;
- any MCP endpoint has production authentication and abuse controls;
- all six tools expose correct names, schemas and read-only annotations;
- reviewer prompts and test cases are ready;
- country availability and policy attestations are decided;
- a software license is selected before the manifest claims one.

## References

- Plugin packaging and distribution documentation
- ChatGPT/plugin connection and testing documentation
- Codex MCP configuration documentation

Verify current platform requirements from the official provider documentation
before a public submission because directory and manifest rules may change.
