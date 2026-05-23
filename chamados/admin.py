"""Admin do app chamados."""

from django.contrib import admin

from .models import Ativo, AtualizacaoChamado, Chamado, Evidencia, Fornecedor, Obra


@admin.register(Fornecedor)
class FornecedorAdmin(admin.ModelAdmin):
    list_display = ("nome", "contato", "telefone", "email", "ativo")
    list_filter = ("ativo",)
    search_fields = ("nome", "contato", "email", "telefone")
    ordering = ("nome",)


@admin.register(Ativo)
class AtivoAdmin(admin.ModelAdmin):
    list_display = ("ativo_prisma", "nome_site", "cidade", "uf", "regional", "ativo")
    list_filter = ("ativo", "uf", "regional", "tipo_imovel", "tipo_site_sla")
    search_fields = ("ativo_prisma", "nome_site", "cidade", "endereco", "regional")
    ordering = ("regional", "cidade", "nome_site")


@admin.register(Chamado)
class ChamadoAdmin(admin.ModelAdmin):
    list_display = (
        "numero_os",
        "ativo",
        "fornecedor",
        "data_abertura",
        "status",
        "criado_por",
    )
    list_filter = ("status", "fornecedor", "data_abertura")
    search_fields = (
        "numero_os",
        "ativo__ativo_prisma",
        "ativo__nome_site",
        "solicitante",
        "denominacao",
    )
    autocomplete_fields = ("ativo", "fornecedor")
    date_hierarchy = "data_abertura"
    ordering = ("-data_abertura", "-criado_em")


@admin.register(Obra)
class ObraAdmin(admin.ModelAdmin):
    list_display = (
        "ativo",
        "data_inicio",
        "data_fim_planejada",
        "data_fim_real",
        "responsavel",
        "ativa",
    )
    list_filter = ("ativa", "data_inicio", "data_fim_planejada")
    search_fields = (
        "ativo__ativo_prisma",
        "ativo__nome_site",
        "descricao",
        "responsavel",
    )
    autocomplete_fields = ("ativo",)
    date_hierarchy = "data_inicio"
    ordering = ("-data_inicio",)


@admin.register(AtualizacaoChamado)
class AtualizacaoChamadoAdmin(admin.ModelAdmin):
    list_display = (
        "chamado",
        "tipo_evento",
        "status_resultante",
        "criado_por",
        "criado_em",
    )
    list_filter = ("tipo_evento", "status_resultante", "criado_em")
    search_fields = (
        "chamado__numero_os",
        "texto_atualizacao",
    )
    autocomplete_fields = ("chamado",)
    ordering = ("-criado_em",)


@admin.register(Evidencia)
class EvidenciaAdmin(admin.ModelAdmin):
    list_display = ("pk", "atualizacao", "tipo", "nome_arquivo", "criado_em")
    list_filter = ("tipo",)
    raw_id_fields = ("atualizacao",)
