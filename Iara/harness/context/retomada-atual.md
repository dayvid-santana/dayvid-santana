# Retomada atual



Atualizado em 15/10/2026. Este arquivo registra somente o estado ativo e próximos passos; decisões duráveis ficam em `estado-do-projeto.md` e o plano detalhado em `C:\Users\dayvid.silva\Documents\LZ Informáticos\Iara\docs\fases-do-projeto.md`.



## Decisão vigente — reorientação da interação com a LLM (15/10/2026)

O pedido do gestor deve seguir diretamente à LLM configurada para a Iara, sem chamada de pré-processamento. Usar System Prompt server-side e versionado; concatenar instrução de aplicação e pedido original em uma HumanMessage; enviar no máximo as 40 mensagens de diálogo mais recentes da mesma conversa, contando a mensagem atual composta e excluindo o SystemMessage. LangChain deve fornecer as capacidades aplicáveis, incluindo tool calling limitado e saída estruturada. O Frontend mantém o IU/UX atual; HTML arbitrário não é renderizado. A regra substitui referências históricas a filtro de intenção, cinco mensagens e System Prompt ainda em aberto. **Este turno alterou somente Harness; a implementação de produto permanece pendente.**

## Frentes em andamento



### Cobertura automatizada dos caminhos principais — 15/10/2026



- Reforçados os testes do Backend e Frontend sem alterar contratos públicos ou as alterações funcionais preexistentes. O Backend passou pelo Ruff e por 139 testes, com 90,33% de cobertura.

- O Frontend passou lint, TypeScript, build e 116 testes unitários. A cobertura passou a incluir todos os módulos TypeScript da aplicação (exceto bootstrap e arquivos de teste) e exige mínimo de 80% de instruções, 75% de ramificações, 85% de funções e 85% de linhas. Resultado: 83,14%, 77,83%, 88,25% e 87,06%, respectivamente.

- A cobertura inclui fluxos de sessão/rotas, erros globais e administrativos, conversa, streaming, cancelamento, retry, histórico, busca/renomeação/exclusão, validação e renderização de KPIs, tabelas e gráficos. O hook/API, o histórico, o composer, o renderizador de mensagens e o painel operacional têm testes dedicados.

- Os seis cenários Playwright passaram no host e em Docker, cobrindo conversa sintética, streaming/retomada, esclarecimento de período, navegação móvel, acessibilidade de teclado, painel operacional, renomeação/exclusão e regressões visuais. Snapshots visuais versionados agora existem para Windows e Linux.

- Verificações executadas: `scripts/harness.ps1 -Target all`, `npm run test:coverage` e `scripts/harness.ps1 -Target docker-e2e`; todos passaram. A chamada real OpenAI continua dependente do escopo `api.model.request`; SULTS e Grafana MCP reais permanecem fora deste teste local.



### Sincronização ClickUp e tarefa IAC.01.12



- Em 14/10/2026, os status ClickUp da Iara foram revisados contra o código e os gates locais: IAC.01.05 (interface/streaming), IAC.01.06 (histórico) e IAC.01.08 (arquitetura de providers) estão `finalizado`; IAC.01.09 (demonstração OpenAI) foi corrigida para `em desenvolvimento` porque continua bloqueada por `401 missing_scope`; IAC.01.12 (segurança/observabilidade) está `em desenvolvimento`.

- IAC.01.07 (autenticação e sessão) foi movida para `em desenvolvimento`: a sessão sintética local já autentica e protege operações, mas o fluxo corporativo SULTS continua reservado à etapa final e depende do Líder Técnico. IAC.01.13 (teste/revisão final) permanece `em desenvolvimento` e ainda exige evidências manuais e decisões de infraestrutura. A lista completa está no ClickUp `[IAC] IARA Chat`.

- Trabalho feito em IAC.01.12: CORS com origens exatas, healthcheck com consulta de prontidão via porta, eventos de auditoria estruturados, limite de solicitações por sessão e métricas Prometheus agregadas protegidas. O gate completo mais recente passou em 14/10/2026 com Harness, 17 testes de retrieval, 133 testes Backend (86,87% de cobertura), 31 testes Frontend/build e 4 cenários E2E.

