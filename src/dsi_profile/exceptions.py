# DSI GitHub Command Center
# Autor: Dayvid Santana
# Criado em: 28/08/2026
# Editado em: 28/08/2026
# Objetivo: Definir erros de domínio com mensagens seguras para configuração de perfil.
"""Exceções específicas da aplicação."""


class ProfileConfigurationError(Exception):
    """Indica que o arquivo de configuração não pode ser carregado ou validado."""


class GitHubApiError(Exception):
    """Indica falha ao consultar a API pública do GitHub."""
