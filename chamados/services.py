"""Camada de servico do app chamados.

Concentra a regra de primeiro report, o registro controlado de
atualizacoes de chamados e a geracao do texto padronizado para WhatsApp.
As views nao devem duplicar essa logica nem manipular AtualizacaoChamado
diretamente fora deste modulo.
"""

from datetime import date, datetime

from django.db import transaction
from django.utils import timezone

from .models import (
    AtualizacaoChamado,
    Chamado,
    Evidencia,
    StatusChamado,
    TipoEventoAtualizacao,
)

STATUS_OPERACIONAIS = frozenset(value for value, _ in StatusChamado.choices)

TITULOS_WHATSAPP = {
    StatusChamado.ABERTO.value: "EMERGENCIAL ABERTA",
    StatusChamado.PENDENTE.value: "EMERGENCIAL PENDENTE",
    StatusChamado.CONCLUIDO.value: "EMERGENCIAL CONCLUÍDA",
    StatusChamado.CANCELADO.value: "EMERGENCIAL CANCELADA",
    StatusChamado.NAO_EMERGENCIAL.value: "NÃO EMERGENCIAL",
}


def is_primeiro_report(chamado: Chamado) -> bool:
    """Indica se o chamado ainda nao possui nenhuma AtualizacaoChamado."""
    return not chamado.atualizacoes.exists()


def obter_tipo_report(chamado: Chamado) -> str:
    """Retorna o tipo_evento adequado para o proximo registro de report."""
    if is_primeiro_report(chamado):
        return TipoEventoAtualizacao.ABERTURA_EMERGENCIAL.value
    return TipoEventoAtualizacao.ATUALIZACAO_STATUS.value


def validar_status_report(status_resultante: str) -> str:
    """Valida que o status informado e operacional aceito pelo model Chamado.

    Levanta ValueError se o status nao constar das choices de StatusChamado.
    "abertura_emergencial" e "emergencial_aberta" sao explicitamente rejeitados
    porque representam evento, nao status do chamado.
    """
    if status_resultante not in STATUS_OPERACIONAIS:
        raise ValueError(
            f"Status invalido para report: {status_resultante!r}."
        )
    return status_resultante


def registrar_report(
    chamado: Chamado,
    texto_atualizacao: str,
    status_resultante: str | None = None,
    usuario=None,
    evidencias: list | None = None,
) -> AtualizacaoChamado:
    """Cria uma AtualizacaoChamado e sincroniza o status do Chamado.

    Regras:
    - No primeiro report (chamado.atualizacoes vazio), tipo_evento sera
      "abertura_emergencial" e o status_resultante padrao e "aberto".
    - Em atualizacoes posteriores, tipo_evento sera "atualizacao_status" e
      status_resultante e obrigatorio.
    - Em ambos os casos, status_resultante e validado contra os status
      operacionais aceitos.
    - O Chamado.status e atualizado para o status_resultante.
    - Se usuario estiver autenticado, e gravado em
      AtualizacaoChamado.criado_por e em Chamado.atualizado_por.
    """
    if not texto_atualizacao or not texto_atualizacao.strip():
        raise ValueError("texto_atualizacao e obrigatorio e nao pode ser vazio.")

    primeiro_report = is_primeiro_report(chamado)

    if primeiro_report:
        tipo_evento = TipoEventoAtualizacao.ABERTURA_EMERGENCIAL.value
        if status_resultante is None:
            status_resultante = StatusChamado.ABERTO.value
    else:
        tipo_evento = TipoEventoAtualizacao.ATUALIZACAO_STATUS.value
        if status_resultante is None:
            raise ValueError(
                "status_resultante e obrigatorio em atualizacoes posteriores."
            )

    status_resultante = validar_status_report(status_resultante)

    usuario_autenticado = (
        usuario if usuario is not None and getattr(usuario, "is_authenticated", False)
        else None
    )

    with transaction.atomic():
        atualizacao = AtualizacaoChamado.objects.create(
            chamado=chamado,
            tipo_evento=tipo_evento,
            texto_atualizacao=texto_atualizacao,
            status_resultante=status_resultante,
            criado_por=usuario_autenticado,
        )
        if evidencias:
            EXTENSOES_PERMITIDAS = {
                "jpg", "jpeg", "png", "webp", "gif", "heic",
                "mp4", "mov", "avi", "mkv", "webm", "pdf",
            }
            TAMANHO_MAXIMO = 20 * 1024 * 1024  # 20 MB
            MAX_ARQUIVOS = 10

            if len(evidencias) > MAX_ARQUIVOS:
                raise ValueError(
                    f"Máximo de {MAX_ARQUIVOS} arquivos por atualização."
                )

            for ordem, arquivo in enumerate(evidencias):
                if not arquivo:
                    continue
                if arquivo.size > TAMANHO_MAXIMO:
                    raise ValueError(
                        f"Arquivo '{arquivo.name}' excede o limite de 20 MB."
                    )
                ext = arquivo.name.rsplit(".", 1)[-1].lower() if "." in arquivo.name else ""
                if ext not in EXTENSOES_PERMITIDAS:
                    raise ValueError(
                        f"Tipo de arquivo não permitido: '{arquivo.name}'. "
                        f"Permitidos: imagens, vídeos e PDF."
                    )
                ev = Evidencia(atualizacao=atualizacao, ordem=ordem)
                ev.arquivo = arquivo
                ev.detectar_tipo()
                ev.save()
        chamado.status = status_resultante
        if usuario_autenticado is not None:
            chamado.atualizado_por = usuario_autenticado
        chamado.save(update_fields=["status", "atualizado_por", "atualizado_em"])

    return atualizacao


