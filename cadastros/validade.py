from datetime import date, timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from .models import AuditoriaEstoqueValidade, EstoqueLote


def _serializar_lote_alerta(lote):
    return {
        "id": lote.id,
        "produto": lote.produto,
        "produto_nome": lote.get_produto_display(),
        "descricao_alerta": lote.descricao_alerta,
        "quantidade": lote.quantidade,
        "unidade": lote.unidade,
        "data_validade": lote.data_validade,
        "dias_para_vencer": lote.dias_para_vencer,
    }


def obter_alertas_validade(data_referencia=None):
    data_referencia = data_referencia or date.today()
    dados = EstoqueLote.alertas(referencia=data_referencia, janela_dias=30)
    proximos = [_serializar_lote_alerta(lote) for lote in dados["proximos"]]
    vencidos = [_serializar_lote_alerta(lote) for lote in dados["vencidos"]]

    mensagem = ""
    texto_acao = ""
    exibir_link = False

    if vencidos:
        mensagem = "Existema produtos vencidos ainda cadastrados no sistema."
        texto_acao = "Clique aqui e veja a lista"
        exibir_link = True
    elif len(proximos) == 1:
        item = proximos[0]
        mensagem = (
            f"{item['descricao_alerta']} está próximo do vencimento, "
            f"vence em {item['data_validade']:%d/%m/%Y}."
        )
    elif len(proximos) > 1:
        mensagem = "Vários produtos cadastrados no sistema estão próximo ao vencimento."
        texto_acao = "Clique aqui e veja a lista"
        exibir_link = True

    return {
        "tem_alerta": bool(proximos or vencidos),
        "tem_vencido": bool(vencidos),
        "mensagem": mensagem,
        "texto_acao": texto_acao,
        "exibir_link": exibir_link,
        "proximos": proximos,
        "vencidos": vencidos,
        "data_referencia": data_referencia,
    }


def registrar_auditoria_validade(
    *,
    evento,
    mensagem,
    usuario=None,
    produto="",
    data_validade=None,
    detalhes=None,
):
    return AuditoriaEstoqueValidade.registrar(
        evento=evento,
        mensagem=mensagem,
        usuario=usuario,
        produto=produto,
        data_validade=data_validade,
        detalhes=detalhes or {},
    )


def _body_email_alerta(alertas):
    linhas = [
        "Alerta automático de validade do estoque",
        f"Data de referência: {alertas['data_referencia']:%d/%m/%Y}",
        "",
    ]

    if alertas["vencidos"]:
        linhas.append("PRODUTOS VENCIDOS:")
        for item in alertas["vencidos"]:
            linhas.append(
                f"- {item['descricao_alerta']} | validade: {item['data_validade']:%d/%m/%Y} "
                f"| saldo: {item['quantidade']} {item['unidade']}"
            )
        linhas.append("")

    if alertas["proximos"]:
        linhas.append("PRODUTOS PRÓXIMOS DO VENCIMENTO (até 30 dias):")
        for item in alertas["proximos"]:
            linhas.append(
                f"- {item['descricao_alerta']} | validade: {item['data_validade']:%d/%m/%Y} "
                f"| saldo: {item['quantidade']} {item['unidade']}"
            )

    linhas.append("")
    linhas.append("Este alerta continua sendo enviado até a baixa do item no estoque.")
    return "\n".join(linhas)


def enviar_alertas_validade_email(*, force=False):
    destinatarios = [
        email.strip()
        for email in getattr(settings, "ESTOQUE_ALERTA_EMAIL_DESTINATARIOS", [])
        if email and email.strip()
    ]
    if not destinatarios:
        return {"enviado": False, "motivo": "sem_destinatarios"}

    alertas = obter_alertas_validade()
    if not alertas["tem_alerta"]:
        return {"enviado": False, "motivo": "sem_alertas"}

    intervalo_horas = max(int(getattr(settings, "ESTOQUE_ALERTA_EMAIL_INTERVALO_HORAS", 24)), 1)
    ultimo_envio = (
        AuditoriaEstoqueValidade.objects.filter(evento=AuditoriaEstoqueValidade.Evento.ALERTA_EMAIL_ENVIADO)
        .order_by("-criado_em")
        .first()
    )
    if (
        not force
        and ultimo_envio
        and (timezone.now() - ultimo_envio.criado_em) < timedelta(hours=intervalo_horas)
    ):
        return {"enviado": False, "motivo": "intervalo"}

    assunto = (
        "ALERTA URGENTE: produtos vencidos no estoque"
        if alertas["tem_vencido"]
        else "ALERTA: produtos próximos do vencimento no estoque"
    )
    corpo = _body_email_alerta(alertas)

    try:
        send_mail(
            subject=assunto,
            message=corpo,
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", ""),
            recipient_list=destinatarios,
            fail_silently=False,
        )
        registrar_auditoria_validade(
            evento=AuditoriaEstoqueValidade.Evento.ALERTA_EMAIL_ENVIADO,
            mensagem=assunto,
            detalhes={
                "destinatarios": destinatarios,
                "qtd_vencidos": len(alertas["vencidos"]),
                "qtd_proximos": len(alertas["proximos"]),
            },
        )
        return {"enviado": True, "assunto": assunto, "destinatarios": destinatarios}
    except Exception as exc:  # pragma: no cover - segurança para produção
        registrar_auditoria_validade(
            evento=AuditoriaEstoqueValidade.Evento.ALERTA_EMAIL_ERRO,
            mensagem="Falha ao enviar alerta de validade por e-mail",
            detalhes={"erro": str(exc), "destinatarios": destinatarios},
        )
        return {"enviado": False, "motivo": "erro_envio", "erro": str(exc)}
