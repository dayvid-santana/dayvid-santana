<!--
DSI GitHub Command Center
Autor: Dayvid Santana
Criado em: 28/08/2026
Editado em: 28/08/2026
Objetivo: Manter um histórico conciso das alterações entregues.
-->
# Changelog

## [Unreleased]

### Added

- Fundação da Fase 1: configuração, validação Pydantic, CLI `validate` e testes iniciais.
- Geração de README de perfil, banner SVG DSI e seis divisores técnicos via `dsi-profile generate`.
- Animações SVG discretas de varredura, radar, pulsos e cursor de terminal, com modo estático.
- Comando `dsi-profile fetch-languages`: agrega bytes de código por linguagem em todos os
  repositórios públicos do usuário (via API do GitHub) e publica um JSON estático
  (`data/languages.json`) com percentuais, título de proficiência por linguagem (patamares
  DELTA a OMEGA) e um título geral de operador, pronto para ser consumido por outros projetos.