# === Geracao de texto WhatsApp =============================================
#
# Esta camada e estritamente read-only: nao grava no banco, nao cria
# AtualizacaoChamado, nao altera Chamado.status nem Chamado.atualizado_por.
# `texto_preview` e `status_preview` sao apenas hipoteses visuais para
# pre-visualizar o texto antes de confirmar uma futura gravacao via
# registrar_report().


def formatar_valor_report(valor) -> str:
    """Normaliza qualquer valor para impressao no texto WhatsApp.

    Retorna "-" para None ou strings vazias/somente espacos. Caso contrario,
    converte para string e remove espacos nas extremidades.
    """
    if valor is None:
        return "-"
    texto = str(valor).strip()
    if not texto:
        return "-"
    return texto


def formatar_data_report(valor) -> str:
    """Formata data/datetime em padrao brasileiro 'dd/mm/aaaa HH:MM'.

    Datetime usa 'dd/mm/aaaa HH:MM'; date (sem hora) usa 'dd/mm/aaaa'.
    Tipos nao reconhecidos delegam para formatar_valor_report.
    """
    if valor is None:
        return "-"
    if isinstance(valor, datetime):
        return valor.strftime("%d/%m/%Y %H:%M")
    if isinstance(valor, date):
        return valor.strftime("%d/%m/%Y")
    return formatar_valor_report(valor)


def obter_titulo_whatsapp(chamado: Chamado, status_preview: str | None = None) -> str:
    """Define o titulo do texto WhatsApp segundo a regra de primeiro report.

    Se o chamado ainda nao tem atualizacoes, o titulo sera sempre
    "EMERGENCIAL ABERTA" (abertura emergencial), independentemente de
    qualquer status_preview. Caso contrario, usa status_preview (validado)
    ou chamado.status para mapear o titulo.
    """
    if is_primeiro_report(chamado):
        return "EMERGENCIAL ABERTA"

    if status_preview is not None:
        validar_status_report(status_preview)
        status_base = status_preview
    else:
        status_base = chamado.status

    if status_base not in TITULOS_WHATSAPP:
        raise ValueError(f"Status invalido para titulo: {status_base!r}.")
    return TITULOS_WHATSAPP[status_base]


def gerar_linhas_historico(chamado: Chamado) -> list[str]:
    """Gera a lista cronologica de linhas do historico do chamado.

    Formato de cada linha (otimizado para colar no WhatsApp):
        - HH:MM (DD/MM) texto

    A hora vem no inicio da linha porque a equipe operacional usa o log
    para acompanhar a evolucao em tempo real. O status NAO e repetido por
    atualizacao — ele ja aparece no cabecalho da mensagem (EMERGENCIAL
    PENDENTE / CONCLUIDA / ...), entao colocar de novo so polui o texto.
    """
    atualizacoes = list(chamado.atualizacoes.order_by("criado_em").prefetch_related("evidencias"))
    if not atualizacoes:
        return ["- Sem atualizações registradas."]

    linhas = []
    for atualizacao in atualizacoes:
        momento = atualizacao.criado_em
        if isinstance(momento, datetime):
            momento_local = timezone.localtime(momento) if timezone.is_aware(momento) else momento
            cabecalho = momento_local.strftime("%H:%M (%d/%m)")
        else:
            cabecalho = formatar_data_report(momento)
        texto = (atualizacao.texto_atualizacao or "").strip() or "-"
        linhas.append(f"- {cabecalho} {texto}")
    return linhas