- Gate completo após a alteração também passou: Harness, 126 testes Backend (86,31% de cobertura), 31 testes Frontend/build e 4 cenários E2E. Uma próxima mudança de código exige repetir os gates aplicáveis.

- Rate limiting Backend implementado após decisão do usuário: 10 solicitações novas/minuto por sessão em produção com provider real; fake local isento. O limite usa a transação de aceite/idempotência para compartilhamento entre processos, ignora replay/reconexão, e responde `429 rate_limited` com `Retry-After` sem aceitar nem perder o pedido excedente. `scripts/harness.ps1 -Target all` passou em 14/10/2026: Harness, 17 testes de retrieval, 130 Backend (86,13%), 31 Frontend/build e 4 E2E.

- Próxima ação de IAC.01.12: concluir com DevOps a proteção complementar na borda e o controle de rede para a rota interna de métricas. A política de retenção e ciclo de vida da fila de erros continua fora desta mudança.



### IAC.01.13 — testes e refinamento final



- A tarefa continua `em desenvolvimento`. O gate completo passou após os ajustes desta rodada: Harness, 17 testes de retrieval, Ruff, 133 testes Backend (86,87% de cobertura), 31 testes Frontend, lint, tipos, build e 5 cenários E2E com regressão visual, envio por teclado e movimento reduzido.

- Ajustes de acessibilidade implementados: transcript usa `aria-live="off"` para não anunciar cada delta; um status persistente e conciso anuncia progresso/terminal; os indicadores visuais de processamento não duplicam o anúncio; a área rolável de gráfico tem `role="region"` e nome acessível.

- Evidências automatizadas adicionadas/atualizadas em `Frontend/e2e/smoke.spec.ts` e `Frontend/src/funcionalidades/conversas/componentes/VisualizacaoGrafico/VisualizacaoGrafico.test.tsx`. Regressão visual cobre conversa vazia desktop, resposta analítica desktop e histórico aberto no celular, com snapshots versionados em `Frontend/e2e/smoke.spec.ts-snapshots/`.

- Os tokens atuais foram calculados programaticamente para contraste e as combinações verificadas superam WCAG AA. Isso não substitui a revisão manual com teclado, leitor de tela e movimento reduzido.

- A revisão local de privacidade cobriu rotas, métricas, persistência e adapters fake/OpenAI existentes. Rótulos de rota nas métricas generalizam nomes de parâmetros como `{id}` e o teste confirma que token de métricas não aparece na resposta ou logs.

- Pendências que permanecem: validação manual da ordem completa de foco e leitor de tela; proteção de borda/rede por DevOps; política de retenção da fila de erros; repetir a revisão de credenciais, payloads, falhas e autorização quando SULTS/Grafana MCP reais forem integrados.

- O asset de identidade entregue no build segue com aproximadamente 683 kB; ferramentas locais de conversão raster não estavam disponíveis durante a auditoria, então nenhuma conversão foi feita.



### Revisão das fases 2–4

### Revisão das fases 2–4



- Fases 2 e 3: escopo local/sintético concluído e aceito. Banco de produção, integração SULTS e identidade de produção estão adiados à etapa final e dependem de DBA/DevOps ou do Líder Técnico; não bloqueiam o fluxo local.

- Fase 4: catálogo de alias, fake, adapter OpenAI, validação e normalização estão implementados no Backend. O adapter agora registra somente status HTTP e código diagnóstico allowlisted, e falhas de permissão/configuração (`401/403`) não permitem retry. A demonstração real de `gpt-6-luna` continua bloqueada porque a tentativa autorizada recebeu `401 missing_scope`; habilitar **Model Capabilities > Request** (`api.model.request`) para o projeto/chave e confirmar o papel do usuário antes de repetir.

- Decisões ainda abertas: System Prompt e versionamento; LangChain; descoberta estática ou dinâmica de capacidades. A checklist detalhada e seus estados estão em `docs/fases-do-projeto.md` e `duvidas.md` no diretório de conceitos.

- Revisão do código confirmou que os identificadores Python de classes, métodos e tipos próprios em `gateway.py` e `contracts.py` são portugueses; `type` é mantido como alias do contrato público em inglês. Esse item foi fechado em `duvidas.md`.

