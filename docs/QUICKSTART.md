# Quickstart

AI Workstation Open Source Intelligence `v0.3.0` has one user-facing Skill and
nine anonymous, read-only Hosted MCP tools.

The repository Plugin now bundles the Skill and the Hosted MCP connection in a
single package for Codex and the ChatGPT desktop Codex host. The immutable
`v0.3.0` release archive predates this packaging change, so publish the complete
package under a new patch version instead of rebuilding `v0.3.0`. The public
ChatGPT directory submission is not yet approved; until then, ChatGPT web users
can still use the MCP endpoint directly in Developer mode.

## Fastest live-data path: ChatGPT web

ChatGPT Developer mode is intended for developers testing remote MCP servers.
It is currently available to eligible Pro, Plus, Business, Enterprise and
Education accounts on the web.

1. In ChatGPT, open **Settings -> Security and login** and enable
   **Developer mode**.
2. Open [ChatGPT Plugins](https://chatgpt.com/plugins).
3. Select the plus button and create a developer-mode app.
4. Enter:

   ```text
   Name: AI Open Source Intelligence
   MCP URL: https://mcp.aiworkstation.cn/mcp
   Authentication: No Authentication
   ```

5. In a new conversation, choose **Developer mode** from the plus menu and
   select the app.
6. Start with one of the prompts below.

Developer-mode apps appear under **Drafts**. Refresh the app from its details
page whenever the server's tools or descriptions change. See the official
[ChatGPT Developer mode documentation](https://developers.openai.com/api/docs/guides/developer-mode).

This path connects the live tools; it does not install the repository Skill.
The reviewed public Plugin will provide the complete one-install experience in
ChatGPT web after directory approval.

## Complete Plugin in Codex / ChatGPT desktop

After this packaging change reaches `main`, add the repository marketplace:

```bash
codex plugin marketplace add \
  zxhwolfe-dev/aiworkstation-open-source-intelligence \
  --ref main
codex plugin marketplace list
```

Open the Plugins Directory, select the added marketplace, and install
**AI Open Source Intelligence**. That single install includes both:

```text
Skill: ai-open-source-intelligence
Hosted MCP: https://mcp.aiworkstation.cn/mcp
```

Restart the client and confirm the connection with `codex mcp list` or `/mcp`
in the Codex TUI. Codex CLI, the Codex IDE extension and the ChatGPT desktop app
on the same Codex host share the installed Plugin configuration. See the
official [Plugin packaging documentation](https://developers.openai.com/plugins/build/plugins).

The immutable `v0.3.0` Marketplace entry is Skills-only. Users intentionally
pinned to that tag must either upgrade to the next patch release or add the
production Hosted MCP manually:

```toml
[mcp_servers.ai_open_source_intelligence]
url = "https://mcp.aiworkstation.cn/mcp"
enabled = true
required = false
default_tools_approval_mode = "auto"
startup_timeout_sec = 20
tool_timeout_sec = 60
```

See the official [Codex MCP documentation](https://developers.openai.com/codex/mcp)
for manual connection troubleshooting.

## Nine Hosted tools

The production endpoint is:

```text
https://mcp.aiworkstation.cn/mcp
```

It exposes exactly:

```text
search_ai_projects
get_project_facts
get_license_evidence
compare_ai_projects
find_alternatives
compose_ai_stack
get_radar_overview
browse_radar_projects
browse_radar_skills
```

The host model performs reasoning and final synthesis. AI Workstation supplies
public Radar data/evidence only; the current product has no server-model or
Premium tool.

## Python / CLI installation

Use the published package for scripting, local MCP hosting or integration
development:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install \
  "aiworkstation-open-source-intelligence[mcp]==0.3.0"
```

Inspect or call the deterministic offline provider:

```bash
OSI_PROVIDER=mock osi-m0 provider-info
OSI_PROVIDER=mock osi-m0 list-tools
OSI_PROVIDER=mock osi-m0 invoke search_ai_projects \
  --arguments '{"query":"Find a self-hosted RAG project with Docker and a Web UI.","locale":"en"}'
```

Start a local stdio MCP server against live public Radar data:

```bash
OSI_PROVIDER=http \
AIWORKSTATION_RADAR_BASE_URL=https://aiworkstation.cn \
osi-mcp
```

Requirement-based selector requests keep AI Workstation model execution
disabled with `use_model=false`.

## Repository development

For editable development from a reviewed checkout:

```bash
git clone https://github.com/zxhwolfe-dev/aiworkstation-open-source-intelligence.git
cd aiworkstation-open-source-intelligence
git checkout v0.3.0
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[mcp]"
python -m unittest discover -s tests -v
osi-validate-plugin --root .
```

Use [`codex-setup.md`](codex-setup.md) for the complete Hosted and local stdio
configuration.

## Recommended first prompts

- Show me the current AI Open Source Radar and its useful categories or rankings.
- Find a self-hosted RAG platform with Docker and a Web UI. Treat those as hard requirements and low-code as a preference.
- Compare Dify and RAGFlow for an enterprise knowledge base.
- Check whether `infiniflow/ragflow` has directly verifiable license evidence.
- Find alternatives to a named project while keeping private deployment as a hard requirement.
- Design an open-source stack for internal document question answering and identify the biggest compatibility unknown.
- Find a project that is cloud-only, fully offline and requires no local installation; return an explicit no-match if the constraints conflict.

## Result and safety model

Every successful tool response separates:

```text
data
verified_facts
recommendations
unknowns
risks
```

- Do not submit passwords, API keys, private source code, customer records or confidential documents.
- The tools are read-only and never install or execute third-party repository code.
- Missing or ambiguous license evidence is not permission and is not legal advice.
- Hard requirements are not silently weakened to manufacture a match.
- The current Skill/MCP path does not call an AI Workstation server-side model.
