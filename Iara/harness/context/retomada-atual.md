# Retomada atual

Atualizado em 16/10/2026. O provider ativo do MVP é a API dedicada da Iara, acessada pelo Model Gateway. As decisões duráveis ficam em `harness/context/estado-do-projeto.md`; o roteiro está em `docs/fases-do-projeto.md` no diretório de documentos do projeto.

## Autenticação SULTS

- O esqueleto está implementado: o formulário de produção envia usuário/senha para `POST /api/v1/autenticacao/login`; o Backend delega à porta `PortaAutenticacaoCorporativa`, cria cookie Iara HttpOnly e persiste apenas hashes de sessão/CSRF e UUID pseudônimo estável.
- A rota falha fechada por padrão. O runtime ainda não injeta adapter SULTS e requer `IARA_AUTH_IDENTITY_KEY`, `IARA_CORPORATE_AUTH_ENABLED=true` fora de development e rate limiting de login pronto; são bloqueios esperados até o Líder Técnico fornecer contrato e ambiente oficial. O fluxo sintético de `localhost` segue sem login.
- Próximo passo ao retomar autenticação: solicitar ao Líder Técnico método oficial de acesso, endpoint/documentação de teste, formato de sucesso/recusa/indisponibilidade e identidade estável; implementar o adapter sem alterar o contrato HTTP da Iara.
- Opções e decisões ainda abertas: `harness/context/autenticacao-sults.md`.

## Frentes em andamento

- O adapter usa `ChatOpenAI` do pacote `langchain-openai` como cliente compatível com Chat Completions. O host chamado é somente `IARA_BASE_URL`; não é a plataforma OpenAI.
- A credencial correta é `IARA_API_KEY`, mantida somente no Backend. `IARA_DEFAULT_KEY` não faz parte do contrato de configuração. O `.env` real permanece ignorado pelo Git e seus valores não devem aparecer em logs ou documentação.
- O catálogo mantém o alias `principal` e resolve o ID fixo `iara-grafana`.
- A chamada segue `temperature=None`, `use_responses_api=False`, `stream_usage=False`, timeout SDK de 360 segundos e `max_retries=0`.
- O endpoint atual rejeita `tools`, `tool_choice` e `parallel_tool_calls`; o fluxo ativo envia System Prompt, até 39 mensagens anteriores e a solicitação atual diretamente, sem pré-processamento LLM e sem campos de tool calling.
- Uma chamada básica e uma chamada completa com o contrato da Iara foram aceitas em 15/10/2026. A resposta completa levou cerca de 77 segundos, então o prazo da aplicação passou de 40 para 120 segundos por padrão, configurável entre 1 e 360.
- Durante a espera, o Backend publica “A Iara continua preparando a resposta” a cada 15 segundos sem consumir uma nova chamada ou tokens adicionais.
- Não houve mudança no contrato SSE, no Frontend, nos blocos públicos ou na política de proteção de credenciais.

## Verificação do streaming ponta a ponta — 16/10/2026

- O caminho ativo confirmado é navegador → `src/api.ts` → proxy HTTP do Vite → `StreamingResponse` do FastAPI → coordenador de solicitações → `ModelGateway` → `AdaptadorIara` (`ChatOpenAI.astream`) → eventos SSE validados → interface. O Grafana MCP real ainda não está conectado; nesta fase não existe um stream separado de dados brutos do MCP.
- O Backend persiste cada snapshot de texto parcial antes de publicar `texto.delta`; os blocos analíticos só são emitidos completos após validação. `Cache-Control: no-cache, no-transform` e `X-Accel-Buffering: no` evitam cache/transformação e buffering por proxies compatíveis. O proxy Vite de desenvolvimento encaminha a resposta HTTP sem uma camada de compressão configurada.
- O botão “Parar” chama o endpoint autenticado de cancelamento e interrompe a tarefa do provider. A queda de uma conexão SSE não cancela a solicitação aceita: ela continua persistida, pode ser acompanhada em outro chat e o navegador retoma pelo último cursor. Essa distinção preserva o requisito de múltiplas conversas simultâneas e evita perder trabalho por uma desconexão transitória.
- Verificações em 16/10: `scripts/harness.ps1 -Target backend` passou com Ruff, 146 testes e 88,51% de cobertura; `scripts/harness.ps1 -Target frontend` passou com lint, tipos, 128 testes e build. O Compose de teste usou provider fake e rede/volumes isolados; 4 dos 6 testes Playwright passaram incluindo fluxos de resposta pelo proxy. Os outros 2 chegaram a falhar somente nas comparações de screenshot (diferença de cerca de 1% de pixels nas referências Linux), sem falha funcional do streaming. Nenhuma chamada real à LLM ou ao Grafana foi feita nesta verificação.
- A implementação de streaming já estava presente e não precisou de alteração de código para esta tarefa. A divergência de snapshots do Compose Linux deve ser investigada como manutenção de regressão visual separada, sem atualizar as referências automaticamente nesta tarefa.

## Verificações e estado

- A configuração privada foi validada sem imprimir chave ou URL: provider `iara`, alias `principal`, endpoint válido e credencial presente.
- `docker compose config --quiet` aceitou o arquivo de ambiente depois da correção da chave malformada.
- A chamada direta básica e a resposta completa estruturada chegaram ao serviço real. O erro HTTP 422 observado com tool calling foi diagnosticado e o adapter foi ajustado para o formato aceito pelo endpoint.
- O smoke público pelo Compose concluiu em 60,3 segundos com cinco estados de progresso, deltas textuais, evento final e mensagem persistida como `completed`; nenhuma credencial, URL ou conteúdo de resposta foi impresso.
- O gate completo do Backend passou: Ruff, 143 testes e 88,08% de cobertura. A validação do Harness passou com 9 agentes, 9 papéis, 7 workflows, 11 skills, 9 prompts e 8 gates.
- Branch ativa: `main` nos repositórios Backend e Frontend. A branch de backup não foi acessada nem alterada.

## Como retomar

1. Preservar `IARA_MODEL_PROVIDER=iara`, `IARA_DEFAULT_MODEL=principal`, `IARA_BASE_URL`, `IARA_API_KEY` e o prazo adequado no ambiente privado do Backend.
2. Ao alterar a integração, repetir o gate Backend e um smoke opt-in pelo fluxo público sem imprimir conteúdo ou credenciais.
3. Não reintroduzir campos de tool calling até existir contrato compatível e decisão específica para a integração MCP.

## Referências

- Leia `harness/context/estado-do-projeto.md` para decisões duráveis e limites de produto.
- Leia `Backend/app/model_gateway.py`, `Backend/app/configuracao.py`, `Backend/app/solicitacoes.py` e `Backend/app/catalogo_modelos.py` para o caminho ativo da integração.
- Leia `Backend/.env.example` para os nomes e formatos das variáveis privadas, sem inserir credenciais no repositório.
