# Frequently Asked Questions

## What is AI Workstation Open Source Intelligence?

It is an evidence-backed research and technology-selection layer for open-source
AI projects. The current product combines one unified Skill with nine read-only
MCP tools for Radar browsing, project discovery, fact and license verification,
comparison, alternatives and candidate stack planning.

## Is this traditional OSINT?

No. “Open Source Intelligence” here means intelligence about **open-source AI
software projects**. It is not a people-investigation, surveillance or general
web-intelligence toolkit.

## Why one Skill instead of three?

Users should not have to choose between project research, comparison and stack
planning before the task begins. The single `ai-open-source-intelligence` Skill
classifies the request and applies the right workflow while preserving the same
evidence, license and hard-constraint rules.

## Does the Skill alone access live Radar data?

No. The Skill provides workflow and decision boundaries. Current facts require
the companion MCP connection. Without live tools, the Skill may explain a
method or verification plan, but it must not invent current project or license
facts.

## What does MCP add?

The MCP server exposes nine structured read-only tools. Six support selection,
verification, comparison, alternatives and stack planning; three browse the
current Radar overview, project collections and Radar Skills library.

The canonical Hosted endpoint is:

```text
https://mcp.aiworkstation.cn/mcp
```

## Which online capabilities are exposed today?

- browse current Radar views, rankings, collections, categories and scenarios;
- browse the Radar Skills library;
- search open-source AI projects from typed requirements;
- fetch current public project facts;
- inspect direct license evidence;
- compare two to five projects;
- find alternatives without weakening hard constraints;
- compose a candidate open-source AI stack and disclose compatibility risks.

## Does MCP expose the whole AI Workstation website?

No. It exposes only the nine declared data/evidence tools. Account features,
private databases, internal operations, payments, Premium inference and website
administration are not exposed.

## Are all tools read-only?

Yes. The nine-tool contract is read-only, non-destructive and idempotent from
the user's business-data perspective. Tools never install or execute
third-party repository code. Some selector requests may create and poll a
short-lived upstream computation task; that control-plane effect is disclosed
and does not modify user or third-party business data.

## Does searching consume AI Workstation model tokens?

No. Requirement-based selector calls use `use_model=false`. ChatGPT, Codex or
another host uses its own model to understand the request and synthesize the
answer; AI Workstation returns public Radar data/evidence and does not run a
second server-side model on this path.

Any future server-model capability must be a separately reviewed product
version with explicit disclosure, identity, quota, privacy and cost controls.

## Why not just let ChatGPT search the web?

General web search finds pages. This product adds a maintained decision
contract: stable project identity, snapshot consistency, evidence levels,
direct-license requirements, hard-constraint handling, explicit no-match
states and a separation between verified facts and analysis.

## What does “verified” mean?

Only fields that cross the explicit evidence boundary enter `verified_facts`.
Values in `data`, recommendations or editorial projections can still be useful,
but are not automatically promoted to verified facts.

## Does a visible license label mean commercial use is safe?

No. Missing or ambiguous evidence remains unknown. Non-standard, custom or
multiple licenses require manual review. License output is technical evidence,
not legal advice.

## Why can `compose_ai_stack` return integration risks?

Individual components can be verified independently while cross-project
compatibility remains untested. A plausible architecture is not a verified
integration claim.

## What happens when nothing satisfies the requirements?

The correct result is an explicit no-match. Hard requirements are not silently
relaxed. Near matches, when shown, remain separate and disclose their blocker.

## Which languages are validated?

The public validation suite covers English (`en`) and Simplified Chinese
(`zh`).

## Is the repository open source?

Yes. The repository is Apache-2.0. That license does not grant rights to private
AI Workstation databases, unpublished datasets, hosted infrastructure or
trademarks.

## Is the Hosted MCP deployed?

Yes. `v0.3.0` is deployed at the canonical HTTPS endpoint in anonymous,
read-only, data-only mode. The container remains on host loopback behind an
Nginx/TLS gateway with request-body, connection and per-IP request controls.
The endpoint has no OAuth, Premium or server-model path in this release.

Production deployment does not mean the combined plugin is already listed in
the public Plugins Directory. Directory submission, publisher verification,
policy review, fresh-install acceptance and staged real-user Alpha testing are
separate remaining steps.

## How do I use it before directory approval?

- ChatGPT web: create a **No Authentication** developer-mode app for the Hosted
  MCP URL.
- Codex / ChatGPT desktop: install the versioned Skill marketplace, then add
  the Hosted URL in Codex MCP configuration.
- Python: install
  `aiworkstation-open-source-intelligence[mcp]==0.3.0`.

See [`QUICKSTART.md`](QUICKSTART.md) for exact steps.
