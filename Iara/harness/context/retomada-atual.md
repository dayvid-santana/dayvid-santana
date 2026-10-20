# Retomada atual

Atualizado em 20/10/2026. O provider LLM segue sendo a API dedicada da Iara via Model Gateway. A API de dados é uma integração HTTP distinta. O usuário confirmou uma amostra real do corpo retornado: Markdown com um bloco `iara-visual` contendo JSON v2 e gráfico `pie`; a amostra não define todos os formatos.

## Canal de raciocínio do provider — implementado em 20/10/2026

- O Monitor captura `choices[0].delta.reasoning_content` separado de `delta.content`; a Iara replica esse comportamento na integração LangChain com um conversor `ChatIara` que preserva apenas o campo dedicado.
- O Backend publica `raciocinio.delta` no schema SSE v2. O Frontend acumula esses trechos dentro da própria faixa visual de processamento; enquanto não há reasoning, a faixa mostra o status operacional. O texto permanece somente no estado volátil da tela, sem spinner após a conclusão.
- O canal não é mesclado à resposta Markdown nem salvo em mensagens, cache, logs ou contexto futuro. A janela em memória de replay SSE permite retomar somente enquanto o processo ainda mantém os eventos da solicitação.
- As verificações de implementação ainda precisam ser executadas antes de declarar os gates concluídos.

## Investigação de timeout — atualização 20/10/2026

Quatro falhas de 19/10 ocorreram cerca de 120 segundos após o aceite, confirmando o prazo total do Backend. A correção de observabilidade foi aplicada sem alterar esse limite: o log HTTP agora dura até o fim do corpo SSE; os loggers operacionais escrevem `INFO` visível em Docker; Gateway distingue timeout do provider, falha de conexão e prazo do Backend; e registra primeiro evento, primeiro texto, primeiro delta público, conclusão/cancelamento sem conteúdo privado.

Uma reprodução sintética pelo provider real concluiu: primeiro evento 140 ms, primeiro texto do provider 1.908 ms, primeiro delta público 2.098 ms, conclusão 2.111 ms e SSE completo 2.128 ms. Não reproduziu timeout. As quatro falhas antigas continuam sem causa interna retrospectiva porque os marcos não existiam à época; uma nova ocorrência será localizável pelos novos registros. Backend: `scripts/harness.ps1 -Target backend` passou com Ruff, 183 testes e 85,89% de cobertura. Evidências e procedimento estão em [`timeout-e-latencia.md`](timeout-e-latencia.md).

## Estado atual do renderer ativo — 19/10/2026

- A decisão registrada no histórico foi implementada como uma origem/serviço separado para `api_html`. O renderer armazena e serve exatamente a string HTML recebida, sem reescrever URLs nem injetar código. Scripts inline recebem hashes CSP; somente a URL versionada externa ECharts observada na amostra é autorizada. CSS inline permanece permitido; conexões, imagens, fontes, workers, frames aninhados, formulários, pop-ups e downloads ficam bloqueados; o iframe não pode ler a Iara nem navegar a janela superior.
- CSP envia diagnósticos efêmeros por diretiva/origem, sem HTML, query ou dados privados. A UI avisa sobre recursos bloqueados; o componente exclui o documento ao desmontar e o serviço aplica TTL de 15 minutos. Inventário e limites estão em `Frontend/renderizador-html/README.md`.
- Verificações desta revisão: renderer Node 7/7; Frontend unitários focados 20/20, lint, typecheck e build passaram; Chromium hermético do renderer 1/1 passou e o teste opcional de integração com ECharts real no jsDelivr passou 2/2 quando habilitado; audit do renderer encontrou 0 vulnerabilidades nas dependências instaladas. Backend `harness.ps1 -Target backend` passou com 179 testes e 85,52% de cobertura; Harness e retrieval/context passaram (17 testes). `harness.ps1 -Target docker-e2e` construiu e iniciou os serviços e o renderer passou, mas o smoke geral ficou 2/7: um snapshot variou 3% e quatro cenários não encontraram as respostas esperadas do provider fake. O `npm run check` completo ficou 138/140: falharam os testes antigos de seleção de conversa durante processamento e classe CSS do histórico. Esses cenários não alteram a evidência isolada do renderer e ficam para triagem própria. Não se afirma compatibilidade com qualquer HTML.

## Histórico: envelope HTML `iara-visuals` — 19/10/2026

- Na primeira implementação, o iframe usava sandbox sem scripts e os dashboards que dependiam de JavaScript apareciam vazios. Esse problema foi resolvido pelo renderer isolado descrito no início deste arquivo; a decisão de execução ativa foi limitada à amostra sintética inspecionada e não habilita compatibilidade irrestrita.
- A extração do envelope continua cobrindo a resposta atual do Model Gateway; não comprova integração HTTP direta com a API empresarial de dados. Essa integração permanece pendente e não deve ser descrita como concluída.
- Os números de testes e gates daquele diagnóstico são históricos. Use o bloco “Estado atual do renderer ativo” acima para o status e os resultados vigentes.

## Fluxo direto da LLM — filtro de intenções removido — 19/10/2026

- Removidos `Backend/app/filtro_intencoes.py`, seus testes, o callback de ferramenta e a consulta analítica que não eram usados pelo adapter ativo. O `ModelGateway` encaminha somente a pergunta original e até 39 mensagens anteriores; não há classificação, reescrita nem segunda chamada de modelo.
- O provider fake entrega sempre a mesma resposta com um gráfico sintético fixo, independente da pergunta, para manter a demonstração visual sem simular compreensão semântica. Ele não representa resposta da API real.
- O contrato de consulta e o adapter de fonte sintética permanecem como protótipos desconectados do fluxo atual; rastreabilidade de completude e progresso da fonte voltou para `planned`.
- Verificação: `scripts/harness.ps1 -Target backend` passou com Ruff, 174 testes e 85,40% de cobertura. `scripts/harness.ps1 -Target harness` passou. O Frontend não teve código alterado; nenhuma verificação visual foi necessária.

