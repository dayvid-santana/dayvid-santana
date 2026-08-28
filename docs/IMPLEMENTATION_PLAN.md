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

## Próximas fases

1. Gerador determinístico do README e marcadores automáticos.
2. Banner e divisores SVG com design system documentado.
3. Cards de projetos e badges.
4. Integração opcional, cache e modo offline para GitHub.
5. Preview HTML local.
6. Publicação segura e limpeza seletiva.
7. Workflows do GitHub Actions.
8. Refinamento visual, acessibilidade e snapshots.
