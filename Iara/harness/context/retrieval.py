"""On-demand local retrieval and bounded context assembly.

This module deliberately uses deterministic path, symbol and lexical signals. It
does not call an embedding provider or persist an index, so every result reflects
the current workspace contents and carries a source hash for traceability.
"""

from __future__ import annotations

import ast
import fnmatch
import hashlib
import json
import math
import os
import re
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import unquote, urlsplit


class ContextBudgetExceeded(ValueError):
    """Raised when mandatory context alone is larger than the configured budget."""

    def __init__(
        self,
        required_tokens: int,
        budget_tokens: int,
        context_kind: str = "mandatory-context",
    ) -> None:
        super().__init__("mandatory context exceeds the requested context budget")
        self.required_tokens = required_tokens
        self.budget_tokens = budget_tokens
        self.context_kind = context_kind


@dataclass(frozen=True)
class Chunk:
    path: str
    start_line: int
    end_line: int
    content: str
    symbol: str | None = None
    chunk_type: str = "text"


@dataclass(frozen=True)
class CandidateSource:
    chunk: Chunk
    signals: frozenset[str]
    sha256: str
    last_modified: str
    scope: str
    related_context: dict[str, str] | None = None


@dataclass(frozen=True)
class Candidate:
    chunk: Chunk
    score: float
    reasons: tuple[str, ...]
    sha256: str
    last_modified: str
    scope: str
    related_context: dict[str, str] | None = None


STOP_WORDS = {
    "a",
    "as",
    "ao",
    "aos",
    "com",
    "como",
    "da",
    "das",
    "de",
    "do",
    "dos",
    "e",
    "em",
    "esta",
    "esse",
    "essa",
    "isso",
    "na",
    "nas",
    "no",
    "nos",
    "o",
    "os",
    "ou",
    "para",
    "por",
    "que",
    "se",
    "sem",
    "sobre",
    "um",
    "uma",
    "the",
    "and",
    "for",
    "from",
    "how",
    "in",
    "is",
    "of",
    "on",
    "or",
    "to",
    "where",
    "what",
    "when",
    "with",
}
DENIED_DIRS = {
    ".aws",
    ".git",
    ".pytest_cache",
    ".ruff_cache",
    ".ssh",
    ".venv",
    ".vite",
    "__pycache__",
    "build",
    "coverage",
    "dist",
    "node_modules",
    "playwright-report",
    "secrets",
    "test-results",
    "venv",
}
DENIED_SUFFIXES = {".db", ".key", ".log", ".pem", ".p12", ".pfx", ".pyc", ".sqlite"}
MAX_GENERIC_CHUNK_LINES = 80
SECRET_VALUE_PATTERN = re.compile(
    r"(?i)(?:api[_-]?key|secret|password|access[_-]?token)\s*[\"']?\s*[:=]\s*[\"']?"
    r"(?!replace-|your-|<|\$\{)[A-Za-z0-9_./+=-]{12,}"
)
RELATED_CONTEXT_HEADING = re.compile(r"^##\s+(?:related context|contexto relacionado)\s*$", re.I)
MARKDOWN_LINK = re.compile(r"\[([^\]]+)\]\(([^)\s]+)(?:\s+[^)]*)?\)")


def estimate_tokens(value: str) -> int:
    """Conservative-ish, dependency-free estimate; not a provider tokenizer."""
    return math.ceil(len(value.encode("utf-8")) / 3)


def _tokens(value: str) -> list[str]:
    expanded = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", value)
    expanded = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1 \2", expanded)
    words = re.findall(r"[\w]+", expanded.casefold(), flags=re.UNICODE)
    return [word for word in words if len(word) > 1 and word not in STOP_WORDS]


def _normalize(value: str) -> str:
    return " ".join(_tokens(value))


def _matches_deny(path: str, patterns: list[str]) -> bool:
    posix_path = PurePosixPath(path)
    for pattern in patterns:
        if (
            posix_path.match(pattern)
            or fnmatch.fnmatchcase(path, pattern)
            or (pattern.startswith("**/") and fnmatch.fnmatchcase(path, pattern[3:]))
        ):
            return True
    parts = posix_path.parts
    if any(part.casefold() in DENIED_DIRS for part in parts):
        return True
    name = posix_path.name.casefold()
    if name.startswith(".env") or name in {
        "package-lock.json",
        "pnpm-lock.yaml",
        "yarn.lock",
        "uv.lock",
    }:
        return True
    if posix_path.suffix.casefold() in DENIED_SUFFIXES:
        return True
    return any(
        part.casefold() in {"credential", "credentials", "secret", "secrets"} for part in parts
    )


