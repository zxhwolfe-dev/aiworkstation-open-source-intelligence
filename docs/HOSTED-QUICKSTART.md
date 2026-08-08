# Hosted one-install Quickstart

## For end users

The final hosted product is intended to require only:

1. install **AI Open Source Intelligence** from the target Plugin directory;
2. choose **Connect / Sign in** when prompted;
3. complete OAuth authorization once;
4. ask normal questions in ChatGPT/Codex.

No Python install, local clone, database credentials or API-key copy/paste should be required for normal hosted use.

### Example requests

```text
Show today's AI open-source ranking.
```

```text
What collections are available? Browse the RAG collection.
```

```text
Show me projects in the RAG category that support Docker/self-hosting.
```

```text
Find a self-hosted RAG project with a Web UI, then verify the license of the strongest candidate.
```

```text
Compare Dify and RAGFlow for an enterprise internal knowledge base.
```

```text
Find installable Skills for code review and open the best match.
```

```text
Do a deep research brief on the strongest self-hosted RAG options for my requirements.
```

The last request may use the explicit Premium AI tool. The first successful Premium AI research task is free; later Premium AI tasks require AI credits.

## For developers before public directory release

Until the combined Plugin connection is registered, local development remains available.

Install:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[mcp]"
```

Offline nine-tool MCP:

```bash
OSI_PROVIDER=mock osi-mcp
```

Live public Radar nine-tool MCP:

```bash
OSI_PROVIDER=http \
AIWORKSTATION_RADAR_BASE_URL=https://aiworkstation.cn \
osi-mcp
```

This developer mode does **not** expose the hosted Premium AI tool or billing because it has no OAuth user identity.

## Hosted preflight

A real hosted operator configures OAuth, backend service authentication and the existing public-bind protections, then runs:

```bash
osi-mcp-hosted --check-config
```

The command must fail if:

- provider is not live HTTP;
- public-bind policy is incomplete;
- OAuth issuer/introspection/client secret/resource is incomplete;
- public OAuth resource is not a credential-free HTTPS `/mcp` URL;
- backend service token is missing.

Example deployment shape:

```bash
docker compose -f compose.public-hosted.example.yml config
docker compose -f compose.public-hosted.example.yml up -d --build
```

Do not publish the endpoint before completing [`PUBLIC-HOSTED-MCP.md`](PUBLIC-HOSTED-MCP.md).

## Live Radar browse probe

Validate the current full browsing contract without Premium AI:

```bash
python -m aiworkstation_osi.radar_browse_probe \
  --base-url https://aiworkstation.cn \
  --locale en

python -m aiworkstation_osi.radar_browse_probe \
  --base-url https://aiworkstation.cn \
  --locale zh
```

This validates current overview, rankings, collections, categories, scenarios, Skills list and Skill detail.

## Premium acceptance

After OAuth and Paddle sandbox are configured, test with a fresh user:

```text
1. Premium task succeeds -> free_trial
2. Premium task again -> upgrade_required + checkout for unsubscribed user
3. Complete sandbox checkout
4. Webhook provisions credits
5. Premium task succeeds -> paid_credits
6. Force model failure -> exact reservation refunded
```

Do not automate a real paid purchase in ordinary CI.
