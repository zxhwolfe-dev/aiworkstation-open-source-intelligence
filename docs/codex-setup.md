# Connect the Local MCP Server to Codex

This guide connects the repository's **local stdio MCP server** to Codex CLI,
the Codex IDE extension, or the ChatGPT desktop app on the same Codex host.

The server remains read-only. Start with the offline mock provider, verify tool
discovery, and then opt into the public AI Workstation HTTP provider.

## 1. Install the project

From the repository root:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[mcp]"
python -m unittest discover -s tests -v
```

Resolve the absolute executable path:

```bash
realpath .venv/bin/osi-mcp
```

Use the returned absolute path in the commands below. A relative path can fail
when Codex starts the MCP process from a different working directory.

## 2. Add the offline server first

```bash
codex mcp add ai-open-source-intelligence \
  --env OSI_PROVIDER=mock \
  -- /ABSOLUTE/PATH/TO/aiworkstation-open-source-intelligence/.venv/bin/osi-mcp
```

Confirm registration:

```bash
codex mcp list
```

Restart the Codex client after changing MCP configuration. In a new session,
ask Codex to list available MCP tools or run a low-risk test such as:

```text
Use the open-source intelligence tools to search for a self-hosted RAG project.
This is the offline test provider, so explicitly show the MOCK_DATA warning.
```

Expected tool names:

- `search_ai_projects`
- `get_project_facts`
- `get_license_evidence`
- `compare_ai_projects`
- `find_alternatives`
- `compose_ai_stack`

## 3. Switch to the public AI Workstation provider

Remove or edit the previous entry, then add the live read-only variant:

```bash
codex mcp add ai-open-source-intelligence-live \
  --env OSI_PROVIDER=http \
  --env AIWORKSTATION_RADAR_BASE_URL=https://aiworkstation.cn \
  --env OSI_HTTP_TIMEOUT_SECONDS=30 \
  --env OSI_HYDRATE_LIMIT=5 \
  -- /ABSOLUTE/PATH/TO/aiworkstation-open-source-intelligence/.venv/bin/osi-mcp
```

Before relying on live output, run the contract probe from the same environment:

```bash
source .venv/bin/activate
osi-probe --base-url https://aiworkstation.cn --locale en
osi-probe --base-url https://aiworkstation.cn --locale zh
```

A failed probe is a contract or connectivity problem, not permission to bypass
the fail-closed checks.

## 4. Run the automated Codex Live acceptance

For release evidence, prefer the one-command acceptance runner instead of a long
manual conversation:

```bash
source .venv/bin/activate
osi-codex-acceptance \
  --root . \
  --provider http \
  --base-url https://aiworkstation.cn \
  --output tmp/codex-acceptance/live.json
```

The command runs `codex exec` in an ephemeral, read-only sandbox and injects one
temporary MCP server through inline Codex configuration. It does **not** persist
or rewrite `~/.codex/config.toml`.

The acceptance workflow asks Codex to exercise all nine tools against live public
Radar data. The MCP process writes a separate privacy-safe JSONL ledger containing
only tool name, outcome, duration, level and error code. Queries, constraints,
project IDs, tool arguments, result payloads, raw request IDs and the Codex
conversation are not written to the ledger.

A passing report requires:

- the `codex exec` process to exit successfully; and
- at least one actual `success` ledger event for every one of the six declared
  MCP tools.

This is stronger evidence than relying on Codex's final prose to claim which
tools it used. Keep the generated report and ledger with the private validation
records. Do not set `--codex-tested` in release readiness unless this real Codex
acceptance has passed on the target Codex host.

The runner uses current Codex CLI capabilities: non-interactive `codex exec`,
ephemeral sessions, read-only sandboxing and inline `-c` configuration overrides.
If the installed Codex version rejects those options, update Codex or run the
manual MCP workflow instead; do not weaken the MCP server's read-only contract.

## 5. Configure with TOML instead of the CLI

Codex reads MCP configuration from `~/.codex/config.toml`. For a trusted project,
you can also place it in `.codex/config.toml` to keep the server scoped to that
project.

Copy [`../examples/codex-config.toml`](../examples/codex-config.toml), replace the
placeholder absolute paths, and add it to the appropriate config file.

Important settings used by the example:

- `command`: absolute path to `.venv/bin/osi-mcp`;
- `cwd`: absolute repository path;
- `env`: explicit provider variables;
- `enabled_tools`: allowlist limited to the six read-only tools;
- `startup_timeout_sec`: server startup budget;
- `tool_timeout_sec`: maximum time for one public Radar request workflow;
- `required = false`: Codex can still start if this pre-release server fails;
- `default_tools_approval_mode = "prompt"`: conservative approval behavior during
  alpha validation.

After the provider and tool annotations have been validated in the target Codex
version, approval settings can be tightened without changing business logic.

## 6. Troubleshooting

### Server does not appear

```bash
codex mcp list
codex mcp --help
```

Check that the configured executable exists and is executable:

```bash
ls -l /ABSOLUTE/PATH/TO/.venv/bin/osi-mcp
```

### Server starts but tool calls fail

Run the same provider outside Codex:

```bash
OSI_PROVIDER=mock osi-m0 provider-info
OSI_PROVIDER=mock osi-m0 invoke search_ai_projects \
  --arguments '{"query":"self-hosted RAG"}'
```

For the live provider:

```bash
OSI_PROVIDER=http \
AIWORKSTATION_RADAR_BASE_URL=https://aiworkstation.cn \
osi-m0 invoke get_project_facts \
  --arguments '{"project_id":"infiniflow/ragflow","locale":"en"}'
```

### Automated Codex acceptance fails

Inspect the generated acceptance JSON first. `missing_tools` means Codex did not
produce a successful call for every tool. A nonzero `codex_returncode` means the
Codex process itself failed or could not initialize the required MCP server.
The safe ledger can be inspected directly without exposing prompts or results.

The acceptance runner intentionally does not persist Codex configuration, copy
authentication files, bypass the Codex sandbox, or use `--yolo`.

### Live provider rejects an answer

This is expected when the public response lacks snapshot identity, evidence
status, a public notice for partial coverage, or a safe license observation.
Capture sanitized response fixtures with the contract-capture command before
changing the adapter.

## Official references

- Codex MCP configuration: <https://developers.openai.com/codex/mcp>
- Codex CLI reference: <https://developers.openai.com/codex/cli/reference>
- Codex configuration reference: <https://developers.openai.com/codex/config-reference>
- MCP Python SDK: <https://github.com/modelcontextprotocol/python-sdk>
