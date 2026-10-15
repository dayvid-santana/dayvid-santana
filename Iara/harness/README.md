# Iara Agent Harness

Este diretorio define o processo recomendado de implementacao e revisao da Iara. Ele registra escopo, contratos, papeis, prompts, skills, ferramentas, gates e sequencias de trabalho para backend, frontend e mudancas full-stack.

## Estrutura

`Backend` e `Frontend` são repositórios Git independentes. As instruções e políticas que precisam acompanhar cada repositório ficam em seu `harness/` local; este `harness/` da raiz contém a camada de integração full-stack e verifica a sincronização entre os manifests locais.

- `config/project.json`: escopo do produto, contrato compartilhado e configuracao do Model Gateway.
- `roles/gestor-usuario.json`: persona sintética para avaliar a experiência da Iara como gestor, sem representar uma conta ou permissão real.
- `config/quality-gates.json`: verificacoes automatizadas e requisitos de seguranca/aceite.
- `config/commit-policy.json` e `COMMIT_GUIDE.md`: formato, momentos e limites para registrar checkpoints no historico Git.
- `config/decisions.json`: fonte de verdade para decisoes de produto, itens em aberto e excecoes de Rules aprovadas.
- `../Backend/harness/rules/` e `../Frontend/harness/rules/`: regras compartilhadas e específicas de cada repositório.
- `Backend/harness/rules/backend.documentation.md` e `Frontend/harness/rules/frontend.documentation.md`: documentação obrigatória do código em docstrings Google no Backend e TSDoc no Frontend, explicando uso, propósito e motivação.
- `config/model-gateway.json`: capacidades do Gateway, com status real e caminhos de evidencia.
- `config/synthetic-data.json`: regras para fixtures e demonstracoes com dados sintéticos.
- `traceability/requirements.json`: matriz de requisitos, estado atual, evidencias e gates.
- `testing/coverage.json`: cenarios de teste ligados a cada requisito, com status e evidencia executavel.
- `agents/` e `roles/`: perfis, responsabilidades e limites de cada atividade.
- `prompts/` e `skills/`: instrucoes de tarefa e conhecimento de dominio reutilizavel.
- `tools/catalog.json`: politica declarativa das ferramentas compartilhadas.
- `orchestrators/` e `workflows/`: sequencia prescrita, condicoes, gates e resultados esperados.
- `Backend/harness/` e `Frontend/harness/`: configuracao e ferramentas especificas de cada componente.

## O que e executado hoje

Na raiz do projeto:

```powershell
.\scripts\harness.ps1 -Target harness
.\scripts\harness.ps1 -Target all
```

O alvo `harness` valida JSON, IDs, papeis, prompts, skills, ferramentas, referencias, contratos do Model Gateway, consistencia de decisoes, rastreabilidade de requisitos, politicas de fixtures sinteticas e sequencias dos workflows. O alvo `context` executa os testes do subsistema de Retrieval. O alvo `all` executa ambos, além de Ruff, Pytest/cobertura, lint, typecheck, Vitest, build e smoke E2E.

Para o ciclo local em containers, use `docker-up`, `docker-e2e` e `docker-down`. O ambiente de desenvolvimento preserva seu volume SQLite ao parar; o smoke Playwright usa um nome de projeto separado, provider fake, rede Compose sem acesso externo e remove seus volumes ao terminar. Compose publica somente `127.0.0.1:5173`; a API permanece na rede interna e só aceita a sessão sintética pelo IP fixo do proxy local em modo `development`.

Os gates `docker.*` são opcionais e exigem Docker Compose v2.24+; não entram em `-Target all`, que continua usando as verificações locais. `docker-up` inicia o stack e espera pelos health checks, `docker-e2e` executa Playwright em uma rede de teste isolada e remove o projeto de teste mesmo após falha, e `docker-down` preserva o volume de desenvolvimento. Os Dockerfiles são apenas para o ciclo local; não representam uma imagem de produção.

O Harness tambem define checkpoints Git em [`COMMIT_GUIDE.md`](COMMIT_GUIDE.md). Ao concluir uma tarefa que alterou arquivos, sempre sugira uma mensagem de commit adequada, separada por repositorio quando necessario. A sugestao nao cria o commit; Backend e Frontend mantem historicos separados e os commits dependem de pedido explicito. O Git externo compartilhado recebe somente arquivos centrais explicitamente listados na politica de commits.

## Cobertura de testes