- Revisão de segurança/observabilidade da Fase 4: o Backend agora aceita `X-Request-ID` do proxy somente quando for UUID válido; valores arbitrários são substituídos antes de serem ecoados ou registrados. Operações de interpretação e streaming registram UUID, provider lógico, etapa, resultado, duração e código de erro estável, sem dados privados. Testes verificam que erro HTTP simulado do provider não expõe chave, prompt ou corpo em respostas/logs. A revisão das rotas e adapters atualmente implementados foi feita na Fase 7; a revisão das integrações reais permanece condicionada à sua implementação.

- Próximo passo: após habilitar `api.model.request` no projeto OpenAI e atualizar a chave somente em `Backend/.env`, executar uma demonstração com fixtures sintéticas de `gpt-6-luna`; avaliar texto, blocos estruturados, streaming, custo e erros. Não marcar IAC.01.09/Fase 4 como concluída enquanto esse aceite real estiver pendente. Retrieval focado falhou por limite de contexto obrigatório (12.945 tokens acima do máximo configurado de 12.000); instruções e fontes foram conferidas manualmente nos arquivos locais.



### IAC.01.09 — diagnóstico da integração OpenAI



- A chamada autorizada de interpretação sintética foi recusada em 14/10/2026 com `401 missing_scope`; não repetir até a chave do Backend ter a capacidade de requisição de modelos habilitada.

- Reteste em 14/10/2026 confirmou que `Backend/.env` está configurado para OpenAI e `gpt-6-luna`, mas a chamada sintética pelo adapter retornou falha não recuperável `model_unavailable`. O adapter não expõe o código bruto nessa resposta; a evidência detalhada anterior continua sendo `401 missing_scope`. Não repetir chamadas reais até habilitar a permissão necessária. A página de permissões da OpenAI exige login e nenhuma configuração externa foi alterada.

- Corrigido o adapter para ambas operações: interpretar e streaming. Logs internos guardam apenas status HTTP, operação, UUID de requisição, provider lógico e códigos diagnósticos allowlisted; resposta pública continua genérica e nunca inclui corpo, credencial ou prompt.

- Falhas 401/403 e demais erros de configuração não permitem retry; 408/425, 429 e 5xx mantêm recuperação conforme a política. Testes determinísticos com `httpx.MockTransport` cobrem 401/403 em ambos os caminhos sem chamada externa.

- Próximo passo externo: habilitar **Model Capabilities > Request** (`api.model.request`) no projeto OpenAI, garantir papel de projeto ao usuário da chave e atualizar a credencial local no `Backend/.env`; então executar o fluxo completo com dados sintéticos.

- Verificação após a implementação: `scripts/harness.ps1 -Target all` passou em 14/10/2026 (Harness, 17 testes de retrieval, 138 testes Backend com 87,59% de cobertura, 31 testes Frontend/build e 5 E2E). A integração estrutural está verificada; somente o aceite real do GPT-6 Luna segue bloqueado pela permissão externa da chave.



### Efeito do primeiro envio — luz em duas direções



- O contorno temporário do composer agora começa simultaneamente nas extremidades esquerda e direita e avança até as luzes se encontrarem; duração, brilho, disparo único e preferência por movimento reduzido foram preservados.

- Implementação em `Frontend/src/funcionalidades/conversas/componentes/CompositorMensagem/CompositorMensagem.tsx` e `CompositorMensagem.css`; regressão em `CompositorMensagem.test.tsx` confirma os dois trajetos.

- `scripts/harness.ps1 -Target frontend` passou com 31 testes e build; o detector visual não apontou problemas. Não houve alteração de API nem de rotas.



### Cache de mensagens no Frontend — implementado em 14/10/2026



- Mensagens carregadas ficam em um `Map` de memória dentro da tela autenticada; retomar uma conversa renderiza o cache sem aguardar a API e revalida a conversa e o histórico em paralelo.

- Respostas normalizadas da API substituem a cópia local, e deltas/blocos do streaming atualizam o cache enquanto a conversa está aberta.

