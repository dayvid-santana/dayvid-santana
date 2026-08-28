# CI/CD e ambientes

## Ambientes

| Ambiente | Fonte Senior | Banco do Hub | Sessão | Objetivo |
| --- | --- | --- | --- | --- |
| Desenvolvimento | CSV | SQLite ou PostgreSQL Docker | mock | desenvolvimento local |
| Integração/homologação | SQL ou mock controlado | PostgreSQL | provedor de teste | validação antes do release |
| Produção | view SQL real | PostgreSQL persistente | provedor real obrigatório | operação |

Produção deve rejeitar `SENIOR_SOURCE=csv`, `MOCK_DATA_ENABLED=true` e `DATABASE_URL` SQLite.

## Pipeline mínimo recomendado

1. checkout com versão identificável;
2. instalar dependências fixadas pelo lockfile;
3. verificar formatação/lint;
4. compilar backend (`compileall`) e frontend (`npm run build`);
5. executar testes unitários;
6. executar testes de integração com banco temporário;
7. validar `docker compose config`;
8. executar smoke test Docker;
9. construir imagens com tag imutável;
10. aplicar migration aprovada;
11. publicar/deployar;
12. verificar `/ready`, frontend, matriz e uma varredura controlada;
13. manter plano de rollback.

## Comandos existentes

Backend:

```powershell
python -m compileall -q app tests
.\scripts\test.ps1
. .\scripts\runAllTests.ps1
runAllTests -SkipDocker
```

Frontend:

```powershell
npm run lint
npm test
npm run build
```

## Release checklist

- [ ] versão e changelog registrados;
- [ ] contratos de API atualizados;
- [ ] migration testada em banco vazio e legado;
- [ ] alteração de schema externo versionada;
- [ ] secrets configurados fora da imagem;
- [ ] CORS revisado;
- [ ] backup verificado;
- [ ] smoke test aprovado;
- [ ] dashboard e varredura conferidos;
- [ ] rollback conhecido.

## Rollback

Rollback de aplicação não deve apagar snapshots. Reverter imagem/configuração e, se necessário, reativar a versão anterior de schema. Rollback de banco exige backup e migration reversível aprovada; nunca executar `DROP` ou limpeza ampla como primeira resposta a um incidente.