`testing/coverage.json` é a matriz central de cenários. Cada requisito de produto deve apontar para pelo menos um cenário. O status `implemented` só é aceito quando o arquivo e o nome do teste existem; `planned`, `manual-required`, `opt-in` e `deferred` deixam claro o que ainda não é cobertura executável. `harness.validate` verifica essas ligações para impedir que um cenário planejado seja apresentado como teste existente.

A matriz cobre testes unitários, integração de repositório/API, estados assíncronos, segurança, fluxo de navegador e revisão manual de UX/acessibilidade. A suite padrão deve usar identidade e providers falsos, fixtures sintéticas e nenhuma chamada externa. A autenticação SULTS, Grafana MCP e demonstração real de provider permanecem verificações explícitas da etapa final; sua ausência não bloqueia as fases locais que usam adapters falsos.

O gate de cobertura percentual do Backend é um piso de regressão, não prova de cobertura funcional. Para considerar uma capacidade testada, os cenários ligados ao requisito também precisam existir e passar. O smoke E2E cobre entrada local sintética, conversa com streaming, blocos analíticos, esclarecimento de período, orientação fora de escopo, retomada do histórico, navegação responsiva e isolamento da página administrativa. Não substitui testes dedicados de todas as falhas nem a revisão manual de acessibilidade.

Os arquivos de agentes, orquestradores e workflows sao **especificacoes declarativas**: `harness.ps1` nao cria agentes, nao interpreta condicoes `when` nem executa automaticamente cada etapa. Os catálogos descrevem permissoes desejadas, mas ainda nao ha um executor que aplique autorizacao por chamada ou sandbox. Nao trate os catalogos, isoladamente, como fronteira de seguranca em runtime.

## Retrieval de contexto

`harness/context/` adiciona retrieval local ao contexto do Harness, para fundamentar trabalho de engenharia no codigo e na documentacao do proprio projeto. Nao e o RAG de dominio da aplicacao Iara. Backend e Frontend registram ferramentas, skills e passos de workflow proprios, fixados aos escopos `backend` e `frontend`; o fluxo full-stack usa a ferramenta compartilhada com roteamento `auto`. Todos chamam a mesma implementacao, sem manter indices ou retrievers duplicados.

A interface Python `harness.context.retrieve_context()` e a CLI `python -m harness.context` consultam o estado atual do workspace a cada chamada:

```powershell
py -3 -m harness.context --query "Onde o Model Gateway define eventos de streaming?" --scope auto --limit 5
```

O Router seleciona escopos (`backend`, `frontend`, `harness` ou `project`). O retrieval hibrido combina correspondencia de caminho, simbolos Python/TypeScript e texto literal, remove trechos sobrepostos, ranqueia por sinais deterministas e monta um pacote com limite configuravel. Cada fonte inclui caminho relativo, linhas, razao, score, hash SHA-256, data de modificacao e conteudo marcado como dado nao confiavel. Consultas adicionais podem ser feitas durante a tarefa com uma pergunta ou escopo mais especifico.

O budget padrao e 6.000 tokens estimados e o maximo e 12.000, configurados em `config/project.json`. A estimativa `ceil(bytes UTF-8 / 3)` nao e tokenizer de um modelo; use-a como limite aproximado. Tarefa e contexto obrigatorio nunca sao descartados para caber: se excederem o budget, a consulta e bloqueada. O retrieval nao registra queries nem persiste conteudo ou indice; ao consultar de novo, hashes refletem os arquivos atuais.

Arquivos `.env*`, segredos conhecidos, credenciais, arquivos privados e binarios/artefatos gerados ficam excluidos; valores suspeitos de chave tambem excluem o arquivo. Resultados sao somente leitura, permanecem dados nao confiaveis e nao ampliam permissoes. Escopo controla selecao de contexto, nao autorizacao de runtime.

Busca semantica por embeddings, grafo de dependencias e cache persistente nao foram adicionados: o workspace atual e pequeno e a busca deterministica resolve o caso sem custo operacional ou provedor adicional. Os catalogos e workflows dos tres escopos registram a recuperacao contextual; o executor de agentes continua sendo uma evolucao futura, portanto hoje Retrieval pode ser chamado pela CLI ou pela interface Python, mas os manifests ainda nao sao executados automaticamente.

## Continuidade entre tarefas