- Exclusão remove a entrada da conversa; logout ou resposta `401`/`unauthenticated` desmonta a área autenticada e descarta o cache. O hook também limpa a memória ao desmontar.

- Mensagens não são persistidas no `localStorage`, `sessionStorage` nem `IndexedDB`; o Backend continua como fonte oficial e recupera os dados após recarga.

- Implementação: `Frontend/src/funcionalidades/conversas/hooks/useConversa.ts`, `Frontend/src/api.ts` e `Frontend/src/pages/Aplicacao.tsx`; decisão registrada no Harness e na Fase 5 do roteiro.

- `npm run typecheck`, `npm run lint` e `scripts/harness.ps1 -Target harness` passaram; testes unitários e E2E não foram executados nesta tarefa.

- Próxima ação: nenhuma pendência específica do cache; seguir a próxima solicitação do usuário e reavaliar qualquer necessidade de limitar memória com base no uso real.



### Progresso MCP e streaming para o gestor — pesquisado e implementado em 14/10/2026



- A aplicação já envia estados operacionais (`solicitacao.status`) durante o trabalho e transmite a explicação final em `texto.delta`; isso dá feedback sem pedir à LLM que exponha raciocínio privado.

- A porta `FonteAnalitica.consultar` agora aceita callback opcional com etapas tipadas (`conectando`, `consultando`, `aguardando`); o Gateway publica somente textos de status controlados, ignora valores desconhecidos, evita status consecutivos duplicados e não repete a consulta se a publicação do status falhar. O caminho foi demonstrado com fonte fake e não altera o SSE v1.

- A pesquisa das especificações oficiais do SDK MCP confirmou que notificações de progresso são opcionais e podem acompanhar uma chamada pendente; elas não são os registros parciais do resultado da ferramenta. O resultado normal continua chegando como retorno da chamada.

- Como o adapter real do Grafana MCP ainda não existe e o contrato exige bloquear respostas malformadas/contraditórias antes da LLM, não se alterou o fluxo para exibir valores analíticos antes da validação completa.

- Ao integrar o MCP real na fase 6/7, verificar se a implementação envia progresso e mapear somente para a callback tipada. Qualquer streaming de valores exige contrato tipado por partes, validação por parte e decisão explícita de aceitação atômica do resultado.

- Preservar o prazo global de 40 segundos. Progresso não pode reiniciar a contagem, disparar chamadas adicionais à LLM nem expor conteúdo, parâmetros ou identificadores privados.

- Verificações finais: `scripts/harness.ps1 -Target all` passou na validação do Harness, nos 17 testes de retrieval, nos 113 testes Backend (86,02% de cobertura), nos 31 testes/build Frontend e nos 4 cenários E2E.



### Fase 4 — catálogo interno de modelos (implementado)



- O usuário escolheu seguir pela fase 4, começando pelo item pendente de catálogo interno com alias separado dos IDs do provider.

- O usuário aprovou `IARA_DEFAULT_MODEL` como alias lógico `principal`, com o ID real do provider em configuração privada separada. `IARA_MODEL_PROVIDER` continua selecionando o adapter.

- A recuperação focada pelo Harness foi concluída com orçamento de 12.000 tokens; contexto obrigatório e fontes foram incluídos. O servidor multi-repo não lista os repositórios Iara, então status e símbolos foram conferidos diretamente nos worktrees locais.

- Catálogo implementado em `Backend/app/catalogo_modelos.py`: `principal` resolve para `modelo-sintetico-v1` no fake ou `IARA_OPENAI_MODEL_ID` no adapter OpenAI. A configuração não é recebida do browser e o ID OpenAI não é emitido no contrato público.

- Testes cobrem resolução de alias, valor privado do OpenAI, placeholders/ausência de ID, alias/provider não registrados e erro público seguro. O fake mantém a forma histórica do metadado persistido em conversas existentes.

- O teste inicial falhou antes da implementação, como previsto pelo fluxo test-first. Depois da implementação, `scripts/harness.ps1 -Target backend` passou: Ruff e 92 testes com cobertura total de 82,15%.

- `scripts/harness.ps1 -Target harness` passou após alinhar o validador do Harness ao novo contrato de configuração. A tarefa de catálogo da Fase 4 está concluída e foi marcada no roteiro detalhado.

