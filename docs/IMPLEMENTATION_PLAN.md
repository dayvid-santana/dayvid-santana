<!--
DSI GitHub Command Center
Autor: Dayvid Santana
Criado em: 28/08/2026
Editado em: 28/08/2026
Objetivo: Registrar as fases, escopo e estado de implementação do projeto.
-->
# Plano de implementação

## Fase 1 — Fundação e configuração — Concluída

- [x] Estruturar pacote, dependências, convenções e configuração de exemplo.
- [x] Modelar e validar `profile.yaml` com Pydantic.
- [x] Implementar carregamento seguro de YAML e comando `dsi-profile validate`.
- [x] Cobrir os fluxos iniciais com testes.
- [x] Executar e corrigir as ferramentas de qualidade no ambiente configurado.

Validação concluída com Ruff, mypy e pytest. O host atual possui Python 3.11.9; a
instalação declarada continua exigindo Python 3.12+, portanto a instalação editável
deverá ser verificada novamente em um interpretador compatível.

## Fase 2 — README e primeira telemetria visual — Concluída

- [x] Criar template determinístico do README de perfil.
- [x] Gerar banner SVG original da DSI.
- [x] Gerar os seis divisores técnicos.
- [x] Referenciar assets locais, com texto alternativo e fallback textual no README.
- [x] Validar SVG como XML e testar geração determinística.
- [x] Adicionar painéis System Readiness e Deployment Map ao README.

## Próximas fases

1. Cards de projetos e badges.
2. Integração opcional, cache e modo offline para GitHub.
3. Preview HTML local.
4. Publicação segura e limpeza seletiva.
5. Workflows do GitHub Actions.
6. Refinamento visual, acessibilidade e snapshots.
