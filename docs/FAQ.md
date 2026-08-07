# Frequently Asked Questions

## What is AI Workstation Open Source Intelligence?

It is an evidence-backed research and technology-selection layer for open-source AI projects. It combines three reusable Skills with six read-only MCP tools for project discovery, fact verification, license evidence, comparison, alternatives, and stack planning.

## Is this traditional OSINT?

No. The product name uses “Open Source Intelligence” in the sense of intelligence about **open-source AI software projects**. It is not a general people-investigation, surveillance, or web-intelligence toolkit.

## Do Skills alone access the live AI Workstation database?

No. A Skill primarily provides instructions, workflow, decision boundaries, and reusable reasoning patterns. The current public Skills package intentionally does not contain a live database connection. Without the companion MCP tools, it must not claim current verified project or license facts.

## Can a Skill technically contain code that calls an API?

A Skill can package supporting scripts or references in environments that permit their execution, but execution and network access are host-dependent and are not a portable substitute for an explicit connector. For a live data product, MCP provides the clearer contract for discovery, authentication, tool schemas, approvals, observability, and cross-client compatibility.

## What does MCP add?

The MCP server turns AI Workstation's public Radar capabilities into six structured read-only tools. The host model can decide when to call a tool, consume the structured result, and explain the evidence to the user.

## Does MCP expose the whole AI Workstation website?

No. MCP exposes only the capabilities explicitly implemented as tools. The current server covers the core **Open Source Intelligence** research workflow, not every AI Workstation product, UI page, account feature, private database operation, maintenance task, or internal API.

## Which online capabilities are exposed today?

- search open-source AI projects from constraints;
- fetch current public project facts;
- inspect direct license evidence;
- compare two to five projects;
- find constrained alternatives;
- compose a candidate open-source AI stack.

## Are MCP tools read-only?

Yes. The current six-tool product contract is read-only, non-destructive, and does not execute or install third-party repository code.

## Does searching consume AI Workstation model tokens?

In the current M1 implementation, the public Radar selector request is sent with `use_model=false`. The backend search/retrieval path therefore does not require an AI Workstation LLM call for the six-tool live acceptance path. The ChatGPT/Codex/MCP host still uses its own model to interpret the user's request, decide which tools to call, and synthesize the answer.

If a future backend mode enables `use_model=true`, that model use must be explicitly configured, metered, rate-limited, and separated from the current deterministic/read-only contract.

## Who pays for the model used to answer the user?

For ChatGPT or Codex plugin/MCP use, the host model is part of the user's host environment and plan. The current public Radar tool calls are ordinary read-only API calls with `use_model=false`. A future AI Workstation-hosted model enhancement would be an additional publisher-side cost and should have its own quotas and commercial policy.

## Why not just let ChatGPT search the web?

General web search can find pages, but this project adds a maintained domain contract: structured project identity, snapshot consistency, evidence levels, direct-license requirements, hard-constraint handling, explicit no-match states, and a separation between verified facts and analysis.

## What does “verified” mean?

Only fields that cross the project's explicit evidence boundary enter `verified_facts`. Analysis or editorial projection values can remain useful in `data` without being promoted to source facts.

## Does a visible license label mean commercial use is safe?

No. A license enters verified facts only when the public detail includes direct license evidence that satisfies the provider contract. Missing or ambiguous license evidence remains unknown. This is technical evidence, not legal advice.

## Why can `compose_ai_stack` return integration risks?

Because individual components can be verified independently while cross-project compatibility remains untested. The product does not convert a plausible architecture into a verified integration claim.

## What happens when nothing satisfies the requirements?

The correct result is an explicit no-match. Hard requirements are not silently relaxed. Near matches, when shown, remain separate and disclose their blocker.

## Which languages are supported?

The current public validation suite covers English (`en`) and Simplified Chinese (`zh`).

## Is the repository open source?

Yes. The public repository is licensed under Apache-2.0. That license covers the public repository, not private AI Workstation databases, unpublished datasets, private services, or trademarks.

## Is the hosted MCP public production infrastructure ready?

Not yet. The guarded HTTP transport is suitable for local/private-alpha deployment. Broad hosted deployment still requires final identity/authentication, revocation, quotas, rate limiting, abuse controls, production monitoring, and service-specific legal/privacy decisions.