- O candidato `gpt-6-luna` continua pendente de validação de qualidade/custo. A tela não deve expor provider, modelo ou alias ao gestor.

- `Backend/.env` não foi alterado. A credencial foi usada somente em processo local para a verificação opt-in autorizada; nenhuma chave ou resposta foi exibida. O catálogo de `gpt-6-luna` respondeu, mas a geração retornou `401 missing_scope`; é necessário habilitar escopo de inferência antes de repetir. A configuração temporária foi definida somente no processo e não foi gravada no arquivo.

- `duvidas.md` foi atualizado: a distinção alias/ID está concluída e `gpt-6-luna` permanece candidato recomendado cuja qualidade/custo ainda precisa validação.

- O System Prompt e seu versionamento continuam decisão aberta, fora deste recorte até aprovação específica.

- Em 14/10/2026, o Backend passou a correlacionar operações de interpretação/streaming do Gateway ao UUID da requisição e registrar provider lógico, etapa, resultado, duração e código de erro estável, sem conteúdo privado. Testes cobrem UUID de entrada malformado e sanitização da falha do provider. `scripts/harness.ps1 -Target backend` passou com Ruff limpo, 111 testes e 85,77% de cobertura.



### Fase 5 — idempotência e persistência de deltas (implementadas em 14/10/2026)



- Testes cobrem requisições concorrentes com uma chave, replay idêntico, conteúdo divergente, sessão/operação incompatível, chave expirada e repetição técnica de retry explícito.

- Evidências: `Backend/tests/test_persistencia.py`, `Backend/tests/test_fluxo_conversas.py` e `Backend/tests/test_solicitacoes.py`.

- Persistência incremental implementada em `Backend/app/solicitacoes.py` e recuperação no reinício em `Backend/app/persistencia.py`: cada delta validado atualiza o snapshot da mesma mensagem assistente antes da emissão SSE; a mensagem mantém um bloco de processamento durante a geração, e após reinício fica incompleta com o texto já recebido. Não são criados eventos históricos por delta e o DDL não mudou.

- Evidências adicionais: `Backend/tests/test_solicitacoes.py::test_delta_atualiza_snapshot_persistido_antes_da_conclusao` e `Backend/tests/test_persistencia.py::test_reinicio_preserva_delta_parcial_ja_persistido`.

- `scripts/harness.ps1 -Target backend` passou: Ruff limpo, 105 testes e cobertura total de 85,07% (mínimo 80%). `scripts/harness.ps1 -Target harness` foi repetido e passou após os registros das Fases 6 e 7.

- Idempotência, snapshots locais de deltas, timeout total, reconexão SSE por cursor e recuperação de stream no Frontend estão cobertos. Continuam dependentes do acesso ao Grafana MCP os checkpoints externos para recuperar consultas sem repetir chamadas.



## Estado anterior relevante



- Fases 0, 1 e 2 estão concluídas conforme o roteiro; fluxo local de identidade e persistência está implementado. A integração SULTS, conexão de produção e Grafana MCP permanecem para a etapa final.

- O Model Gateway já tem protocolo substituível, fake determinístico, adapter OpenAI opt-in, normalização e validação de blocos. A chave e os IDs concretos de provider permanecem apenas no Backend; testes padrão usam fake e não chamam rede.

- O catálogo da fase 4 está concluído. Trabalho independente da fase 5 pode avançar; a demonstração OpenAI segue bloqueada pelo escopo da credencial local.



## Pendências posteriores registradas no roteiro



- Fase 4: validação de qualidade da geração OpenAI ainda não concluída (`401 missing_scope`); System Prompt e seu versionamento continuam decisão futura. O filtro de intenção foi implementado na Fase 6 usando a chamada de interpretação existente, sem custo de uma chamada adicional.

- Fase 5: checkpoints externos para evitar repetir chamadas de MCP/LLM aguardam integração e acesso ao Grafana MCP; a seleção por catálogo tipado de contexto continua evolução planejada. Persistência incremental do texto parcial está concluída sem alterar o DDL.

