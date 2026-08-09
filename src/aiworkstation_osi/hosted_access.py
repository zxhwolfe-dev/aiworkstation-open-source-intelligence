"""Hosted MCP access-mode policy.

The public Hosted service can run in two explicit modes:

- ``public``: nine anonymous, read-only Radar tools. No OAuth or Premium backend
  configuration is loaded. Edge/gateway IP abuse controls are required.
- ``oauth``: the existing OAuth-protected nine-tool + Premium tool surface.

``public`` is the default so a free Hosted MCP does not depend on a third-party
identity provider. OAuth remains available as a replaceable identity boundary
for future member-linked Premium access.
"""

from __future__ import annotations

import os

HOSTED_ACCESS_PUBLIC = "public"
HOSTED_ACCESS_OAUTH = "oauth"
HOSTED_ACCESS_MODES = (HOSTED_ACCESS_PUBLIC, HOSTED_ACCESS_OAUTH)


def load_hosted_access_mode() -> str:
    value = str(os.getenv("OSI_HOSTED_ACCESS_MODE") or HOSTED_ACCESS_PUBLIC).strip().lower()
    if value not in HOSTED_ACCESS_MODES:
        raise ValueError(
            "OSI_HOSTED_ACCESS_MODE must be public or oauth"
        )
    return value
