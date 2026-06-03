# PROJETO - SOBREAVISO

Aplicação Django para gestão operacional de chamados emergenciais, ativos
do parque imobiliário, fornecedores, obras e reports de sobreaviso.

## Visão geral

Sistema interno destinado à operação. O acesso exige autenticação, mas o
**login serve apenas para identificar quem está operando** — não há
controle por perfil, grupo, papel ou permissão granular. Qualquer usuário
logado pode operar livremente (criar chamado, atualizar report, importar
planilha, editar ativo etc.).

Essa é uma **decisão funcional** do projeto: os controles importantes para
esta fase são robustez, rastreabilidade dos dados e integridade das
importações, não bloqueio por papel de usuário.

## Funcionalidades principais

- **Autenticação**: login, cadastro, logout e recuperação de senha por
  e-mail (backend de console em DEV, configurável por env em PROD).
- **Home** com cards de métricas (Prédios × Lojas / Pendentes / Concluídos)
  e atalhos para os principais módulos.
- **Matriz de Ativos**: listagem com filtros (busca, cidade, UF, regional,
  ativo/inativo, qualidade de dados), cadastro, edição, detalhe e
  autocomplete para uso em outros formulários.
- **Importação Excel de Ativos** com detecção flexível de cabeçalhos.
- **Fornecedores**: listagem, filtros, cadastro, edição, detalhe.
- **Importação Excel de Fornecedores** com detecção flexível de cabeçalhos.
- **Obras**: listagem, cadastro, edição, detalhe e indicadores derivados
  (em andamento, planejada, atrasada, concluída, inativa).
- **Importação Excel de Obras** com detecção flexível de cabeçalhos.
- **Chamados**: listagem com filtros, cadastro vinculado a um ativo, detalhe.
- **Atualizar Report**: tela operacional dedicada com cards de contadores
  (Total filtrado, Abertos, Pendentes, Concluídos, Cancelados,
  Não emergenciais, Primeiro report pendente), filtros, exportação Excel,
  formulário de atualização por chamado e identificação automática do
  primeiro report da OS.
- **Geração de texto para WhatsApp** a partir do estado dos chamados
  (módulo `services.py` — usado pela tela de Atualizar Report).
- **Tratamento de arquivo `.xlsx` inválido**: as três rotas de importação
  capturam `BadZipFile`, `InvalidFileException` e `ValueError`, devolvem
  mensagem amigável e mantêm o banco intacto.
- **Preservação de dados em importações parciais** de Ativos e
  Fornecedores: planilha com coluna ausente ou célula vazia NÃO sobrescreve
  o valor existente do registro.

## Proteções de segurança implementadas

Independentes da decisão de "sistema aberto para qualquer logado" (ver
abaixo), estão ativas as seguintes defesas técnicas:

- **`SECRET_KEY` obrigatória em produção**: com `DEBUG=False`, a ausência de
  `DJANGO_SECRET_KEY` levanta `ImproperlyConfigured` e impede o boot — nunca
  sobe com chave previsível. Em DEV, cai para uma chave insegura com aviso.
- **Força bruta no login** mitigada por **django-axes**: lockout por
  combinação (usuário + IP), limite de 5 tentativas, cooloff de 30 min,
  reset no sucesso. Bloqueio exibe `templates/chamados/lockout.html`.
- **Rate limiting de cadastro e recuperação de senha** (que o axes não
  cobre): limite por IP via cache (`chamados/ratelimit.py`), 10 POSTs/hora
  por scope; excedido devolve `429` com
  `templates/chamados/muitas_requisicoes.html`.
- **Upload de planilhas `.xlsx`** com teto de **10 MB** nos três formulários
  de importação (evita esgotar memória — o `.xlsx` é lido inteiro para a RAM).
- **Evidências validadas por conteúdo (magic bytes)**, além da extensão:
  imagens e PDF estritos; vídeo com check leve de container.
- **`/media/` autenticado**: arquivos de evidência são servidos por
  `serve_evidencia` (exige login, com proteção contra path traversal).
- **`X-Content-Type-Options: nosniff` sempre ativo** (inclusive em DEV);
  demais cabeçalhos de hardening (HSTS, cookies *secure*, SSL redirect)
  ativos quando `DEBUG=False`.

## Regras de negócio importantes

### Acesso
- Sistema aberto para qualquer usuário logado.
- Login serve para identificar o operador (registrado nos chamados,
  reports e atualizações).
