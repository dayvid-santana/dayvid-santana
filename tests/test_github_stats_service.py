# DSI GitHub Command Center
# Autor: Dayvid Santana
# Criado em: 28/08/2026
# Editado em: 28/08/2026
# Objetivo: Validar a agregação de métricas de atividade via GitHub Search API.
"""Testes do serviço de coleta de estatísticas via API do GitHub."""

import httpx
import pytest

from dsi_profile.exceptions import GitHubApiError
from dsi_profile.services.github_stats_service import GitHubStatsService


def _handler(request: httpx.Request) -> httpx.Response:
    if request.url.path == "/users/octocat/repos":
        if request.url.params.get("page") == "1":
            return httpx.Response(
                200,
                json=[
                    {"name": "repo-a", "fork": False, "stargazers_count": 10},
                    {"name": "repo-b", "fork": True, "stargazers_count": 100},
                ],
            )
        return httpx.Response(200, json=[])
    if request.url.path == "/search/issues":
        query = request.url.params.get("q", "")
        if "type:pr" in query:
            return httpx.Response(200, json={"total_count": 5})
        if "type:issue" in query:
            return httpx.Response(200, json={"total_count": 2})
        return httpx.Response(200, json={"total_count": 0})
    if request.url.path == "/search/commits":
        return httpx.Response(200, json={"total_count": 42})
    if request.url.path == "/users/ghost/repos":
        return httpx.Response(404, json={"message": "Not Found"})
    if request.url.path == "/users/ratelimited/repos":
        return httpx.Response(403, json={"message": "API rate limit exceeded for ..."})
    return httpx.Response(404)


def _service() -> GitHubStatsService:
    return GitHubStatsService(transport=httpx.MockTransport(_handler))


def test_build_report_excludes_forks_by_default() -> None:
    """Estrelas e contagem de repositórios não devem incluir forks por padrão."""
    with _service() as service:
        report = service.build_report("octocat")
    assert report.repository_count == 1
    assert report.star_count == 10


def test_build_report_includes_forks_when_requested() -> None:
    """A flag include_forks deve somar estrelas de repositórios forkados também."""
    with _service() as service:
        report = service.build_report("octocat", include_forks=True)
    assert report.repository_count == 2
    assert report.star_count == 110


def test_build_report_reads_pull_requests_issues_and_commits() -> None:
    """PRs, issues e commits devem vir da Search API, separados por tipo de query."""
    with _service() as service:
        report = service.build_report("octocat")
    assert report.pull_request_count == 5
    assert report.issue_count == 2
    assert report.commit_count == 42
    assert report.github_username == "octocat"


def test_unknown_user_raises_domain_error() -> None:
    """Um usuário inexistente deve levantar GitHubApiError com mensagem clara."""
    with _service() as service, pytest.raises(GitHubApiError):
        service.build_report("ghost")


def test_rate_limit_raises_domain_error_with_guidance() -> None:
    """O limite de requisições deve orientar o uso de GITHUB_TOKEN."""
    with _service() as service, pytest.raises(GitHubApiError, match="GITHUB_TOKEN"):
        service.build_report("ratelimited")
