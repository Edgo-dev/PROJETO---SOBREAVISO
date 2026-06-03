"""
Django settings for sobreaviso project.

Bootstrap inicial. As regras de negocio de chamados emergenciais serao adicionadas em fases futuras.
"""

import os
from datetime import timedelta
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")

# DEBUG — padrão False; ativar explicitamente em DEV
DEBUG = os.environ.get("DJANGO_DEBUG", "False") == "True"

# SECRET_KEY — obrigatória em produção
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "")
if not SECRET_KEY:
    if not DEBUG:
        # Em produção (DEBUG=False) uma chave previsível compromete sessões,
        # CSRF e tokens de reset de senha. Falha cedo em vez de subir inseguro.
        raise ImproperlyConfigured(
            "DJANGO_SECRET_KEY não definida. "
            "Defina uma chave forte por variável de ambiente em produção."
        )
    import warnings
    warnings.warn(
        "DJANGO_SECRET_KEY não definida. "
        "Usando chave insegura — NUNCA use em produção.",
        stacklevel=2,
    )
    SECRET_KEY = "django-insecure-dev-only-change-me"

ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    if host.strip()
]

# ── Hardening sempre ativo (inofensivo em DEV) ────────────
# nosniff impede o navegador de reinterpretar o Content-Type de arquivos
# servidos por serve_evidencia; vale também em DEV, onde antes ficava ausente.
SECURE_CONTENT_TYPE_NOSNIFF = True

# ── Hardening de produção (quebra http local, fica condicional) ──
if not DEBUG:
    SECURE_SSL_REDIRECT            = True
    SECURE_HSTS_SECONDS            = 31536000   # 1 ano
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD            = True
    SESSION_COOKIE_SECURE          = True
    CSRF_COOKIE_SECURE             = True
    SECURE_REFERRER_POLICY         = "strict-origin-when-cross-origin"
    X_FRAME_OPTIONS                = "DENY"

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "axes",
    "chamados",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "chamados.middleware.LoginRequiredMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # AxesMiddleware deve ser o último: observa o resultado da autenticação.
    "axes.middleware.AxesMiddleware",
]

AUTHENTICATION_BACKENDS = [
    # AxesStandaloneBackend deve vir primeiro: bloqueia antes de checar a senha.
    "axes.backends.AxesStandaloneBackend",
    "chamados.backends.NomeSobrenomeBackend",
    "django.contrib.auth.backends.ModelBackend",
]

# ── django-axes: proteção contra força bruta no login ──────
# Lockout por combinação (usuário + IP) para não travar um escritório inteiro
# atrás de um único IP quando só um operador erra a senha.
AXES_FAILURE_LIMIT = 5
AXES_COOLOFF_TIME = timedelta(minutes=30)
AXES_LOCKOUT_PARAMETERS = [["username", "ip_address"]]
AXES_RESET_ON_SUCCESS = True
AXES_USERNAME_CALLABLE = "chamados.backends.axes_username"
# Quando bloqueado, o AxesMiddleware substitui a resposta por este template.
AXES_LOCKOUT_TEMPLATE = "chamados/lockout.html"

LOGIN_URL = "chamados:login"
LOGIN_REDIRECT_URL = "chamados:home"
LOGOUT_REDIRECT_URL = "chamados:login"


# ====================================================================
#  E-mail (usado pelo fluxo de recuperacao de senha)
# ====================================================================
# Em DEV o padrao e o backend "console", que imprime o e-mail no terminal
# onde o runserver esta rodando — util pra testar sem SMTP real.
# Em PROD basta definir EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
# (ou outro) e preencher EMAIL_HOST, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD
# no arquivo .env.
EMAIL_BACKEND = os.getenv(
    "EMAIL_BACKEND",
    "django.core.mail.backends.console.EmailBackend",
)
EMAIL_HOST = os.getenv("EMAIL_HOST", "")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "True").lower() in ("1", "true", "yes")
EMAIL_USE_SSL = os.getenv("EMAIL_USE_SSL", "False").lower() in ("1", "true", "yes")
DEFAULT_FROM_EMAIL = os.getenv(
    "DEFAULT_FROM_EMAIL", "Sobreaviso <noreply@sobreaviso.local>"
)

ROOT_URLCONF = "sobreaviso.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "sobreaviso.wsgi.application"
ASGI_APPLICATION = "sobreaviso.asgi.application"


# Banco de dados
# Bootstrap usa SQLite. Migracao futura para PostgreSQL/Neon via DATABASE_URL
# sera tratada em fase posterior, sem complicar a estrutura atual.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True


STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