- Não há perfil/permissão/grupo. Toda tela interna é redirecionada para
  login quando o usuário é anônimo — quando logado, libera tudo.

### Importações parciais (Ativos e Fornecedores)
- Coluna **ausente** no cabeçalho → preserva o valor existente.
- Coluna **presente** com célula vazia → preserva o valor existente.
- Coluna **presente** com valor preenchido → atualiza.
- Para registros **novos**, o comportamento permissivo é mantido: campos
  ausentes/vazios entram como `""`.

### Importações com arquivo inválido
- `.xlsx` corrompido / não é zip / formato estranho → captura, log,
  mensagem amigável (`"Arquivo Excel inválido ou corrompido. Envie uma
  planilha .xlsx válida."`), tela renderizada com status 200, zero gravações
  no banco (a leitura ocorre antes do bloco transacional).

### Métricas da Home
Calculadas em `chamados.views._metricas_home` e formalmente testadas em
`HomeMetricasCoerentesTests`:

- **Lojas** = `Ativo.tipo_imovel` contém `"loja"` (case-insensitive).
  Cobre `LOJA`, `LOJA SHOPPING IGUATEMI`, `Loja Comercial` etc.
- **Prédios** = negação de Lojas. Inclui `tipo_imovel` vazio (`""`),
  `PREDIO`, `TÉCNICO`, `SEDE`, `CD`, qualquer outro valor que não contenha
  `"loja"`.
- **`Ativo.ativo = False`** continua sendo contado nas métricas — é
  inventário total do parque, não "parque operacional".
- **Pendentes** = chamados com status `ABERTO` ∪ `PENDENTE`.
- **Concluídos** = chamados com status estritamente `CONCLUIDO`.
- **`CANCELADO`** e **`NAO_EMERGENCIAL`** não entram em pendentes nem em
  concluídos.
- Fornecedores e Obras não compõem métrica no hero da Home hoje.

## Stack técnica

Conforme `requirements.txt` e `sobreaviso/settings.py`:

- **Python 3** (testado com 3.13 no ambiente do desenvolvedor).
- **Django** `>=6.0,<6.1`.
- **openpyxl** `>=3.1,<4.0` — leitura/geração de planilhas `.xlsx`.
- **python-dotenv** `>=1.0,<2.0` — carga de variáveis a partir de `.env`.
- **django-axes** `>=6.0,<7.0` — proteção contra força bruta no login.
- **Banco de dados local**: SQLite (`db.sqlite3` na raiz). Migração para
  banco externo é planejada para fase posterior — ver "Limitações atuais
  / próximos passos".
- **Templates**: Django Templates em `templates/` (com `base.html` e
  `chamados/`).
- **Static**: assets-fonte em `static/css/` e `static/js/`.
- **E-mail**: backend de console em DEV; configurável via variáveis de
  ambiente (`EMAIL_BACKEND`, `EMAIL_HOST`, …) — usado pela recuperação de
  senha.
- **Autenticação**: backend padrão do Django + `NomeSobrenomeBackend`
  customizado (em `chamados/backends.py`) para aceitar login por nome.

## Estrutura do projeto

```
manage.py
requirements.txt
README.md
.gitignore
.gitattributes
.env.example
sobreaviso/
    settings.py
    urls.py
    wsgi.py
    asgi.py
chamados/
    models.py          # Ativo, Fornecedor, Chamado, AtualizacaoChamado, Obra
    views.py           # Views HTTP (home, listagens, importações, report...)
    importadores.py    # Leitura flexível de .xlsx (ativos/fornecedores/obras)
    services.py        # Regras de report, WhatsApp e validação de evidências
    forms.py           # Formulários (incluindo *ImportForm)
    backends.py        # NomeSobrenomeBackend + axes_username (login auxiliar)
    ratelimit.py       # throttle_post: rate limiting de cadastro/reset por IP
    middleware.py      # LoginRequiredMiddleware (escopo de identificação)
    urls.py            # Rotas do app
    admin.py
    tests.py           # Suíte completa
    migrations/        # 0001_initial, 0002_…, 0003_obra, 0004_seed_fornecedores_padrao
templates/
    base.html
    chamados/          # Telas (home, ativos, fornecedores, obras, chamados, report, auth)
static/
    css/app.css
    js/app.js
```

