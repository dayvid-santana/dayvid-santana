# Desenvolvimento, testes e evolução

## Testes existentes

### Backend

O backend usa pytest e separa testes unitários e de integração. A suíte cobre:

- CPF, validação e ingestão CSV/SQL;
- banco, preparação explícita e migração de colunas legadas;
- JSON Schema, JSONPath, seleção por CPF e conversões;
- scanner, concorrência, timeout, HTTP e snapshots;
- integração por lista, duplicidades e paginação;
- agendamento automático e trava;
- alertas e Situação 7;
- APIs, detalhes, paginação, filtros e monitoramento;
- armazenamento de logos e sessão mock;
- configuração de produção.

Comandos:

```powershell
cd HUB_acesso_Backend
.\.venv\Scripts\Activate.ps1
.\scripts\test.ps1
pytest -q -m unit
pytest -q -m integration
```

`scripts/runAllTests.ps1` agrega compilação, testes, validação do Compose e smoke test Docker. Use `-SkipDocker` quando o daemon não estiver disponível.

### Frontend

Vitest + Testing Library cobrem serviços HTTP, normalização, filtros, matriz, cards, paginação, contexto de tema e roteamento.

```powershell
cd HUB_acesso_Frontend
npm test
npm run lint
npm run build
```

## Como alterar com segurança

1. Se alterar um status ou contrato de domínio, atualize `app/schemas/domain.py`, o serializer das rotas, os tipos em `src/types.ts`, a normalização em `src/services/accessApi.ts` e os testes.
2. Se alterar schema/mapeamento, crie uma nova versão; não reinterprete snapshots antigos como se usassem o contrato novo.
3. Se alterar tabela, atualize o modelo, a preparação/migration e os testes de banco.
4. Se alterar a fonte Senior, preserve o contrato das dez colunas e mantenha CSV/SQL compatíveis.
5. Se alterar integração externa, teste pelo menos sucesso, ausência, autenticação, timeout, payload inválido e rate limit.
6. Se alterar uma tela, valide carregamento, vazio, erro, paginação, atualização e navegação direta pela URL.

## Riscos e limitações atuais

- **Autenticação de usuário mock:** qualquer substituição precisa definir provedor, sessão, expiração, logout, perfis e autorização no backend.
- **Migration incremental no script:** a preparação atual atende evolução do protótipo, mas um ambiente crítico deve migrar para ferramenta versionada, como Alembic, com revisão e rollback.
- **Payloads JSON em colunas genéricas:** simplificam integrações, mas podem exigir índices/colunas derivadas em grande volume.
- **Retenção de snapshots:** o crescimento histórico precisa de política de retenção, particionamento ou arquivamento.
- **Credenciais no cadastro:** devem migrar para secret manager/cofre e nunca ser devolvidas em respostas administrativas.
- **Identidade do colaborador:** mudanças de vínculo geram outra chave composta; relatórios históricos precisam deixar isso claro.
- **Resolução de alertas:** o fechamento depende de nova varredura, então a operação precisa de frequência adequada e monitoramento de falhas.

## Evoluções recomendadas

1. Implementar autenticação e autorização reais no backend, sem confiar apenas no perfil guardado no `localStorage`.
2. Adotar migrations versionadas e observabilidade estruturada.
3. Criar retenção/particionamento de snapshots e índices de busca PostgreSQL, incluindo `pg_trgm` quando necessário.
4. Adicionar métricas de duração, sucesso, timeout, rate limit e atraso da última varredura.
5. Definir contratos de integração por sistema em arquivos versionados e promover alterações entre ambientes.
6. Formalizar ações de remediação fora do Hub, mantendo o Hub como auditor e evidência até que uma integração de revogação seja autorizada.

