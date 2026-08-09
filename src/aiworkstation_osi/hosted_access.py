"""Hosted MCP access policy for the public data-only product.

The current product deliberately supports exactly one Hosted mode:

- ``public``: nine anonymous, read-only Radar data/evidence tools.

There is no runtime switch for OAuth, Premium, publisher-model execution,
subscriptions or AI credits in this release. If member-linked server-model
capabilities are introduced later, they must ship as a new reviewed product
version rather than being enabled through a hidden environment toggle.
"""

from __future__ import annotations

import os

HOSTED_ACCESS_PUBLIC = "public"
HOSTED_ACCESS_MODES = (HOSTED_ACCESS_PUBLIC,)


def load_hosted_access_mode() -> str:
    value = str(os.getenv("OSI_HOSTED_ACCESS_MODE") or HOSTED_ACCESS_PUBLIC).strip().lower()
    if value != HOSTED_ACCESS_PUBLIC:
        raise ValueError("OSI_HOSTED_ACCESS_MODE must be public; server-model/OAuth Hosted modes are disabled")
    return value