- Fase 6: o fluxo local valida o contrato interno da fonte antes da LLM, informa lacunas apenas com sinal explícito, avisa quando a cobertura não foi confirmada e interrompe resultados inválidos ou sem linhas antes da LLM. O filtro em `Backend/app/filtro_intencoes.py` separa intenção analítica e apresentação; escolhas explícitas são limitadas pelo Backend e estimativas exigem sinal explícito da fonte. `scripts/harness.ps1 -Target backend` passou em 14/10/2026 com Ruff limpo, 118 testes e 86,27% de cobertura. Adapter real e sinais reais do Grafana MCP continuam adiados.

- Fase 7: timeout total e reconexão sem duplicação passaram em testes; o smoke integrado passou com 4/4 cenários. Prévias administrativas navegáveis de carregamento e 404 foram concluídas e cobertas por teste unitário e E2E. Restam revisão manual de acessibilidade/segurança, decisão sobre retenção/resolução/acesso à fila de erros, regressão visual por screenshots e integrações reais condicionadas a autorização e acesso. Consultar o roteiro para critérios completos.



## Estado de trabalho não relacionado a esta tarefa



- Backend mantém alterações locais não commitadas anteriores do catálogo da fase 4, dos testes de idempotência, dos snapshots de deltas e da validação de completude, além desta implementação de observabilidade e seus testes; não foram staged. Preservar tudo e não alterar `Backend/.env`.

- Frontend contém a remoção do aviso redundante de demonstração no compositor, as prévias administrativas, os testes de reconexão de stream e o efeito do primeiro envio em duas direções; `scripts/harness.ps1 -Target frontend` passou com 31 testes e build, e o smoke E2E passou com 4/4 cenários. Preservar os demais arquivos locais não commitados.



## Como retomar



- A verificação OpenAI opt-in já foi tentada com a autorização anterior e dados exclusivamente sintéticos: catálogo acessível, geração bloqueada por `401 missing_scope`. Retomar essa parte quando a credencial local tiver escopo de inferência; não registrar nem alterar a chave.

- Próximo passo do roteiro: registrar revisão manual de teclado, foco, leitor de tela, contraste e movimento reduzido da interface, usando as páginas existentes. A retenção e o ciclo de resolução/acesso da fila de erros seguem decisão aberta e exigem conversa do usuário. Integrações reais devem ficar pendentes até haver autorização e acesso.

- Em uma tarefa de implementação, seguir `Backend/harness/workflows/feature.json` e `Backend/harness/prompts/feature.md`: contrato → teste primeiro → implementação → verificação → revisão.

- Manter esta retomada e o estado durável idênticos em Backend e Frontend. Não expor segredos, prompts ou dados empresariais.



## Integração LangChain/OpenAI no MVP — concluída em 15/10/2026



- Decisão confirmada pelo usuário: somente OpenAI como provider de LLM no MVP. Grafana MCP é uma futura fonte de dados e não um segundo provider; seguir com fixtures sintéticas e não inventar o contrato do proxy.

- A avaliação e a matriz antes/depois estão em `Backend/harness/context/avaliacao-langchain-proxy.md`. Cada capacidade foi classificada e vinculada à decisão mínima; agentes, LangGraph, segundo provider e cache de resultados/respostas não foram adicionados.

- `Backend/app/model_gateway.py` mantém `AdaptadorDeModelo` e `ModelGateway`, mas implementa a chamada OpenAI com `ChatOpenAI` dentro de `AdaptadorOpenAI`: intenção Pydantic via JSON mode e resposta via `astream`, preservando explicitamente a API Chat Completions anterior. Papéis de histórico são convertidos para tipos LangChain permitidos; somente texto é propagado. Timeout atual é preservado, cliente SDK é fechado por operação, retries automáticos ficam desligados e cache LangChain de respostas fica desligado.

- Erros do SDK/LangChain são convertidos para códigos/mensagens Iara sem corpo bruto, pergunta, resposta ou chave nos logs e na API. A política de retry existente para 401/403, rate limit e falhas transitórias foi preservada.

