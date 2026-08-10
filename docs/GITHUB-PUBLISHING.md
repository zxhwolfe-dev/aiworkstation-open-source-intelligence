# GitHub Publishing Checklist

This document contains the exact repository metadata and manual GitHub UI settings for the first public release.

## About

**Description**

```text
Evidence-backed research, comparison, license verification, and stack planning for open-source AI projects. 1 Skill + 9 read-only MCP tools.
```

**Website**

```text
https://aiworkstation.cn/githubai/
```

## Topics

Add these repository topics:

```text
mcp
model-context-protocol
openai
chatgpt
codex
agent-skills
open-source-ai
rag
ai-agents
developer-tools
llm
technology-selection
```

## Repository features

Recommended:

- Issues: enabled
- Discussions: enabled
- Wiki: optional/off unless it gains a real maintenance owner
- Projects: optional
- Preserve Releases

Suggested Discussions categories:

- Announcements
- Q&A
- Ideas
- Show and Tell

## Social preview

Create a 1280×640 social-preview image with:

- product name: `AI Open Source Intelligence`;
- subtitle: `Evidence-backed open-source AI research & technology selection`;
- small line: `1 Skill · 9 read-only MCP tools`;
- AI Workstation branding;
- visual language: clean developer tool / radar / open-source network, not surveillance or hacker imagery;
- avoid GitHub mascot/trademark misuse.

Upload it in repository Settings → General → Social preview.

## README language surface

`README.md` is the primary English product page.

`README.zh-CN.md` is the Simplified Chinese equivalent.

Keep the language switch at the top of both files.

## First GitHub Release

Use the guarded `github-release` workflow after the final release candidate passes CI/live/Codex validation.

Recommended first release:

```text
Tag: v0.3.0
Commit: the full 40-character SHA of the reviewed release candidate
Title: v0.3.0 — AI Open Source Intelligence
Pre-release: Yes
```

Release notes source:

```text
CHANGELOG.md
```

Assets:

- deterministic Skills ZIP;
- `SHA256SUMS`;
- `bundle-report.json`.

## Before clicking Publish

- [ ] Cohort 1 critical/high feedback triaged
- [ ] release candidate CI 3.10/3.12 green
- [ ] bilingual live validation green
- [ ] current-commit Codex acceptance green
- [ ] public artifact privacy review green
- [ ] README links checked
- [ ] Apache-2.0 and Terms reviewed by publisher
- [ ] GitHub About / Topics set
- [ ] Social preview uploaded
- [ ] release notes match actual functionality
- [ ] release is marked pre-release

## After publishing

- pin the release announcement in Discussions;
- update the product website with the release link;
- share one concrete use case rather than a generic “we launched an MCP” announcement;
- monitor Issue templates for installation/evidence regressions;
- do not describe the hosted MCP as public-production-ready until its separate gates pass.
