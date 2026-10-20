#!/usr/bin/env python3
"""Validate Iara's shared and component harness definitions using stdlib only."""

# Data: 19/10/2026
# Objetivo: Validar a decisão de preservar integralmente a resposta da API de dados,
#           sem atrelar os gates do Harness a MCP, formato gráfico ou transformação.

from __future__ import annotations

import json
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
ERRORS: list[str] = []
LOOP_POLICY_ID = "iara.repair-loop"


def fail(where: Path | str, message: str) -> None:
    ERRORS.append(f"{where}: {message}")


def load_json(path: Path) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(path.relative_to(ROOT), f"JSON invalido: {exc}")
        return None
    if not isinstance(value, dict):
        fail(path.relative_to(ROOT), "a raiz precisa ser um objeto JSON")
        return None
    no_secrets(path, value)
    return value


def files_for(component: Path, kind: str) -> list[Path]:
    folder = component / "harness" / kind
    return sorted(
        folder.glob("*.json" if kind in {"agents", "roles", "orchestrators", "workflows"} else "*")
    )


def json_entities(component: Path, kind: str) -> dict[str, tuple[Path, dict[str, Any]]]:
    result: dict[str, tuple[Path, dict[str, Any]]] = {}
    for path in files_for(component, kind):
        if path.suffix.lower() != ".json":
            continue
        entity = load_json(path)
        if entity is None:
            continue
        entity_id = entity.get("id")
        if not isinstance(entity_id, str) or not entity_id:
            fail(path.relative_to(ROOT), "campo 'id' obrigatorio")
            continue
        if entity_id in result:
            fail(path.relative_to(ROOT), f"id duplicado: {entity_id}")
        result[entity_id] = (path, entity)
    return result


def markdown_entities(component: Path, kind: str) -> dict[str, Path]:
    result: dict[str, Path] = {}
    for path in files_for(component, kind):
        if path.suffix.lower() != ".md":
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except OSError as exc:
            fail(path.relative_to(ROOT), str(exc))
            continue
        if not content.startswith("---\n"):
            fail(path.relative_to(ROOT), "arquivo Markdown precisa iniciar com frontmatter YAML")
            continue
        frontmatter = content.split("---", 2)[1]
        match = re.search(r"(?m)^id:\s*([A-Za-z0-9_.-]+)\s*$", frontmatter)
        if not match:
            fail(path.relative_to(ROOT), "frontmatter precisa declarar um id")
            continue
        entity_id = match.group(1)
        if entity_id in result:
            fail(path.relative_to(ROOT), f"id duplicado: {entity_id}")
        result[entity_id] = path
    return result


def check_refs(where: Path, refs: Any, available: set[str], label: str) -> None:
    if not isinstance(refs, list):
        fail(where.relative_to(ROOT), f"'{label}' precisa ser uma lista")
        return
    for ref in refs:
        if ref not in available:
            fail(where.relative_to(ROOT), f"referencia {label} inexistente: {ref}")


def validate_loop_policy_config() -> None:
    path = ROOT / "harness/config/loop-policy.json"
    policy = load_json(path)
    if policy is None:
        return
    if policy.get("schema_version") != 1 or policy.get("id") != LOOP_POLICY_ID:
        fail(path.relative_to(ROOT), f"loop policy precisa declarar schema_version 1 e id {LOOP_POLICY_ID}")
    if policy.get("execution") != "agent-guided-declarative":
        fail(path.relative_to(ROOT), "execution deve deixar claro que a politica e declarativa e guiada por agente")
    for field in ("triggers", "cycle", "success_when", "pause_when", "guardrails"):
        if not isinstance(policy.get(field), list) or not policy[field]:
            fail(path.relative_to(ROOT), f"{field} precisa ser uma lista nao vazia")
    retry_limit = policy.get("retry_limit")
    if (
        not isinstance(retry_limit, dict)
        or retry_limit.get("metric") != "consecutive-failures-with-the-same-root-cause"
        or not isinstance(retry_limit.get("max"), int)
        or isinstance(retry_limit.get("max"), bool)
        or retry_limit.get("max", 0) < 1
        or not retry_limit.get("reset_when")
    ):
        fail(path.relative_to(ROOT), "retry_limit precisa limitar falhas consecutivas pela mesma causa e definir quando reseta")
    if policy.get("on_limit") != "pause-with-evidence-and-next-options":
        fail(path.relative_to(ROOT), "atingir retry_limit deve pausar com evidencias e proximas opcoes")
    if policy.get("resume_at") != "paused-or-failed-step":
        fail(path.relative_to(ROOT), "retomada deve continuar do passo pausado ou com falha")
    completion = policy.get("completion_discipline", {})
    if (
        completion.get("partial_delivery_is_completion") is not False
        or completion.get("iteration_limit") != "pause-with-evidence-never-success"
        or completion.get("blocked_work")
        != "finish-independent-authorized-work-then-record-evidence-cause-and-next-action"
        or not completion.get("active_until")
        or not completion.get("interruption_or_status_request")
    ):
        fail(path.relative_to(ROOT), "completion_discipline precisa impedir conclusao parcial e preservar retomada com evidencia")
    if not policy.get("execution_note"):
        fail(path.relative_to(ROOT), "execution_note precisa informar o estado atual de execucao pelo runner")


def validate_orchestrator_loop_ref(path: Path, orchestrator: dict[str, Any]) -> None:
    if orchestrator.get("loop_policy_ref") != LOOP_POLICY_ID:
        fail(path.relative_to(ROOT), f"loop_policy_ref precisa apontar para {LOOP_POLICY_ID}")
    loop_entry_steps = orchestrator.get("loop_entry_steps")
    steps = orchestrator.get("steps", [])
    if (
        not isinstance(loop_entry_steps, list)
        or not loop_entry_steps
        or any(not isinstance(step, str) for step in loop_entry_steps)
        or not set(loop_entry_steps).issubset(set(steps))
    ):
        fail(path.relative_to(ROOT), "loop_entry_steps precisa listar checkpoints existentes do orquestrador")


def no_secrets(path: Path, value: Any) -> None:
    content = json.dumps(value, ensure_ascii=False)
    patterns = [
        r"(?<![A-Za-z0-9])sk-[A-Za-z0-9_-]{20,}",
        r"(?i)[\"']?(?:api[_-]?key|secret|password|access[_-]?token)[\"']?\s*:\s*[\"'](?!replace-|your-|<)[^\"']{8,}[\"']",
    ]
    for pattern in patterns:
        if re.search(pattern, content):
            fail(path.relative_to(ROOT), "possivel credencial literal encontrada")
            return


def validate_commit_policy() -> None:
    """Keep the shared Git checkpoint policy complete and explicit."""
    policy_path = ROOT / "harness/config/commit-policy.json"
    policy = load_json(policy_path) or {}
    if policy.get("schema_version") != 1:
        fail(policy_path.relative_to(ROOT), "schema_version precisa ser 1")
        return
    required_types = {"feat", "fix", "refactor", "test", "docs", "style", "build", "ci", "chore"}
    if not required_types.issubset(set(policy.get("types", {}))):
        fail(policy_path.relative_to(ROOT), "types deve definir os tipos de commit obrigatorios")
    if not policy.get("message_format") or not policy.get("scopes"):
        fail(policy_path.relative_to(ROOT), "message_format e scopes precisam estar definidos")
    checkpoints = policy.get("checkpoints", {})
    for key in ("user_directed", "after_cohesive_change", "after_verified_feature_or_bugfix", "before_handoff_or_release"):
        if checkpoints.get(key) is not True:
            fail(policy_path.relative_to(ROOT), f"checkpoint {key} precisa estar habilitado")
    if checkpoints.get("automatic_commit") is not False:
        fail(policy_path.relative_to(ROOT), "commits automaticos devem permanecer desabilitados")
    repositories = policy.get("repositories", {})
    if repositories.get("backend") != "Backend/" or repositories.get("frontend") != "Frontend/":
        fail(policy_path.relative_to(ROOT), "mapeamento dos repositorios Backend e Frontend incorreto")
    if not repositories.get("shared_harness"):
        fail(policy_path.relative_to(ROOT), "ownership de commits do Harness compartilhado precisa estar documentado")
    guide = ROOT / "harness/COMMIT_GUIDE.md"
    if not guide.is_file():
        fail(guide.relative_to(ROOT), "guia de commits do Harness nao existe")
    elif "git diff --cached" not in guide.read_text(encoding="utf-8"):
        fail(guide.relative_to(ROOT), "guia precisa exigir revisao do index antes do commit")


def validate_context_continuity() -> None:
    """Require durable project context and synchronized task handoffs in every scope."""
    project_path = ROOT / "harness/config/project.json"
    project = load_json(project_path) or {}
    continuity = project.get("context_retrieval", {}).get("continuity", {})
    canonical_paths = {
        "estado-do-projeto.md": continuity.get("canonical_project_state"),
        "retomada-atual.md": continuity.get("canonical_active_handoff"),
    }
    for filename, relative in canonical_paths.items():
        if not isinstance(relative, str) or not relative:
            fail(project_path.relative_to(ROOT), f"continuity precisa declarar caminho canônico para {filename}")
            continue
        canonical = (ROOT / relative).resolve()
        if canonical == ROOT or ROOT not in canonical.parents:
            fail(project_path.relative_to(ROOT), f"caminho canônico de continuidade sai do workspace: {relative}")
            continue
        if not canonical.is_file():
            fail(canonical.relative_to(ROOT), "arquivo canônico de contexto/retomada ausente")
            continue
        try:
            canonical_content = canonical.read_bytes()
        except OSError as exc:
            fail(canonical.relative_to(ROOT), f"arquivo canônico de contexto ilegível: {exc}")
            continue
        if not canonical_content or len(canonical_content) > 32768:
            fail(canonical.relative_to(ROOT), "arquivo de contexto deve ter conteúdo e no máximo 32 KiB")
        expected_headings = (
            ["## Missão e limites", "## Decisões de interação com a LLM", "## Estado do trabalho"]
            if filename == "estado-do-projeto.md"
            else ["## Frentes em andamento", "## Como retomar"]
        )
        decoded = canonical_content.decode("utf-8", errors="replace")
        for heading in expected_headings:
            if heading not in decoded:
                fail(canonical.relative_to(ROOT), f"resumo de continuidade sem seção obrigatória: {heading}")
        for component in ("Backend", "Frontend"):
            mirror_root = continuity.get("component_mirrors", {}).get(component.casefold())
            if not isinstance(mirror_root, str) or not mirror_root:
                fail(project_path.relative_to(ROOT), f"continuity sem diretório de espelho para {component}")
                continue
            mirror = (ROOT / mirror_root / filename).resolve()
            if mirror == ROOT or ROOT not in mirror.parents:
                fail(project_path.relative_to(ROOT), f"caminho de espelho sai do workspace: {mirror_root}")
                continue
            if not mirror.is_file():
                fail(mirror.relative_to(ROOT), "espelho local de contexto/retomada ausente")
                continue
            try:
                if mirror.read_bytes() != canonical_content:
                    fail(mirror.relative_to(ROOT), "espelho de contexto diverge do arquivo canônico")
            except OSError as exc:
                fail(mirror.relative_to(ROOT), f"espelho de contexto ilegível: {exc}")
    if continuity.get("read_before_task_retrieval") is not True:
        fail(project_path.relative_to(ROOT), "estado durável precisa ser leitura obrigatória antes do Retrieval")
    if continuity.get("update_after_user_decision") is not True or continuity.get("update_before_handoff") is not True:
        fail(project_path.relative_to(ROOT), "protocolo de continuidade precisa atualizar decisões e handoffs")
    if continuity.get("mirror_policy") != "byte-identical":
        fail(project_path.relative_to(ROOT), "espelhos de contexto devem usar mirror_policy byte-identical")
    retrieval_path = ROOT / "harness/context/retrieval.py"
    retrieval_source = retrieval_path.read_text(encoding="utf-8") if retrieval_path.is_file() else ""
    for marker in ("def _continuity_context(", '"continuity_context_sources": continuity_sources'):
        if marker not in retrieval_source:
            fail(retrieval_path.relative_to(ROOT), "Retrieval precisa injetar estado e retomada como contexto obrigatório")
            break
    cli_path = ROOT / "harness/context/__main__.py"
    cli_source = cli_path.read_text(encoding="utf-8") if cli_path.is_file() else ""
    if "ensure_ascii=True" not in cli_source:
        fail(cli_path.relative_to(ROOT), "CLI deve produzir JSON compatível com terminais Windows")


