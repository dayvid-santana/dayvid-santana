# Segurança e privacidade

## Escopo dos dados

O Hub processa dados funcionais e de acesso: nome, CPF, matrícula, empresa, filial, cargo, situação funcional, perfis, permissões, identificadores de origem, datas e payloads externos. CPF e informações de acesso são dados sensíveis para fins de segurança operacional e devem ter acesso restrito.

## Estado atual

| Controle | Situação atual |
| --- | --- |
| Credencial externa fora das respostas | implementado: API informa apenas se está configurada |
| Validação de URL e tipo de autenticação | implementado no cadastro |
| TLS da chamada externa | suportado; CA pode ser configurada |
| CORS configurável | implementado |
| Usuário autenticado de verdade | não implementado; sessão mock |
| Autorização backend por perfil | não implementada como controle efetivo |
| CPF mascarado | não implementado de forma consistente |
| Secret manager | não implementado |
| Auditoria de ações administrativas | parcial; há evidência de snapshots/alertas, não de usuário executor |

## CPF: comportamento atual e correção necessária

`colaboradorPublico()` serializa `numero_cpf` normalizado. A matriz também renderiza esse campo diretamente. Portanto, o risco não deve ser escondido na documentação.

Correção recomendada:

1. manter CPF completo somente em serviços internos que fazem consulta;
2. criar serializer público que devolva CPF mascarado, por exemplo `***.***.***-09`;
3. evitar CPF completo em URLs, logs e mensagens de erro;
4. restringir detalhes de payload a usuários autorizados;
5. adicionar testes que rejeitem CPF completo nas respostas públicas.

## Ameaças principais

- credencial de API vazada em banco, log, dump ou resposta administrativa;
- acesso não autorizado a payload bruto e permissões;
- sessão mock usada em ambiente exposto;
- CORS amplo permitindo origem indevida;
- endpoint de descoberta usado para sondar redes internas;
- upload de logo com conteúdo não permitido;
- snapshots sem retenção acumulando dados além da necessidade;
- SSRF via URL de integração cadastrada por usuário não confiável.

## Controles obrigatórios para produção

- substituir `SESSION_PROVIDER=mock` por provedor real com expiração, revogação e MFA conforme política;
- aplicar autorização no backend, não apenas no frontend/localStorage;
- usar secret manager e rotação de credenciais;
- limitar e validar egress das URLs externas e do endpoint de discovery;
- restringir `CORS_ORIGINS` aos domínios oficiais;
- habilitar TLS entre frontend, API, banco e integrações;
- criptografar backups e controlar restauração;
- remover segredos/CPF/payload de logs e ferramentas de observabilidade;
- definir retenção e base legal para dados pessoais;
- registrar usuário, motivo e timestamp das ações administrativas.

## Checklist de revisão

- [ ] ambiente de produção rejeita SQLite e mock;
- [ ] não há segredo no repositório, imagem ou arquivo versionado;
- [ ] `/api/sessao`, administração, alertas e detalhes exigem autenticação real;
- [ ] CPF público está mascarado;
- [ ] payload bruto possui controle de acesso;
- [ ] CORS e headers de segurança foram revisados;
- [ ] upload valida extensão, MIME, tamanho e conteúdo;
- [ ] backups têm teste de restauração;
- [ ] retenção e descarte foram aprovados por segurança/privacidade;
- [ ] dependências são atualizadas e verificadas.

