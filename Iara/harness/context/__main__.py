"""JSON/CLI entry point for an agent or orchestrator to request context."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from .retrieval import ContextBudgetExceeded, retrieve_context


def _request_from_args() -> dict[str, Any]:
    parser = argparse.ArgumentParser(
        description="Retrieve bounded, traceable context from the Iara workspace."
    )
    parser.add_argument(
        "--request-json", action="store_true", help="Read a JSON request from stdin."
    )
    parser.add_argument("--query", help="Task or retrieval query.")
    parser.add_argument(
        "--scope", default="auto", help="auto, project, backend, frontend or harness."
    )
    parser.add_argument("--limit", type=int, help="Maximum source chunks to return.")
    parser.add_argument(
        "--context-budget-tokens", type=int, help="Maximum estimated context tokens."
    )
    args = parser.parse_args()
    if args.request_json:
        request = json.load(sys.stdin)
        if not isinstance(request, dict):
            raise ValueError("JSON request must be an object")
        return request
    if not args.query:
        parser.error("provide --query or --request-json")
    return {
        "query": args.query,
        "scope": args.scope,
        "limit": args.limit,
        "context_budget_tokens": args.context_budget_tokens,
    }


def main() -> int:
    try:
        request = _request_from_args()
        result = retrieve_context(
            query=request.get("query"),
            scope=request.get("scope", "auto"),
            limit=request.get("limit"),
            context_budget_tokens=request.get("context_budget_tokens"),
            filters=request.get("filters"),
            mandatory_context=request.get("mandatory_context"),
            previous_sources=request.get("previous_sources"),
        )
    except ContextBudgetExceeded as exc:
        print(
            json.dumps(
                {
                    "status": "blocked",
                    "error": f"{exc.context_kind}-exceeds-budget",
                    "required_tokens": exc.required_tokens,
                    "budget_tokens": exc.budget_tokens,
                },
                ensure_ascii=True,
            )
        )
        return 2
    except (ValueError, TypeError, json.JSONDecodeError) as exc:
        print(
            json.dumps({"status": "failed", "error": str(exc)}, ensure_ascii=True), file=sys.stderr
        )
        return 2
    print(json.dumps(result, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