def validate_product_harness() -> None:
    """Enforce decision, gateway, traceability, UX and synthetic-data policies."""
    validate_context_continuity()
    validate_loop_policy_config()
    validate_commit_policy()
    decisions_path = ROOT / "harness/config/decisions.json"
    decisions = load_json(decisions_path) or {}
    if decisions.get("schema_version") != 1:
        fail(decisions_path.relative_to(ROOT), "schema_version precisa ser 1")
    decision_items = decisions.get("decisions", {})
    expected_decisions = {
        "language",
        "database",
        "docker",
        "authentication",
        "security_baseline",
        "data",
        "context_contract",
        "llm_interaction",
        "model",
        "provider",
        "langchain",
        "conversation_deletion",
        "conversation_navigation",
        "message_cache",
        "request_idempotency",
        "rate_limiting",
        "operational_metrics",
        "user_token_usage",
    }
    if set(decision_items) != expected_decisions:
        fail(
            decisions_path.relative_to(ROOT),
            "decisions precisa cobrir linguagem, banco, auth, segurança, dados, modelo, provider e LangChain",
        )
    for key, decision in decision_items.items():
        if not isinstance(decision, dict) or not decision.get("status") or not decision.get("value"):
            fail(decisions_path.relative_to(ROOT), f"decisao {key} precisa declarar status e value")
        if not isinstance(decision.get("evidence"), list) or not decision["evidence"]:
            fail(decisions_path.relative_to(ROOT), f"decisao {key} precisa apontar evidencias")
        for evidence in decision.get("evidence", []):
            if not (ROOT / evidence).exists():
                fail(decisions_path.relative_to(ROOT), f"evidencia inexistente para {key}: {evidence}")

    project_path = ROOT / "harness/config/project.json"
    project = load_json(project_path) or {}
    gateway = project.get("model_gateway", {})
    model_decision = decision_items.get("model", {})
    provider_decision = decision_items.get("provider", {})
    project_decisions = project.get("decisions", {})
    expected_project_decisions = {
        "language": decision_items.get("language", {}).get("value"),
        "database": decision_items.get("database", {}).get("value"),
        "docker": decision_items.get("docker", {}).get("value"),
        "authentication": decision_items.get("authentication", {}).get("value"),
        "security_baseline": decision_items.get("security_baseline", {}).get("value"),
        "message_cache": decision_items.get("message_cache", {}).get("value"),
        "request_idempotency": decision_items.get("request_idempotency", {}).get("value"),
        "rate_limiting": decision_items.get("rate_limiting", {}).get("value"),
        "operational_metrics": decision_items.get("operational_metrics", {}).get("value"),
        "user_token_usage": decision_items.get("user_token_usage", {}).get("value"),
        "data": decision_items.get("data", {}).get("value"),
        "model": f"fixed-catalog-model-{model_decision.get('catalog_model_id')}; logical-alias-{model_decision.get('logical_alias')}",
        "provider": provider_decision.get("value"),
        "langchain": decision_items.get("langchain", {}).get("value"),
        "llm_interaction": decision_items.get("llm_interaction", {}).get("value"),
    }
    if project_decisions != expected_project_decisions:
        fail(project_path.relative_to(ROOT), "decisions do projeto divergem da fonte de verdade decisions.json")
    # A origem é uma API HTTP direta; este gate protege a fronteira Backend-only e
    # impede que futuras alterações voltem a exigir o fluxo antigo de ferramentas MCP.
    data_source = project.get("company_data_source", {})
    if (
        data_source.get("selected_source") != "API de dados"
        or data_source.get("invocation_boundary") != "backend-only"
        or data_source.get("direct_database_access") is not False
        or data_source.get("response_policy")
        != "preserve-original-body-byte-for-byte-no-filter-or-transformation"
        or data_source.get("development_fallback") != "synthetic-json-fixtures"
    ):
        fail(project_path.relative_to(ROOT), "API de dados deve ser backend-only, preservar o corpo original sem filtro e manter fixtures sintéticas até a integração")
    status_id_modelo = gateway.get("model_id_status")
    manifesto_decisoes_modelo = (
        load_json(ROOT / "harness" / "config" / "decisions.json") or {}
    )
    model_decision = manifesto_decisoes_modelo.get("decisions", {}).get("model", {})
    if model_decision.get("status") == "selection-pending" and status_id_modelo not in {
        "project-selection-required",
        "candidate-configured-validation-required",
    }:
        fail(
            project_path.relative_to(ROOT),
            "status do ID do modelo precisa refletir selecao ou validacao pendente",
        )
    if model_decision.get("status") == "decided-for-iara-service" and (
        status_id_modelo != "fixed-in-catalog"
        or gateway.get("model_id_catalog_value") != model_decision.get("catalog_model_id")
    ):
        fail(
            project_path.relative_to(ROOT),
            "modelo fixo da Iara precisa corresponder ao ID registrado no catálogo",
        )
    if model_decision.get("environment_variable") != gateway.get("model_alias_env"):
        fail(decisions_path.relative_to(ROOT), "variavel do alias diverge do Model Gateway")
    if model_decision.get("provider_model_id_environment_variables") != gateway.get(
        "provider_model_id_env"
    ):
        fail(decisions_path.relative_to(ROOT), "variaveis de IDs de provider divergem do Model Gateway")
    if provider_decision.get("credential_environment_variable") != gateway.get("provider_credential_env"):
        fail(decisions_path.relative_to(ROOT), "credencial do provider diverge do Model Gateway")

    local_decisions = {
        "language": decision_items.get("language", {}).get("value"),
        "database": decision_items.get("database", {}).get("value"),
        "docker": decision_items.get("docker", {}).get("value"),
        "authentication": decision_items.get("authentication", {}).get("value"),
        "security_baseline": decision_items.get("security_baseline", {}).get("value"),
        "request_idempotency": decision_items.get("request_idempotency", {}).get("value"),
        "rate_limiting": decision_items.get("rate_limiting", {}).get("value"),
        "operational_metrics": decision_items.get("operational_metrics", {}).get("value"),
        "user_token_usage": decision_items.get("user_token_usage", {}).get("value"),
        "data": decision_items.get("data", {}).get("value"),
        "conversation_deletion": decision_items.get("conversation_deletion", {}).get("value"),
        "conversation_navigation": decision_items.get("conversation_navigation", {}).get("value"),
        "message_cache": decision_items.get("message_cache", {}).get("value"),
        "context_contract": {
            key: value
            for key, value in decision_items.get("context_contract", {}).items()
            if key != "evidence"
        },
        "llm_interaction": decision_items.get("llm_interaction", {}).get("value"),
        "model": {
            "status": model_decision.get("status"),
            "selection_criterion": model_decision.get("selection_criterion"),
            "environment_variable": model_decision.get("environment_variable"),
            "configuration_semantics": model_decision.get("configuration_semantics"),
            "logical_alias": model_decision.get("logical_alias"),
            "provider_model_id_environment_variables": model_decision.get(
                "provider_model_id_environment_variables"
            ),
            "user_visibility": model_decision.get("user_visibility"),
            "candidate": model_decision.get("candidate"),
            "candidate_status": model_decision.get("candidate_status"),
            "catalog_model_id": model_decision.get("catalog_model_id"),
        },
        "provider": {
            "value": provider_decision.get("value"),
            "credential_environment_variable": provider_decision.get("credential_environment_variable"),
            "base_url_environment_variable": provider_decision.get("base_url_environment_variable"),
        },
        "langchain": decision_items.get("langchain", {}).get("value"),
        "llm_interaction": decision_items.get("llm_interaction", {}).get("value"),
    }
    component_roots = {"backend": ROOT / "Backend", "frontend": ROOT / "Frontend"}
    for component, component_root in component_roots.items():
        component_config_path = component_root / "harness/config/harness.json"
        component_config = load_json(component_config_path) or {}
        local_decisions_path = component_root / "harness/config/decisions.json"
        local_decision_manifest = load_json(local_decisions_path) or {}
        # Component manifests store shared decisions under `decisions`; the older
        # `shared_decisions` key is not part of the current committed manifest schema.
        component_shared_decisions = local_decision_manifest.get("decisions", {})
        for decision_name, expected_decision in local_decisions.items():
            recorded_decision = component_shared_decisions.get(decision_name)
            if decision_name in {"model", "provider"} and isinstance(recorded_decision, dict):
                normalized_decision = {
                    key: recorded_decision.get(key) for key in expected_decision
                }
            elif decision_name == "context_contract" and isinstance(recorded_decision, dict):
                normalized_decision = {
                    key: value
                    for key, value in recorded_decision.items()
                    if key != "evidence"
                }
            elif isinstance(recorded_decision, dict):
                normalized_decision = recorded_decision.get("value")
            else:
                normalized_decision = recorded_decision
            if normalized_decision != expected_decision:
                fail(
                    local_decisions_path.relative_to(ROOT),
                    f"decisao compartilhada divergente: {decision_name}",
                )
        for relative in local_decision_manifest.get("evidence", []):
            if not (component_root / relative).exists():
                fail(local_decisions_path.relative_to(ROOT), f"evidencia local inexistente: {relative}")
        expected_paths = {
            "project_decisions_manifest": "harness/config/decisions.json",
            "requirements_traceability_manifest": "harness/traceability/requirements.json",
        }
        if component == "backend":
            expected_paths["synthetic_data_policy_manifest"] = "harness/config/synthetic-data.json"
        else:
            expected_paths["quality_gates_manifest"] = "harness/config/quality-gates.json"
        for field, relative in expected_paths.items():
            if component_config.get(field) != relative or not (component_root / relative).is_file():
                fail(component_config_path.relative_to(ROOT), f"{field} precisa apontar ao manifesto versionado local {relative}")
        local_trace_path = component_root / "harness/traceability/requirements.json"
        local_trace = load_json(local_trace_path) or {}
        local_criteria = local_trace.get("criteria", [])
        if not local_criteria:
            fail(local_trace_path.relative_to(ROOT), "a rastreabilidade local precisa conter criterios")
        local_gate_ids = set(component_config.get("commands", {})) | set(component_config.get("manual_gates", []))
        if component == "backend":
            local_gate_ids.add("provider.live-demo")
        for criterion in local_criteria:
            if not isinstance(criterion, dict) or not criterion.get("id") or not criterion.get("requirement") or criterion.get("status") not in {"planned", "scaffold", "policy-defined", "implemented"}:
                fail(local_trace_path.relative_to(ROOT), "cada criterio local precisa de id, requisito e status valido")
                continue
            if not criterion.get("evidence") or not criterion.get("gates"):
                fail(local_trace_path.relative_to(ROOT), f"criterio local incompleto: {criterion.get('id')}")
            for relative in criterion.get("evidence", []):
                if not (component_root / relative).exists():
                    fail(local_trace_path.relative_to(ROOT), f"evidencia local inexistente para {criterion['id']}: {relative}")
            if not set(criterion.get("gates", [])).issubset(local_gate_ids):
                fail(local_trace_path.relative_to(ROOT), f"gate local nao declarado para {criterion['id']}")

    regras_compartilhadas: list[dict[str, str]] = []
    for componente in ("Backend", "Frontend"):
        pasta_regras = ROOT / componente / "harness/rules"
        mapa_compartilhado: dict[str, str] = {}
        for caminho in pasta_regras.glob("*.md"):
            conteudo = caminho.read_text(encoding="utf-8")
            frente = conteudo.split("---", 2)[1] if conteudo.startswith("---\n") else ""
            id_match = re.search(r"(?m)^id:\s*([A-Za-z0-9_.-]+)\s*$", frente)
            scope_match = re.search(r"(?m)^scope:\s*([A-Za-z0-9_.-]+)\s*$", frente)
            if id_match and scope_match and scope_match.group(1) == "shared":
                mapa_compartilhado[id_match.group(1)] = conteudo.strip()
        regras_compartilhadas.append(mapa_compartilhado)
    if regras_compartilhadas[0] != regras_compartilhadas[1]:
        fail("Backend/harness/rules e Frontend/harness/rules", "regras shared precisam ter os mesmos IDs e conteúdo nos dois repositórios")

    excecoes = decisions.get("rule_exceptions", [])
    if not isinstance(excecoes, list):
        fail(decisions_path.relative_to(ROOT), "rule_exceptions precisa ser uma lista")
        excecoes = []
    ids_excecoes: set[str] = set()
    for excecao in excecoes:
        campos_obrigatorios = ("id", "rule_id", "scope", "reason", "approved_by", "approved_at")
        if not isinstance(excecao, dict) or any(not excecao.get(campo) for campo in campos_obrigatorios):
            fail(decisions_path.relative_to(ROOT), "cada excecao precisa de id, regra, escopo, justificativa e aprovacao")
            continue
        if excecao["id"] in ids_excecoes:
            fail(decisions_path.relative_to(ROOT), f"id de excecao duplicado: {excecao['id']}")
        ids_excecoes.add(excecao["id"])
        regra_existe = any(
            (ROOT / componente / "harness/rules" / f"{excecao['rule_id']}.md").is_file()
            for componente in ("Backend", "Frontend")
        )
        if not regra_existe:
            fail(decisions_path.relative_to(ROOT), f"regra inexistente na excecao {excecao['id']}: {excecao['rule_id']}")
        if not excecao.get("review_by") and not excecao.get("review_condition"):
            fail(decisions_path.relative_to(ROOT), f"excecao sem revisao definida: {excecao['id']}")
        for campo in ("approved_at", "review_by"):
            if excecao.get(campo):
                try:
                    date.fromisoformat(str(excecao[campo]))
                except ValueError:
                    fail(decisions_path.relative_to(ROOT), f"{campo} deve usar uma data ISO valida em {excecao['id']}")

    env_path = ROOT / "Backend/.env.example"
    try:
        env_text = env_path.read_text(encoding="utf-8")
    except OSError as exc:
        env_text = ""
        fail(env_path.relative_to(ROOT), f"nao foi possivel ler configuracao de exemplo: {exc}")
    model_id_variables = list(gateway.get("provider_model_id_env", {}).values())
    for variable in [gateway.get("provider_credential_env")]:
        if not variable or not re.search(rf"(?m)^{re.escape(variable)}=replace-", env_text):
            fail(env_path.relative_to(ROOT), f"{variable} deve permanecer placeholder ate configuracao local")
    if gateway.get("model_id_status") == "candidate-configured-validation-required":
        candidate = decision_items.get("model", {}).get("candidate")
        for variable in model_id_variables:
            if not candidate or not re.search(
                rf"(?m)^{re.escape(variable)}={re.escape(candidate)}$", env_text
            ):
                fail(
                    env_path.relative_to(ROOT),
                    f"{variable} deve corresponder ao modelo candidato registrado",
                )
    else:
        for variable in model_id_variables:
            if not variable or not re.search(rf"(?m)^{re.escape(variable)}=replace-", env_text):
                fail(
                    env_path.relative_to(ROOT),
                    f"{variable} deve permanecer placeholder ate configuracao local",
                )
    readme_path = ROOT / "README.md"
    try:
        readme_text = readme_path.read_text(encoding="utf-8").casefold()
    except OSError as exc:
        readme_text = ""
        fail(readme_path.relative_to(ROOT), f"README indisponivel: {exc}")
    required_readme_terms = ["IARA_DEFAULT_MODEL", "IARA_BASE_URL", "IARA_API_KEY", "dados sintéticos", "sqlite", "ddl", "sso", "líder técnico"]
    for term in required_readme_terms:
        if term.casefold() not in readme_text:
            fail(readme_path.relative_to(ROOT), f"README precisa registrar decisao/status: {term}")

    gateway_path = ROOT / "harness/config/model-gateway.json"
    gateway_manifest = load_json(gateway_path) or {}
    if gateway_manifest.get("schema_version") != 1:
        fail(gateway_path.relative_to(ROOT), "schema_version precisa ser 1")
    # Suspended representa uma decisão deliberada de produto, diferente de uma
    # capability esquecida ou inválida; por isso é um estado verificável do Harness.
    statuses = {"planned", "scaffold", "test-only", "policy-defined", "implemented", "suspended"}
    capabilities = gateway_manifest.get("capabilities", {})
    for capability, record in capabilities.items():
        if record.get("status") not in statuses:
            fail(gateway_path.relative_to(ROOT), f"status invalido para capability {capability}")
        evidence = record.get("evidence", [])
        if record.get("status") in {"scaffold", "implemented", "test-only", "policy-defined"} and not evidence:
            fail(gateway_path.relative_to(ROOT), f"{capability} requer evidencia para status {record.get('status')}")
        for relative in evidence:
            if not (ROOT / relative).exists():
                fail(gateway_path.relative_to(ROOT), f"evidencia inexistente para {capability}: {relative}")
    if gateway_manifest.get("implementation_status") == "implemented" and any(
        record.get("status") != "implemented" for record in capabilities.values()
    ):
        fail(gateway_path.relative_to(ROOT), "Gateway nao pode estar completo enquanto capabilities estiverem pendentes")
    if gateway_manifest.get("provider_independent_contract") != "Backend/app/gateway.py":
        fail(gateway_path.relative_to(ROOT), "contrato independente do provider deve apontar para Backend/app/gateway.py")
    if gateway_manifest.get("response_block_contracts") != "Backend/app/contracts.py":
        fail(gateway_path.relative_to(ROOT), "contratos de conteudo devem apontar para Backend/app/contracts.py")
    alias_capability = capabilities.get("model_alias_resolution", {})
    if (
        alias_capability.get("status") != "implemented"
        or alias_capability.get("logical_alias_env") != gateway.get("model_alias_env")
        or alias_capability.get("default_alias") != gateway.get("default_model_alias")
        or alias_capability.get("provider_model_id_env") != gateway.get("provider_model_id_env")
        or alias_capability.get("backend_only") is not True
    ):
        fail(
            gateway_path.relative_to(ROOT),
            "catálogo de aliases deve estar implementado e corresponder à configuração privada do Backend",
        )
    required_invariants = {
        "frontend-never-receives-provider-credentials",
        "provider-invocation-is-backend-only",
        "all-provider-outputs-are-normalized-to-iara-contracts",
        "structured-output-is-validated-before-persistence-or-rendering",
        "public-errors-never-contain-raw-provider-payloads",
        "default-automated-suite-uses-fake-adapter-without-network",
    }
    if not required_invariants.issubset(set(gateway_manifest.get("invariants", []))):
        fail(gateway_path.relative_to(ROOT), "invariantes minimos do Model Gateway estao incompletos")

    trace_path = ROOT / "harness/traceability/requirements.json"
    trace = load_json(trace_path) or {}
    if trace.get("schema_version") != 1 or not isinstance(trace.get("criteria"), list) or not trace["criteria"]:
        fail(trace_path.relative_to(ROOT), "criterios de rastreabilidade precisam ser uma lista nao vazia")
    criterion_ids: set[str] = set()
    valid_statuses = {"planned", "scaffold", "policy-defined", "implemented"}
    gates_path = ROOT / "harness/config/quality-gates.json"
    gates = load_json(gates_path) or {}
    declared_gates = gates.get("gates", []) if isinstance(gates.get("gates", []), list) else []
    declared_acceptance = gates.get("acceptance_checks", []) if isinstance(gates.get("acceptance_checks", []), list) else []
    valid_evidence = {
        item.get("id")
        for item in declared_gates + declared_acceptance
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    ux_config = gates.get("ux_review", {}) if isinstance(gates.get("ux_review", {}), dict) else {}
    if isinstance(ux_config.get("id"), str):
        valid_evidence.add(ux_config["id"])
    for criterion in trace.get("criteria", []):
        if not isinstance(criterion, dict) or not isinstance(criterion.get("id"), str):
            fail(trace_path.relative_to(ROOT), "cada criterio precisa de id")
            continue
        criterion_id = criterion["id"]
        if criterion_id in criterion_ids:
            fail(trace_path.relative_to(ROOT), f"criterio duplicado: {criterion_id}")
        criterion_ids.add(criterion_id)
        if criterion.get("status") not in valid_statuses:
            fail(trace_path.relative_to(ROOT), f"status invalido no criterio {criterion_id}")
        if not criterion.get("requirement") or not criterion.get("evidence") or not criterion.get("gates"):
            fail(trace_path.relative_to(ROOT), f"criterio {criterion_id} precisa de requisito, evidencia e gate")
        for relative in criterion.get("evidence", []):
            if not (ROOT / relative).exists():
                fail(trace_path.relative_to(ROOT), f"evidencia inexistente para {criterion_id}: {relative}")
        if not set(criterion.get("gates", [])).issubset(valid_evidence):
            fail(trace_path.relative_to(ROOT), f"gate de rastreabilidade desconhecido em {criterion_id}")

    coverage_config = gates.get("test_coverage", {})
    coverage_path = ROOT / "harness/testing/coverage.json"
    coverage = load_json(coverage_path) or {}
    if (
        coverage_config.get("manifest") != "harness/testing/coverage.json"
        or coverage_config.get("enforced_by") != "harness.validate"
    ):
        fail(gates_path.relative_to(ROOT), "test_coverage precisa apontar para a matriz e ser validado pelo Harness")
    if coverage.get("schema_version") != 1 or not isinstance(coverage.get("scenarios"), list):
        fail(coverage_path.relative_to(ROOT), "matriz de testes precisa declarar schema_version 1 e scenarios")
    suite_ids = {
        item.get("id")
        for item in coverage.get("suites", [])
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    if not suite_ids:
        fail(coverage_path.relative_to(ROOT), "matriz precisa declarar suites")
    coverage_scenario_ids: set[str] = set()
    covered_criteria: set[str] = set()
    valid_scenario_statuses = {"implemented", "planned", "manual-required", "opt-in", "deferred"}
    for scenario in coverage.get("scenarios", []):
        if not isinstance(scenario, dict) or not isinstance(scenario.get("id"), str):
            fail(coverage_path.relative_to(ROOT), "cada cenario precisa de id")
            continue
        scenario_id = scenario["id"]
        if scenario_id in coverage_scenario_ids:
            fail(coverage_path.relative_to(ROOT), f"cenario de teste duplicado: {scenario_id}")
        coverage_scenario_ids.add(scenario_id)
        status = scenario.get("status")
        if status not in valid_scenario_statuses:
            fail(coverage_path.relative_to(ROOT), f"status invalido no cenario {scenario_id}")
        if scenario.get("suite") not in suite_ids:
            fail(coverage_path.relative_to(ROOT), f"suite desconhecida no cenario {scenario_id}")
        requirement_ids = scenario.get("requirement_ids", [])
        if not isinstance(requirement_ids, list):
            fail(coverage_path.relative_to(ROOT), f"requirement_ids precisa ser lista em {scenario_id}")
            requirement_ids = []
        for requirement_id in requirement_ids:
            if requirement_id not in criterion_ids:
                fail(coverage_path.relative_to(ROOT), f"requisito desconhecido em {scenario_id}: {requirement_id}")
            covered_criteria.add(requirement_id)
        evidence_items = scenario.get("evidence", [])
        if not isinstance(evidence_items, list):
            fail(coverage_path.relative_to(ROOT), f"evidence precisa ser lista em {scenario_id}")
            evidence_items = []
        if status == "implemented" and not evidence_items:
            fail(coverage_path.relative_to(ROOT), f"cenario implementado precisa de evidencia: {scenario_id}")
        for evidence in evidence_items:
            if not isinstance(evidence, dict) or not isinstance(evidence.get("path"), str):
                fail(coverage_path.relative_to(ROOT), f"evidencia invalida em {scenario_id}")
                continue
            evidence_file = ROOT / evidence["path"]
            if not evidence_file.is_file():
                fail(coverage_path.relative_to(ROOT), f"arquivo de evidencia inexistente em {scenario_id}: {evidence['path']}")
                continue
            test_name = evidence.get("test_name")
            if status == "implemented" and not isinstance(test_name, str):
                fail(coverage_path.relative_to(ROOT), f"teste implementado precisa de test_name: {scenario_id}")
            elif isinstance(test_name, str):
                try:
                    evidence_text = evidence_file.read_text(encoding="utf-8")
                except OSError as exc:
                    fail(coverage_path.relative_to(ROOT), f"nao foi possivel ler evidencia de {scenario_id}: {exc}")
                else:
                    if test_name not in evidence_text:
                        fail(coverage_path.relative_to(ROOT), f"test_name nao encontrado em {evidence['path']}: {test_name}")
        if status == "manual-required" and not scenario.get("evidence_required"):
            fail(coverage_path.relative_to(ROOT), f"cenario manual precisa listar evidencia requerida: {scenario_id}")
        if status == "deferred" and not scenario.get("defer_reason"):
            fail(coverage_path.relative_to(ROOT), f"cenario adiado precisa explicar o motivo: {scenario_id}")
    missing_criteria = criterion_ids - covered_criteria
    if missing_criteria:
        fail(coverage_path.relative_to(ROOT), f"requisitos sem cenario de teste rastreado: {sorted(missing_criteria)}")

    required_manifest_links = {
        "decision_consistency": "harness/config/decisions.json",
        "model_gateway_contract": "harness/config/model-gateway.json",
        "requirement_traceability": "harness/traceability/requirements.json",
        "synthetic_data_policy": "harness/config/synthetic-data.json",
    }
    for section, manifest in required_manifest_links.items():
        if gates.get(section, {}).get("manifest") != manifest or gates.get(section, {}).get("enforced_by") != "harness.validate":
            fail(gates_path.relative_to(ROOT), f"{section} precisa estar ligado ao gate harness.validate")
    expected_component_manifests = {
        "decision_consistency": ["Backend/harness/config/decisions.json", "Frontend/harness/config/decisions.json"],
        "model_gateway_contract": "Backend/harness/config/model-gateway.json",
        "requirement_traceability": ["Backend/harness/traceability/requirements.json", "Frontend/harness/traceability/requirements.json"],
        "synthetic_data_policy": "Backend/harness/config/synthetic-data.json",
    }
    for section, expected in expected_component_manifests.items():
        field = "component_manifests" if isinstance(expected, list) else "backend_manifest"
        declared = gates.get(section, {}).get(field)
        if declared != expected:
            fail(gates_path.relative_to(ROOT), f"{section}.{field} precisa apontar aos arquivos dos repositorios individuais")
        paths = expected if isinstance(expected, list) else [expected]
        for relative in paths:
            if not (ROOT / relative).is_file():
                fail(gates_path.relative_to(ROOT), f"manifest individual inexistente: {relative}")
    ux = gates.get("ux_review", {})
    if ux.get("frontend_manifest") != "Frontend/harness/config/quality-gates.json":
        fail(gates_path.relative_to(ROOT), "revisao UX deve apontar ao gate versionado no repositorio Frontend")
    ux_checks = {"keyboard-navigation", "visible-focus", "loading-empty-error-and-retry-states", "desktop-and-mobile-layout", "chart-text-alternative", "contrast-and-readable-density"}
    if ux.get("id") != "frontend.ux-review" or ux.get("kind") != "manual-evidence" or not ux_checks.issubset(set(ux.get("must_verify", []))):
        fail(gates_path.relative_to(ROOT), "ux_review precisa exigir revisao visual/acessivel e seus criterios minimos")
    if not {"screenshots", "keyboard-walkthrough", "issues-or-none"}.issubset(set(ux.get("evidence", []))):
        fail(gates_path.relative_to(ROOT), "ux_review deve produzir evidencias verificaveis")
    backend_component_path = ROOT / "Backend/harness/config/harness.json"
    backend_component = load_json(backend_component_path) or {}
    backend_gateway = backend_component.get("model_gateway", {})
    gateway_topics = {"server-side-model-selection-and-visibility", "canonical-event-normalization", "structured-validation-before-persistence-or-rendering", "timeouts-and-cancellation", "safe-error-normalization", "credential-isolation", "request-correlation-without-private-payload-logs", "direct-manager-request-no-llm-preprocessing", "system-prompt-and-request-composition", "forty-message-same-conversation-context-window", "bounded-authorized-langchain-tool-calling", "structured-output-and-html-safety", "token-usage-and-tool-round-observability"}
    if backend_gateway.get("status_manifest") != "harness/config/model-gateway.json" or backend_gateway.get("contract_quality_gate") != "harness.validate" or backend_gateway.get("implementation_status_must_have_evidence") is not True or not gateway_topics.issubset(set(backend_gateway.get("required_review_topics", []))):
        fail(backend_component_path.relative_to(ROOT), "Harness do backend precisa exigir evidencias e revisao completa do Model Gateway")
    local_gateway_path = ROOT / "Backend/harness/config/model-gateway.json"
    local_gateway = load_json(local_gateway_path) or {}
    if local_gateway.get("provider_independent_contract") != "app/gateway.py" or local_gateway.get("response_block_contracts") != "app/contracts.py":
        fail(local_gateway_path.relative_to(ROOT), "manifest local deve usar caminhos relativos ao repositório Backend")
    for capability, record in local_gateway.get("capabilities", {}).items():
        if record.get("status") in {"scaffold", "implemented", "test-only", "policy-defined"} and not record.get("evidence"):
            fail(local_gateway_path.relative_to(ROOT), f"capability {capability} precisa de evidencia")
        for relative in record.get("evidence", []):
            if not (ROOT / "Backend" / relative).exists():
                fail(local_gateway_path.relative_to(ROOT), f"evidencia local inexistente para {capability}: {relative}")
    local_synthetic_path = ROOT / "Backend/harness/config/synthetic-data.json"
    local_synthetic = load_json(local_synthetic_path) or {}
    if local_synthetic.get("fixture_root") != "fixtures/synthetic" or not (ROOT / "Backend" / local_synthetic.get("fixture_root", "")).is_dir():
        fail(local_synthetic_path.relative_to(ROOT), "fixtures precisam estar no Backend/fixtures/synthetic do repositório")
    # Fixtures continuam sintéticas enquanto endpoint, autenticação e contrato da
    # API não forem entregues; o nome da integração não altera a regra de privacidade.
    if local_synthetic.get("company_data_source", {}).get("selected") != "API de dados" or local_synthetic.get("rules", {}).get("real_personal_or_company_data_allowed") is not False:
        fail(local_synthetic_path.relative_to(ROOT), "fixtures devem continuar sintéticas e registrar a API de dados como integração selecionada")
    workspace_synthetic = load_json(ROOT / "harness/config/synthetic-data.json") or {}
    if workspace_synthetic.get("fixture_root") != f"Backend/{local_synthetic.get('fixture_root', '')}":
        fail(local_synthetic_path.relative_to(ROOT), "política local deve corresponder ao caminho de fixtures do workspace")
    backend_workflow_path = ROOT / "Backend/harness/workflows/feature.json"
    backend_workflow = load_json(backend_workflow_path) or {}
    gateway_step = next((step for step in backend_workflow.get("steps", []) if step.get("id") == "gateway-implementation"), {})
    gateway_outputs = {"server-side-model-selection", "normalized-events-and-errors", "timeout-and-cancellation-behavior", "validated-iara-content", "credential-and-log-boundary", "gateway-status-and-evidence-updated"}
    if not gateway_outputs.issubset(set(gateway_step.get("outputs", []))):
        fail(backend_workflow_path.relative_to(ROOT), "workflow do backend precisa produzir evidencia dos aspectos do Model Gateway")
    frontend_source = ROOT / "Frontend/src"
    provider_patterns = [
        re.compile(r"(?i)from\s+['\"]openai['\"]|require\(['\"]openai['\"]\)"),
        re.compile(r"(?i)api\.openai\.com|OPENAI_API_KEY"),
    ]
    for source_file in frontend_source.rglob("*"):
        if source_file.is_file() and source_file.suffix.lower() in {".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"}:
            try:
                source_text = source_file.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError) as exc:
                fail(source_file.relative_to(ROOT), f"nao foi possivel inspecionar limite de provider: {exc}")
                continue
            if any(pattern.search(source_text) for pattern in provider_patterns):
                fail(source_file.relative_to(ROOT), "frontend nao pode importar SDK OpenAI nem acessar credencial/endpoint do provider")
    frontend_component_path = ROOT / "Frontend/harness/config/harness.json"
    frontend_component = load_json(frontend_component_path) or {}
    frontend_policy = frontend_component.get("test_policy", {})
    if frontend_policy.get("manual_review_gate") != ux.get("id") or not ux_checks.issubset(set(frontend_policy.get("visual_gates", []))):
        fail(frontend_component_path.relative_to(ROOT), "Harness do frontend precisa ligar gates visuais a revisao UX obrigatoria")
    if not {"desktop-and-mobile-screenshots", "keyboard-and-focus-walkthrough", "chart-text-alternative-check", "contrast-density-and-state-review", "issues-or-none"}.issubset(set(frontend_policy.get("manual_review_evidence", []))):
        fail(frontend_component_path.relative_to(ROOT), "Harness do frontend precisa exigir evidencias UX verificaveis")
    local_frontend_gates_path = ROOT / "Frontend/harness/config/quality-gates.json"
    local_frontend_gates = load_json(local_frontend_gates_path) or {}
    local_ux = local_frontend_gates.get("manual_review", {})
    if local_ux.get("id") != "frontend.ux-review" or not ux_checks.issubset(set(local_ux.get("must_verify", []))):
        fail(local_frontend_gates_path.relative_to(ROOT), "gate UX local precisa cobrir os criterios minimos de acessibilidade e visual")
    if not set(frontend_policy.get("manual_review_evidence", [])).issubset(set(local_ux.get("evidence", []))):
        fail(local_frontend_gates_path.relative_to(ROOT), "gate UX local precisa corresponder ao manifesto do componente")
    frontend_workflow_path = ROOT / "Frontend/harness/workflows/feature.json"
    frontend_workflow = load_json(frontend_workflow_path) or {}
    feature_ux_steps = {step.get("id"): step for step in frontend_workflow.get("steps", []) if isinstance(step, dict)}
    feature_ux_review = feature_ux_steps.get("review", {})
    if feature_ux_review.get("check") != "manual-ux-review" or feature_ux_review.get("required") is not True:
        fail(frontend_workflow_path.relative_to(ROOT), "workflow de feature do frontend precisa de revisao visual/acessivel obrigatoria")
    for workflow_name in ("bugfix.json", "release.json"):
        review_workflow_path = ROOT / "Frontend/harness/workflows" / workflow_name
        review_workflow = load_json(review_workflow_path) or {}
        manual_review = next((step for step in review_workflow.get("steps", []) if step.get("agent") == "frontend.code-reviewer"), {})
        if manual_review.get("check") is None:
            fail(review_workflow_path.relative_to(ROOT), "workflows de bugfix/release precisam declarar revisao UX quando aplicavel")
    workflow_path = ROOT / "harness/workflows/fullstack-feature.json"
    workflow = load_json(workflow_path) or {}
    ux_step = next((step for step in workflow.get("steps", []) if step.get("id") == "visual-accessibility-review"), {})
    required_ux_outputs = {"desktop-and-mobile-screenshots", "keyboard-and-focus-walkthrough", "chart-text-alternative-check", "contrast-density-and-state-review", "issues-or-none"}
    if ux_step.get("required") is not True or ux_step.get("check") != "manual-ux-review" or not required_ux_outputs.issubset(set(ux_step.get("outputs", []))):
        fail(workflow_path.relative_to(ROOT), "workflow full-stack precisa incluir evidencia obrigatoria de revisao visual/acessibilidade")
    if "Revisao visual e de acessibilidade foi registrada com evidencias" not in workflow.get("completion_criteria", []):
        fail(workflow_path.relative_to(ROOT), "conclusao full-stack precisa exigir registro da revisao visual/acessibilidade")

    synthetic_path = ROOT / "harness/config/synthetic-data.json"
    synthetic = load_json(synthetic_path) or {}
    if synthetic.get("schema_version") != 1:
        fail(synthetic_path.relative_to(ROOT), "schema_version precisa ser 1")
    fixture_root = ROOT / synthetic.get("fixture_root", "")
    if not fixture_root.is_dir():
        fail(synthetic_path.relative_to(ROOT), "diretorio de fixtures sinteticas ausente")
    rules = synthetic.get("rules", {})
    if rules.get("real_personal_or_company_data_allowed") is not False or rules.get("credentials_or_secrets_allowed") is not False or rules.get("external_data_fetch_during_default_checks") is not False:
        fail(synthetic_path.relative_to(ROOT), "politica deve proibir dados reais, credenciais e fetch externo")
    metadata = synthetic.get("required_metadata", {})
    try:
        field_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in synthetic.get("rules", {}).get("prohibited_field_name_patterns", [])]
    except re.error as exc:
        field_patterns = []
        fail(synthetic_path.relative_to(ROOT), f"expressao invalida para nome de campo proibido: {exc}")
    for fixture in sorted(fixture_root.rglob("*.json")):
        try:
            payload = json.loads(fixture.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            fail(fixture.relative_to(ROOT), f"fixture JSON invalida: {exc}")
            continue
        no_secrets(fixture, payload)
        marker = payload.get(metadata.get("path", "_metadata"), {}) if isinstance(payload, dict) else {}
        if not isinstance(marker, dict) or marker.get(metadata.get("classification_key", "classification")) != metadata.get("classification_value", "synthetic") or not marker.get(metadata.get("purpose_key", "purpose")):
            fail(fixture.relative_to(ROOT), "fixture precisa rotular metadados synthetic e purpose")
        def inspect_keys(value: Any) -> None:
            if isinstance(value, dict):
                for key, child in value.items():
                    if key != metadata.get("path") and any(pattern.search(str(key)) for pattern in field_patterns):
                        fail(fixture.relative_to(ROOT), f"nome de campo proibido: {key}")
                    inspect_keys(child)
            elif isinstance(value, list):
                for child in value:
                    inspect_keys(child)
        inspect_keys(payload)


def validate_component(name: str, base: Path, config_path: Path) -> dict[str, Any] | None:
    config = load_json(config_path)
    if config is None:
        return None
    if config.get("component") != name:
        fail(config_path.relative_to(ROOT), f"component esperado: {name}")
    if config.get("schema_version") != 1:
        fail(config_path.relative_to(ROOT), "schema_version do componente precisa ser 1")
    component_root = (config_path.parent / config.get("component_root", "")).resolve()
    if component_root != base.resolve():
        fail(
            config_path.relative_to(ROOT),
            f"component_root aponta para {component_root}, esperado {base.resolve()}",
        )
    if not base.is_dir():
        fail(base.relative_to(ROOT), "diretorio do componente ausente")
    project_root = (config_path.parent / config.get("project_root", "")).resolve()
    if project_root != ROOT.resolve():
        fail(
            config_path.relative_to(ROOT),
            f"project_root aponta para {project_root}, esperado {ROOT.resolve()}",
        )

    agents = json_entities(base, "agents")
    roles = json_entities(base, "roles")
    orchestrators = json_entities(base, "orchestrators")
    workflows = json_entities(base, "workflows")
    prompts = markdown_entities(base, "prompts")
    skills = markdown_entities(base, "skills")
    rules = markdown_entities(base, "rules")
    for path in rules.values():
        try:
            frontmatter = path.read_text(encoding="utf-8").split("---", 2)[1]
        except (OSError, IndexError):
            fail(path.relative_to(ROOT), "frontmatter de regra indisponivel")
            continue
        scope_match = re.search(r"(?m)^scope:\s*([A-Za-z0-9_.-]+)\s*$", frontmatter)
        severity_match = re.search(r"(?m)^severity:\s*(blocking|required|advisory)\s*$", frontmatter)
        if not scope_match or scope_match.group(1) not in {"shared", name}:
            fail(path.relative_to(ROOT), "scope deve ser shared ou corresponder ao componente")
        if not severity_match:
            fail(path.relative_to(ROOT), "severity deve ser blocking, required ou advisory")
    tool_catalog_path = base / "harness" / "tools" / "catalog.json"
    tool_catalog = load_json(tool_catalog_path) or {}
    if tool_catalog.get("schema_version") not in {1, 2}:
        fail(tool_catalog_path.relative_to(ROOT), "schema_version de tools precisa ser 1 ou 2")
    if tool_catalog.get("enforcement", {}).get("status") != "declarative":
        fail(
            tool_catalog_path.relative_to(ROOT),
            "catalogo deve declarar que a politica ainda e declarativa",
        )
    if tool_catalog.get("network", {}).get("default") != "disabled":
        fail(
            tool_catalog_path.relative_to(ROOT),
            "rede das ferramentas do componente deve ser desabilitada por padrao",
        )
    if tool_catalog.get("network", {}).get("external_provider_calls") not in {"deny", "denied"}:
        fail(
            tool_catalog_path.relative_to(ROOT),
            "ferramentas de componente nao podem chamar providers externos diretamente",
        )
    tools: dict[str, dict[str, Any]] = {}
    catalog_tools = tool_catalog.get("tools", [])
    if not isinstance(catalog_tools, list) or not catalog_tools:
        fail(tool_catalog_path.relative_to(ROOT), "tools precisa ser uma lista nao vazia")
        catalog_tools = []
    known_kinds = {
        "filesystem-read",
        "filesystem-write",
        "filesystem-list",
        "filesystem-search",
        "command",
        "browser",
        "context-retrieval",
    }
    scopes = tool_catalog.get("scopes", {})
    for tool in catalog_tools:
        if not isinstance(tool, dict) or not isinstance(tool.get("id"), str):
            fail(tool_catalog_path.relative_to(ROOT), "cada ferramenta precisa de id")
            continue
        tool_id = tool["id"]
        if tool_id in tools:
            fail(tool_catalog_path.relative_to(ROOT), f"id de ferramenta duplicado: {tool_id}")
        tools[tool_id] = tool
        if tool.get("kind") not in known_kinds:
            fail(
                tool_catalog_path.relative_to(ROOT),
                f"tipo de ferramenta desconhecido: {tool.get('kind')}",
            )
        if not isinstance(tool.get("purpose"), str) or not tool["purpose"].strip():
            fail(tool_catalog_path.relative_to(ROOT), f"purpose ausente para {tool_id}")
        if not isinstance(tool.get("allowed_roles"), list) or not tool["allowed_roles"]:
            fail(
                tool_catalog_path.relative_to(ROOT),
                f"allowed_roles precisa ser lista nao vazia em {tool_id}",
            )
        else:
            check_refs(tool_catalog_path, tool["allowed_roles"], set(roles), f"roles de {tool_id}")
        kind = tool.get("kind")
        if (
            isinstance(kind, str)
            and kind.startswith("filesystem-")
            and tool.get("scope") not in scopes
        ):
            fail(
                tool_catalog_path.relative_to(ROOT),
                f"scope de filesystem nao declarado para {tool_id}",
            )
        if tool.get("kind") == "command" and tool.get("command_id") not in config.get(
            "commands", {}
        ):
            fail(
                tool_catalog_path.relative_to(ROOT),
                f"command_id nao declarado em commands: {tool.get('command_id')}",
            )
        if tool.get("kind") == "command":
            target = config.get("commands", {}).get(tool.get("command_id"))
            if target not in {"setup", "harness", "backend", "frontend", "e2e", "all"}:
                fail(
                    tool_catalog_path.relative_to(ROOT),
                    f"target de comando desconhecido para {tool.get('command_id')}: {target}",
                )
        if tool.get("kind") == "context-retrieval":
            if tool.get("scope") not in scopes:
                fail(
                    tool_catalog_path.relative_to(ROOT),
                    f"scope do retrieval nao declarado para {tool_id}",
                )
            if tool.get("retrieval_scope") != name:
                fail(
                    tool_catalog_path.relative_to(ROOT),
                    f"retrieval de {tool_id} precisa ficar restrito ao escopo {name}",
                )
            if tool.get("handler") != "harness.context.retrieve_context":
                fail(
                    tool_catalog_path.relative_to(ROOT),
                    f"handler compartilhado incorreto em {tool_id}",
                )
            if (
                tool.get("retrieved_content_trust") != "untrusted-data"
                or tool.get("retrieval_does_not_grant_permissions") is not True
            ):
                fail(
                    tool_catalog_path.relative_to(ROOT),
                    f"trust e permissoes nao definidos corretamente em {tool_id}",
                )
        if tool.get("kind") == "browser" and (
            tool.get("scope") != "localhost-only" or tool.get("navigation") != "localhost-only"
        ):
            fail(
                tool_catalog_path.relative_to(ROOT),
                f"browser precisa estar limitado a localhost: {tool_id}",
            )

    for category, available in (
        ("agents", agents),
        ("roles", roles),
        ("orchestrators", orchestrators),
        ("workflows", workflows),
    ):
        check_refs(config_path, config.get(category), set(available), category)
    check_refs(config_path, config.get("prompts"), set(prompts), "prompts")
    check_refs(config_path, config.get("skills"), set(skills), "skills")
    declared_rules = config.get("rules")
    check_refs(config_path, declared_rules, set(rules), "rules")
    if isinstance(declared_rules, list):
        for rule_id in set(rules) - set(declared_rules):
            fail(rules[rule_id].relative_to(ROOT), "regra nao registrada em config/harness.json")
    check_refs(config_path, config.get("tools"), set(tools), "tools")
    context_tool_ids = {
        tool_id for tool_id, tool in tools.items() if tool.get("kind") == "context-retrieval"
    }

    for path, agent in agents.values():
        if agent.get("role") not in roles:
            fail(path.relative_to(ROOT), f"role inexistente: {agent.get('role')}")
        if agent.get("prompt") not in prompts:
            fail(path.relative_to(ROOT), f"prompt inexistente: {agent.get('prompt')}")
        check_refs(path, agent.get("skills", []), set(skills), "skills")
        check_refs(path, agent.get("tools", []), set(tools), "tools")
        check_refs(
            path,
            agent.get("tools", []),
            set(config.get("tools", [])),
            "tools declaradas no harness de componente",
        )
        for tool_id in context_tool_ids:
            if tool_id not in agent.get("tools", []):
                fail(
                    path.relative_to(ROOT),
                    f"agent sem ferramenta de retrieval do escopo {name}: {tool_id}",
                )
        for tool_id in agent.get("tools", []):
            allowed_roles = tools.get(tool_id, {}).get("allowed_roles", [])
            if allowed_roles and agent.get("role") not in allowed_roles:
                fail(
                    path.relative_to(ROOT),
                    f"role {agent.get('role')} nao autorizado para tool {tool_id}",
                )
        check_refs(path, agent.get("workflows", []), set(workflows), "workflows")

    for path, orchestrator in orchestrators.values():
        workflow = orchestrator.get("workflow")
        if workflow not in workflows:
            fail(path.relative_to(ROOT), f"workflow inexistente: {workflow}")
            continue
        _, workflow_data = workflows[workflow]
        declared_steps = [
            step.get("id") for step in workflow_data.get("steps", []) if isinstance(step, dict)
        ]
        orchestration_steps = orchestrator.get("steps")
        if orchestration_steps != declared_steps:
            fail(
                path.relative_to(ROOT),
                f"steps devem corresponder, na mesma ordem, ao workflow {workflow}: {declared_steps}",
            )
        validate_orchestrator_loop_ref(path, orchestrator)
        guidance = orchestrator.get("step_guidance", {})
        if guidance and set(guidance) != set(declared_steps):
            fail(
                path.relative_to(ROOT),
                "step_guidance deve definir exatamente todos os passos do workflow",
            )
        for step_id, details in guidance.items():
            if (
                not isinstance(details, dict)
                or not details.get("objective")
                or not details.get("deliverables")
            ):
                fail(
                    path.relative_to(ROOT),
                    f"step_guidance.{step_id} precisa de objective e deliverables",
                )
            if isinstance(details, dict) and "tool" in details and details["tool"] not in tools:
                fail(
                    path.relative_to(ROOT),
                    f"tool inexistente em step_guidance.{step_id}: {details['tool']}",
                )
        check_refs(path, orchestrator.get("quality_gates", []), set(tools), "quality_gates")
        if orchestrator.get("execution") not in {"sequential"}:
            fail(path.relative_to(ROOT), "execution deve ser sequential neste harness")
        if orchestrator.get("delegation") != "disabled":
            fail(path.relative_to(ROOT), "delegation deve permanecer disabled")
        allowed_policies = {
            "fix-before-next-step",
            "fix-before-handoff",
            "stop-at-failed-gate-fix-and-rerun",
        }
        if orchestrator.get("failure_policy") not in allowed_policies:
            fail(
                path.relative_to(ROOT),
                f"failure_policy precisa parar para corrigir falhas: {sorted(allowed_policies)}",
            )

    for path, workflow in workflows.values():
        steps = workflow.get("steps")
        if not isinstance(steps, list) or not steps:
            fail(path.relative_to(ROOT), "workflow precisa ter steps nao vazios")
            continue
        if workflow.get("execution") != "sequential":
            fail(path.relative_to(ROOT), "execution do workflow precisa ser sequential")
        if workflow.get("failure_policy") != "stop-fix-and-rerun-impacted-steps":
            fail(
                path.relative_to(ROOT),
                "failure_policy precisa parar, corrigir e repetir passos impactados",
            )
        if workflow.get("id") == "iara.fullstack-feature" and workflow.get("completion_policy_ref") != "iara.task-completion":
            fail(path.relative_to(ROOT), "workflow full-stack precisa referenciar iara.task-completion")
        if (
            workflow.get("condition_semantics")
            != "execute-when-when-matches-required-means-blocking-when-executed"
        ):
            fail(
                path.relative_to(ROOT),
                "condition_semantics precisa definir quando condicoes sao executadas e bloqueantes",
            )
        for field in ("inputs", "outputs", "completion_criteria"):
            if not isinstance(workflow.get(field), list) or not workflow[field]:
                fail(path.relative_to(ROOT), f"workflow precisa declarar {field} nao vazio")
        step_ids: set[str] = set()
        workflow_context_tool = False
        for step in steps:
            if not isinstance(step, dict) or not isinstance(step.get("id"), str):
                fail(path.relative_to(ROOT), "cada step precisa de id")
                continue
            if step["id"] in step_ids:
                fail(path.relative_to(ROOT), f"step duplicado: {step['id']}")
            step_ids.add(step["id"])
            if not isinstance(step.get("required"), bool):
                fail(
                    path.relative_to(ROOT), f"step {step['id']} precisa declarar required booleano"
                )
            if "when" in step and (not isinstance(step["when"], str) or not step["when"].strip()):
                fail(path.relative_to(ROOT), f"condicao when invalida no step {step['id']}")
            if "agent" in step and "prompt" not in step and "component_workflow" not in step:
                fail(
                    path.relative_to(ROOT),
                    f"step {step['id']} com agent precisa de prompt ou component_workflow",
                )
            if "prompt" in step and "agent" not in step:
                fail(path.relative_to(ROOT), f"step {step['id']} com prompt precisa declarar agent")
            if not any(field in step for field in ("agent", "tool", "component_workflow", "check")):
                fail(
                    path.relative_to(ROOT),
                    f"step {step['id']} precisa declarar agent, tool, component_workflow ou check",
                )
            for field, available in (("agent", agents), ("prompt", prompts)):
                if field in step and step[field] not in available:
                    fail(
                        path.relative_to(ROOT),
                        f"{field} inexistente no step {step['id']}: {step[field]}",
                    )
            if "tool" in step and step["tool"] not in tools:
                fail(
                    path.relative_to(ROOT), f"tool inexistente no step {step['id']}: {step['tool']}"
                )
            if step.get("tool") in context_tool_ids:
                workflow_context_tool = True
            if "component_workflow" in step and step["component_workflow"] not in workflows:
                fail(
                    path.relative_to(ROOT),
                    f"component_workflow inexistente: {step['component_workflow']}",
                )
        for group in workflow.get("at_least_one_from", []):
            if (
                not isinstance(group, list)
                or not group
                or any(step_id not in step_ids for step_id in group)
            ):
                fail(path.relative_to(ROOT), f"at_least_one_from contem step inexistente: {group}")
        if context_tool_ids and not workflow_context_tool:
            fail(
                path.relative_to(ROOT),
                f"workflow {workflow.get('id')} precisa ter passo de retrieval do componente",
            )

    for folder in (
        "agents",
        "config",
        "orchestrators",
        "prompts",
        "roles",
        "skills",
        "tools",
        "workflows",
    ):
        directory = base / "harness" / folder
        if not directory.is_dir() or not any(directory.iterdir()):
            fail(directory.relative_to(ROOT), "categoria do harness ausente ou vazia")
    return config


def main() -> int:
    validate_product_harness()
    project_path = ROOT / "harness" / "config" / "project.json"
    project = load_json(project_path)
    if project is None or project.get("schema_version") != 1:
        fail(project_path.relative_to(ROOT), "schema_version precisa ser 1")
        project = project or {}
    gates_path = ROOT / "harness" / "config" / "quality-gates.json"
    gates = load_json(gates_path) or {}
    if gates.get("schema_version") != 1:
        fail(gates_path.relative_to(ROOT), "schema_version precisa ser 1")
    gate_items = gates.get("gates", [])
    if not isinstance(gate_items, list) or not gate_items:
        fail(gates_path.relative_to(ROOT), "gates precisa ser uma lista nao vazia")
        gate_items = []
    gate_ids: set[str] = set()
    gates_by_id: dict[str, dict[str, Any]] = {}
    targets = {
        "setup",
        "harness",
        "context",
        "backend",
        "frontend",
        "e2e",
        "docker-up",
        "docker-e2e",
        "docker-down",
        "all",
    }
    runner_path = ROOT / "scripts" / "harness.ps1"
    try:
        runner_text = runner_path.read_text(encoding="utf-8")
    except OSError as exc:
        runner_text = ""
        fail(runner_path.relative_to(ROOT), f"runner ausente ou ilegivel: {exc}")
    target_match = re.search(r"ValidateSet\(([^)]*)\)", runner_text)
    runner_targets = set(re.findall(r"'([^']+)'", target_match.group(1))) if target_match else set()
    if runner_targets != targets:
        fail(
            runner_path.relative_to(ROOT),
            f"ValidateSet deve corresponder aos targets conhecidos: {sorted(targets)}",
        )
    for gate in gate_items:
        if not isinstance(gate, dict) or not isinstance(gate.get("id"), str):
            fail(gates_path.relative_to(ROOT), "cada quality gate precisa de id")
            continue
        gate_id = gate["id"]
        if gate_id in gate_ids:
            fail(gates_path.relative_to(ROOT), f"id de quality gate duplicado: {gate_id}")
        gate_ids.add(gate_id)
        gates_by_id[gate_id] = gate
        if gate.get("runner") != "scripts/harness.ps1":
            fail(
                gates_path.relative_to(ROOT),
                f"runner de {gate_id} nao aponta para scripts/harness.ps1",
            )
        if gate.get("target") not in runner_targets:
            fail(
                gates_path.relative_to(ROOT),
                f"target de {gate_id} nao existe no runner: {gate.get('target')}",
            )
        if (
            not isinstance(gate.get("required"), bool)
            or not isinstance(gate.get("purpose"), str)
            or not gate["purpose"].strip()
        ):
            fail(gates_path.relative_to(ROOT), f"{gate_id} precisa declarar required e purpose")
    check_refs(project_path, project.get("quality_gates"), gate_ids, "quality_gates")
    if set(project.get("quality_gates", [])) != {
        gate_id for gate_id, gate in gates_by_id.items() if gate.get("required") is True
    }:
        fail(
            project_path.relative_to(ROOT),
            "quality_gates do projeto deve listar exatamente todos os gates obrigatorios",
        )
    shared_agents = json_entities(ROOT, "agents")
    shared_roles = json_entities(ROOT, "roles")
    shared_orchestrators = json_entities(ROOT, "orchestrators")
    shared_workflows = json_entities(ROOT, "workflows")
    shared_prompts = markdown_entities(ROOT, "prompts")
    shared_skills = markdown_entities(ROOT, "skills")
    shared_tools_path = ROOT / "harness" / "tools" / "catalog.json"
    shared_tools_catalog = load_json(shared_tools_path) or {}
    if shared_tools_catalog.get("schema_version") != 1:
        fail(
            shared_tools_path.relative_to(ROOT),
            "schema_version do catalogo compartilhado precisa ser 1",
        )
    if shared_tools_catalog.get("enforcement", {}).get("status") != "declarative":
        fail(
            shared_tools_path.relative_to(ROOT),
            "catalogo compartilhado deve declarar enforcement declarativo",
        )
    if shared_tools_catalog.get("execution_policy", {}).get("registered_commands_only") is not True:
        fail(
            shared_tools_path.relative_to(ROOT),
            "execucao compartilhada deve aceitar apenas comandos registrados",
        )
    shared_tool_items = shared_tools_catalog.get("tools", [])
    if not isinstance(shared_tool_items, list) or not shared_tool_items:
        fail(shared_tools_path.relative_to(ROOT), "tools precisa ser uma lista nao vazia")
        shared_tool_items = []
    shared_tools = {
        tool.get("id"): tool
        for tool in shared_tool_items
        if isinstance(tool, dict) and isinstance(tool.get("id"), str)
    }
    shared_tool_ids = set(shared_tools)
    if len(shared_tools) != len(shared_tool_items):
        fail(
            shared_tools_path.relative_to(ROOT), "tools precisa ser lista de objetos com ids unicos"
        )
    for tool in shared_tools.values():
        if not isinstance(tool.get("purpose"), str) or not tool["purpose"].strip():
            fail(
                shared_tools_path.relative_to(ROOT),
                f"purpose ausente para ferramenta {tool.get('id')}",
            )
        if not isinstance(tool.get("allowed_roles"), list) or not tool["allowed_roles"]:
            fail(
                shared_tools_path.relative_to(ROOT),
                f"allowed_roles precisa ser lista nao vazia em {tool.get('id')}",
            )
        if tool.get("kind") not in {"filesystem-read", "command", "context-retrieval"}:
            fail(
                shared_tools_path.relative_to(ROOT),
                f"tipo de ferramenta compartilhada nao permitido: {tool.get('kind')}",
            )
        if tool.get("kind") == "filesystem-read" and tool.get(
            "scope"
        ) not in shared_tools_catalog.get("scopes", {}):
            fail(
                shared_tools_path.relative_to(ROOT),
                f"scope de ferramenta inexistente: {tool.get('scope')}",
            )
        if tool.get("kind") == "context-retrieval":
            if tool.get("scope") not in shared_tools_catalog.get("scopes", {}):
                fail(
                    shared_tools_path.relative_to(ROOT),
                    f"scope de retrieval inexistente: {tool.get('scope')}",
                )
            if (
                tool.get("handler") != "harness.context.retrieve_context"
                or not (ROOT / "harness" / "context" / "retrieval.py").is_file()
            ):
                fail(
                    shared_tools_path.relative_to(ROOT),
                    "handler de retrieval nao aponta para implementacao existente",
                )
            if (
                tool.get("retrieved_content_trust") != "untrusted-data"
                or tool.get("retrieval_does_not_grant_permissions") is not True
            ):
                fail(
                    shared_tools_path.relative_to(ROOT),
                    "retrieval deve marcar fontes como dados nao confiaveis e nao ampliar permissoes",
                )
            returned_fields = set(tool.get("returns", []))
            if not {"related_context", "related_context_links"}.issubset(returned_fields):
                fail(
                    shared_tools_path.relative_to(ROOT),
                    "retrieval compartilhado precisa expor proveniencia do contexto relacionado",
                )
        check_refs(
            shared_tools_path,
            tool.get("allowed_roles", []),
            set(shared_roles),
            f"roles de {tool.get('id')}",
        )
        if tool.get("kind") == "command" and tool.get("command_id") not in gate_ids:
            fail(
                shared_tools_path.relative_to(ROOT),
                f"command_id nao declarado nos quality gates: {tool.get('command_id')}",
            )
        if tool.get("kind") == "command":
            gate = gates_by_id.get(tool.get("command_id"), {})
            if tool.get("id") != tool.get("command_id"):
                fail(
                    shared_tools_path.relative_to(ROOT),
                    f"id e command_id precisam coincidir para ferramenta {tool.get('id')}",
                )
            if tool.get("network") == "loopback-only" and gate.get("target") != "e2e":
                fail(
                    shared_tools_path.relative_to(ROOT),
                    f"loopback so pode ser liberado para gate e2e: {tool.get('id')}",
                )
            if tool.get("network") == "disabled" and gate.get("target") == "e2e":
                fail(
                    shared_tools_path.relative_to(ROOT),
                    f"gate e2e requer loopback explicito: {tool.get('id')}",
                )
    check_refs(
        project_path,
        [gate for gate in project.get("quality_gates", [])],
        shared_tool_ids,
        "tools dos quality gates",
    )
    network_policy = shared_tools_catalog.get("network", {})
    if network_policy.get("harness_tools", {}).get("default") != "disabled":
        fail(
            shared_tools_path.relative_to(ROOT),
            "rede de ferramentas do Harness deve permanecer desabilitada por padrao",
        )
    if network_policy.get("harness_tools", {}).get("external_provider_calls") != "denied":
        fail(
            shared_tools_path.relative_to(ROOT),
            "ferramentas de agentes nao podem chamar providers diretamente",
        )
    if (
        network_policy.get("product_runtime", {}).get("provider_calls")
        != "backend-model-gateway-only"
    ):
        fail(
            shared_tools_path.relative_to(ROOT),
            "chamadas do produto devem passar exclusivamente pelo Model Gateway do backend",
        )
    if (
        network_policy.get("product_runtime", {}).get("local_credential_source")
        != "Backend/.env:IARA_API_KEY"
    ):
        fail(
            shared_tools_path.relative_to(ROOT),
            "fonte local da credencial da Iara precisa ser Backend/.env",
        )
    component_configs: dict[str, dict[str, Any]] = {}

    for component in ("backend", "frontend"):
        info = project.get("implementation", {}).get(component, {})
        base = ROOT / info.get("path", "")
        config_path = ROOT / info.get("harness", "")
        component_configs[component] = validate_component(component, base, config_path) or {}

    gateway = project.get("model_gateway", {})
    backend_gateway = component_configs.get("backend", {}).get("model_gateway", {})
    frontend_boundary = component_configs.get("frontend", {}).get("ai_boundary", {})
    shared_contracts = set(project.get("execution", {}).get("shared_contracts", []))
    retrieval = project.get("context_retrieval", {})
    if not isinstance(retrieval, dict):
        fail(project_path.relative_to(ROOT), "context_retrieval precisa ser um objeto")
        retrieval = {}
    default_budget = retrieval.get("default_context_tokens")
    maximum_budget = retrieval.get("max_context_tokens")
    if (
        not isinstance(default_budget, int)
        or not isinstance(maximum_budget, int)
        or not (1 <= default_budget <= maximum_budget)
    ):
        fail(
            project_path.relative_to(ROOT),
            "context_retrieval precisa definir budgets inteiros positivos e ordenados",
        )
    related_link_limit = retrieval.get("max_related_context_links")
    if (
        not isinstance(related_link_limit, int)
        or isinstance(related_link_limit, bool)
        or not (0 <= related_link_limit <= 10)
    ):
        fail(
            project_path.relative_to(ROOT),
            "max_related_context_links deve ser inteiro entre 0 e 10",
        )
    scope_config = retrieval.get("scopes", {})
    if not isinstance(scope_config, dict) or not scope_config:
        fail(project_path.relative_to(ROOT), "context_retrieval.scopes precisa declarar escopos")
        scope_config = {}
    for scope_name, roots in scope_config.items():
        if not isinstance(roots, list) or not roots:
            fail(
                project_path.relative_to(ROOT),
                f"escopo context_retrieval.{scope_name} precisa ter raizes",
            )
            continue
        for relative in roots:
            if not isinstance(relative, str) or not relative:
                fail(project_path.relative_to(ROOT), f"raiz invalida no escopo {scope_name}")
                continue
            resolved = (ROOT / relative).resolve()
            if ROOT.resolve() not in resolved.parents and resolved != ROOT.resolve():
                fail(
                    project_path.relative_to(ROOT),
                    f"raiz de retrieval escapa do workspace: {relative}",
                )
            if not resolved.exists():
                fail(project_path.relative_to(ROOT), f"raiz de retrieval inexistente: {relative}")
    route_keywords = retrieval.get("route_keywords", {})
    if not isinstance(route_keywords, dict) or any(
        name not in scope_config for name in route_keywords
    ):
        fail(project_path.relative_to(ROOT), "route_keywords deve mapear para escopos declarados")
    if not isinstance(retrieval.get("allowed_extensions"), list) or not retrieval.get(
        "allowed_extensions"
    ):
        fail(project_path.relative_to(ROOT), "allowed_extensions precisa ser uma lista nao vazia")
    deny_globs = retrieval.get("deny_globs", [])
    if not isinstance(deny_globs, list) or not any(
        isinstance(pattern, str) and ".env" in pattern for pattern in deny_globs
    ):
        fail(
            project_path.relative_to(ROOT), "deny_globs do retrieval precisa excluir arquivos .env"
        )
    retrieval_tool = shared_tools.get("context.retrieve", {})
    declared_retrieval_budget = (
        retrieval_tool.get("input_schema", {})
        .get("properties", {})
        .get("context_budget_tokens", {})
        .get("maximum")
    )
    if declared_retrieval_budget != maximum_budget:
        fail(
            shared_tools_path.relative_to(ROOT),
            "budget maximo da ferramenta deve corresponder a context_retrieval.max_context_tokens",
        )
    if retrieval_tool.get("input_schema", {}).get("properties", {}).get("query", {}).get(
        "maxLength"
    ) != retrieval.get("max_query_chars"):
        fail(
            shared_tools_path.relative_to(ROOT),
            "limite da consulta deve corresponder ao schema da ferramenta de retrieval",
        )
    for component in ("backend", "frontend"):
        component_catalog_path = (
            ROOT
            / project.get("implementation", {}).get(component, {}).get("path", "")
            / "harness"
            / "tools"
            / "catalog.json"
        )
        component_catalog = load_json(component_catalog_path) or {}
        local_id = f"{component}.context.retrieve"
        local_tool = next(
            (
                tool
                for tool in component_catalog.get("tools", [])
                if isinstance(tool, dict) and tool.get("id") == local_id
            ),
            {},
        )
        properties = local_tool.get("input_schema", {}).get("properties", {})
        if (
            local_tool.get("retrieval_scope") != component
            or properties.get("scope", {}).get("const") != component
        ):
            fail(
                component_catalog_path.relative_to(ROOT),
                f"retrieval local precisa permanecer restrito ao escopo {component}",
            )
        if properties.get("context_budget_tokens", {}).get("maximum") != maximum_budget:
            fail(
                component_catalog_path.relative_to(ROOT),
                f"budget local precisa corresponder ao limite compartilhado de {maximum_budget}",
            )
        if properties.get("query", {}).get("maxLength") != retrieval.get("max_query_chars"):
            fail(
                component_catalog_path.relative_to(ROOT),
                "limite local da consulta diverge do config compartilhado",
            )
        if not {"related_context", "related_context_links"}.issubset(
            set(local_tool.get("returns", []))
        ):
            fail(
                component_catalog_path.relative_to(ROOT),
                "retrieval local precisa expor proveniencia do contexto relacionado",
            )
    for key in (
        "provider_credential_env",
        "local_env_file",
        "model_alias_env",
        "provider_model_id_env",
        "provider_base_url_env",
    ):
        backend_key = {
            "provider_credential_env": "credential_env",
            "local_env_file": "local_env_file",
            "model_alias_env": "default_model_env",
            "provider_model_id_env": "provider_model_id_env",
            "provider_base_url_env": "base_url_env",
        }[key]
        if gateway.get(key) != backend_gateway.get(backend_key):
            fail(
                project_path.relative_to(ROOT),
                f"model_gateway.{key} precisa corresponder ao contrato do backend",
            )
    if gateway.get("initial_provider") != backend_gateway.get("initial_provider"):
        fail(
            project_path.relative_to(ROOT),
            "provider inicial precisa corresponder ao Model Gateway do backend",
        )
    for block in gateway.get("structured_output_blocks", []):
        if block not in shared_contracts:
            fail(
                project_path.relative_to(ROOT),
                f"bloco de saida estruturada nao declarado em shared_contracts: {block}",
            )
    if gateway.get("streaming_events") != backend_gateway.get("canonical_stream_events"):
        fail(
            project_path.relative_to(ROOT),
            "eventos de streaming do contrato compartilhado e backend precisam coincidir e manter a ordem",
        )
    if any(event not in shared_contracts for event in gateway.get("streaming_events", [])):
        fail(
            project_path.relative_to(ROOT),
            "todos os eventos de streaming precisam estar declarados em shared_contracts",
        )
    if (
        gateway.get("invocation_boundary") != "backend-only"
        or frontend_boundary.get("provider_access") != "backend-model-gateway-only"
    ):
        fail(
            project_path.relative_to(ROOT),
            "chamadas ao provider devem permanecer no backend/Model Gateway",
        )
    if frontend_boundary.get("provider_credentials_in_browser") is not False:
        fail(
            project_path.relative_to(ROOT),
            "credenciais de provider nao podem estar disponiveis no browser",
        )
    if (
        frontend_boundary.get("provider_model_id_exposed") is not False
        or frontend_boundary.get("model_visibility") != "hidden-from-gestor"
        or frontend_boundary.get("model_selection_ui") is not False
        or frontend_boundary.get("persist_model_metadata_backend_only") is not True
    ):
        fail(
            project_path.relative_to(ROOT),
            "provider/modelo devem ficar ocultos da UI; metadados de modelo só podem persistir internamente no backend",
        )
    demo = gateway.get("demonstration", {})
    backend_data_source = component_configs.get("backend", {}).get("company_data_source", {})
    # A resposta da API de dados é opaca: o gate confirma passthrough do conteúdo,
    # mantendo autorização e isolamento fora de qualquer normalização do payload.
    if (
        backend_data_source.get("source") != "API de dados"
        or backend_data_source.get("invocation_boundary") != "backend-only"
        or backend_data_source.get("direct_database_access") is not False
        or backend_data_source.get("response_policy")
        != "byte-for-byte-passthrough-including-all-html-and-chart-types"
    ):
        fail(project_path.relative_to(ROOT), "Backend deve acessar a API de dados e preservar o payload original sem alteração")
    if demo.get("required_for_product_acceptance") is not True or demo.get("provider") != "Iara":
        fail(
            project_path.relative_to(ROOT),
            "aceite do produto requer demonstracao opt-in com o provider Iara",
        )
    if (
        demo.get("model_alias_source") != gateway.get("model_alias_env")
        or demo.get("provider_model_id_source")
        != gateway.get("provider_model_id_source")
        or demo.get("credential_env") != gateway.get("provider_credential_env")
        or demo.get("base_url_env") != gateway.get("provider_base_url_env")
    ):
        fail(
            project_path.relative_to(ROOT),
            "demonstracao deve usar modelo e credencial configurados no backend",
        )
    if demo.get("data") != "synthetic-fixtures-default; live-grafana-mcp-requires-explicit-authorization":
        fail(project_path.relative_to(ROOT), "demonstracao deve usar fixtures sintéticas ou acesso explicitamente autorizado ao Grafana MCP")
    security = gates.get("security", {})
    if (
        security.get("provider_calls_in_default_suite") is not False
        or security.get("default_provider_adapter") != "fake"
    ):
        fail(
            gates_path.relative_to(ROOT),
            "suite padrao deve usar provider fake sem chamadas externas",
        )
    if security.get("validate_structured_response_before_persist_or_render") is not True:
        fail(
            gates_path.relative_to(ROOT),
            "respostas da LLM precisam ser validadas antes de persistir ou renderizar",
        )
    acceptance_checks = gates.get("acceptance_checks", [])
    if not isinstance(acceptance_checks, list) or not acceptance_checks:
        fail(
            gates_path.relative_to(ROOT),
            "acceptance_checks precisa declarar demonstracao real opt-in",
        )
        acceptance_checks = []
    acceptance_ids: set[str] = set()
    for check in acceptance_checks:
        if not isinstance(check, dict) or not isinstance(check.get("id"), str):
            fail(gates_path.relative_to(ROOT), "cada acceptance_check precisa ter id")
            continue
        if check["id"] in acceptance_ids:
            fail(gates_path.relative_to(ROOT), f"acceptance_check duplicado: {check['id']}")
        acceptance_ids.add(check["id"])
        if (
            check.get("kind") != "manual-opt-in"
            or check.get("required_for") != "product-acceptance"
        ):
            fail(
                gates_path.relative_to(ROOT),
                f"{check['id']} precisa ser demonstracao manual opt-in de aceite",
            )
        if (
            check.get("data") != "synthetic-fixtures-default; live-grafana-mcp-requires-explicit-authorization"
            or not isinstance(check.get("must_verify"), list)
            or not check["must_verify"]
        ):
            fail(
                gates_path.relative_to(ROOT),
                f"{check['id']} precisa declarar a pol?tica de fonte de dados e as verifica??es",
            )
        if (
            not isinstance(check.get("evidence_must_not_include"), list)
            or not check["evidence_must_not_include"]
        ):
            fail(
                gates_path.relative_to(ROOT), f"{check['id']} precisa declarar evidencias proibidas"
            )
    env_example = ROOT / "Backend" / ".env.example"
    env_example_text = ""
    try:
        env_example_text = env_example.read_text(encoding="utf-8")
        required_environment = [
            gateway.get("provider_credential_env"),
            gateway.get("provider_base_url_env"),
            gateway.get("model_alias_env"),
            *gateway.get("provider_model_id_env", {}).values(),
        ]
        for variable in required_environment:
            if not variable or not re.search(rf"(?m)^{re.escape(variable)}=", env_example_text):
                fail(
                    env_example.relative_to(ROOT),
                    f"variavel requerida ausente do exemplo de configuracao: {variable}",
                )
    except OSError as exc:
        fail(env_example.relative_to(ROOT), f"nao foi possivel ler exemplo de configuracao: {exc}")
    env_lines = dict(re.findall(r"(?m)^([A-Za-z_][A-Za-z0-9_]*)=(.*)$", env_example_text))
    manifesto_decisoes_modelo = (
        load_json(ROOT / "harness" / "config" / "decisions.json") or {}
    )
    model_decision = manifesto_decisoes_modelo.get("decisions", {}).get("model", {})
    if env_lines.get(gateway.get("model_alias_env"), "").strip() != gateway.get(
        "default_model_alias"
    ):
        fail(
            env_example.relative_to(ROOT),
            "alias padrão do `.env.example` precisa corresponder ao catálogo interno",
        )
    status_id_modelo = gateway.get("model_id_status")
    for variable in [gateway.get("provider_credential_env")]:
        value = env_lines.get(variable, "").strip()
        if value and not (
            value.startswith("replace-") or value.startswith("your-") or value.startswith("<")
        ):
            fail(
                env_example.relative_to(ROOT),
                f"{variable} precisa ser placeholder, nunca credencial/modelo concreto",
            )
    if status_id_modelo == "fixed-in-catalog":
        if (
            model_decision.get("catalog_model_id") != gateway.get("model_id_catalog_value")
            or gateway.get("provider_model_id_env") != {}
        ):
            fail(
                project_path.relative_to(ROOT),
                "modelo fixo do catálogo precisa corresponder à decisão e não exigir variável externa",
            )
    ignore_expectations = {
        ROOT / ".gitignore": "Backend/.env",
        ROOT / "Backend" / ".gitignore": ".env",
    }
    for ignore_path, ignored_secret in ignore_expectations.items():
        try:
            ignore_lines = {
                line.strip() for line in ignore_path.read_text(encoding="utf-8").splitlines()
            }
        except OSError as exc:
            fail(ignore_path.relative_to(ROOT), f"arquivo de ignore ausente ou ilegivel: {exc}")
            continue
        if ignored_secret not in ignore_lines:
            fail(ignore_path.relative_to(ROOT), f"{ignored_secret} precisa estar ignorado pelo Git")
    root_ignore_lines = (
        {line.strip() for line in (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()}
        if (ROOT / ".gitignore").is_file()
        else set()
    )
    if "!Backend/.env.example" not in root_ignore_lines:
        fail(
            (ROOT / ".gitignore").relative_to(ROOT),
            "Backend/.env.example precisa permanecer versionavel",
        )

    for path, agent in shared_agents.values():
        if agent.get("role") not in shared_roles:
            fail(path.relative_to(ROOT), f"role inexistente: {agent.get('role')}")
        if agent.get("prompt") not in shared_prompts:
            fail(path.relative_to(ROOT), f"prompt inexistente: {agent.get('prompt')}")
        check_refs(path, agent.get("skills", []), set(shared_skills), "skills")
        check_refs(path, agent.get("tools", []), set(shared_tools), "tools")
        for tool_id in agent.get("tools", []):
            tool = shared_tools.get(tool_id, {})
            if agent.get("role") not in tool.get("allowed_roles", []):
                fail(
                    path.relative_to(ROOT),
                    f"role {agent.get('role')} nao autorizado para tool {tool_id}",
                )
        check_refs(path, agent.get("workflows", []), set(shared_workflows), "workflows")
    for path, orchestrator in shared_orchestrators.values():
        if orchestrator.get("workflow") not in shared_workflows:
            fail(path.relative_to(ROOT), f"workflow inexistente: {orchestrator.get('workflow')}")
        else:
            workflow_id = orchestrator["workflow"]
            _, workflow_data = shared_workflows[workflow_id]
            declared_steps = [
                step.get("id") for step in workflow_data.get("steps", []) if isinstance(step, dict)
            ]
            if orchestrator.get("steps") != declared_steps:
                fail(
                    path.relative_to(ROOT),
                    f"steps devem corresponder, na mesma ordem, ao workflow {workflow_id}: {declared_steps}",
                )
        validate_orchestrator_loop_ref(path, orchestrator)
        if orchestrator.get("execution") != "sequential":
            fail(path.relative_to(ROOT), "execution deve ser sequential")
        if orchestrator.get("delegation") != "disabled":
            fail(path.relative_to(ROOT), "delegation deve permanecer disabled")
        if orchestrator.get("failure_policy") not in {
            "fix-before-next-step",
            "fix-before-handoff",
            "stop-at-failed-gate-fix-and-rerun",
        }:
            fail(
                path.relative_to(ROOT),
                "failure_policy precisa bloquear avanco enquanto houver falha",
            )
    for path, workflow in shared_workflows.values():
        steps = workflow.get("steps")
        if not isinstance(steps, list) or not steps:
            fail(path.relative_to(ROOT), "workflow compartilhado precisa ter steps nao vazios")
            continue
        if workflow.get("execution") != "sequential":
            fail(path.relative_to(ROOT), "execution do workflow precisa ser sequential")
        if workflow.get("failure_policy") != "stop-fix-and-rerun-impacted-steps":
            fail(
                path.relative_to(ROOT),
                "failure_policy precisa parar, corrigir e repetir passos impactados",
            )
        if (
            workflow.get("condition_semantics")
            != "execute-when-when-matches-required-means-blocking-when-executed"
        ):
            fail(path.relative_to(ROOT), "condition_semantics do workflow invalida")
        for field in ("inputs", "outputs", "completion_criteria"):
            if not isinstance(workflow.get(field), list) or not workflow[field]:
                fail(path.relative_to(ROOT), f"workflow precisa declarar {field} nao vazio")
        if (
            workflow.get("condition_semantics")
            != "execute-when-when-matches-required-means-blocking-when-executed"
        ):
            fail(path.relative_to(ROOT), "condition_semantics do workflow invalida")
        step_ids: set[str] = set()
        for step in steps:
            if not isinstance(step, dict) or not isinstance(step.get("id"), str):
                fail(path.relative_to(ROOT), "cada step compartilhado precisa de id")
                continue
            step_id = step["id"]
            if step_id in step_ids:
                fail(path.relative_to(ROOT), f"step duplicado: {step_id}")
            step_ids.add(step_id)
            if not isinstance(step.get("required"), bool):
                fail(path.relative_to(ROOT), f"step {step_id} precisa declarar required booleano")
            if "agent" in step and "prompt" not in step and "component_workflow" not in step:
                fail(
                    path.relative_to(ROOT),
                    f"step {step_id} com agent precisa de prompt ou component_workflow",
                )
            if "prompt" in step and "agent" not in step:
                fail(path.relative_to(ROOT), f"step {step_id} com prompt precisa declarar agent")
            if not any(field in step for field in ("agent", "tool", "component_workflow", "check")):
                fail(path.relative_to(ROOT), f"step {step_id} precisa declarar executor")
            if "agent" in step and step["agent"] not in shared_agents:
                fail(
                    path.relative_to(ROOT), f"agent inexistente no step {step_id}: {step['agent']}"
                )
            if "prompt" in step and step["prompt"] not in shared_prompts:
                fail(
                    path.relative_to(ROOT),
                    f"prompt inexistente no step {step_id}: {step['prompt']}",
                )
            if "tool" in step and step["tool"] not in shared_tools:
                fail(path.relative_to(ROOT), f"tool inexistente no step {step_id}: {step['tool']}")
            if "component_workflow" in step:
                target = step["component_workflow"]
                owner = target.split(".", 1)[0]
                if target not in component_configs.get(owner, {}).get("workflows", []):
                    fail(path.relative_to(ROOT), f"workflow de componente nao registrado: {target}")
        for group in workflow.get("at_least_one_from", []):
            if (
                not isinstance(group, list)
                or not group
                or any(step_id not in step_ids for step_id in group)
            ):
                fail(path.relative_to(ROOT), f"at_least_one_from contem step inexistente: {group}")

    if ERRORS:
        print("Validacao do Harness: FALHOU")
        for error in ERRORS:
            print(f" - {error}")
        return 1
    component_counts = {
        "agents": sum(
            len(json_entities(ROOT / item, "agents")) for item in ("Backend", "Frontend")
        ),
        "roles": sum(len(json_entities(ROOT / item, "roles")) for item in ("Backend", "Frontend")),
        "workflows": sum(
            len(json_entities(ROOT / item, "workflows")) for item in ("Backend", "Frontend")
        ),
        "skills": sum(
            len(markdown_entities(ROOT / item, "skills")) for item in ("Backend", "Frontend")
        ),
        "prompts": sum(
            len(markdown_entities(ROOT / item, "prompts")) for item in ("Backend", "Frontend")
        ),
    }
    totals = {
        "agentes": len(shared_agents) + component_counts["agents"],
        "papeis": len(shared_roles) + component_counts["roles"],
        "workflows": len(shared_workflows) + component_counts["workflows"],
        "skills": len(shared_skills) + component_counts["skills"],
        "prompts": len(shared_prompts) + component_counts["prompts"],
        "gates": len(gate_ids),
    }
    print(
        "Validacao do Harness: OK | "
        + " | ".join(f"{key}={value}" for key, value in totals.items())
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
