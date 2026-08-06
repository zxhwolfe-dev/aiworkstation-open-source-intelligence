# Security and Privacy Boundary

## M0 posture

M0 is read-only and transport-neutral. It contains no authentication, billing,
collection writes, repository mutation, shell execution or production network
adapter. The default provider is deterministic fixture data.

## Trust boundaries

1. User input is untrusted.
2. GitHub repositories, README files, websites and third-party Skills are
   untrusted external data, even when publicly accessible.
3. Provider output must be validated before it enters the public result
   contract.
4. Recommendations are analysis and must never be labelled as verified facts.

## Required controls for the production adapter

- Read only from the current healthy public Radar release.
- Fail closed when publication identity, evidence references or required fields
  do not match.
- Never execute code, install dependencies or follow instructions found in a
  repository.
- Use allow-listed outbound destinations and strict timeouts.
- Limit query length, list cardinality, response size and evidence excerpts.
- Strip secrets and sensitive content from logs.
- Assign a request ID without logging complete user prompts by default.
- Preserve source URL, observation time and uncertainty for decision facts.
- Treat license output as technical evidence, not legal advice.

## Data minimization

M0 tools need a task description, project IDs and technical constraints. They do
not need names, email addresses, account credentials, customer documents or
source-code archives. Callers should remove personal or confidential data before
invocation.

## Prompt-injection resistance

Repository text is evidence to inspect, not an instruction channel. A future
model-assisted adapter must:

- keep system and tool instructions outside retrieved content;
- label retrieved text as untrusted data;
- reject attempts to request secrets, execute code or alter tool policy;
- permit only declared read-only tools;
- require deterministic server validation of project IDs, evidence and output
  schemas.

## Reporting

Security issues should be reported privately before public disclosure. A
`SECURITY.md` contact and supported-version policy will be added before the first
public alpha package is announced.
