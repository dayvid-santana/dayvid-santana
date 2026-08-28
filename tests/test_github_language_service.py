# DSI GitHub Command Center
# Autor: Dayvid Santana
# Criado em: 28/08/2026
# Editado em: 28/08/2026
# Objetivo: Validar a agregação de linguagens e o mapeamento de patamares de proficiência.
"""Testes do serviço de coleta de linguagens via API do GitHub."""

import httpx
import pytest

from dsi_profile.exceptions import GitHubApiError
from dsi_profile.services.github_language_service import GitHubLanguageService


def _handler(request: httpx.Request) -> httpx.Response:
    if request.url.path == "/users/octocat/repos":
        if request.url.params.get("page") == "1":
            return httpx.Response(
                200,
                json=[
                    {"name": "repo-a", "fork": False},
                    {"name": "repo-b", "fork": True},
                ],
            )
        return httpx.Response(200, json=[])
    if request.url.path == "/repos/octocat/repo-a/languages":
        return httpx.Response(200, json={"Python": 800, "HTML": 200})
    if request.url.path == "/repos/octocat/repo-b/languages":
        return httpx.Response(200, json={"JavaScript": 1_000})
    if request.url.path == "/users/ghost/repos":
        return httpx.Response(404, json={"message": "Not Found"})
    if request.url.path == "/users/ratelimited/repos":
        return httpx.Response(403, json={"message": "API rate limit exceeded for ..."})
    return httpx.Response(404)


def _service() -> GitHubLanguageService:
    return GitHubLanguageService(transport=httpx.MockTransport(_handler))


def test_build_report_excludes_forks_by_default() -> None:
    """Repositórios forkados não devem contribuir para a proficiência agregada."""
    with _service() as service:
        report = service.build_report("octocat")
    assert report.repository_count == 1
    assert report.total_bytes == 1_000
    names = {language.name for language in report.languages}
    assert names == {"Python", "HTML"}


def test_build_report_includes_forks_when_requested() -> None:
    """A flag include_forks deve trazer linguagens de repositórios forkados."""
    with _service() as service:
        report = service.build_report("octocat", include_forks=True)
    assert report.repository_count == 2
    names = {language.name for language in report.languages}
    assert names == {"Python", "HTML", "JavaScript"}


def test_ranks_and_operator_title_reflect_dominant_language() -> None:
    """A linguagem com maior percentual deve liderar a lista e definir o título do operador."""
    with _service() as service:
        report = service.build_report("octocat")
    top = report.languages[0]
    assert top.name == "Python"
    assert top.percentage == 80.0
    assert top.rank_code == "OMEGA"
    assert report.operator_title == "OMEGA-CLASS PYTHON OPERATOR"
    html = next(language for language in report.languages if language.name == "HTML")
    assert html.percentage == 20.0
    assert html.rank_code == "ALPHA"


def test_unknown_user_raises_domain_error() -> None:
    """Um usuário inexistente deve levantar GitHubApiError com mensagem clara."""
    with _service() as service, pytest.raises(GitHubApiError):
        service.build_report("ghost")


def test_rate_limit_raises_domain_error_with_guidance() -> None:
    """O limite de requisições deve orientar o uso de GITHUB_TOKEN."""
    with _service() as service, pytest.raises(GitHubApiError, match="GITHUB_TOKEN"):
        service.build_report("ratelimited")
