"""URLs do app chamados."""

from django.contrib.auth import views as auth_views
from django.urls import path, reverse_lazy

from . import views

app_name = "chamados"

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("cadastro/", views.register_view, name="register"),
    path(
        "recuperar-senha/",
        auth_views.PasswordResetView.as_view(
            template_name="chamados/password_reset.html",
            email_template_name="chamados/password_reset_email.html",
            subject_template_name="chamados/password_reset_subject.txt",
            success_url=reverse_lazy("chamados:password_reset_done"),
        ),
        name="password_reset",
    ),
    path(
        "recuperar-senha/enviado/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="chamados/password_reset_done.html",
        ),
        name="password_reset_done",
    ),
    path(
        "recuperar-senha/confirmar/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="chamados/password_reset_confirm.html",
            success_url=reverse_lazy("chamados:password_reset_complete"),
        ),
        name="password_reset_confirm",
    ),
    path(
        "recuperar-senha/concluido/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="chamados/password_reset_complete.html",
        ),
        name="password_reset_complete",
    ),
    path("", views.home, name="home"),
    path("ativos/", views.ativos_list, name="ativos_list"),
    path("ativos/novo/", views.ativo_create, name="ativo_create"),
    path("ativos/importar/", views.ativos_import, name="ativos_import"),
    path(
        "ativos/autocomplete/",
        views.ativos_autocomplete,
        name="ativos_autocomplete",
    ),
    path("ativos/<int:pk>/", views.ativo_detail, name="ativo_detail"),
    path("ativos/<int:pk>/editar/", views.ativo_update, name="ativo_update"),
    path(
        "ativos/<int:pk>/obras-ativas/",
        views.ativo_obras_ativas,
        name="ativo_obras_ativas",
    ),
    path("obras/", views.obras_list, name="obras_list"),
    path("obras/novo/", views.obra_create, name="obra_create"),
    path("obras/importar/", views.obras_import, name="obras_import"),
    path(
        "obras/modelo/",
        views.obras_template_download,
        name="obras_template_download",
    ),
    path("obras/<int:pk>/", views.obra_detail, name="obra_detail"),
    path("obras/<int:pk>/editar/", views.obra_update, name="obra_update"),
    path("fornecedores/", views.fornecedores_list, name="fornecedores_list"),
    path("fornecedores/novo/", views.fornecedor_create, name="fornecedor_create"),
    path(
        "fornecedores/importar/",
        views.fornecedores_import,
        name="fornecedores_import",
    ),
    path(
        "fornecedores/modelo/",
        views.fornecedores_template_download,
        name="fornecedores_template_download",
    ),
    path("fornecedores/<int:pk>/", views.fornecedor_detail, name="fornecedor_detail"),
    path(
        "fornecedores/<int:pk>/editar/",
        views.fornecedor_update,
        name="fornecedor_update",
    ),
    path("consolidado-obras/", views.consolidado_obras, name="consolidado_obras"),
    path("chamados/", views.chamados_list, name="chamados_list"),
    path("chamados/novo/", views.chamado_create, name="chamado_create"),
    path("chamados/<int:pk>/", views.chamado_detail, name="chamado_detail"),
    path("atualizar-report/", views.atualizar_report_list, name="atualizar_report_list"),
    path(
        "atualizar-report/exportar/",
        views.atualizar_report_exportar_excel,
        name="atualizar_report_exportar_excel",
    ),
    path(
        "atualizar-report/<int:pk>/",
        views.atualizar_report_form,
        name="atualizar_report_form",
    ),
]
