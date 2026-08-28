<!--
DSI GitHub Command Center
Autor: Dayvid Santana
Criado em: 28/08/2026
Editado em: 28/08/2026
Objetivo: Descrever a separação inicial de responsabilidades da aplicação.
-->
# Arquitetura

Na Fase 1, `models.py` contém o domínio validado, `config.py` traduz YAML em modelos e `cli.py` apresenta operações ao usuário. Dependências futuras de rede, renderização e escrita deverão ficar em módulos e serviços próprios, sem lógica de negócio em templates ou na CLI.

Toda saída derivada será produzida em `dist/`; dados remotos opcionais serão isolados em `.cache/dsi-profile/`.