def gerar_texto_whatsapp(
    chamado: Chamado,
    status_preview: str | None = None,
    texto_preview: str | None = None,
) -> str:
    """Monta o texto padronizado para copiar e colar no WhatsApp.

    Funcao pura: nao grava no banco, nao cria AtualizacaoChamado, nao altera
    Chamado.status nem Chamado.atualizado_por. status_preview e texto_preview
    servem apenas para visualizar como o texto ficaria; nao sao persistidos.
    """
    titulo = obter_titulo_whatsapp(chamado, status_preview=status_preview)

    if status_preview is not None and not is_primeiro_report(chamado):
        status_display = dict(StatusChamado.choices).get(status_preview, status_preview)
    else:
        status_display = chamado.get_status_display()

    ativo = chamado.ativo
    fornecedor_nome = (
        chamado.fornecedor.nome if chamado.fornecedor_id else None
    )

    linhas = [
        titulo,
        "",
        "Informamos o acompanhamento da OS emergencial:",
        "",
        f"Número da OS: {formatar_valor_report(chamado.numero_os)}",
        f"Status do atendimento: {formatar_valor_report(status_display)}",
        f"Categoria: {formatar_valor_report(chamado.denominacao)}",
        f"Data de abertura: {formatar_data_report(chamado.data_abertura)}",
        f"Ativo Prisma: {formatar_valor_report(ativo.ativo_prisma)}",
        f"Nome do Site: {formatar_valor_report(ativo.nome_site)}",
        f"Tipo de Prédio: {formatar_valor_report(ativo.tipo_imovel)}",
        f"Endereço: {formatar_valor_report(ativo.endereco)}",
        f"Cidade/UF: {formatar_valor_report(ativo.cidade)}/{formatar_valor_report(ativo.uf)}",
        f"Regional: {formatar_valor_report(ativo.regional)}",
        f"Líder Regional: {formatar_valor_report(ativo.lider_coordenacao)}",
        f"Tipo de imóvel / SLA: {formatar_valor_report(ativo.tipo_site_sla)}",
        f"Fornecedor: {formatar_valor_report(fornecedor_nome)}",
        f"Command Center: {formatar_valor_report(chamado.command_center)}",
        f"Ação tomada: {formatar_valor_report(chamado.acao_tomada)}",
        f"Solicitante: {formatar_valor_report(chamado.solicitante)}",
        f"Contato: {formatar_valor_report(chamado.contato_solicitante)}",
        (
            "Portaria / retirada de chave: "
            f"{formatar_valor_report(chamado.dados_portaria_retirada_chave)}"
        ),
        "Descrição:",
        formatar_valor_report(chamado.detalhamento_situacao),
        "Atualizações:",
    ]
    linhas.extend(gerar_linhas_historico(chamado))

    if texto_preview is not None and str(texto_preview).strip():
        linhas.extend(
            [
                "Prévia da atualização:",
                f"- {str(texto_preview).strip()}",
            ]
        )

    return "\n".join(linhas)


# ─── Criação de chamado ───────────────────────────────────
def criar_chamado(form, usuario=None) -> "Chamado":
    """Persiste um novo Chamado a partir de um ChamadoForm válido."""
    chamado = form.save(commit=False)
    usuario_autenticado = (
        usuario
        if usuario is not None and getattr(usuario, "is_authenticated", False)
        else None
    )
    if usuario_autenticado:
        chamado.criado_por = usuario_autenticado
        chamado.atualizado_por = usuario_autenticado
    chamado.save()
    return chamado


# ─── Conclusão de obra ────────────────────────────────────
def concluir_obra(obra) -> bool:
    """
    Marca a obra como concluída com a data de hoje.
    Retorna True se concluiu, False se já estava concluída.
    """
    from datetime import date
    if obra.data_fim_real:
        return False
    obra.data_fim_real = date.today()
    obra.save(update_fields=["data_fim_real", "atualizado_em"])
    return True


# ─── Registro de usuário ──────────────────────────────────
def registrar_usuario(first_name: str, last_name: str,
                       email: str, password: str):
    """
    Cria um novo User com username derivado do email.
    Retorna o User criado.
    """
    from django.contrib.auth import get_user_model
    UserModel = get_user_model()
    base_username = email.split("@")[0][:140] or "usuario"
    username = base_username
    sufixo = 1
    while UserModel.objects.filter(username=username).exists():
        sufixo += 1
        username = f"{base_username}{sufixo}"
    return UserModel.objects.create_user(
        username=username,
        email=email,
        first_name=first_name,
        last_name=last_name,
        password=password,
    )
