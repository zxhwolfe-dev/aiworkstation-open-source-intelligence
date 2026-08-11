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

Use the guarded `github-release` workflow after the final release candidate passes CI/live/Codex validation. This single workflow builds and creates the GitHub Release, validates and promotes the exact wheel/sdist to PyPI with Trusted Publishing, and builds the exact commit-addressed image in GHCR. The former split release-event workflows are retired; no `release: published` fan-out is used.

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

The workflow first creates a Draft Release and stages exactly these six assets:

- deterministic Skills ZIP;
- `SHA256SUMS`;
- `bundle-report.json`;
- one exact-version Python wheel;
- one exact-version Python sdist;
- `PYTHON-DISTS-SHA256SUMS`.

The Release remains Draft while PyPI and GHCR are validated. It is made public
only by the final promotion job after both downstream promotions succeed and
the tag, prerelease flag, and six-asset set are checked again.

If a Release is already public when a downstream job starts or resumes, both
publishers switch to verify-only mode. PyPI must already contain exactly the
wheel and sdist with the Release SHA256 values; GHCR must already contain the
exact `:sha-<full-commit>` image with matching OCI revision, `OSI_IMAGE_COMMIT`,
and repository digest. Missing or mismatched public artifacts fail closed and
are never repaired by uploading or rebuilding.

The GHCR image is published only as
`ghcr.io/zxhwolfe-dev/aiworkstation-open-source-intelligence:sha-<full-commit>`.
The `sha-<full-commit>` value is an explicit image tag, not a nested image path;
no `latest` tag is created or promoted.

GHCR promotion builds a missing Draft image locally first. Only after a fresh
Release identity check following the build, and a second exact image lookup,
does it push. If any observation is Public, that sticky state cannot return to
write mode; Public recovery only pulls and verifies the existing image.

Draft identity is read from the authenticated Releases API (`release_id`,
`target_commitish`, and asset IDs); the Draft path does not assume that a
`refs/tags/<tag>` ref already exists. It fails closed if the API proves that a
tag already exists before promotion, and resolves the published tag to the
commit again after the Release is made public. A rerun may safely accept an already-public Release
only when its release ID, target commit, prerelease state, assets, PyPI hashes,
and GHCR digest all match.

If a run fails, rerun the failed jobs in the same workflow run first. Do not
create another tag or delete/overwrite Draft assets. Existing PyPI files may be
reused only when their filename and SHA256 exactly match the Release checksum;
any hash, asset, tag, or commit mismatch requires manual investigation.

The workflow dispatch identity is immutable: it must be run from `main`, with
the input commit equal to that run's `GITHUB_SHA`. Only a first-time Draft
creation rechecks the moving `origin/main` immediately before creating the
Release. Rerun failed jobs from the original workflow run to preserve the same
SHA; a new run cannot use a later or unrelated commit to resume an old Release.
The temporary Actions artifact uses `overwrite: true` only to make a rerun of
the validated PyPI job safe; GitHub Release assets are never overwritten.

## Before clicking Publish

Configure the PyPI Trusted Publisher for this repository and
`.github/workflows/release.yml` (environment `pypi`) before running the
workflow. It uses OIDC and does not use a long-lived API token.
The Trusted Publisher identity is owner `zxhwolfe-dev`, repository
`aiworkstation-open-source-intelligence`, workflow filename `release.yml`, and
environment `pypi`. Configure a required reviewer on the `pypi` GitHub
environment for production release control.

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
