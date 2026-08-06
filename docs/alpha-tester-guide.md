# External Alpha Tester Guide

This guide is for a small, invited alpha group testing the three Skills and six
read-only MCP tools. The alpha is not a hosted public product and does not carry
a service-level guarantee.

## What testers receive

The alpha may be tested in two modes:

### Skills-only package

Contains:

- `open-source-project-research`
- `open-source-project-comparison`
- `open-source-stack-planner`

This mode teaches the agent the workflow and safety boundaries. It does not
provide live Radar tools by itself. The Skill must disclose that live facts are
unavailable rather than fabricate results.

### Local MCP mode

Adds six read-only tools:

- `search_ai_projects`
- `get_project_facts`
- `get_license_evidence`
- `compare_ai_projects`
- `find_alternatives`
- `compose_ai_stack`

Start with the offline mock provider, then enable the public HTTP provider only
after the tester understands the data and license limitations.

## Test environment

Recommended:

- Python 3.12;
- a fresh virtual environment;
- a current Codex CLI or another MCP host;
- no production credentials in the environment;
- a disposable working directory.

Install from a reviewed repository checkout:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[mcp]"
python -m unittest discover -s tests -v
```

Follow [`codex-setup.md`](codex-setup.md) to connect `osi-mcp`.

## First test: offline mock

Run:

```bash
OSI_PROVIDER=mock osi-mcp
```

Expected behavior:

- exactly six tools are visible;
- tool calls return structured results;
- `MOCK_DATA` appears as a high-severity risk;
- mock results are not described as current project facts;
- invalid arguments return stable model-readable errors;
- no repository code is executed.

## Second test: public read-only provider

After offline testing:

```bash
export OSI_PROVIDER=http
export AIWORKSTATION_RADAR_BASE_URL=https://aiworkstation.cn
export OSI_HTTP_TIMEOUT_SECONDS=30
export OSI_HYDRATE_LIMIT=5
osi-mcp
```

Expected behavior:

- only anonymous public Radar endpoints are read;
- project facts include source and observation information;
- missing licenses remain unknown;
- non-standard licenses carry manual-review risk;
- no-match results are explicit;
- near matches are not silently promoted;
- project comparisons reject mixed snapshots;
- stack compatibility remains a recommendation until tested.

## Required scenarios

Test at least these six tasks:

1. Find a Docker-based self-hosted RAG project with a Web UI.
2. Verify deployment and license evidence for one named project.
3. Compare Dify and RAGFlow for a clearly stated enterprise use case.
4. Find a lighter alternative while preserving one hard deployment constraint.
5. Design a small internal knowledge-base stack and identify the highest-risk
   compatibility unknown.
6. Provide mutually incompatible requirements and confirm an honest no-match
   answer.

Run at least one scenario in Chinese and one in English.

## What not to test

Do not:

- submit passwords, API keys, customer documents or private source code;
- ask the tools to install, build or execute a third-party project;
- treat the license output as legal advice;
- use the result as the only basis for a production procurement decision;
- load test the public Radar;
- automate repeated requests outside an agreed test window.

## Feedback format

For every issue, provide:

```text
Commit SHA:
Client and version:
Operating system:
Provider: mock or http
Language: zh or en
Skill or tool:
Sanitized request summary:
Expected behavior:
Observed behavior:
Was a fact presented without evidence? yes/no
Was a recommendation presented as fact? yes/no
Were unknowns and risks visible? yes/no
Relevant error code:
Reproduction steps:
```

Do not include credentials, private prompts or confidential project data.

## Severity

- **Critical**: write action, repository execution, secret exposure, unsafe
  license claim or cross-boundary prompt injection.
- **High**: fabricated project fact, near match presented as full match, mixed
  snapshot comparison or hidden blocking constraint.
- **Medium**: incorrect ranking, weak explanation, confusing unknown state or
  incomplete evidence.
- **Low**: wording, formatting, documentation or installation friction.

Critical and high-severity security issues must follow `SECURITY.md` rather than
a public issue.

## Exit criteria

The invited alpha is successful when:

- testers can install the Skills-only package;
- Codex discovers exactly six tools in MCP mode;
- all required scenarios complete without writes or execution;
- no verified fact lacks evidence;
- no missing license is interpreted as permission;
- at least ten testers complete two sessions;
- at least five testers return for a second week;
- all critical and high-severity findings are closed or explicitly block the
  next release.
