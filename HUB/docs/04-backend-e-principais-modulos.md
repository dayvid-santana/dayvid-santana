# Backend e principais módulos

## Organização

```text
HUB_acesso_Backend/
├── app/main.py                 # criação da API, lifespan, CORS, health/readiness
├── app/api/routes.py            # rotas REST e consultas de apresentação
├── app/core/config.py           # Settings e validações de ambiente
├── app/models/database.py       # entidades SQLAlchemy, engine e schema check
├── app/schemas/domain.py        # contratos Pydantic, enums e regras de cadastro
├── app/data_sources/senior.py   # adaptadores CSV/SQL e cache
├── app/services/
│   ├── scanner.py               # chamadas, classificação e ciclo de varredura
│   ├── mapping.py               # JSON Schema, JSONPath e normalização
│   ├── audit.py                 # reconciliação de alertas e divergências
│   ├── discovery.py             # descoberta assistida de API/schema/mapeamento
│   ├── list_integration.py      # integração por coleção paginada
│   ├── scan_scheduler.py        # execução automática
│   ├── integration_diagnostics.py # causas e mensagens operacionais
│   ├── authentication.py        # montagem de cabeçalhos externos
│   ├── session_provider.py      # sessão do usuário, atualmente mock
│   └── logo_storage.py          # validação e armazenamento de logos
└── scripts/                    # preparação, testes e diagnóstico
```

## `app/main.py`

Cria a instância FastAPI, configura CORS, monta arquivos estáticos e inclui o roteador `/api`. No lifespan, verifica o banco, cria a trava compartilhada e inicia/encerra o `AgendadorVarredura`.

Endpoints de infraestrutura:

- `GET /health`: processo vivo; não garante dependências.
- `GET /ready`: verifica banco, schema e disponibilidade da fonte Senior; retorna `503` se alguma dependência estiver indisponível.

## `app/core/config.py`

`Settings` lê `.env` e variáveis de ambiente. Valida a combinação de ambiente e fonte: em produção, exige fonte SQL, view, banco não-SQLite e dados mock desabilitados. A configuração é cacheada por `obterConfiguracoes()`.

## `app/models/database.py`

Define as seis entidades principais e o engine SQLAlchemy. Para bancos não SQLite, habilita `pool_pre_ping` e `pool_recycle`. `prepararBancoDados()` cria/atualiza o schema de forma explícita; `verificarBancoDados()` apenas verifica tabelas e colunas e não faz alteração silenciosa.

## `app/schemas/domain.py`

Centraliza contratos de domínio e de entrada das rotas. Além dos modelos `Collaborator`, `NormalizedAccess`, `SystemCreate` e `SystemUpdate`, define os enums de status e validações como:

- CPF válido e normalizado;
- slug em kebab-case;
- template individual contendo `{cpf}`;
- credencial coerente com o tipo de autenticação;
- campos obrigatórios de integração em lista;
- limites de timeout, página e arquivo.

## `app/data_sources/senior.py`

O adaptador CSV valida cabeçalho, linhas, CPF, campos obrigatórios, duplicidade da chave composta e CPF compartilhado entre vínculos. A implementação SQL consulta uma view com o mesmo contrato e valida identificadores da view. Ambas oferecem iteração em lotes e `verificarDisponibilidade()`.

O cache de leitura é usado nos endpoints de consulta e tem TTL configurável. A varredura sempre deve obter dados atuais, não depender do cache de leitura do dashboard.

## `app/services/mapping.py`

Valida o JSON Schema Draft 2020-12 e devolve erros com caminho e mensagem. O subconjunto de JSONPath suporta campos aninhados e listas. As regras podem indicar caminho, valor fixo, default e conversão de tipo. Aliases em português são canonizados para o formato interno.

Para respostas em lista existe `_selecao_lista`: o motor procura o item cujo campo de CPF corresponde ao colaborador e não escolhe cegamente o primeiro registro.

## `app/services/scanner.py`

Orquestra a consulta individual, a validação, o mapeamento, a persistência e a reconciliação de alertas. Usa concorrência limitada por sistema, registra duração/HTTP e captura falhas sem interromper todo o ciclo. O ciclo processa a fonte em lotes, mantendo o consumo de memória controlado.

## `app/services/audit.py`

Gera ou atualiza alertas `SITUACAO_7` quando a situação funcional e o acesso atual satisfazem a regra. Também reconcilia divergências relacionadas a cargo. O status persistido deve ser interpretado junto com o snapshot atual.

## `app/services/discovery.py`

Recebe URL e CPF de teste, tenta variações de caminho/query, interpreta objeto ou coleção JSON, procura um item correspondente ao CPF e sugere schema/mapeamento. O fluxo é dividido em descoberta e confirmação para que o administrador revise a configuração antes do cadastro.

## `app/services/list_integration.py`

Consulta uma coleção uma vez por ciclo, seguindo `parametro_pagina`, `parametro_limite` e `tamanho_pagina`. Para cada registro, normaliza CPF e indexa o resultado para todos os colaboradores correspondentes. Interrompe em página vazia, página menor, total atingido ou teto de segurança; falha no meio não deve parecer resultado parcial bem-sucedido.

