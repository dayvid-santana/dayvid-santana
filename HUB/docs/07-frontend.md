# Frontend

## Stack e execução

O frontend usa React 19, TypeScript, Vite, CSS modular/global e Vitest com Testing Library. O proxy de desenvolvimento encaminha `/api` para `http://localhost:8088`.

Scripts:

```powershell
npm run dev
npm run build
npm run lint
npm test
```

## Navegação

| Visão | Caminho | Objetivo |
| --- | --- | --- |
| Matrix | `/` | visão central de colaboradores × sistemas |
| Alerts | `/alertas` | auditoria de alertas |
| Branch | `/filiais` | filtros e métricas por filial |
| Role | `/cargos` | comparação por cargo com carregamento sob demanda |
| Admin | `/admin` | sistemas e schemas |
| Login | `/login` | entrada da aplicação |

`routing.ts` traduz caminho em visão e `App.tsx` controla histórico, sessão, filtros, carregamento e seleção de detalhes. A administração só é liberada quando o perfil da sessão é `ADMIN`.

## Estado central em `App.tsx`

O componente mantém busca, filtros, registros, sistemas, opções, resumos, alertas, paginação, seleção de célula/colaborador, carregamento e erro. A busca da matriz usa debounce e paginação server-side. Quando uma célula é selecionada, o frontend chama o endpoint de detalhe em vez de reconstruir o payload localmente.

## Páginas

### `MatrixPage`

Exibe `DashboardStats`, `AccessToolbar`, banner de Situação 7, feedback de resultados e `AccessMatrix`. A matriz recebe sistemas ativos e colaboradores já normalizados.

### `AlertsPage`

Carrega alertas paginados, filtra tipo/empresa/status, exibe `AlertCard` e abre `AlertDetailsModal`. Permite alterar estados de gestão conforme as restrições da API.

### `BranchPage`

Permite escolher filiais, carrega métricas agregadas e apresenta colaboradores críticos ou a matriz da unidade. A escolha de filial apenas restringe consulta; não altera dados.

### `RolePage`

Lista cargos com busca e accordion. Ao abrir um cargo, carrega colaboradores sob demanda, em páginas de 50 registros, e mantém cache por cargo aberto.

### `AdminPage`

Gerencia sistemas, ativos/inativos, logos, autenticação, método, timeout, integração individual/lista e versões de schema/mapeamento. Também permite testar integração e usar o fluxo de descoberta.

### `LoginPage`

Tenta `POST /api/login`; enquanto essa rota não existe, usa fallback para `GET /api/sessao`. Armazena apenas o objeto de usuário em `localStorage` na chave `hub-acesso:sessao`. A senha não é conferida no provedor mock.

## Componentes principais

- `AccessMatrix`: tabela dinâmica; colunas são os sistemas ativos e células mostram estado, tempo e acesso.
- `AccessFilters`/`AccessToolbar`: busca e filtros de empresa, filial, cargo e tipo.
- `DashboardStats`: indicadores do painel.
- `AccessDetailsPanel`: detalhes do snapshot por colaborador/sistema.
- `AlertCard`/`AlertDetailsModal`: ciclo de gestão do alerta.
- `CriticalEmployeeList`: atalho para casos de Situação 7.
- `StatusLegend`/`StatusBadge`/`EmployeeSituationTag`: linguagem visual dos estados.
- `SystemLogo`/`LogoUpload`: identidade visual e administração das logos.
- `ThemeContext`/`ThemeToggle`: tema claro/escuro.

## Normalização no cliente

`src/services/accessApi.ts` converte respostas com nomes legados ou atuais para os tipos `Employee`, `System`, `Cell`, `ResumoPainel` e `AlertaAuditoria`. O backend continua sendo responsável pela regra e pelo status; essa normalização existe para compatibilidade de contrato e renderização.

