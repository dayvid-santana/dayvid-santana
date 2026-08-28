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
- Sétima seção do perfil, "LANGUAGE PROFICIENCY", exibindo no README raiz os dados de
  `data/languages.json` (título do operador e proficiência por linguagem), com aviso para
  rodar `fetch-languages` quando o arquivo ainda não existe.
- Console animado `assets/language-console.svg`: barras de proficiência por linguagem com
  preenchimento animado e cor por patamar, varredura de fundo e indicador de status,
  seguindo a linguagem visual do banner DSI. Embutido no README raiz.
- Workflow `update-profile.yml`: roda diariamente (e sob demanda) `fetch-languages` +
  `generate` e faz commit automático quando os dados mudam, mantendo a proficiência sempre
  atualizada sem intervenção manual.
- Console animado `assets/capabilities-console.svg` para a seção "System Capabilities":
  mesma linguagem visual do console de linguagens, com barra de nível colorida pelo status
  declarado (OPERATIONAL/ACTIVE em verde, TRAINING em âmbar) e destaque da tecnologia de
  maior nível como "CORE". Substitui a lista simples em markdown no README raiz.
- Comando `dsi-profile fetch-stats`: agrega estrelas, pull requests, issues e uma contagem
  aproximada de commits (via GitHub Search API) do usuário e publica `data/mission-stats.json`.
- Console animado `assets/mission-telemetry.svg` ("Mission Telemetry"): cartão com Commits,
  Stars, Pull Requests, Issues e Repositórios, números com efeito de brilho e ícones com
  pulso sutil; aviso de que a contagem de commits é aproximada (indexação por e-mail
  verificado). Embutido logo após "Personnel Record" no README raiz.
- Console animado `assets/tech-stack-console.svg` ("Tech Stack"): barras de linguagem
  coloridas pela cor de marca real de cada linguagem (linguist/GitHub) à esquerda, e um radar
  "Focus Sectors" à direita agrupando as tecnologias declaradas por categoria, com varredura
  giratória e partículas decorativas. Geometria calculada em `services/sector_chart.py`
  (determinística, com testes dedicados). Embutido após "Language Proficiency" no README raiz.
- Workflow `update-profile.yml` agora também roda `fetch-stats`, mantendo a telemetria de
  missão sempre atualizada junto com a proficiência em linguagens.
