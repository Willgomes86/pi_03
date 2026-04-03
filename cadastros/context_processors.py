from .validade import obter_alertas_validade


def alerta_validade_global(request):
    if not getattr(request, "user", None) or not request.user.is_authenticated:
        return {"alerta_validade_global": {"tem_alerta": False}}
    return {"alerta_validade_global": obter_alertas_validade()}
