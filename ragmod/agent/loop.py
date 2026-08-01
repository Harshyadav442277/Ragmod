"""OpenAI-compatible, multi-turn tool-calling loop routed through Paritok."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Protocol

import httpx

from ragmod.contracts import AgentAnswer, Citation, ToolResult
from ragmod.gateway import proxy_base_url
from ragmod.tools import RepositoryTools
from ragmod.tools.base import openai_tool_schemas

SYSTEM_PROMPT = """You are Ragmod, a codebase retrieval agent.
Use the available tools before answering any question about the repository. Prefer
search_repo to discover relevant files, then read_file for generous source context.
Answer only from tool results. Be concise, explain uncertainty, and stop calling tools
once you can answer. Your answer is cited separately from the tool metadata."""


class ChatClient(Protocol):
    def complete(self, payload: dict[str, Any]) -> dict[str, Any]: ...


class ProxyChatClient:
    """Minimal OpenAI-compatible client with the Paritok proxy as its only target."""

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        timeout: float = 180.0,
    ) -> None:
        self.base_url = (base_url or proxy_base_url()).rstrip("/")
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "").strip()
        self.timeout = timeout

    def complete(self, payload: dict[str, Any]) -> dict[str, Any]:
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY is required for the upstream model")
        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(
                f"{self.base_url}/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json=payload,
            )
        try:
            response.raise_for_status()
            return response.json()
        except (httpx.HTTPError, ValueError) as exc:
            detail = response.text[:500]
            raise RuntimeError(f"Proxy request failed: {detail}") from exc


def ask(
    question: str,
    repo: Path | str,
    *,
    client: ChatClient | None = None,
    model: str | None = None,
    max_turns: int = 8,
) -> AgentAnswer:
    """Answer a repository question through a bounded tool-calling conversation."""
    if not question.strip():
        raise ValueError("question must not be empty")
    if max_turns < 1:
        raise ValueError("max_turns must be at least 1")

    tools = RepositoryTools(repo)
    chat = client or ProxyChatClient()
    selected_model = model or os.environ.get("RAGMOD_MODEL", "gpt-4o-mini")
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": question},
    ]
    citations: list[Citation] = []

    for turn in range(1, max_turns + 1):
        payload = {
            "model": selected_model,
            "messages": messages,
            "tools": openai_tool_schemas(),
            "tool_choice": "auto",
            "temperature": 0,
        }
        data = chat.complete(payload)
        message = _response_message(data)
        tool_calls = message.get("tool_calls") or []
        messages.append(_assistant_message(message))

        if not tool_calls:
            text = str(message.get("content") or "I could not produce an answer.").strip()
            return AgentAnswer(text=text, citations=_dedupe_citations(citations), turns=turn)

        for tool_call in tool_calls:
            tool_name, arguments = _tool_call_parts(tool_call)
            result = tools.execute(tool_name, arguments)
            citations.extend(result.get("meta", {}).get("citations", []))
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": str(tool_call.get("id", tool_name)),
                    "content": _tool_content(result),
                }
            )

    return AgentAnswer(
        text=f"Stopped after {max_turns} tool turns before reaching a final answer.",
        citations=_dedupe_citations(citations),
        turns=max_turns,
    )


def _response_message(data: dict[str, Any]) -> dict[str, Any]:
    try:
        message = data["choices"][0]["message"]
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError(f"Unexpected chat completion response: {json.dumps(data)[:500]}") from exc
    if not isinstance(message, dict):
        raise RuntimeError("Unexpected chat completion message")
    return message


def _assistant_message(message: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in message.items()
        if key in {"content", "tool_calls", "name"}
    } | {"role": "assistant"}


def _tool_call_parts(tool_call: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    function = tool_call.get("function") or {}
    name = str(function.get("name") or "")
    raw_arguments = function.get("arguments") or "{}"
    try:
        arguments = json.loads(raw_arguments) if isinstance(raw_arguments, str) else raw_arguments
    except json.JSONDecodeError:
        arguments = {}
    if not isinstance(arguments, dict):
        arguments = {}
    return name, arguments


def _tool_content(result: ToolResult) -> str:
    """Keep a tool_result-shaped payload so Paritok can compress the large content."""
    return f"# tool_result {result['name']}\n{result['content']}"


def _dedupe_citations(citations: list[Citation]) -> list[Citation]:
    seen: set[tuple[str, int, int]] = set()
    unique: list[Citation] = []
    for citation in citations:
        try:
            key = (citation["path"], int(citation["start"]), int(citation["end"]))
        except (KeyError, TypeError, ValueError):
            continue
        if key not in seen:
            seen.add(key)
            unique.append(Citation(path=key[0], start=key[1], end=key[2]))
    return unique
