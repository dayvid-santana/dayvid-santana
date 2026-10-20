# Iara

A Iara é uma aplicação conversacional para gestores. Ela entende a pergunta, busca os dados pela fonte autorizada e usa uma LLM para explicar os resultados em texto e blocos analíticos. O MVP prioriza um produto seguro, utilizável e extensível; não a construção de um agente autônomo.

## Visão rápida

- **Frontend:** React, TypeScript, Vite e Tailwind. Conversa com a API Iara e apresenta histórico, respostas progressivas, KPIs, tabelas e gráficos.
- **Backend:** FastAPI, Pydantic e SQLite local para a demonstração. Controla sessão, conversas, mensagens, erros e comunicação com o Model Gateway.
- **Model Gateway:** abstrai o modelo usado. O provider falso é o padrão local e de testes; o provider LLM do MVP é o endpoint da Iara, acessado pelo cliente LangChain compatível com Chat Completions no Backend.
- **Fonte de dados:** fixtures JSON sintéticas no ambiente atual. A API de dados será integrada por HTTP no Backend; sua resposta será repassada exatamente como recebida, inclusive HTML e todos os tipos de gráfico.
- **Contratos:** mensagem pública v1 para histórico e v2 para visualizações HTML/SVG estáticas, além dos payloads SSE correspondentes, ficam em `contracts/`; consulta e completude internas pertencem ao Backend.
- **Painel administrativo:** `/admin`, disponível somente em localhost no modo de desenvolvimento. Mostra saúde, logs técnicos sanitizados e a fila de erros, sem acesso às conversas.
- **Ambiente local:** Docker Compose conecta Frontend e Backend para desenvolvimento e testes integrados; a API fica privada, o SQLite de desenvolvimento persiste em volume, e o smoke usa provider fake e dados isolados.

## O que funciona hoje

Em `localhost`, o Frontend cria automaticamente uma sessão sintética sem pedir login ou clique para entrar. A API restringe esse acesso ao ambiente local, persiste conversas e mensagens, envia eventos SSE, permite cancelar e tentar novamente, e reconstrói os blocos salvos ao reabrir o histórico. Perguntas abertas pedem o detalhe que falta; respostas curtas podem usar o contexto recente da conversa; solicitações fora de escopo recebem uma orientação clara.

O fluxo de demonstração usa dados inventados de vendas do Produto A. Isso serve para exercitar o caminho completo, não define os assuntos empresariais que a Iara poderá responder. O adapter SULTS já usa a biblioteca interna do Faturas, mas a validação no tenant real depende de homologação autorizada. API de dados e banco de produção permanecem para a etapa final do MVP.

## Decisões do projeto

- Fora do modo de desenvolvimento, o Backend pode validar usuário e senha pelo SULTS usando a biblioteca interna do Faturas e emitir uma sessão própria da Iara. O fluxo permanece desligado até configurar o segredo, autorizar o ambiente e concluir a homologação com o Líder Técnico; a borda também precisa limitar tentativas por origem.
- SQLite é usado localmente para desenvolver e validar persistência. A equipe entregará ao DBA um único arquivo DDL ao finalizar o MVP; SQLite local não determina a tecnologia de produção.
- O provider do MVP é a API da Iara. `IARA_DEFAULT_MODEL` contém o alias lógico `principal`, que resolve no catálogo do Backend para `iara-grafana`; `IARA_BASE_URL` e `IARA_API_KEY` ficam somente no ambiente do Backend. A interface não mostra provider ou modelo ao gestor.
- A API de dados é o serviço empresarial previsto; a resposta é encaminhada sem filtro nem transformação, inclusive HTML e qualquer gráfico. Desenvolvimento e demonstrações seguem com fixtures sintéticas por um período prolongado, inclusive depois que o acesso real estiver disponível.
- Nomes de código e banco criados pela equipe ficam em português; os campos públicos já aprovados e protocolos externos mantêm seus nomes oficiais.

As decisões e pendências estão registradas em [harness/config/decisions.json](harness/config/decisions.json); o plano de evolução está registrado em `docs/fases-do-projeto.md` no diretório de documentos do projeto.

## Executar localmente com Docker

Requisitos: Docker Desktop com Docker Compose v2.24 ou superior e PowerShell. O fluxo recomendado prepara o Backend, o Frontend e o SQLite persistente em containers:

```powershell
.\scripts\harness.ps1 -Target docker-up
```

Abra `http://localhost:5173`. A API não é publicada na máquina; o navegador conversa com ela pelo proxy local do Vite. Se a porta 5173 já estiver em uso, defina `$env:IARA_FRONTEND_PORT=5174` antes de executar o Harness. O volume `iara_dados_sqlite` preserva as conversas sintéticas entre reinícios, inclusive após `docker-down`.

O ambiente usa `APP_ENV=development`, fixtures sintéticas e provider fake por padrão. Para habilitar uma chamada ao endpoint da Iara, configure `Backend/.env` conforme `Backend/.env.example`; esse arquivo é passado somente ao container Backend e nunca incluído nas imagens.

Para executar o smoke integrado dentro de containers isolados, com provider fake, rede sem acesso externo e remoção dos volumes de teste ao final:

```powershell
.\scripts\harness.ps1 -Target docker-e2e
```

Para parar o ambiente local e manter o banco:

```powershell
.\scripts\harness.ps1 -Target docker-down
```

O modo manual sem Docker continua disponível. Execute `scripts/harness.ps1 -Target setup`, inicie Uvicorn em `Backend` e Vite em `Frontend`, conforme os READMEs de cada repositório.

Para usar a API da Iara, configure `IARA_MODEL_PROVIDER=iara`, `IARA_BASE_URL`, `IARA_API_KEY` e `IARA_DEFAULT_MODEL=principal` no `Backend/.env`, seguindo `Backend/.env.example`. O alias resolve para `iara-grafana` no catálogo do Backend. O código usa `ChatOpenAI` como cliente compatível com Chat Completions; ele não envia chamadas à plataforma OpenAI. A chamada real é opt-in e a fonte de dados permanece sintética.

## Verificações

Execute a partir da raiz:

| Comando | O que verifica |
| --- | --- |
| `scripts/harness.ps1 -Target harness` | Regras, referências e contratos do Harness |
| `scripts/harness.ps1 -Target context` | Retrieval de contexto e seus limites |
| `scripts/harness.ps1 -Target backend` | Ruff, Pytest e cobertura mínima de 80% |
| `scripts/harness.ps1 -Target frontend` | Lint, TypeScript, testes unitários e build |
| `scripts/harness.ps1 -Target e2e` | Fluxo de demonstração, histórico responsivo e painel administrativo com processos locais |
| `scripts/harness.ps1 -Target docker-e2e` | Mesmo smoke Playwright em Docker, com provider fake, rede isolada e limpeza do SQLite de teste |
| `scripts/harness.ps1 -Target all` | Todos os gates locais |

Os testes comuns usam provider falso e dados sintéticos. Chamadas reais de provider não fazem parte da suite padrão.

## Estrutura

```text
Backend/       API, Model Gateway, persistência e adapters de resposta direta
Frontend/      aplicação React, features e renderizadores
contracts/     contratos JSON compartilhados
harness/       decisões, regras, workflows e cobertura
scripts/       runner e validador do Harness
```

`Backend` e `Frontend` são repositórios Git independentes. O `harness/` da raiz coordena o workspace e confere consistência entre eles. Os manifests de agente e workflow descrevem a execução esperada; o runner local aplica os gates, mas não executa delegação automática.
