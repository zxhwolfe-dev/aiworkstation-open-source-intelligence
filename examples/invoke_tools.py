"""Run deterministic offline examples after `python -m pip install -e .`."""

from __future__ import annotations

import json

from aiworkstation_osi import invoke_tool


EXAMPLES = (
    (
        "search_ai_projects",
        {
            "query": "Find a self-hosted RAG project with Docker and a web UI.",
            "constraints": {
                "self_hosted": "required",
                "docker": "required",
                "web_ui": "required",
            },
            "request_id": "example-search",
        },
    ),
    (
        "compare_ai_projects",
        {
            "project_ids": ["langgenius/dify", "infiniflow/ragflow"],
            "criteria": ["private deployment", "document processing", "license"],
            "request_id": "example-compare",
        },
    ),
    (
        "compose_ai_stack",
        {
            "business_goal": "Build an internal document question-answering system.",
            "constraints": {"self_hosted": "required", "budget": "limited"},
            "request_id": "example-stack",
        },
    ),
)


if __name__ == "__main__":
    for tool_name, arguments in EXAMPLES:
        print(f"\n## {tool_name}")
        print(json.dumps(invoke_tool(tool_name, arguments), ensure_ascii=False, indent=2))