## Como rodar localmente (Windows PowerShell)

```powershell
python -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
pip install -r requirements.txt

copy .env.example .env

python manage.py migrate
python manage.py createsuperuser   # opcional, para acessar /admin/
python manage.py runserver
```

- Home: <http://127.0.0.1:8000/>
- Admin: <http://127.0.0.1:8000/admin/>

Telas internas redirecionam para `/login/` quando o usuário não está
autenticado (o cadastro está aberto em `/cadastro/`).

## Variáveis de ambiente

Há um template em `.env.example` que deve ser copiado para um `.env` real
(que **NÃO é versionado** — está coberto pelas regras `.env` e `.env.*`
do `.gitignore`, com `!.env.example` explícito para preservar o template).

Variáveis lidas em `sobreaviso/settings.py`:

| Variável | Default | Função |
|---|---|---|
| `DJANGO_SECRET_KEY` | *(vazio)* | Chave de sessão/CSRF. **Obrigatória com `DEBUG=False`** — sem ela o boot falha (`ImproperlyConfigured`). Em DEV cai para chave insegura com aviso. |
| `DJANGO_DEBUG` | `False` | `True`/`False`. Padrão **`False`** (seguro). Ativar explicitamente em DEV. |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1` | Lista separada por vírgula. |
| `EMAIL_BACKEND` | `django.core.mail.backends.console.EmailBackend` | Em DEV imprime o e-mail no terminal. Em PROD, trocar para SMTP. |
| `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` | `""` / `587` / `""` / `""` | Credenciais SMTP quando aplicável. |
| `EMAIL_USE_TLS` / `EMAIL_USE_SSL` | `True` / `False` | TLS/SSL do SMTP. |
| `DEFAULT_FROM_EMAIL` | `Sobreaviso <noreply@sobreaviso.local>` | Endereço remetente padrão. |

Nunca coloque segredos reais no Git. Use `.env` localmente e variáveis de
ambiente injetadas pelo orquestrador em produção.

## Banco de dados local

- O banco local é um único arquivo `db.sqlite3` na raiz do projeto.
- **`db.sqlite3` está no `.gitignore`** e não deve ser versionado — cada
  desenvolvedor mantém o seu local, e o estado real do schema é dado
  pelas migrations.
- Para zerar o banco local: feche o `runserver`, apague `db.sqlite3` e
  rode `python manage.py migrate` novamente. A migration de seed
  `chamados.0004_seed_fornecedores_padrao` repopula a tabela de
  fornecedores padrão.
- Para ambiente real/deploy multiusuário, recomenda-se migrar para banco
  externo (PostgreSQL, por exemplo). Essa migração **ainda não está
  implementada** — ver "Limitações atuais / próximos passos".

## Importações Excel

Todas as três importações aceitam `.xlsx` com cabeçalhos flexíveis:
sinônimos comuns são reconhecidos, colunas em ordem aleatória são
suportadas, colunas extras são silenciosamente ignoradas, e uma eventual
linha de título antes do cabeçalho é detectada nas primeiras seis linhas.

Arquivo inválido (não-zip, formato errado, corrompido) é tratado com
mensagem amigável — nenhuma gravação ocorre.

### Ativos — `POST /ativos/importar/`

Cabeçalho-chave **obrigatório**: `Ativo Prisma` (ou sinônimos como
`Prisma`, `Cod Prisma`, `Cod Ativo`, `ID Ativo`, etc.). Sem ele, o sistema
recusa a importação por não haver como identificar o registro.

Cabeçalhos reconhecidos (lista parcial; ver `MAPEAMENTO_CABECALHOS_ATIVO`
em `chamados/importadores.py` para o conjunto completo de sinônimos):

`Ativo Prisma`, `Nome do Site`, `Endereço`, `Cidade`, `UF`, `Regional`,
`Tipo de imóvel`, `Líder da Coordenação`, `Tipo Site / SLA`,
`Status (Ativo/Inativo)`.

Importação parcial **preserva** os campos opcionais quando a coluna está
ausente ou vem vazia em um registro existente.

### Fornecedores — `POST /fornecedores/importar/`

Cabeçalho-chave **obrigatório**: `Nome` (ou sinônimos como `Supervisor`,
`Nome do Supervisor`, `Responsável`, `Contato Principal`).

Cabeçalhos reconhecidos:

`Nome`, `Telefone`, `E-mail`, `Empresa`, `Estados atendidos`.

Importação parcial **preserva** os campos opcionais quando a coluna está
ausente ou vem vazia em um registro existente.

### Obras — `POST /obras/importar/`

Cabeçalhos **obrigatórios**:

`Ativo Prisma`, `Descrição da Obra`, `Data Início`, `Data Fim Planejada`.

Cabeçalhos opcionais reconhecidos: `Responsável`, `Observações`.

A obra é vinculada a um Ativo já existente pela coluna `Ativo Prisma`.
Datas aceitas em vários formatos: `dd/mm/aaaa`, `aaaa-mm-dd`, `dd-mm-aaaa`,
`dd/mm/aa`, `dd.mm.aaaa`, além de células nativas de data do Excel.

## Testes

Comandos canônicos:

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test chamados.tests -v 1
```

