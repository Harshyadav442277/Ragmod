"""Tool names and OpenAI-style schemas (stubbed until Wave 1)."""

from __future__ import annotations

from typing import Any

TOOL_NAMES = ("search_repo", "read_file", "list_dir", "run_tests")


def openai_tool_schemas() -> list[dict[str, Any]]:
    """Full toolset so Paritok can stub unused schemas (cache-friendly)."""
    return [
        {
            "type": "function",
            "function": {
                "name": "search_repo",
                "description": "Search the repository with ripgrep. Returns many hits.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "pattern": {"type": "string"},
                        "glob": {"type": "string"},
                    },
                    "required": ["pattern"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "read_file",
                "description": "Read a source file with generous surrounding context.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string"},
                        "start": {"type": "integer"},
                        "end": {"type": "integer"},
                    },
                    "required": ["path"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "list_dir",
                "description": "List a directory in the repository.",
                "parameters": {
                    "type": "object",
                    "properties": {"path": {"type": "string"}},
                    "required": ["path"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "run_tests",
                "description": "Run the project test suite and return stdout/stderr.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "selector": {"type": "string"},
                    },
                },
            },
        },
    ]
