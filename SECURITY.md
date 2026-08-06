# Security Policy

## Supported versions

This repository is pre-alpha. Only the latest commit on `main` is considered for
security fixes. No production service or public MCP endpoint is shipped yet.

## Reporting a vulnerability

Do not open a public issue for a vulnerability involving credentials, private
data, prompt injection that crosses a trust boundary, or a potential remote-code
execution path.

Until a dedicated security mailbox is published, use the private contact method
listed on the AI Workstation website and include:

- affected commit or version;
- reproduction steps;
- expected and observed behavior;
- impact and required preconditions;
- suggested mitigation, when available.

Do not include real secrets, customer data or malicious payloads that could harm
third parties.

## Security guarantees in M0

- all declared tools are read-only;
- the default provider performs no network access;
- third-party repository code is never executed;
- mock data is explicitly marked and cannot be presented as verified facts;
- production integration is blocked on fail-closed public-release validation.