O Retrieval não é memória automática do agente e não conserva o histórico do chat. Para reduzir perda de contexto, a implementação injeta em toda resposta os arquivos canônicos `harness/context/estado-do-projeto.md` (decisões duráveis) e `harness/context/retomada-atual.md` (frentes abertas/próximo passo) como contexto obrigatório, com SHA-256 e consumo contabilizado no orçamento. O agente ainda deve ler o `AGENTS.md`, os manifestos de decisão e a mensagem mais recente do usuário. Backend e Frontend têm cópias locais byte a byte idênticas, verificadas pelo validador, pois seus escopos não incluem documentos externos do usuário.

Após decisão confirmada, atualize o estado e os manifestos estruturados antes de codificar com base nela. Em pausa/entrega, atualize a retomada com o que foi feito, evidências, pendências e próxima ação. Não armazene transcrições, chaves, prompts privados nem dados empresariais. `harness.validate` rejeita cópias ausentes/divergentes e resumos excessivamente grandes; `harness.context` detecta fontes antigas por hash. Isso é uma proteção operacional, não garantia de memória perfeita: instruções diretas mais recentes do usuário prevalecem, e ausência de evidência deve ser relatada.

### Persistência e critério de conclusão

A regra bloqueante compartilhada `iara.task-completion` nos Harnesses Backend e Frontend mantém cada pedido autorizado ativo até que o trabalho necessário e seus critérios aplicáveis sejam atendidos. Interrupção, compactação de contexto, resposta parcial ou pergunta de status não encerram o objetivo; após atender a interrupção, retome do checkpoint. Antes do handoff, confronte critérios com evidências e não marque como concluída uma tarefa com trabalho autorizado necessário pendente.

Se uma aprovação, decisão do usuário ou dependência externa impedir parte da tarefa, conclua primeiro o trabalho independente autorizado, registre a causa e a próxima ação em `retomada-atual.md` e pause apenas a parte bloqueada. O limite de tentativas do loop nunca significa sucesso. Itens fora de escopo ou explicitamente adiados devem permanecer identificados como tais e não bloquear o pedido atual. Esta regra não amplia autorização, não contorna limites de segurança e não transforma loops declarativos em execução automática.

## Regras de execucao e dados

As regras registradas no `config/harness.json` de cada repositório estão ativas; arquivos não registrados são propostas. `blocking` interrompe o workflow até correção ou exceção aprovada; `required` precisa ser resolvida antes da conclusão ou ter exceção aprovada; `advisory` é não bloqueante e deve ser considerada na revisão. O validador confirma escopo e severidade, IDs registrados, exceções e igualdade das regras compartilhadas entre Backend e Frontend. Registre exceções aprovadas em `config/decisions.json` com `id`, `rule_id`, `scope`, `reason`, `approved_by`, `approved_at` e `review_by` ou `review_condition`.

Tarefas de alta complexidade, segurança ou impacto significativo exigem aprovação explícita antes da execução. Autenticação/autorização, credenciais, dados empresariais reais, chamadas externas reais, mudanças incompatíveis de contrato ou DDL, arquitetura, ampliação do MVP, publicação e operações irreversíveis são exemplos de alto impacto. O pedido explícito do usuário autoriza somente o escopo solicitado; tarefas localizadas e reversíveis, documentação dentro de decisões aprovadas e verificações locais não precisam de confirmação adicional.

