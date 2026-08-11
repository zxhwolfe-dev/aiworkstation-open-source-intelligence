# AI Open Source Intelligence

**One Skill. Nine live read-only Radar tools. Evidence-backed open-source AI research without a second server-side model call.**

[简体中文](README.zh-CN.md) · [AI Workstation](https://aiworkstation.cn/) · [AI Open Source Radar](https://aiworkstation.cn/githubai/) · [Quickstart](docs/QUICKSTART.md)

AI Open Source Intelligence is the Skills/MCP product layer for **AI Open Source Radar**.

## Product shape

```text
User in ChatGPT / Codex / compatible host
                 |
                 v
      1 unified product Skill
                 |
                 v
      9 read-only MCP tools
                 |
                 v
     AI Workstation public Radar
```

The user does not choose separate research/comparison/stack Skills. The single Skill routes the task internally.

The **host model** performs natural-language reasoning and synthesis. The AI Workstation server provides data/evidence only on this product path.

## One active Skill

```text
ai-open-source-intelligence
```

It handles:

- browsing rankings, collections, categories, scenarios and the Radar Skills library;
- finding projects from deployment, privacy, integration, budget and license requirements;
- verifying named-project facts and license evidence;
- comparing two to five projects for a concrete use case;
- finding alternatives while preserving hard requirements;
- planning candidate open-source AI stacks and exposing unverified compatibility.

The only product Skill is packaged from:

```text
product-skills/ai-open-source-intelligence/SKILL.md
```

The previous split research/comparison/stack Skill files are removed from the current product and distribution bundle.

## Nine standard MCP tools

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

All nine are read-only. They do not execute or install third-party repository code.

## No AI Workstation server-model execution

This is a hard product boundary for the current release.

The Hosted MCP exposes **no Premium model tool**, no checkout tool and no runtime OAuth/Premium switch. Requirement-based selection calls the public Radar selector with:

```text
use_model=false
```

Therefore an ordinary Skill/MCP workflow is:

```text
ChatGPT/Codex host model
        -> chooses/read tools
        -> AI Workstation public Radar data/evidence
        -> host model synthesizes the final answer
```

It is **not**:

```text
host model -> AI Workstation model -> second model bill
```

If member-linked server-model capabilities are added later, they must ship as a new reviewed product version rather than being enabled through a hidden environment variable.

## Evidence model

Every tool result separates:

1. **verified facts** — source-backed observations that crossed the evidence boundary;
2. **recommendations** — host-model/rules analysis;
3. **unknowns** — unavailable or unverified information;
4. **risks** — license, maintenance, deployment, security and integration limits.

A value in `data` is not automatically a verified fact. License evidence is deliberately stricter and is technical evidence, not legal advice.

## Official resources in results

MCP tool results include canonical, non-tracking publisher links under:

```text
data.official_resources
```

with:

- AI Workstation — https://aiworkstation.cn/
- AI Open Source Radar — https://aiworkstation.cn/githubai/
- this open-source project — https://github.com/zxhwolfe-dev/aiworkstation-open-source-intelligence

The unified Skill may show these once at the end of a normal user-facing answer. They are kept separate from verified facts so publisher attribution never changes a research conclusion.

## Hosted MCP

Canonical endpoint:

```text
https://mcp.aiworkstation.cn/mcp
```

Current Hosted mode is intentionally:

```text
anonymous
read-only
data-only
9 tools
no OAuth
no WorkOS dependency
no Premium/server model
```

The container stays on host loopback `127.0.0.1:8001` behind Nginx/TLS.

### Anonymous abuse controls

The gateway uses two per-IP request windows plus a connection cap:

- short-window: `60 requests/minute`, burst `30`;
- sustained: `10 requests/minute`, burst `300`;
- concurrent connections: `10` per IP;
- MCP request body: `256 KB` maximum;
- unrelated paths on the dedicated MCP hostname return `404`.

This is intentionally request-based rather than token-based because the nine data tools do not consume AI Workstation model tokens.

## Use it now

The repository Plugin now packages the unified Skill and the production Hosted
MCP configuration together. After this change reaches `main`, Codex and the
ChatGPT desktop Codex host can install both from one marketplace entry. The
public ChatGPT directory listing is still pending review. Today:

- Codex / ChatGPT desktop users can install the complete repository Plugin;
- ChatGPT web users can register `https://mcp.aiworkstation.cn/mcp` as a
  **No Authentication** developer-mode app while the public listing is pending;
- Python users can install the released CLI/MCP package with:

```bash
python -m pip install \
  "aiworkstation-open-source-intelligence[mcp]==0.3.0"
```

See the [Quickstart](docs/QUICKSTART.md) for exact ChatGPT, Codex and Python
steps. The immutable `v0.3.0` archive remains the earlier Skills-only artifact;
publish the complete Plugin under a new patch version rather than replacing it.

## Local development

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[mcp]"
```

Offline fixture data:

```bash
OSI_PROVIDER=mock osi-mcp
```

Live public Radar data:

```bash
OSI_PROVIDER=http \
AIWORKSTATION_RADAR_BASE_URL=https://aiworkstation.cn \
osi-mcp
```

Hosted configuration check requires an exact candidate identity:

```bash
OSI_PROVIDER=http \
OSI_HOSTED_ACCESS_MODE=public \
OSI_RELEASE_COMMIT=<exact-40-char-sha> \
OSI_IMAGE_COMMIT=<same-exact-40-char-sha> \
osi-mcp-hosted --check-config
```

Setting `OSI_HOSTED_ACCESS_MODE=oauth` fails closed in the current release.

## Safety rules

- never execute third-party repository code as part of research;
- never infer permission from a missing license;
- never silently weaken a hard requirement to manufacture a match;
- never claim cross-project compatibility without evidence or a controlled test;
- never substitute model memory for unavailable live evidence;
- never enable AI Workstation server-side model execution in the current standard Skill/MCP path.

## Development checks

```bash
python -m compileall -q src tests
python -m unittest discover -s tests -v
osi-validate-plugin --root .
osi-readiness --root .
```

CI covers Python 3.10 and 3.12, deterministic Skill packaging, MCP round trips, data-only Hosted configuration and container packaging.

## License

The public repository is licensed under Apache-2.0. That does not grant rights to private AI Workstation databases, unpublished datasets, credentials, infrastructure or trademarks.