## API de dados: passthrough integral aprovado — 19/10/2026

- Decisão: encaminhar e persistir sem alterações o corpo original da API de dados, incluindo HTML e todo tipo de gráfico. Não filtrar, normalizar, converter, resumir, reconstruir nem descartar formatos desconhecidos.
- A apresentação isola HTML do DOM principal sem alterar o conteúdo. Scripts inline usam hashes CSP; a única URL externa autorizada é a dependência versionada inspecionada na amostra sintética. A política não promete compatibilidade universal.
- Implementação desta etapa: bloco público `api_html` v2 e evento `bloco.pronto` transportam a string HTML sem a allowlist da LLM. `VisualizacaoHtmlApiDados` envia o original ao serviço HTTP `renderizador-html`, numa origem separada, e exibe a URL opaca em iframe sandbox sem `allow-same-origin`; o serviço apaga o documento ao desmontar ou após TTL. O Backend persiste e reabre o HTML original em histórico v2.
- Estado ponta a ponta: o produtor da API de dados segue não integrado e endpoint, autenticação e contrato do corpo completo permanecem pendentes. A extração sintética após `iara-visuals`, transporte, persistência/retomada e renderização isolada dos recursos documentados foram testados; recursos não aprovados continuam bloqueados e diagnosticados. Não declarar a integração HTTP real como concluída.
- Verificações executadas nesta revisão: serviço renderer 7 testes Node; Frontend 20 testes unitários focados, Playwright Chromium E2E 1/1, lint, typecheck e build; Backend 25 testes de HTML, contratos e persistência; `npm audit --omit=dev` sem vulnerabilidades. A biblioteca ECharts externa real não é baixada no teste hermético: a URL aprovada é simulada com um script sintético no Chromium.
- O retorno chamado “Retorno Final” termina sem fechar o bloco de código; a variante “Retorno Parcial Preservado” contém o fechamento. O normalizador atual `Backend/app/normalizacao_visual_iara.py` pertence ao fluxo da LLM, exige o fence de fechamento, converte os dados para `chart` e descarta campos não previstos. Essa transformação explica a omissão do gráfico quando aplicada à amostra final e não deve ser usada na fronteira da API de dados.
- Bloqueio concreto: ainda falta endpoint, método/autenticação, content type, encoding, headers, contrato exaustivo, semântica de streaming, limites e dependências de scripts/recursos do HTML. O conteúdo empresarial real da amostra não será persistido em arquivos, testes, logs ou evidências.
- Próximo passo: projetar o adapter HTTP e o caminho de persistência/eventos da API de dados como carga opaca, usando fixture sintética equivalente para verificar que corpo e metadados necessários não são alterados; renderizadores podem interpretar formatos conhecidos à parte, sem substituir nem descartar o corpo original.
- Não registrar payload empresarial real em logs, fixtures, screenshots ou no Harness. Fixtures sintéticas permanecem o padrão de desenvolvimento e demonstração.

## Falhas observadas nos pedidos de gráficos — 19/10/2026

- Cinco pedidos separados passaram pelo endpoint público da Iara. O pedido de linha concluiu com bloco `chart` estruturado; barras e dispersão excederam o prazo da solicitação; pizza e área concluíram em texto sem bloco visual. O stream público não contém o corpo bruto do provider, então não permite afirmar se os dois últimos foram descritos ou se um visual foi rejeitado internamente.
- Na saída `iara-visual` da LLM, gráficos tipados continuam limitados a `line`, `bar` e `pie`. Gráficos `area` e `scatter` validados são reconstruídos como SVG estático no bloco HTML v2, com resumo acessível, cores explícitas preservadas e paleta colorida de fallback. O SVG é sanitizado e exibido pelo iframe isolado já existente; não se amplia o contrato tipado.
- Removidos o filtro de intenções e o caminho legado de consulta/ferramenta no Backend. A interface de adapter aceita somente pergunta e contexto aprovado; o provider fake emite uma resposta fixa de simulação. Os testes correspondentes exercitam a interação direta.
- A validação de HTML/SVG agora aceita apenas opacidade `fill-opacity` no intervalo 0–1 e alinhamento `text-anchor` entre `start`, `middle` e `end`. Erros de normalização visual registram motivo estático sanitizado e ID de correlação, sem conteúdo da resposta.
- A API de dados real segue sem integração: endpoint, autenticação e contrato ainda faltam. A regra de passthrough byte a byte permanece inalterada e não pode ser testada pela chamada LLM atual. Não registrar respostas externas nem presumir que o retorno remoto corresponde à fixture local.
- Verificação focada: Ruff passou; 13 testes Backend e 44 testes Frontend passaram. As suítes completas reportam 6 falhas Backend em testes do fluxo de fonte analítica legado e 2 falhas Frontend em teste de troca de chat e expectativa antiga de classe CSS. O smoke E2E passou em 3/6: dois snapshots tiveram cerca de 3% de diferença e um fluxo de contexto sintético não encontrou o título de bloco esperado. São falhas fora do renderer área/dispersão; investigar separadamente antes de declarar os gates gerais verdes.

As anotações posteriores abaixo registram checkpoints anteriores e são históricas; onde mencionarem Grafana MCP, validação/allowlist da resposta, conversão de gráficos ou HTML, prevalece a decisão de passthrough acima para a API de dados.

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