- A sequência, delegação desabilitada e política de parar/corrigir/reexecutar são prescritas nos manifests; o runner executa gates, mas não interpreta todos os workflows nem delega automaticamente a agentes.
- Mudancas de uma camada devem seguir o workflow daquela camada; mudancas de contrato/API/streaming devem seguir o fluxo full-stack.
- A suite automatizada padrão usa provider fake, fixtures sintéticas e nenhuma credencial ou rede externa. O adapter OpenAI real é opt-in e não foi verificado sem chave e modelo escolhidos.
- O catálogo interno usa `IARA_DEFAULT_MODEL` como alias lógico (`principal`) e mantém o ID concreto OpenAI em `IARA_OPENAI_MODEL_ID`. A demonstração OpenAI real continua pendente da validação do modelo candidato e da configuração privada no `.env`. O fluxo padrão permanece sintético por período prolongado, mesmo após a liberação do Grafana MCP.
- O Grafana MCP é a fonte empresarial selecionada, mas o acesso real fica para a etapa final do MVP. Até lá, o Backend usa fixtures sintéticas por uma porta substituível e não acessa diretamente o banco empresarial.
- O gestor não verá nem escolherá provider/modelo. O Backend pode manter esses metadados para histórico técnico sem incluí-los no contrato público.
- O adapter OpenAI lê `OPENAI_API_KEY` somente pela configuração do Backend; em desenvolvimento, a origem é `Backend/.env`. A chave nunca chega ao Frontend, logs ou respostas públicas.
- O Model Gateway já tem protocolo substituível, provider fake, adapter OpenAI com LangChain isolado no Backend, normalização de erros, validação de blocos, streaming, alias interno e observabilidade operacional por provider, além de timeout/cancelamento. O resumo mensal da conta usa somente tokens informados pela OpenAI e registros mínimos deduplicados por chamada; o acesso real ao Grafana MCP permanece na etapa final.
- A politica exige interromper o fluxo diante de gate obrigatorio falho e repetir os gates afetados, mas hoje isso depende de quem executa o trabalho.
- A matriz `traceability/requirements.json` separa requisitos implementados, planejados, adiados e definidos por politica, e liga cada um às evidencias e gates que devem demonstrá-lo. O validador confirma arquivos e referencias; o agente ainda precisa produzir a evidencia de comportamento nos gates de backend/frontend/E2E.
- Toda mudança full-stack requer a etapa `visual-accessibility-review`: registrar capturas desktop/mobile, percurso por teclado/foco, alternativa textual dos graficos e estado dos problemas encontrados (ou `none`). O smoke Playwright cobre fluxos funcionais sintéticos; não substitui essa revisão manual de acessibilidade.
- Mudancas exclusivas do frontend aplicam a mesma revisao obrigatoria no workflow `Frontend/harness/workflows/feature.json`; correcoes de defeitos visuais passam pela revisao de frontend definida no workflow de bugfix. O gate `frontend.ux-review` e evidência manual, não um teste automatizado.
- `Backend/fixtures/synthetic/` aceita JSON marcado com `_metadata.classification = "synthetic"` e `_metadata.purpose`. O validador verifica sintaxe, metadados e nomes de campos proibidos. Uma pessoa ainda deve revisar os valores para confirmar que sao ficticios.

## Estado do produto

Backend e Frontend já formam uma demonstração funcional local com identidade sintética, SQLite, histórico retomável, fluxo de conversa SSE, provider falso, fixtures sintéticas, blocos analíticos, cancelamento, nova tentativa e página administrativa sem acesso às conversas. O DDL fica em `Backend/sql/esquema.sql`. SULTS real, Grafana MCP real e banco de produção ainda não estão conectados.

O protocolo do provider fica em `Backend/app/gateway.py`; a política vigente de interação direta, System Prompt, contexto de 40 mensagens e ferramentas LangChain está em `Backend/harness/rules/backend.model-orchestration.md`; a implementação atual em `Backend/app/model_gateway.py` ainda precisa ser adaptada antes de ser considerada conforme; o coordenador publica eventos SSE em `Backend/app/solicitacoes.py`. O modal de consumo mensal existe no Frontend, mas coleta, persistência e endpoint autenticado do Backend ainda estão pendentes; não se calcula preço. O manifesto `config/model-gateway.json` registra capacidades implementadas e futuras com suas evidências. A validação real de qualidade/custo do modelo e a integração real do Grafana MCP continuam pendentes.

### Referências entre contextos

Um Markdown pode declarar relações condicionais sob `## Related context` ou `## Contexto relacionado`, em bullets como `- When ... see [Security](security.md).` ou `- Quando ... consulte [Seguranca](security.md).`. A expansão segue no máximo três referências relevantes e somente um salto. O alvo precisa estar presente no escopo e passar os mesmos filtros e regras de segurança da busca direta. Referências externas, absolutas, fora do workspace ou fora do escopo não são seguidas. A resposta registra `related_context` na fonte e `trace.related_context_links` com origem, destino, motivo e estado; trechos relacionados usam o mesmo orçamento e não são contexto obrigatório.

## Loops de correção

`config/loop-policy.json` define o ciclo comum de recuperação para os orquestradores de Backend, Frontend e full-stack. Cada orquestrador referencia a política e declara quais checkpoints iniciam o ciclo. O agente diagnostica a causa, corrige, repete somente os passos afetados e dependentes, solicita revisão independente e registra evidências.

A política é declarativa e orienta o agente; o runner atual valida sua estrutura, mas ainda não executa loops automaticamente. Três falhas consecutivas pela mesma causa pausam o fluxo com evidências e opções, nunca contam como conclusão. Aprovações, decisões pendentes, critérios ambíguos e dependências externas indisponíveis também pausam o loop; depois da resolução, ele retoma do passo interrompido.
