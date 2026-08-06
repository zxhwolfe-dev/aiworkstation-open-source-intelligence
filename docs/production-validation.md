# M1 Production Validation Runbook

This runbook validates the public AI Workstation Radar contract before the MCP
server is distributed to external testers. All steps are anonymous and
read-only.

## Preconditions

```bash
cd /path/to/aiworkstation-open-source-intelligence
git status
git pull origin main

python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[mcp]"
```

Do not proceed with uncommitted local edits unless they are intentional and
reviewed.

## 1. Run the complete local suite

```bash
python -m unittest discover -s tests -v
python -m json.tool schemas/tool-manifest.json >/dev/null
python -m json.tool schemas/tool-result.schema.json >/dev/null
python -m json.tool evals/cases.json >/dev/null
```

Also smoke-test command installation:

```bash
osi-m0 provider-info
osi-m0 list-tools
osi-probe --help
osi-capture-contracts --help
```

Record the commit under test:

```bash
git rev-parse HEAD
```

## 2. Run English and Chinese public probes

```bash
mkdir -p tmp/public-validation

osi-probe \
  --base-url https://aiworkstation.cn \
  --locale en \
  --project-id infiniflow/ragflow \
  --output tmp/public-validation/probe-en.json

osi-probe \
  --base-url https://aiworkstation.cn \
  --locale zh \
  --project-id infiniflow/ragflow \
  --output tmp/public-validation/probe-zh.json
```

Both reports should have `"ok": true`. Do not weaken adapter checks merely to
turn a failed probe green. First determine whether the failure is:

- network or TLS connectivity;
- missing or stale public data;
- a changed public response shape;
- missing snapshot identity;
- malformed selector evidence or near matches;
- an expected unknown license;
- a genuine adapter bug.

## 3. Capture sanitized public contract fixtures

Create separate directories for each language:

```bash
osi-capture-contracts \
  --base-url https://aiworkstation.cn \
  --locale en \
  --project-id infiniflow/ragflow \
  --output-dir tmp/public-validation/contracts-en

osi-capture-contracts \
  --base-url https://aiworkstation.cn \
  --locale zh \
  --project-id infiniflow/ragflow \
  --output-dir tmp/public-validation/contracts-zh
```

Each directory should contain:

```text
manifest.json
project-list.json
project-detail.json
selector-formal.json
selector-no-match.json
```

The capture removes user queries, client IDs, credentials and internal
publication fields. Review the files manually before committing any fixture:

```bash
grep -RniE 'authorization|cookie|api[_-]?key|access[_-]?token|email|source_hash|evidence_ids|claim_refs|publication_version|"query"' \
  tmp/public-validation/contracts-en \
  tmp/public-validation/contracts-zh
```

Expected result: no matches.

## 4. Review the response contracts

### Project list

Confirm:

- non-empty `snapshot_id`;
- stable project identity;
- exact project search resolves the intended record;
- no internal publication fields appear.

### Project detail

Confirm:

- detail `item` is present;
- detail snapshot matches the list snapshot, or the public contract provides a
  documented compatible identity;
- license, deployment and update-time fields use the shapes expected by the
  adapter;
- transparency contains public-safe evidence metadata;
- archived status is explicit.

### Selector formal result

Confirm:

- `evidence_status` is `available`, or `partial` with a visible notice;
- formal projects carry stable IDs;
- no near matches are mixed into formal results;
- internal fields do not leak.

### Selector no-match result

Confirm:

- there is an explicit `no_match_reason` when no formal result exists;
- near matches, if present, have exactly one `conflict` or `unverified` blocker;
- no more than three near matches are exposed;
- relaxing a hard requirement is never automatic.

## 5. Test the MCP server from Codex

Follow [`codex-setup.md`](codex-setup.md), initially with:

```text
OSI_PROVIDER=mock
```

Then switch to:

```text
OSI_PROVIDER=http
AIWORKSTATION_RADAR_BASE_URL=https://aiworkstation.cn
```

Test these workflows:

1. Search for a self-hosted RAG project.
2. Verify one named project's deployment and license.
3. Compare Dify and RAGFlow for an explicit scenario.
4. Find alternatives while preserving hard constraints.
5. Compose a stack and verify that compatibility remains a recommendation, not
   a fact.
6. Use an impossible requirement set and confirm an honest no-match result.

## 6. Decide whether an upstream change is necessary

A change to `akaiagents` is justified only when the public contract cannot
safely provide one of these required elements:

- stable project identity;
- public snapshot identity;
- public evidence source and observation time;
- unambiguous missing-license representation;
- explicit selector evidence state;
- explicit no-match reason;
- near-match blocker status.

Document the smallest additive API change first. Do not import private modules or
modify `akaiagents` from this repository.

## 7. External-alpha release gate

Do not invite external testers until all are true:

- local tests pass;
- GitHub Actions succeeds on Python 3.10 and 3.12;
- English and Chinese probes pass;
- sanitized fixtures have been reviewed;
- Codex discovers exactly six tools;
- no tool writes data or executes repository code;
- license output preserves the non-legal-advice boundary;
- known limitations are documented in README and release notes.
