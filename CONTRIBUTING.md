# Contributing

Thanks for helping improve AI Workstation Open Source Intelligence.

## Before you start

This repository is the public distribution and integration layer. The private AI Workstation data-production system, private databases, unpublished datasets, credentials, and internal operations are intentionally outside this repository.

Please keep contributions within the public product boundary:

- Skills and their evaluation cases;
- six read-only tool contracts and adapters;
- public Radar contract handling;
- evidence, license, snapshot, privacy, and safety boundaries;
- MCP transports and packaging;
- documentation, tests, developer experience, and accessibility.

## Development setup

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[mcp]"
python -m compileall -q src tests
python -m unittest discover -s tests -v
osi-validate-plugin --root .
```

The supported Python versions are 3.10 and 3.12 in CI.

## Design rules

Changes must preserve the core product contract:

1. verified facts stay separate from recommendations;
2. unknown information remains explicit;
3. license permission is never inferred from missing evidence;
4. hard constraints are not silently relaxed;
5. near matches do not become formal matches;
6. comparison data must not mix incompatible snapshots;
7. third-party repository code is never installed or executed by research tools;
8. public-contract captures must remain sanitized;
9. the six public product tools remain read-only unless a future major release explicitly changes the product boundary.

## Pull requests

Keep pull requests focused. Include:

- the user-visible problem;
- the smallest implementation that solves it;
- relevant tests;
- evidence that existing fact/license/privacy boundaries still pass;
- documentation changes when behavior or public contracts change.

Run the full test suite before requesting review.

## Issues

Use the repository issue templates for ordinary bugs, incorrect facts/evidence behavior, public-contract regressions, project coverage requests, and feature ideas.

Do not post exploitable security findings, real secrets, private prompts, private source code, customer data, or unsanitized captures in public issues. Follow [`SECURITY.md`](SECURITY.md) for security reports.

## Licensing of contributions

Unless you explicitly state otherwise, contributions intentionally submitted for inclusion in this repository are provided under the Apache License 2.0, consistent with the repository license.
