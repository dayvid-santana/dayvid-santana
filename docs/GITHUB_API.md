<!--
DSI GitHub Command Center
Autor: Dayvid Santana
Criado em: 28/08/2026
Editado em: 28/08/2026
Objetivo: Definir regras de segurança para a futura integração opcional com GitHub.
-->
# Integração GitHub

A integração futura será opt-in. `GITHUB_TOKEN` será lido apenas do ambiente ou de `.env` local, nunca do YAML, de logs ou de exceções. As chamadas deverão usar timeout, retries limitados, cache local e modo offline. Os testes usarão mocks, sem acesso à internet.
