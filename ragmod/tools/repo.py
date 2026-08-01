"""Filesystem-backed tools for inspecting one checked-out code repository."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from ragmod.contracts import ToolResult

MAX_SEARCH_LINES = 200
MAX_LIST_ENTRIES = 200
READ_CONTEXT_LINES = 40
TEST_TIMEOUT_SECONDS = 120


class RepositoryTools:
    """Execute Ragmod's toolset, confined to one repository root."""

    def __init__(self, root: Path | str) -> None:
        self.root = Path(root).resolve()
        if not self.root.is_dir():
            raise ValueError(f"Repository root is not a directory: {self.root}")

    def execute(self, name: str, arguments: dict[str, Any]) -> ToolResult:
        handlers = {
            "search_repo": self.search_repo,
            "read_file": self.read_file,
            "list_dir": self.list_dir,
            "run_tests": self.run_tests,
        }
        handler = handlers.get(name)
        if handler is None:
            return self._error(name, f"Unknown tool: {name}")
        try:
            return handler(**arguments)
        except (OSError, TypeError, ValueError) as exc:
            return self._error(name, str(exc))

    def search_repo(self, pattern: str, glob: str | None = None) -> ToolResult:
        if not pattern:
            raise ValueError("pattern must not be empty")
        command = [
            "rg",
            "--line-number",
            "--no-heading",
            "--color",
            "never",
            "--glob",
            "!.git",
        ]
        if glob:
            command.extend(["--glob", glob])
        command.extend([pattern, "."])
        try:
            completed = subprocess.run(
                command,
                cwd=self.root,
                text=True,
                capture_output=True,
                timeout=30,
                check=False,
            )
            if completed.returncode not in (0, 1):
                raise ValueError(completed.stderr.strip() or "ripgrep failed")
            all_lines = completed.stdout.splitlines()
        except FileNotFoundError:
            # ripgrep not installed — try git grep, then pure-Python fallback
            all_lines = self._git_grep_fallback(pattern, glob)
            if all_lines is None:
                all_lines = self._python_search(pattern, glob)

        hits = all_lines[:MAX_SEARCH_LINES]
        citations = []
        for hit in hits:
            parts = hit.split(":", 2)
            if len(parts) < 3 or not parts[1].isdigit():
                continue
            citations.append(
                {"path": Path(parts[0]).as_posix(), "start": int(parts[1]), "end": int(parts[1])}
            )
        suffix = "\n[truncated after 200 matches]" if len(all_lines) > len(hits) else ""
        content = "\n".join(hits) + suffix
        if not content:
            content = "No matches found."
        return ToolResult(
            name="search_repo",
            content=content,
            meta={"pattern": pattern, "glob": glob, "citations": citations},
        )

    def _git_grep_fallback(self, pattern: str, glob: str | None) -> list[str] | None:
        """Try git grep as a fallback when ripgrep is missing."""
        command = ["git", "grep", "-n", "--no-color", "-I", pattern, "--", "."]
        try:
            completed = subprocess.run(
                command,
                cwd=self.root,
                text=True,
                capture_output=True,
                timeout=30,
                check=False,
            )
            if completed.returncode not in (0, 1):
                return None
            return completed.stdout.splitlines()
        except FileNotFoundError:
            return None

    def _python_search(self, pattern: str, glob_filter: str | None = None) -> list[str]:
        """Pure-Python line search — last resort when neither rg nor git is available."""
        hits: list[str] = []
        skip_dirs = {".git", "__pycache__", "node_modules", ".venv", "venv"}
        for path in sorted(self.root.rglob("*")):
            if not path.is_file():
                continue
            rel = path.relative_to(self.root)
            if any(part in skip_dirs or part.startswith(".") for part in rel.parts):
                continue
            if glob_filter and not rel.match(glob_filter):
                continue
            try:
                lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
            except Exception:
                continue
            for line_no, line in enumerate(lines, start=1):
                if pattern in line:
                    hits.append(f"{rel.as_posix()}:{line_no}:{line}")
                    if len(hits) >= MAX_SEARCH_LINES:
                        return hits
        return hits

    def read_file(
        self,
        path: str,
        start: int | None = None,
        end: int | None = None,
    ) -> ToolResult:
        file_path = self._resolve(path)
        if not file_path.is_file():
            raise ValueError(f"Not a file: {path}")
        try:
            lines = file_path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError as exc:
            raise ValueError(f"Not a UTF-8 text file: {path}") from exc

        requested_start = max(1, start or 1)
        requested_end = max(requested_start, end or len(lines))
        if not lines:
            raise ValueError(f"File is empty: {path}")
        if requested_start > len(lines):
            raise ValueError(f"start line {requested_start} is beyond end of file ({len(lines)} lines)")
        actual_start = max(1, requested_start - READ_CONTEXT_LINES)
        actual_end = min(len(lines), requested_end + READ_CONTEXT_LINES)
        selected = lines[actual_start - 1 : actual_end]
        numbered = "\n".join(
            f"{line_no}: {line}" for line_no, line in enumerate(selected, start=actual_start)
        )
        relative = file_path.relative_to(self.root).as_posix()
        return ToolResult(
            name="read_file",
            content=f"# read_file {relative}:{actual_start}-{actual_end}\n{numbered}",
            meta={
                "path": relative,
                "start": actual_start,
                "end": actual_end,
                "requested_start": requested_start,
                "requested_end": requested_end,
                "citations": [{"path": relative, "start": actual_start, "end": actual_end}],
            },
        )

    def list_dir(self, path: str = ".") -> ToolResult:
        directory = self._resolve(path)
        if not directory.is_dir():
            raise ValueError(f"Not a directory: {path}")
        entries = sorted(directory.iterdir(), key=lambda entry: (not entry.is_dir(), entry.name.lower()))
        rendered = []
        for entry in entries[:MAX_LIST_ENTRIES]:
            rel = entry.relative_to(self.root).as_posix()
            rendered.append(f"{rel}/" if entry.is_dir() else rel)
        if len(entries) > len(rendered):
            rendered.append("[truncated after 200 entries]")
        return ToolResult(
            name="list_dir",
            content="\n".join(rendered) or "Directory is empty.",
            meta={"path": directory.relative_to(self.root).as_posix()},
        )

    def run_tests(self, selector: str | None = None) -> ToolResult:
        command = [sys.executable, "-m", "pytest", "-q"]
        if selector:
            candidate = Path(selector)
            if candidate.is_absolute() or ".." in candidate.parts:
                raise ValueError("selector must stay inside the repository")
            command.append(selector)
        completed = subprocess.run(
            command,
            cwd=self.root,
            text=True,
            capture_output=True,
            timeout=TEST_TIMEOUT_SECONDS,
            check=False,
        )
        output = (completed.stdout + completed.stderr).strip()
        return ToolResult(
            name="run_tests",
            content=output or "pytest produced no output.",
            meta={"selector": selector, "returncode": completed.returncode},
        )

    def _resolve(self, requested: str) -> Path:
        candidate = Path(requested)
        if candidate.is_absolute():
            raise ValueError("Absolute paths are not allowed")
        resolved = (self.root / candidate).resolve()
        if not resolved.is_relative_to(self.root):
            raise ValueError("Path escapes the repository root")
        return resolved

    @staticmethod
    def _error(name: str, message: str) -> ToolResult:
        return ToolResult(name=name, content=f"Tool error: {message}", meta={"error": True})
