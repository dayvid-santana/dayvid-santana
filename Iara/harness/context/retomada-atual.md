# Retomada atual

Atualizado em 16/10/2026. O provider ativo do MVP é a API dedicada da Iara, acessada pelo Model Gateway. As decisões duráveis ficam em `harness/context/estado-do-projeto.md`; o roteiro está em `docs/fases-do-projeto.md` no diretório de documentos do projeto.

## HTML visual v2 — 16/10/2026

- Implementado contrato `mensagem-v2.schema.json` e SSE v2: `html` contém `title`, `summary` e fragmento estático. v1 permanece para histórico. O Backend atribui v2 quando a resposta inclui HTML, migra o CHECK do SQLite local sem apagar mensagens e serializa `bloco.pronto` com aliases públicos.
- O Gateway aceita HTML somente no campo `html` do array após `@@IARA_BLOCOS@@`; a allowlist reconstrói HTML/SVG estático e rejeita scripts, estilos, links, eventos e recursos externos. HTML solto no texto é bloqueado antes do SSE. O Frontend usa iframe sandbox com CSP e resumo acessível.
- O System Prompt v10 está arquivado e não é enviado. O contrato e a validação do Backend continuam permitindo KPI visual, gráficos estáticos e gráficos tipados. O serviço real ainda não forneceu amostra do envelope HTML/MCP; ajustar somente após receber contrato ou exemplo real, sem relaxar a validação.
- Verificações focadas: 68 testes Backend de HTML, contratos, SSE, histórico e fluxo de solicitações passaram; 69 testes Frontend de contratos/renderização passaram; Ruff, lint, tipos, build e validação do Harness passaram. Chromium headless confirmou que um SVG com retângulo é renderizado dentro de iframe sandbox com CSP. Gate completo Backend: 160 passaram e 6 falharam na última execução integral; os três testes novos de rejeição de markup passaram depois no recorte focado em expectativas antigas de estimativa/completude/progresso; gate completo Frontend: 134 passaram e 2 falharam em navegação/histórico lateral, falhas já registradas antes desta tarefa. Não declarar gates completos como aprovados.

## Autenticação SULTS

- O formulário envia usuário/senha para `POST /api/v1/autenticacao/login`; a porta `PortaAutenticacaoCorporativa` usa o adapter `autenticacao_sults.py` com a biblioteca interna copiada do Faturas. O adapter confirma o login no tenant HTTPS fixo, descarta tokens do ERP e a Iara emite cookie HttpOnly próprio, CSRF e UUID pseudônimo. O Docker inclui a biblioteca e suas dependências.
- A rota segue fechada por padrão e requer `IARA_AUTH_IDENTITY_KEY` e `IARA_CORPORATE_AUTH_ENABLED=true` fora de development. O Backend limita oito tentativas por login em quinze minutos no SQLite compartilhado. O fluxo sintético de `localhost` e `?login=teste` continuam sem validar SULTS ou acessar conversas corporativas.
- Verificação em 16/10: 30 testes focados de autenticação, isolamento e conversas passaram; Ruff e Harness passaram; build Docker e import da biblioteca na imagem passaram. O gate completo Backend teve 173 testes aprovados e seis falhas anteriores em expectativas do Model Gateway, sem relação com autenticação. Próximo passo: homologação real com conta autorizada, confirmar identidade imutável no ERP e proteção de tentativas por origem na borda com DevOps.
- Opções e decisões ainda abertas: `harness/context/autenticacao-sults.md`.

## Frentes em andamento

- O adapter usa `ChatOpenAI` do pacote `langchain-openai` como cliente compatível com Chat Completions. O host chamado é somente `IARA_BASE_URL`; não é a plataforma OpenAI.
- A credencial correta é `IARA_API_KEY`, mantida somente no Backend. `IARA_DEFAULT_KEY` não faz parte do contrato de configuração. O `.env` real permanece ignorado pelo Git e seus valores não devem aparecer em logs ou documentação.
- O catálogo mantém o alias `principal` e resolve o ID fixo `iara-grafana`.
- A chamada segue `temperature=None`, `use_responses_api=False`, `stream_usage=False`, timeout SDK de 360 segundos e `max_retries=0`.
- O endpoint atual rejeita `tools`, `tool_choice` e `parallel_tool_calls`; o fluxo ativo envia até 39 mensagens anteriores e a solicitação atual diretamente, sem SystemMessage, sem pré-processamento LLM e sem campos de tool calling.
- Uma chamada básica e uma chamada completa com o contrato da Iara foram aceitas em 15/10/2026. A resposta completa levou cerca de 77 segundos, então o prazo da aplicação passou de 40 para 120 segundos por padrão, configurável entre 1 e 360.
- Durante a espera, o Backend publica “A Iara continua preparando a resposta” a cada 15 segundos sem consumir uma nova chamada ou tokens adicionais.
- Em 16/10 foi corrigida uma falha de fronteira: JSON enviado pelo modelo sem o delimitador interno era interpretado como texto e podia sair em `texto.delta`. O Backend agora bloqueia objetos/arrays serializados antes de persistir/publicar; KPIs numéricos validados viram gráficos antes de `bloco.pronto`; o Frontend oculta JSON legado já persistido.

## JSON público e KPIs em gráficos — 16/10/2026

- A saída em texto aceita somente prosa Markdown. O Gateway aceita blocos tipados após `@@IARA_BLOCOS@@` e normaliza o fence `iara-visual` v2 observado no endpoint dedicado em `chart` validado. JSON arbitrário e HTML solto em `text` continuam bloqueados.
- Em 16/10/2026, os pedidos reais de vendas e pizza retornaram Markdown e `iara-visual`, sem HTML/SVG. A pizza foi emitida em `bloco.pronto` e persistida como `chart/pie`; o caminho HTML v2 passou em testes sintéticos, mas depende de amostra real do serviço/MCP para aceite ponta a ponta.
- O contrato v1 continua compatível, mas o Backend converte `kpi` e `kpi_group` numéricos validados em um ou mais `chart`. Grupos com unidades/moedas diferentes são separados para não comparar escalas incompatíveis; KPIs textuais não viram gráfico.
- `TextoMarkdown` protege o histórico: se encontrar uma serialização JSON antiga em texto, mostra aviso seguro e não o conteúdo bruto.
- System Prompt suspenso; versões anteriores arquivadas em `Backend/app/prompts/system_prompts.md`. HTML/SVG estático exige bloco `html` v2, allowlist no Backend, iframe sandbox com CSP e resumo acessível. HTML solto, origem técnica e payload bruto continuam bloqueados.
- Verificação focada: cinco testes do Backend passaram (bloqueio de JSON bruto, KPI individual/grupo em gráficos, fluxo SSE e renderizações sintéticas); `TextoMarkdown` passou com cinco casos. `scripts/harness.ps1 -Target harness` passou.
- Gates completos: Backend — Ruff passou; 146 testes passaram, 6 falharam e cobertura total foi 86,64%. As falhas restantes são expectativas de teste antigas sobre estimativas, avisos de completude e textos de progresso, em desacordo com decisões recentes e alterações que já estavam no código. Frontend — lint e TypeScript passaram; 128 testes passaram e 2 falharam em seleção de conversa e classe de layout, fora do componente Markdown desta correção. O teste focado de Markdown passou.

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
