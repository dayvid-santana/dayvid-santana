# Hub de Acessos — documentação

## Para que serve este conjunto de documentos

Este diretório é a referência de entendimento do projeto **Hub de Acessos**. Ele foi escrito para uma pessoa que não acompanhou a implementação e precisa compreender o problema, a arquitetura, os dados, os módulos, os contratos e a operação do sistema.

## Mapa de leitura

1. [Visão geral e necessidades atendidas](01-visao-geral-e-necessidades.md) — contexto, objetivos, usuários e limites do produto.
2. [Arquitetura](02-arquitetura.md) — componentes, fronteiras, fluxos e decisões estruturais.
3. [Domínio e modelo de dados](03-dominio-e-modelo-de-dados.md) — identidade, estados, snapshots, alertas e banco.
4. [Backend e principais módulos](04-backend-e-principais-modulos.md) — responsabilidades do código Python.
5. [Integrações e motor de varredura](05-integracoes-e-varredura.md) — Senior, APIs externas, schemas, mapeamento e agendamento.
6. [API HTTP](06-api-http.md) — endpoints consumidos pelo frontend e usados na administração/operação.
7. [Frontend](07-frontend.md) — telas, componentes, estado da aplicação e navegação.
8. [Configuração, execução e operação](08-configuracao-execucao-e-operacao.md) — ambiente local, Docker, produção e diagnóstico.
9. [Desenvolvimento, testes e evolução](09-desenvolvimento-testes-e-evolucao.md) — como validar mudanças, riscos conhecidos e próximos passos.
10. [Contratos detalhados da API](10-contratos-detalhados-da-api.md) — payloads, parâmetros, paginação e erros.
11. [Banco de dados e migrations](11-banco-de-dados-e-migrations.md) — ERD, tabelas, índices, preparação e backup.
12. [Guia de integração](12-guia-de-integracao.md) — cadastro de uma integração do início à primeira varredura.
13. [Runbook operacional](13-runbook-operacional.md) — procedimentos de inicialização, diagnóstico, recuperação e incidentes.
14. [Segurança e privacidade](14-seguranca-e-privacidade.md) — estado atual, riscos, dados pessoais e checklist.
15. [Manual do usuário](15-manual-do-usuario.md) — utilização das telas por perfil.
16. [CI/CD e ambientes](16-ci-cd-e-ambientes.md) — validação, promoção e release.
17. [Testes e critérios de aceite](17-testes-e-criterios-de-aceite.md) — matriz de cobertura e qualidade mínima.
18. [Glossário e decisões](18-glossario-e-decisoes.md) — vocabulário comum e decisões arquiteturais.

## Estrutura do repositório

O projeto é composto por dois aplicativos independentes:

```text
HUB/
├── HUB_acesso_Backend/       # API FastAPI, persistência e integrações
├── HUB_acesso_Frontend/      # SPA React/Vite/TypeScript
└── docs/                     # documentação consolidada
```

Os READMEs e documentos dentro de cada aplicativo continuam sendo referências técnicas locais. Este diretório explica como as peças se relacionam.

## Estado atual importante

- O backend já suporta fonte Senior por CSV e por view PostgreSQL.
- O PostgreSQL guarda sistemas, versões de schema, snapshots, alertas e diagnósticos.
- A matriz não consulta APIs externas durante a navegação: ela renderiza o último snapshot persistido.
- A varredura pode ser disparada por `POST /api/varreduras` ou executada automaticamente em intervalo configurável.
- O fluxo de login ainda é um provedor mock. Não há autenticação real de usuário implementada.
- A preparação/alteração do schema do banco deve ser executada explicitamente com `scripts/prepare_database.py`.
