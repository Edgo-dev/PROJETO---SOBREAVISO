# Sistema de Sobreaviso

Bootstrap inicial do projeto Django para gestao de chamados emergenciais.

## Status

Fase atual: **bootstrap**. Nenhuma regra de negocio implementada. As entidades (`Ativo`, `Fornecedor`, `Chamado`, `AtualizacaoChamado`, `Report`, `OS`, `Status`) e a tela "Atualizar Report" serao criadas nas proximas fases.

## Stack

- Python + Django 5
- SQLite (bootstrap). Migracao futura para PostgreSQL/Neon via `DATABASE_URL`.
- python-dotenv, openpyxl

## Estrutura

```
PROJETO - SOBREAVISO/
├── manage.py
├── requirements.txt
├── .gitignore
├── .env.example
├── README.md
├── sobreaviso/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── chamados/
│   ├── __init__.py
│   ├── apps.py
│   ├── admin.py
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   ├── tests.py
│   └── migrations/
│       └── __init__.py
├── templates/
│   ├── base.html
│   └── chamados/
│       └── home.html
└── static/
    ├── css/app.css
    └── js/app.js
```

## Setup local (Windows / PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
copy .env.example .env
python manage.py migrate
python manage.py runserver
```

Home: http://127.0.0.1:8000/
Admin: http://127.0.0.1:8000/admin/

## Testes

```powershell
python manage.py test
```
