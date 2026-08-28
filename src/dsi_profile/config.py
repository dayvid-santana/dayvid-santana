# DSI GitHub Command Center
# Autor: Dayvid Santana
# Criado em: 28/08/2026
# Editado em: 28/08/2026
# Objetivo: Carregar YAML com segurança e convertê-lo em configuração DSI validada.
"""Leitura e validação de arquivos de perfil."""

from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from dsi_profile.exceptions import ProfileConfigurationError
from dsi_profile.models import ProfileConfig


def load_profile_config(path: Path) -> ProfileConfig:
    """Carrega e valida um arquivo YAML, expondo erros claros ao chamador."""
    if not path.is_file():
        raise ProfileConfigurationError(f"Arquivo de configuração não encontrado: {path}")
    try:
        raw: Any = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as error:
        raise ProfileConfigurationError(f"YAML inválido em {path}: {error}") from error
    if not isinstance(raw, dict):
        raise ProfileConfigurationError("A configuração YAML deve conter um objeto no nível raiz.")
    try:
        return ProfileConfig.model_validate(raw)
    except ValidationError as error:
        raise ProfileConfigurationError(f"Configuração inválida em {path}:\n{error}") from error