No marco atual do repositório, a suíte `chamados.tests` está estabilizada
com **352 testes**. Esse número é o estado registrado no último commit
validado — qualquer alteração futura deve ser verificada com os comandos
acima.

Principais áreas cobertas:

- **Modelos**: `AtivoModelTests`, `FornecedorModelTests`, `ChamadoModelTests`,
  `AtualizacaoChamadoModelTests`.
- **Importadores (lógica isolada)**: `ImportadorAtivosFlexivelTests`,
  `ImportadorFornecedoresFlexivelTests`, `ImportadorObrasFlexivelTests`.
- **Importação parcial preservando dados**: `ImportacaoParcialAtivosTests`,
  `ImportacaoParcialFornecedoresTests`.
- **Arquivo Excel inválido**: `ImportacaoAtivosArquivoInvalidoTests`,
  `ImportacaoFornecedoresArquivoInvalidoTests`,
  `ImportacaoObrasArquivoInvalidoTests`.
- **POST HTTP válido das importações**: `ImportacaoValidaHttpTests`.
- **Métricas da Home formalmente travadas**: `HomeMetricasCoerentesTests`.
- **Contrato anônimo→302 / autenticado→200**:
  `AutenticacaoTelasInternasContratoTests` e testes equivalentes em cada
  classe de view.
- **Fluxo de report / WhatsApp**: `ServiceIsPrimeiroReportTests`,
  `ServiceObterTipoReportTests`, `ServiceValidarStatusReportTests`,
  `ServiceRegistrarReportTests`, `FormatadoresReportTests`,
  `ObterTituloWhatsappTests`, `GerarTextoWhatsappTests`,
  `AtualizarReportViewTests`.
- **Segurança**: limite de tamanho de upload (`AtivosImportTests`),
  validação de evidência por conteúdo (`ServiceRegistrarReportTests`),
  lockout de força bruta (`LoginRateLimitTests`) e rate limiting de
  cadastro/reset (`ThrottlePostTests`).
- **Views de listagem/CRUD**: `AtivosListViewTests`, `AtivoCreateViewTests`,
  `AtivoUpdateViewTests`, `AtivoDetailViewTests`,
  `FornecedoresViewTests`, `ChamadosListViewTests`,
  `ChamadoDetailViewTests`, `ChamadoCreateViewTests`,
  `ChamadoCreatePersistenciaTests`, `ConsolidadoObrasViewTests`,
  `HomeViewTests`, `HomeLinkTests`, `HomeNovoChamadoLinkTests`,
  `AtivoDetailLinkTests`, `AtivosImportTests`,
  `AtivosAutocompleteViewTests`.

Observação: ao rodar com `-v 2`, alguns testes emitem traceback de
`BadZipFile` no stderr — é o `logger.warning(exc_info=True)` das views
de importação, comportamento intencional. Os testes seguem com status
`ok`.

## Git e pacote limpo

- **`.gitignore`** protege: `.venv/`, `venv/`, `env/`, `__pycache__/`,
  `*.pyc`, `db.sqlite3`, `db.sqlite3-journal`, `.env`, `.env.*` (com
  exceção explícita de `!.env.example`), `staticfiles/`, `media/`,
  `*.log`, `.coverage`, `htmlcov/`, `.pytest_cache/`, `.vscode/`,
  `.idea/`.
- **`.gitattributes`** força normalização para LF na master (Python,
  HTML, CSS, JS, MD, TXT, JSON, YAML, TOML, CFG, INI, SH); arquivos
  binários típicos (`*.xlsx`, `*.png`, etc.) ficam marcados como
  `binary`. Reduz ruído CRLF/LF tipico do ambiente Windows.

