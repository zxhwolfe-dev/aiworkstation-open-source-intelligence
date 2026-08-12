# Production Monitoring Baseline

This record establishes the first privacy-minimized operational baseline for
the public Hosted MCP. It does not contain client IP addresses, request paths,
queries, tool arguments, response payloads, User-Agent values, or request IDs.

## Identity and observation window

```text
Observed: 2026-08-12 09:35:53+08:00 through 2026-08-12 10:26:09+08:00
Production release: v0.3.0
Source/runtime commit: 7b92e463a1da567afd5d1310601afdf1c6674646
GHCR digest: sha256:ca97a9192fa0b6bdd9b62628acc48c74f7cb6b127ef88fcbacaaa6e6f5aed849
Container health: healthy
Container restart count: 0
Public upstream binding: 127.0.0.1:8001
Rollback snapshot: /opt/aiworkstation-osi/.deploy-backups/20260811T143404Z
```

The image OCI revision and `OSI_IMAGE_COMMIT` both matched the source/runtime
commit. The rollback snapshot and its `ROLLBACK-COMMAND.txt` were present.

## Gateway sample

The dedicated Nginx metrics log contained 30 records:

```text
HTTP 200: 21
HTTP 202:  6
HTTP 404:  3
HTTP 429:  0
HTTP 5xx:  0
Nginx error-log records: 0
```

The three `404` records were expected closed-path validation requests and had no
upstream duration. The remaining 27 upstream requests had:

```text
total/upstream duration minimum: 0.001 s
total/upstream duration average: 3.927 s
total/upstream duration p50:     0.003 s
total/upstream duration p95:     7.241 s
total/upstream duration maximum: 87.370 s
```

The maximum occurred within MCP acceptance traffic and remained below the
configured 180-second proxy timeout. This small, validation-heavy sample is not
representative enough to set an availability objective or change the anonymous
rate limits.

## Operational decision

- Keep the current `60 requests/minute` short-window, `10 requests/minute`
  sustained, and `10 connections/IP` controls unchanged.
- Continue daily review during External Alpha for status counts, `429`, `5xx`,
  p50/p95/max latency, Nginx errors, container health/restarts, and Radar
  upstream failures.
- Record real-user traffic separately from scripted acceptance runs before
  tuning thresholds.
- Keep the exact production image and rollback snapshot through the initial
  observation period.
- Apply the candidate Docker `json-file` limit (`10 MiB` times five files) only
  after the configuration change reaches `main`, using the same production
  image digest and a configuration-only container recreation.
- Assign a named incident and rollback owner before inviting the wider cohort.