def _contains_secret_material(text: str) -> bool:
    return "-----BEGIN PRIVATE KEY-----" in text or SECRET_VALUE_PATTERN.search(text) is not None


def _read_config(root: Path) -> dict[str, Any]:
    config_path = root / "harness" / "config" / "project.json"
    try:
        project = json.loads(config_path.read_text(encoding="utf-8"))
        config = project["context_retrieval"]
    except (OSError, json.JSONDecodeError, KeyError, TypeError) as exc:
        raise ValueError(f"invalid context retrieval configuration: {exc}") from exc
    if not isinstance(config, dict):
        raise ValueError("context_retrieval configuration must be an object")
    return config


def _continuity_context(root: Path, config: dict[str, Any]) -> tuple[list[str], list[dict[str, str]]]:
    """Load required durable project state before ranking task-specific sources."""
    continuity = config.get("continuity", {})
    if not isinstance(continuity, dict) or continuity.get("read_before_task_retrieval") is not True:
        return [], []

    paths = [
        continuity.get("canonical_project_state"),
        continuity.get("canonical_active_handoff"),
    ]
    mandatory: list[str] = []
    sources: list[dict[str, str]] = []
    for relative in paths:
        if not isinstance(relative, str) or not relative:
            raise ValueError("continuity must declare canonical state and handoff paths")
        candidate = (root / relative).resolve()
        if candidate == root or root not in candidate.parents:
            raise ValueError(f"continuity path escapes workspace: {relative}")
        try:
            content_bytes = candidate.read_bytes()
            content = content_bytes.decode("utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            raise ValueError(f"required continuity source is unavailable: {relative}") from exc
        if not content_bytes or len(content_bytes) > 32768:
            raise ValueError(f"required continuity source is empty or exceeds 32 KiB: {relative}")
        digest = hashlib.sha256(content_bytes).hexdigest()
        mandatory.append(f"Source: {PurePosixPath(relative).as_posix()}\nSHA256: {digest}\n{content}")
        sources.append({"source": PurePosixPath(relative).as_posix(), "sha256": digest})
    return mandatory, sources


def _route_scopes(query: str, requested_scope: str, config: dict[str, Any]) -> list[str]:
    scopes = config.get("scopes", {})
    if not isinstance(requested_scope, str):
        raise TypeError("scope must be a string")
    if requested_scope != "auto":
        if requested_scope not in scopes:
            raise ValueError(f"unknown retrieval scope: {requested_scope}")
        return [requested_scope]

    query_tokens = set(_tokens(query))
    router = config.get("route_keywords", {})
    selected = [
        name
        for name, keywords in router.items()
        if name in scopes and query_tokens.intersection(_tokens(" ".join(keywords)))
    ]
    # Harness guidance is useful alongside component context and remains a
    # separate, explicitly configured scope.
    if selected and "harness" in scopes and "harness" not in selected:
        selected.append("harness")
    if not selected:
        selected = [name for name in scopes if name != "project"]
    return selected


def _resolve_roots(root: Path, scope: str, scope_data: Any) -> list[Path]:
    if not isinstance(scope_data, list) or not scope_data:
        raise ValueError(f"scope '{scope}' must declare one or more roots")
    resolved: list[Path] = []
    for relative in scope_data:
        if not isinstance(relative, str) or not relative:
            raise ValueError(f"invalid path in scope '{scope}'")
        candidate = (root / relative).resolve()
        if candidate != root and root not in candidate.parents:
            raise ValueError(f"scope path escapes workspace: {relative}")
        if (candidate.is_dir() or candidate.is_file()) and candidate not in resolved:
            resolved.append(candidate)
    return resolved


def _iter_files(
    root: Path, roots: list[Path], config: dict[str, Any], filters: dict[str, Any]
) -> list[Path]:
    deny_patterns = config.get("deny_globs", [])
    if not isinstance(deny_patterns, list):
        raise TypeError("deny_globs must be a list")
    include_globs = filters.get("path_globs", [])
    if include_globs and (
        not isinstance(include_globs, list) or not all(isinstance(x, str) for x in include_globs)
    ):
        raise TypeError("filters.path_globs must be a list of strings")
    max_files = int(config.get("max_files_scanned", 5000))
    max_file_bytes = int(config.get("max_file_bytes", 262144))
    allowed_extensions = {
        str(extension).casefold() for extension in config.get("allowed_extensions", [])
    }
    files: list[Path] = []
    for scope_root in roots:
        if scope_root.is_file():
            walk_files = [scope_root]
        else:
            walk_files = []
            for current, directories, filenames in os.walk(scope_root, followlinks=False):
                current_path = Path(current)
                directories[:] = sorted(
                    name
                    for name in directories
                    if name.casefold() not in DENIED_DIRS and not (current_path / name).is_symlink()
                )
                for filename in filenames:
                    candidate = current_path / filename
                    if candidate.is_symlink():
                        continue
                    walk_files.append(candidate)
                    if len(files) + len(walk_files) >= max_files:
                        break
                if len(files) + len(walk_files) >= max_files:
                    break
        for path in walk_files:
            try:
                relative = path.relative_to(root).as_posix()
                if path.suffix.casefold() not in allowed_extensions or _matches_deny(
                    relative, deny_patterns
                ):
                    continue
                if include_globs and not any(
                    PurePosixPath(relative).match(pattern) for pattern in include_globs
                ):
                    continue
                if path.stat().st_size > max_file_bytes:
                    continue
            except (OSError, ValueError):
                continue
            if path not in files:
                files.append(path)
            if len(files) >= max_files:
                return files
    return files


def _generic_chunks(
    relative: str, lines: list[str], max_lines: int = MAX_GENERIC_CHUNK_LINES
) -> list[Chunk]:
    chunks: list[Chunk] = []
    start = 0
    while start < len(lines):
        end = min(start + max_lines, len(lines))
        if end < len(lines):
            blank = next(
                (index for index in range(end - 1, start + 15, -1) if not lines[index].strip()),
                None,
            )
            if blank is not None:
                end = blank + 1
        content = "\n".join(lines[start:end]).strip()
        if content:
            chunks.append(Chunk(relative, start + 1, end, content, chunk_type="text"))
        start = max(end, start + 1)
    return chunks


def _markdown_chunks(relative: str, lines: list[str], max_lines: int) -> list[Chunk]:
    headings = [index for index, line in enumerate(lines) if re.match(r"^#{1,6}\s+", line)]
    if not headings:
        return _generic_chunks(relative, lines, max_lines)
    starts = sorted({0, *headings})
    chunks: list[Chunk] = []
    parents: list[str] = []
    for position, start in enumerate(starts):
        end = starts[position + 1] if position + 1 < len(starts) else len(lines)
        if start in headings:
            level = len(lines[start]) - len(lines[start].lstrip("#"))
            title = re.sub(r"^#{1,6}\s+", "", lines[start]).strip()
            parents = parents[: level - 1]
            parents.append(title)
        section_lines = lines[start:end]
        heading_path = " > ".join(parents) or None
        content = "\n".join(section_lines).strip()
        if content and len(section_lines) <= max_lines:
            chunks.append(
                Chunk(relative, start + 1, end, content, heading_path, "markdown-section")
            )
        elif content:
            for piece in _generic_chunks(relative, section_lines, max_lines):
                chunks.append(
                    Chunk(
                        relative,
                        start + piece.start_line,
                        start + piece.end_line,
                        piece.content,
                        heading_path,
                        "markdown-section",
                    )
                )
    return chunks


def _python_chunks(relative: str, text: str, lines: list[str], max_lines: int) -> list[Chunk]:
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return _generic_chunks(relative, lines, max_lines)
    chunks: list[Chunk] = []

    def visit(nodes: list[ast.stmt], parent: str | None = None) -> None:
        for node in nodes:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                start = min([node.lineno, *(decorator.lineno for decorator in node.decorator_list)])
                end = getattr(node, "end_lineno", node.lineno)
                name = f"{parent}.{node.name}" if parent else node.name
                chunks.append(
                    Chunk(relative, start, end, "\n".join(lines[start - 1 : end]), name, "symbol")
                )
                if isinstance(node, ast.ClassDef):
                    visit(node.body, name)

    visit(tree.body)
    if not chunks:
        return _generic_chunks(relative, lines, max_lines)
    return chunks


SYMBOL_DECLARATION = re.compile(
    r"^\s*(?:export\s+)?(?:default\s+)?(?:declare\s+)?(?:async\s+)?"
    r"(?:function|class|interface|type|enum|const|let|var)\s+([A-Za-z_$][\w$]*)"
)


def _source_chunks(
    relative: str, text: str, max_lines: int = MAX_GENERIC_CHUNK_LINES
) -> list[Chunk]:
    lines = text.splitlines()
    if not lines:
        return []
    suffix = PurePosixPath(relative).suffix.casefold()
    if suffix == ".md":
        return _markdown_chunks(relative, lines, max_lines)
    if suffix == ".py":
        return _python_chunks(relative, text, lines, max_lines)
    if suffix in {".ts", ".tsx", ".js", ".jsx", ".mjs"}:
        declarations = [
            (index, match.group(1))
            for index, line in enumerate(lines)
            if (match := SYMBOL_DECLARATION.match(line))
        ]
        if declarations:
            starts = sorted({0, *(index for index, _ in declarations)})
            symbol_at = {index: name for index, name in declarations}
            chunks: list[Chunk] = []
            for position, start in enumerate(starts):
                end = starts[position + 1] if position + 1 < len(starts) else len(lines)
                content = "\n".join(lines[start:end]).strip()
                if content:
                    chunks.append(
                        Chunk(
                            relative,
                            start + 1,
                            end,
                            content,
                            symbol_at.get(start),
                            "symbol" if start in symbol_at else "text",
                        )
                    )
            return chunks
    return _generic_chunks(relative, lines, max_lines)


def _rank_chunk(
    query: str,
    relative: str,
    chunk: Chunk,
    query_tokens: set[str],
) -> tuple[float, list[str]]:
    path_tokens = set(_tokens(relative.replace("/", " ").replace("_", " ").replace("-", " ")))
    symbol_tokens = set(_tokens(chunk.symbol or ""))
    content_tokens = set(_tokens(chunk.content))
    reasons: list[str] = []
    score = 0.0

    if chunk.symbol and _normalize(chunk.symbol) and _normalize(chunk.symbol) in _normalize(query):
        score += 12.0
        reasons.append(f"símbolo exato: {chunk.symbol}")
    elif query_tokens.intersection(symbol_tokens):
        score += 4.0 * len(query_tokens.intersection(symbol_tokens))
        reasons.append("termos coincidem com símbolo")

    path_overlap = query_tokens.intersection(path_tokens)
    if path_overlap:
        score += 3.0 * len(path_overlap)
        reasons.append("termos coincidem com caminho")

    text_overlap = query_tokens.intersection(content_tokens)
    if text_overlap:
        coverage = len(text_overlap) / max(len(query_tokens), 1)
        score += 7.0 * coverage + min(2.0, 0.15 * len(text_overlap))
        reasons.append(f"correspondência textual: {len(text_overlap)}/{len(query_tokens)} termos")

    if not reasons:
        return 0.0, []
    return round(score, 4), reasons


def _candidate_signals(
    query: str, relative: str, chunk: Chunk, query_tokens: set[str]
) -> frozenset[str]:
    path_tokens = set(_tokens(relative.replace("/", " ").replace("_", " ").replace("-", " ")))
    symbol_tokens = set(_tokens(chunk.symbol or ""))
    content_tokens = set(_tokens(chunk.content))
    signals: set[str] = set()
    normalized_symbol = _normalize(chunk.symbol or "")
    if normalized_symbol and normalized_symbol in _normalize(query):
        signals.add("symbol_exact")
    elif query_tokens.intersection(symbol_tokens):
        signals.add("symbol")
    if query_tokens.intersection(path_tokens):
        signals.add("path")
    if query_tokens.intersection(content_tokens):
        signals.add("text")
    return frozenset(signals)


def _rank_candidates(
    query: str,
    query_tokens: set[str],
    sources: list[CandidateSource],
    min_score: float,
) -> list[Candidate]:
    ranked: list[Candidate] = []
    for source in sources:
        score, reasons = _rank_chunk(
            query,
            source.chunk.path,
            source.chunk,
            query_tokens,
        )
        if score < min_score:
            continue
        if source.related_context:
            reasons.insert(
                0,
                "related context from "
                f"{source.related_context['source']}: {source.related_context['reason']}",
            )
        ranked.append(
            Candidate(
                source.chunk,
                score,
                tuple(reasons),
                source.sha256,
                source.last_modified,
                source.scope,
                source.related_context,
            )
        )
    return sorted(
        ranked,
        key=lambda item: (-item.score, item.chunk.path.casefold(), item.chunk.start_line),
    )


def _candidate_results(
    root: Path,
    files: list[Path],
    scopes: list[str],
    scope_roots: dict[str, list[Path]],
    query: str,
    limit: int,
    max_chunk_lines: int,
    min_score: float,
    related_context: dict[str, str] | None = None,
) -> tuple[list[Candidate], int]:
    query_tokens = set(_tokens(query))
    results: dict[tuple[str, int, int], CandidateSource] = {}
    files_read = 0
    for path in files:
        try:
            raw = path.read_bytes()
            text = raw.decode("utf-8")
            if _contains_secret_material(text):
                continue
            relative = path.relative_to(root).as_posix()
            modified = datetime.fromtimestamp(path.stat().st_mtime, UTC).isoformat()
        except (OSError, UnicodeDecodeError, ValueError):
            continue
        files_read += 1
        digest = hashlib.sha256(raw).hexdigest()
        matched_scopes = [
            scope
            for scope in scopes
            if any(
                path == scope_root or scope_root in path.parents
                for scope_root in scope_roots[scope]
            )
        ]
        scope = matched_scopes[0] if matched_scopes else "project"
        for chunk in _source_chunks(relative, text, max_chunk_lines):
            signals = _candidate_signals(query, relative, chunk, query_tokens)
            if not signals:
                continue
            key = (relative, chunk.start_line, chunk.end_line)
            candidate = CandidateSource(chunk, signals, digest, modified, scope, related_context)
            previous = results.get(key)
            if previous is None:
                results[key] = candidate
            else:
                results[key] = CandidateSource(
                    chunk,
                    previous.signals | signals,
                    digest,
                    modified,
                    previous.scope,
                    related_context,
                )
    candidates = _rank_candidates(query, query_tokens, list(results.values()), min_score)
    return candidates[:limit], files_read


def _discover_related_context(
    root: Path,
    candidates: list[Candidate],
    files: list[Path],
    query: str,
    scopes: list[str],
    scope_roots: dict[str, list[Path]],
    config: dict[str, Any],
) -> tuple[list[Candidate], list[dict[str, str]], int]:
    """Expand relevant, explicit Markdown references by one hop within scope."""
    max_links = int(config.get("max_related_context_links", 3))
    max_chunk_lines = int(config.get("max_chunk_lines", MAX_GENERIC_CHUNK_LINES))
    file_map = {path.relative_to(root).as_posix().casefold(): path for path in files}
    query_tokens = set(_tokens(query))
    related: dict[tuple[str, int, int], Candidate] = {}
    traces: list[dict[str, str]] = []
    visited_targets: set[str] = set()
    links_evaluated = 0
    limit_trace_added = False
    files_read = 0

    origin_paths = dict.fromkeys(candidate.chunk.path for candidate in candidates)
    for origin in origin_paths:
        if PurePosixPath(origin).suffix.casefold() != ".md":
            continue
        source_path = file_map.get(origin.casefold())
        if source_path is None:
            continue
        try:
            text = source_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        lines = text.splitlines()
        in_related_section = False
        for line in lines:
            heading = re.match(r"^(#{1,6})\s+", line)
            if heading:
                if len(heading.group(1)) <= 2:
                    in_related_section = bool(RELATED_CONTEXT_HEADING.match(line))
                elif not in_related_section:
                    continue
                if not in_related_section:
                    continue
            if not in_related_section:
                continue
            for link in MARKDOWN_LINK.finditer(line):
                trigger = line[: link.start()].strip(" -*\t")
                if not query_tokens.intersection(_tokens(trigger)):
                    continue
                if links_evaluated >= max_links:
                    if not limit_trace_added:
                        traces.append(
                            {
                                "source": origin,
                                "target": link.group(2),
                                "reason": "configured-related-link-limit-reached",
                                "status": "limit-reached",
                            }
                        )
                        limit_trace_added = True
                    continue
                links_evaluated += 1
                href = link.group(2)
                parsed = urlsplit(href)
                if parsed.scheme or parsed.netloc or parsed.path.startswith(("/", "\\")):
                    traces.append(
                        {
                            "source": origin,
                            "target": href,
                            "reason": "external-or-absolute-reference-denied",
                            "status": "denied",
                        }
                    )
                    continue
                target_ref = unquote(parsed.path)
                if not target_ref or "\\" in target_ref:
                    traces.append(
                        {
                            "source": origin,
                            "target": href,
                            "reason": "invalid-reference-path",
                            "status": "denied",
                        }
                    )
                    continue
                candidate_path = (
                    root / PurePosixPath(origin).parent / PurePosixPath(target_ref)
                ).resolve()
                if candidate_path != root and root not in candidate_path.parents:
                    traces.append(
                        {
                            "source": origin,
                            "target": href,
                            "reason": "reference-escapes-workspace",
                            "status": "denied",
                        }
                    )
                    continue
                try:
                    target = candidate_path.relative_to(root).as_posix()
                except ValueError:
                    continue
                accessible_target = file_map.get(target.casefold())
                if accessible_target is None:
                    traces.append(
                        {
                            "source": origin,
                            "target": target,
                            "reason": "outside-current-scope-or-filter",
                            "status": "not-accessible",
                        }
                    )
                    continue
                if target.casefold() in visited_targets:
                    continue
                visited_targets.add(target.casefold())
                reason = MARKDOWN_LINK.sub(lambda match: match.group(1), line).strip(" -*\t")
                relation = {
                    "source": origin,
                    "reason": reason[:500],
                }
                linked_candidates, count = _candidate_results(
                    root,
                    [accessible_target],
                    scopes,
                    scope_roots,
                    f"{query} {trigger}",
                    int(config.get("max_candidates", 100)),
                    max_chunk_lines,
                    0,
                    related_context=relation,
                )
                files_read += count
                traces.append(
                    {
                        "source": origin,
                        "target": target,
                        "reason": reason[:500],
                        "status": "candidate-found" if linked_candidates else "no-relevant-chunks",
                    }
                )
                for candidate in linked_candidates:
                    key = (
                        candidate.chunk.path,
                        candidate.chunk.start_line,
                        candidate.chunk.end_line,
                    )
                    related.setdefault(key, candidate)

    return list(related.values()), traces, files_read


def _overlaps_selected(candidate: Candidate, selected: list[Candidate]) -> bool:
    for previous in selected:
        if candidate.chunk.path != previous.chunk.path:
            continue
        intersection = max(
            0,
            min(candidate.chunk.end_line, previous.chunk.end_line)
            - max(candidate.chunk.start_line, previous.chunk.start_line)
            + 1,
        )
        candidate_size = candidate.chunk.end_line - candidate.chunk.start_line + 1
        previous_size = previous.chunk.end_line - previous.chunk.start_line + 1
        if intersection / min(candidate_size, previous_size) >= 0.8:
            return True
    return False


def _overlaps_previous(candidate: Candidate, previous_sources: list[dict[str, Any]]) -> bool:
    for previous in previous_sources:
        if candidate.chunk.path != previous["source"]:
            continue
        location = previous["location"]
        intersection = max(
            0,
            min(candidate.chunk.end_line, location["end_line"])
            - max(candidate.chunk.start_line, location["start_line"])
            + 1,
        )
        candidate_size = candidate.chunk.end_line - candidate.chunk.start_line + 1
        previous_size = location["end_line"] - location["start_line"] + 1
        if intersection / min(candidate_size, previous_size) >= 0.8:
            return True
    return False


def _previous_context_sources(
    previous_sources: list[dict[str, Any]] | None,
    root: Path,
    accessible_files: set[str],
    max_chunk_lines: int,
) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    if previous_sources is None:
        return [], []
    if not isinstance(previous_sources, list):
        raise TypeError("previous_sources must be a list")
    retained: list[dict[str, Any]] = []
    invalidated: list[dict[str, str]] = []
    seen: set[tuple[str, int, int]] = set()
    for previous in previous_sources:
        if not isinstance(previous, dict):
            raise TypeError("each previous source must be an object")
        source = previous.get("source")
        location = previous.get("location")
        content = previous.get("content")
        if (
            not isinstance(source, str)
            or not isinstance(location, dict)
            or not isinstance(location.get("start_line"), int)
            or not isinstance(location.get("end_line"), int)
            or isinstance(location.get("start_line"), bool)
            or isinstance(location.get("end_line"), bool)
            or location.get("start_line", 0) < 1
            or location.get("end_line", 0) < location.get("start_line", 0)
            or not isinstance(content, str)
        ):
            raise ValueError("previous source is missing a valid path, location or content")
        start_line = location["start_line"]
        end_line = location["end_line"]
        key = (source, start_line, end_line)
        if key in seen:
            continue
        seen.add(key)
        posix_path = PurePosixPath(source)
        if posix_path.is_absolute() or ".." in posix_path.parts or source not in accessible_files:
            invalidated.append({"source": source, "reason": "outside-current-scope-or-filter"})
            continue
        path = root.joinpath(*posix_path.parts)
        try:
            source_bytes = path.read_bytes()
            current_hash = hashlib.sha256(source_bytes).hexdigest()
            source_text = source_bytes.decode("utf-8")
        except OSError:
            invalidated.append({"source": source, "reason": "source-unavailable"})
            continue
        except UnicodeDecodeError:
            invalidated.append({"source": source, "reason": "source-unavailable"})
            continue
        if current_hash != previous.get("sha256"):
            invalidated.append({"source": source, "reason": "source-changed"})
            continue
        if _contains_secret_material(source_text):
            invalidated.append({"source": source, "reason": "source-now-excluded"})
            continue
        content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        if content_hash != previous.get("content_sha256"):
            invalidated.append({"source": source, "reason": "retrieved-content-changed"})
            continue
        current_chunk = next(
            (
                chunk
                for chunk in _source_chunks(source, source_text, max_chunk_lines)
                if chunk.start_line == start_line and chunk.end_line == end_line
            ),
            None,
        )
        if current_chunk is None or current_chunk.content != content:
            invalidated.append({"source": source, "reason": "content-does-not-match-source"})
            continue
        rendered = f"Source: {source}:{start_line}-{end_line}\n{content}"
        retained.append(
            {
                "source": source,
                "location": {"start_line": start_line, "end_line": end_line},
                "symbol": previous.get("symbol"),
                "chunk_type": previous.get("chunk_type", "text"),
                "scope": previous.get("scope"),
                "score": previous.get("score", 0),
                "reason": previous.get("reason", []),
                "sha256": current_hash,
                "content_sha256": content_hash,
                "last_modified": previous.get("last_modified"),
                "estimated_tokens": estimate_tokens(rendered),
                "content": content,
                "related_context": previous.get("related_context"),
                "trust": "untrusted-data",
            }
        )
    return retained, invalidated


def retrieve_context(
    query: str,
    *,
    scope: str = "auto",
    limit: int | None = None,
    context_budget_tokens: int | None = None,
    filters: dict[str, Any] | None = None,
    mandatory_context: list[str] | None = None,
    previous_sources: list[dict[str, Any]] | None = None,
    workspace_root: Path | str | None = None,
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return ranked, traceable source chunks assembled within a token estimate.

    Call this function again with a narrower or expanded query to request more
    context during a task. Mandatory context is never silently discarded.
    """
    started = time.perf_counter()
    if not isinstance(query, str) or not query.strip():
        raise ValueError("query must be a non-empty string")
    root = Path(workspace_root).resolve() if workspace_root else Path(__file__).resolve().parents[2]
    retrieval_config = config or _read_config(root)
    if len(query) > int(retrieval_config.get("max_query_chars", 4000)):
        raise ValueError("query exceeds the configured character limit")
    scopes_config = retrieval_config.get("scopes", {})
    if not isinstance(scopes_config, dict) or not scopes_config:
        raise ValueError("at least one retrieval scope must be configured")
    continuity_context, continuity_sources = _continuity_context(root, retrieval_config)
    selected_scopes = _route_scopes(query, scope, retrieval_config)
    scope_roots = {
        name: _resolve_roots(root, name, scopes_config[name]) for name in selected_scopes
    }
    all_roots: list[Path] = []
    for roots in scope_roots.values():
        for item in roots:
            if item not in all_roots:
                all_roots.append(item)

    request_filters = {} if filters is None else filters
    if not isinstance(request_filters, dict):
        raise TypeError("filters must be an object")
    candidates_limit = int(retrieval_config.get("max_candidates", 100))
    raw_result_limit = limit if limit is not None else retrieval_config.get("default_results", 8)
    if not isinstance(raw_result_limit, int) or isinstance(raw_result_limit, bool):
        raise TypeError("limit must be an integer")
    result_limit = raw_result_limit
    if (
        isinstance(result_limit, bool)
        or result_limit < 1
        or result_limit > int(retrieval_config.get("max_results", 20))
    ):
        raise ValueError("limit is outside the configured retrieval bounds")
    files = _iter_files(root, all_roots, retrieval_config, request_filters)
    accessible_paths = {path.relative_to(root).as_posix() for path in files}
    retained_previous, invalidated_previous = _previous_context_sources(
        previous_sources,
        root,
        accessible_paths,
        int(retrieval_config.get("max_chunk_lines", MAX_GENERIC_CHUNK_LINES)),
    )
    candidates, files_read = _candidate_results(
        root,
        files,
        selected_scopes,
        scope_roots,
        query,
        candidates_limit,
        int(retrieval_config.get("max_chunk_lines", MAX_GENERIC_CHUNK_LINES)),
        float(retrieval_config.get("min_candidate_score", 0)),
    )
    related_candidates, related_links, related_files_read = _discover_related_context(
        root,
        candidates,
        files,
        query,
        selected_scopes,
        scope_roots,
        retrieval_config,
    )
    files_read += related_files_read

    max_budget = int(retrieval_config.get("max_context_tokens", 12000))
    raw_budget = (
        context_budget_tokens
        if context_budget_tokens is not None
        else retrieval_config.get("default_context_tokens", 6000)
    )
    if not isinstance(raw_budget, int) or isinstance(raw_budget, bool):
        raise TypeError("context_budget_tokens must be an integer")
    budget = raw_budget
    if budget < 1 or budget > max_budget:
        raise ValueError(f"context budget must be between 1 and {max_budget} tokens")
    if mandatory_context is not None and (
        not isinstance(mandatory_context, list)
        or any(not isinstance(item, str) for item in mandatory_context)
    ):
        raise TypeError("mandatory_context must be a list of strings")
    effective_mandatory_context = [
        *continuity_context,
        *(item for item in (mandatory_context or []) if item),
    ]
    required_parts = [query.strip(), *effective_mandatory_context]
    mandatory_tokens = sum(estimate_tokens(item) for item in required_parts)
    previous_tokens = sum(source["estimated_tokens"] for source in retained_previous)
    required_tokens = mandatory_tokens + previous_tokens
    if required_tokens > budget:
        kind = "working-context" if retained_previous else "mandatory-context"
        raise ContextBudgetExceeded(required_tokens, budget, kind)

    selected: list[Candidate] = []
    used_tokens = required_tokens
    duplicate_count = 0

    def try_select(candidate: Candidate) -> bool:
        nonlocal used_tokens, duplicate_count
        if _overlaps_selected(candidate, selected) or _overlaps_previous(
            candidate,
            retained_previous,
        ):
            duplicate_count += 1
            return False
        rendered = (
            f"Source: {candidate.chunk.path}:{candidate.chunk.start_line}-"
            f"{candidate.chunk.end_line}\n{candidate.chunk.content}"
        )
        source_tokens = estimate_tokens(rendered)
        if used_tokens + source_tokens > budget:
            return False
        selected.append(candidate)
        used_tokens += source_tokens
        return True

    related_paths = list(dict.fromkeys(item.chunk.path for item in related_candidates))
    related_slots = min(len(related_paths), max(0, result_limit - 1))
    primary_limit = result_limit - related_slots
    for candidate in candidates:
        if len(selected) >= primary_limit:
            break
        try_select(candidate)
    related_paths_selected: set[str] = set()
    for candidate in related_candidates:
        if len(related_paths_selected) >= related_slots or len(selected) >= result_limit:
            break
        if candidate.chunk.path in related_paths_selected:
            continue
        if try_select(candidate):
            related_paths_selected.add(candidate.chunk.path)
    for candidate in candidates:
        if len(selected) >= result_limit:
            break
        if candidate in selected:
            continue
        try_select(candidate)
    for candidate in related_candidates:
        if len(selected) >= result_limit:
            break
        if candidate in selected:
            continue
        try_select(candidate)

    selected_sources = []
    for candidate in selected:
        chunk = candidate.chunk
        rendered = f"Source: {chunk.path}:{chunk.start_line}-{chunk.end_line}\n{chunk.content}"
        selected_sources.append(
            {
                "source": chunk.path,
                "location": {"start_line": chunk.start_line, "end_line": chunk.end_line},
                "symbol": chunk.symbol,
                "chunk_type": chunk.chunk_type,
                "scope": candidate.scope,
                "score": candidate.score,
                "reason": list(candidate.reasons),
                "sha256": candidate.sha256,
                "content_sha256": hashlib.sha256(chunk.content.encode("utf-8")).hexdigest(),
                "last_modified": candidate.last_modified,
                "estimated_tokens": estimate_tokens(rendered),
                "content": chunk.content,
                "related_context": candidate.related_context,
                "trust": "untrusted-data",
            }
        )

    assembled_sources = [*retained_previous, *selected_sources]
    selected_source_paths = {source["source"] for source in assembled_sources}
    for link in related_links:
        if link["status"] != "candidate-found":
            continue
        if link["target"] in selected_source_paths:
            link["status"] = "included"
        elif link["target"] in {source["source"] for source in retained_previous}:
            link["status"] = "already-in-working-context"
        else:
            link["status"] = "not-selected-by-budget-or-result-limit"
    elapsed_ms = round((time.perf_counter() - started) * 1000, 3)
    return {
        "status": "succeeded" if assembled_sources else "no-results",
        "query": query.strip(),
        "scope": scope,
        "routed_scopes": selected_scopes,
        "task_context": query.strip(),
        "mandatory_context": effective_mandatory_context,
        "continuity_context_sources": continuity_sources,
        "sources": assembled_sources,
        "budget": {
            "unit": "estimated_tokens",
            "estimator": "ceil(utf8_bytes/3)",
            "maximum": budget,
            "mandatory": mandatory_tokens,
            "working": previous_tokens,
            "retrieved": used_tokens - required_tokens,
            "used": used_tokens,
            "remaining": budget - used_tokens,
        },
        "trace": {
            "strategies": ["path", "symbol", "text", "explicit-related-context"],
            "candidate_count": len(candidates) + len(related_candidates),
            "selected_count": len(selected_sources),
            "previous_count": len(retained_previous),
            "invalidated_previous_sources": invalidated_previous,
            "related_context_links": related_links,
            "related_context_count": sum(
                1 for source in selected_sources if source["related_context"]
            ),
            "duplicate_count": duplicate_count,
            "files_scanned": len(files),
            "files_read": files_read,
            "duration_ms": elapsed_ms,
            "persistent_index": False,
            "query_content_logged": False,
        },
        "assembly_policy": {
            "mandatory_context_is_never_dropped": True,
            "retrieved_content_is_untrusted": True,
            "permission_scope_is_not_expanded_by_retrieval": True,
        },
    }