### Gerar pacote limpo de código

```powershell
git archive --format zip --output "../PROJETO-SOBREAVISO-CODIGO-LIMPO.zip" HEAD
```

`git archive` exporta apenas o conteúdo de `HEAD` — por construção, o
ZIP gerado **NÃO contém**:

- `.git/`
- `.venv/`
- `db.sqlite3`
- `__pycache__/`
- `.env` (mas inclui o template `.env.example`)
- `media/`
- `staticfiles/`

E contém todos os artefatos versionados: `manage.py`, `requirements.txt`,
`README.md`, `.gitignore`, `.gitattributes`, `.env.example`, `chamados/`,
`sobreaviso/`, `static/`, `templates/`.

## Limitações atuais / próximos passos

Esta seção lista o estado de hardening e as pendências conhecidas. Onde um
item já foi implementado, isso é dito explicitamente; o restante continua
pendente.

- **Hardening de produção**: já implementado o essencial — `DEBUG=False`
  por padrão, `SECRET_KEY` obrigatória em produção (boot falha sem ela),
  HTTPS-only condicional (`SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`,
  `CSRF_COOKIE_SECURE`, HSTS) e `nosniff` sempre ativo. **Ainda pendente**:
  apertar `ALLOWED_HOSTS` para os hosts reais e rodar o checklist do
  `manage.py check --deploy` no ambiente de produção.
- **Cache compartilhado para o rate limiting**: o throttle de cadastro/reset
  (`chamados/ratelimit.py`) usa o cache do Django. Com o `LocMemCache` padrão
  a contagem é **por processo** — em produção multi-worker, configure
  `CACHES` com Redis/Memcached para a contagem valer entre os workers.
- **Migrations do django-axes no deploy**: rodar `python manage.py migrate`
  no ambiente real cria as tabelas `axes_*` usadas pelo lockout.
- **Banco de produção**: migrar SQLite para PostgreSQL (ou equivalente),
  por exemplo via `DATABASE_URL`. SQLite atende a operação local
  mono-processo, não a uso multiusuário concorrente em produção.
- **Servir estáticos em produção**: configurar WhiteNoise (ou CDN /
  servidor de assets) e rodar `collectstatic` no deploy. Hoje o projeto
  serve via `runserver` (dev only).
- **WSGI/ASGI de produção**: integrar Gunicorn (ou Uvicorn p/ ASGI)
  atrás de um proxy reverso.
- **E-mail real**: trocar `console.EmailBackend` por SMTP real e validar
  fluxo de recuperação de senha em ambiente produtivo.
- **Ruído de log nos testes**: `logger.warning(..., exc_info=True)`
  imprime traceback no stderr durante testes de arquivo inválido.
  Para CI silencioso, considerar `LOGGING` específico de teste ou
  `assertLogs`.
- **Tempo da suíte**: ~5 min para rodar 343 testes (uso intensivo de
  `force_login` e criação de usuários). Otimização via `setUpTestData`
  pode reduzir drasticamente.
- **Versionamento de migrations seed**: a migration
  `0004_seed_fornecedores_padrao` cria 8 fornecedores. Testes devem
  usar contagem **relativa** (`antes_count + 1`), nunca absoluta.

## Como validar antes de qualquer alteração

Rotina padrão para verificar que um marco está em estado consistente:

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test chamados.tests -v 1
git status --short
```

Os três comandos Django devem terminar limpos (`No issues`,
`No changes detected`, `OK`), e o `git status` deve estar vazio antes
de gerar um pacote ou criar uma nova fase de trabalho.

## Observação sobre segurança e permissões

- O sistema **não foi desenhado** para controle de acesso granular.
- Qualquer usuário logado pode operar — esta é decisão funcional do
  projeto, não esquecimento de implementação.
- Futuras melhorias de segurança devem focar em **robustez**,
  **rastreabilidade** (já há identificação do operador em chamados/
  reports/atualizações), **logs** e **integridade dos dados**, e não
  em bloqueio por perfil/papel/grupo.
- Se em algum momento o requisito mudar, a alteração precisará ser
  explícita: refazer telas críticas, escrever testes para a nova regra
  e rever middleware. **Não há atalho** para "ligar permissão depois"
  sem revisitar conscientemente as decisões já tomadas.
