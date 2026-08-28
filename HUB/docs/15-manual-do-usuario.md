# Manual do usuário

## Acesso

Abra o frontend, informe usuário e senha e selecione **Entrar**. No estado atual, a tela usa sessão mock; a senha não é realmente validada. Em produção, não considerar essa tela um controle de acesso até a autenticação real ser implementada.

## Matriz de acessos

A visão inicial cruza colaboradores nas linhas com sistemas nas colunas. Use a busca e os filtros de empresa, filial, cargo, situação e tipo. A paginação e a busca são feitas no backend.

### Interpretar células

- **Com acesso:** resposta válida indica acesso ativo.
- **Sem acesso:** a origem respondeu com o código de ausência configurado.
- **Payload inválido:** a origem respondeu, mas o contrato não foi atendido.
- **Erro de integração:** falha HTTP, rede, autenticação, rate limit ou servidor.
- **Tempo excedido:** chamada superou o timeout.
- **Não consultado:** ainda não existe snapshot para aquela combinação.
- **Acesso divergente:** acesso confirmado, mas incompatível com uma regra de negócio.

Não trate “erro de integração” como “sem acesso”.

Clique em uma célula para abrir detalhes do snapshot: HTTP, duração, resultado normalizado, perfis, permissões, versão de schema e erros. Payload original pode conter informação sensível.

## Alertas

Na tela **Alertas**, filtre por tipo, empresa e status. A prioridade principal é `SITUACAO_7`: colaborador com código funcional 7 e acesso ativo/divergente.

Fluxo recomendado:

1. abrir o alerta;
2. conferir colaborador, sistema, última consulta e risco;
3. investigar o acesso na origem;
4. marcar `EM_ANALISE` ou `RECONHECIDO`;
5. remover o acesso na origem quando indevido;
6. aguardar nova varredura para resolver;
7. usar `IGNORADO` somente com justificativa documentada.

## Filiais

Em **Filiais**, selecione uma unidade para ver métricas, erros, divergências e colaboradores críticos. A seleção é apenas um filtro; ela não altera o cadastro.

## Cargos

Em **Cargos**, pesquise pelo nome/código e expanda um cargo. Os colaboradores são carregados sob demanda e paginados. Use essa visão para comparar acessos de pessoas com a mesma função.

## Administração

Somente o perfil `ADMIN` deve acessar **Administração**.

### Cadastrar sistema

1. criar slug em minúsculas com hífen;
2. informar nome, URL e tipo de integração;
3. definir autenticação e timeout;
4. para individual, incluir `{cpf}`;
5. para lista, informar `campo_cpf` e paginação;
6. inserir JSON Schema e mapeamento;
7. salvar e testar com CPF autorizado;
8. ativar somente após validar o resultado.

### Alterar schema

Salvar schema/mapeamento cria uma nova versão. A versão anterior permanece para explicar snapshots históricos.

### Logo

Enviar imagem compatível dentro do limite configurado. Não use logo como mecanismo de armazenamento de dados.

## Atualização de dados

A matriz mostra o último snapshot persistido. Se houver dados antigos, consulte a hora da última verificação e solicite uma varredura manual ou aguarde o agendamento automático.

