# Plugin Packaging and Distribution

The repository is now a valid **skills-only Codex plugin package** for local
installation and workflow testing. It is not yet a public-directory submission
and does not yet bundle or reference the live MCP connection.

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

The repository already contains a local stdio MCP server, but the plugin
manifest deliberately does not declare `mcpServers` or `apps` yet.

A bundled `.mcp.json` would need a portable command that is guaranteed to exist
after plugin installation. The current `osi-mcp` command is installed into a
project-specific Python environment and cannot safely be assumed to exist on an
arbitrary user's machine.

An `.app.json` mapping requires a registered MCP server connection technical ID.
That ID is created only after the MCP endpoint has been connected in ChatGPT
developer mode. A public submission also requires a public HTTPS Streamable HTTP
endpoint; the local stdio server alone is not sufficient.

Publishing a broken MCP reference would be worse than publishing a clear
Skills-only alpha. The current package therefore exposes the three workflows,
while developers can connect the local MCP server separately through
[`codex-setup.md`](codex-setup.md).

## Manifest decisions

`.codex-plugin/plugin.json` currently includes:

- stable kebab-case identity;
- semantic version;
- publisher, repository and product links;
- the `./skills/` package path;
- install-surface descriptions;
- read/research/compare capabilities;
- starter prompts;
- brand color.

It intentionally omits:

- `license`, because no open-source license has been granted;
- `privacyPolicyURL` and `termsOfServiceURL`, because plugin-specific public
  legal pages have not been published;
- `mcpServers`, because there is no portable bundled MCP command yet;
- `apps`, because there is no registered hosted MCP technical ID yet;
- image paths, because final icon, logo and screenshots have not been prepared.

Do not add placeholder or inaccurate legal, license, asset or MCP fields merely
to make the manifest look complete.

## Repo-scoped marketplace

`.agents/plugins/marketplace.json` exposes the repository-root plugin as a local
entry. From a local clone, the ChatGPT desktop app can use the repo marketplace
after restart. Codex can also register a marketplace source:

```bash
codex plugin marketplace add zxhwolfe-dev/aiworkstation-open-source-intelligence --ref main
codex plugin marketplace list
```

For a purely local clone:

```bash
codex plugin marketplace add /ABSOLUTE/PATH/TO/aiworkstation-open-source-intelligence
codex plugin marketplace list
```

Local marketplace installation tests only the packaged Skills. Configure the
stdio MCP server separately until the plugin receives a proper MCP mapping.

## Offline package validation

Run the package validator from the repository root:

```bash
python -m pip install -e ".[mcp]"
osi-validate-plugin --root .
```

The validator checks:

- required manifest identity and semantic version;
- `./`-prefixed paths that remain inside the plugin root;
- the rule that `.codex-plugin/` contains only `plugin.json`;
- Skill directory presence, frontmatter names and descriptions;
- install-surface descriptions, prompts, color and read-only capabilities;
- optional `.mcp.json` and `.app.json` targets when declared;
- marketplace identity, local source path, policy and category;
- intentional public-release blockers such as missing license and legal URLs.

The command exits successfully when the local Skills package is structurally
ready. Its JSON report keeps `public_submission_ready=false` while legal or
publication gates remain unresolved.

Low-level checks remain useful:

```bash
python -m json.tool .codex-plugin/plugin.json >/dev/null
python -m json.tool .agents/plugins/marketplace.json >/dev/null
python -m unittest tests.test_plugin_package -v
python -m unittest tests.test_plugin_validation -v
```

Then restart the ChatGPT desktop app and verify:

- the marketplace appears as `AI Workstation Local Plugins`;
- the plugin appears as `AI Open Source Intelligence`;
- all three Skills are available;
- starter prompts describe project research, comparison and stack planning;
- the package does not claim write access or a live MCP connection.

## Add the MCP connection later

Choose exactly one packaging route after live validation.

### Route A: registered MCP connection

Use this for ChatGPT and public-plugin testing:

1. Deploy or tunnel a Streamable HTTP MCP endpoint.
2. Enable ChatGPT developer mode.
3. Register the endpoint in ChatGPT Plugins.
4. Copy the generated technical ID beginning with `plugin_asdk_app`.
5. Add a root `.app.json` mapping.
6. Add `"apps": "./.app.json"` to `plugin.json`.
7. Test the installed combined plugin in a new chat.

Do not commit an organization-specific technical ID until the intended
publishing organization and endpoint are final.

### Route B: bundled MCP server

Use this only when installation supplies a portable executable without manual
project setup:

1. Define a root `.mcp.json` direct or wrapped server map.
2. Ensure its command works from the installed plugin cache.
3. Avoid hard-coded developer paths.
4. Add `"mcpServers": "./.mcp.json"` to `plugin.json`.
5. Test enable/disable and approval policy from Codex plugin configuration.

The current editable Python installation does not satisfy this portability gate.

## Public submission gates

A public plugin may be Skills-only, MCP-only or combined. This project should
not enter the submission portal until:

- the intended publisher identity is verified;
- public website, support contact, privacy policy and terms are ready;
- the Skill package passes local marketplace tests;
- English and Chinese evaluation cases pass;
- GitHub Actions succeeds on supported Python versions;
- the public Radar probes and sanitized contract fixtures pass;
- any MCP endpoint is public HTTPS Streamable HTTP and passes MCP Inspector;
- all six tools expose correct names, descriptions, schemas and read-only
  annotations;
- starter prompts and reviewer test cases are prepared;
- country availability and policy attestations are decided;
- an actual software license is selected before the manifest claims one.

## Official references

- Package plugins: <https://developers.openai.com/plugins/build/plugins>
- Connect and test: <https://developers.openai.com/plugins/deploy/connect-chatgpt>
- Submit plugins: <https://developers.openai.com/plugins/deploy/submission>
- Codex MCP configuration: <https://developers.openai.com/codex/mcp>