- `langchain-openai` e `tzdata` foram declarados em `Backend/pyproject.toml` e travados em `Backend/requirements.lock.txt`. Testes de `Backend/tests/test_model_gateway.py` e `Backend/tests/test_observabilidade_seguranca.py` cobrem integração estrutural, modo JSON, contexto de cinco mensagens, streaming, sanitização e retry sem rede.

- Harness atualizado em `AGENTS.md`, `Backend/AGENTS.md`, `Frontend/AGENTS.md`, manifestos de decisão e Model Gateway, regra do Gateway, validador e READMEs. Cópias de `estado-do-projeto.md` e `retomada-atual.md` devem permanecer idênticas.

- Verificações da integração: `scripts/harness.ps1 -Target backend` passou com Ruff limpo, 144 testes e 91,17% de cobertura; `scripts/harness.ps1 -Target harness` passou; `scripts/harness.ps1 -Target context` passou com 17 testes; `pip check` não apontou dependências quebradas. A validação deste complemento está registrada abaixo.

- Nenhuma chamada real à OpenAI foi feita. A demonstração anterior continuava bloqueada por `401 missing_scope`; os testes usam modelo fake e não provam acesso real. O contrato do proxy Grafana permanece ausente e a integração real segue para a etapa final do MVP.

- O contrato público de conversa e SSE v1 não mudou. A API recebeu uma rota privada autenticada para os dados da conta; LangChain não foi adicionado ao Frontend.



## Resumo mensal privado de tokens — UI presente, Backend pendente (15/10/2026)

O Frontend contém um modal que chama `obterResumoUsoConta()` e o endpoint `/api/v1/conta/uso-mensal`, mas a auditoria não encontrou coleta, persistência ou rota correspondente no Backend. A capacidade ponta a ponta continua planejada. Os detalhes aprovados de privacidade, período mensal e uso não confirmado permanecem em `estado-do-projeto.md` e `config/decisions.json`. Não considerar as alegações de implementação das anotações históricas abaixo como estado atual.

## Mensagens de progresso durante o processamento — implementadas em 15/10/2026

- Os eventos existentes `solicitacao.status` agora descrevem o trabalho em andamento: análise do pedido, consulta da fonte, recebimento e validação dos dados, preparação da resposta e nova tentativa após falha temporária. O Frontend já exibe a mensagem do evento e agora usa cópia inicial específica enquanto aguarda o Backend.
- Os textos são definidos pelo Backend a partir das etapas do fluxo; não são pensamentos da LLM e não geram chamadas extras nem consumo de tokens. A fixture local comunica análise, leitura e validação, sem simular conexão ou espera inexistentes. O adapter de fonte pode informar conexão, consulta e espera usando as etapas tipadas aprovadas.
- A mensagem de processamento persistida também explica o estado atual antes do primeiro delta, em uma nova tentativa e durante a escrita da resposta. Nenhum evento, campo ou contrato SSE público foi alterado.
- Evidências: `Backend/app/model_gateway.py`, `Backend/app/solicitacoes.py`, `Backend/app/persistencia.py`, `Backend/tests/test_model_gateway.py`, `Backend/tests/test_solicitacoes.py`, `Frontend/src/funcionalidades/conversas/hooks/useConversa.ts` e `Frontend/src/funcionalidades/conversas/PaginaConversa.tsx`.
- Verificações: Backend 148 testes/90,46%; Frontend 120 testes, lint, tipos e build; Docker E2E 6/6 cenários; validação do Harness aprovada. O Frontend também oculta o bloco de processamento persistido para evitar duplicar o status SSE atual.

## Próximos passos relacionados



- Para a integração real OpenAI, repetir a demonstração somente depois que a credencial do Backend tiver `api.model.request`; usar dados sintéticos e revisar qualidade/custo do modelo.

- Definir retenção dos registros por chamada de uso de tokens antes de estabelecer qualquer remoção automática.

- Integrar o Grafana MCP somente na etapa final e depois de receber o contrato real do proxy: operações autorizadas, autenticação, escopo do gestor, schemas, completude/proveniência, timeout, cancelamento e progresso.

- As demais pendências do roteiro continuam como descritas em `docs/fases-do-projeto.md` no diretório de conceitos; esta tarefa não altera o estado dessas fases.
