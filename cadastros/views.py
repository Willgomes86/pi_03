from datetime import date
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import transaction
from django.db.models import DecimalField, Q, Sum, Value
from django.db.models.functions import Coalesce
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils.dateparse import parse_date

from .forms import DoacaoForm, FamiliaForm, LoginForm, PerfilForm, RepasseForm
from .models import AuditoriaEstoqueValidade, Doacao, EstoqueItem, EstoqueLote, Familia, Filho, Repasse
from .validade import obter_alertas_validade, registrar_auditoria_validade


def superuser_required(user):
    return user.is_superuser


def _parse_decimal(value):
    if not value:
        return None
    try:
        normalized = str(value).strip()
        if "," in normalized and "." in normalized:
            normalized = normalized.replace(".", "").replace(",", ".")
        elif "," in normalized:
            normalized = normalized.replace(",", ".")
        return Decimal(normalized)
    except (InvalidOperation, TypeError):
        return None


def _parse_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _estoque_resumo():
    itens = {item.produto: item for item in EstoqueItem.objects.all()}
    resumo = []
    for produto_codigo, produto_nome in EstoqueItem.produtos_controlados():
        item = itens.get(produto_codigo)
        resumo.append(
            {
                "codigo": produto_codigo,
                "produto": produto_nome,
                "quantidade": item.quantidade if item else 0,
                "unidade": item.unidade if item else "un",
            }
        )
    return resumo


def home(request):
    context = {"indicadores": None, "doacoes_recentes": [], "repasses_recentes": [], "estoque_itens": []}

    if request.user.is_authenticated:
        total_familias = Familia.objects.count()
        total_doacoes = Doacao.objects.count()
        total_repasses = Repasse.objects.count()

        valor_doado = Doacao.objects.aggregate(
            total=Coalesce(
                Sum("valor"),
                Value(0),
                output_field=DecimalField(max_digits=12, decimal_places=2),
            )
        )["total"]
        valor_repassado = Repasse.objects.aggregate(
            total=Coalesce(
                Sum("valor_estimado"),
                Value(0),
                output_field=DecimalField(max_digits=12, decimal_places=2),
            )
        )["total"]

        context["indicadores"] = {
            "total_familias": total_familias,
            "total_doacoes": total_doacoes,
            "total_repasses": total_repasses,
            "valor_doado": valor_doado,
            "valor_repassado": valor_repassado,
            "saldo": valor_doado - valor_repassado,
        }
        context["doacoes_recentes"] = Doacao.objects.all()[:5]
        context["repasses_recentes"] = Repasse.objects.select_related("familia").all()[:5]
        context["estoque_itens"] = _estoque_resumo()[:5]

    return render(request, "home.html", context)


def login(request):
    if request.user.is_authenticated:
        return redirect("home")

    form = LoginForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        username = form.cleaned_data["username"]
        password = form.cleaned_data["password"]

        user = authenticate(request, username=username, password=password)
        if user is None:
            messages.error(request, "Usuário ou senha inválidos.")
        else:
            auth_login(request, user)
            messages.success(request, f"Bem-vindo, {user.first_name or user.username}.")
            return redirect("home")

    return render(request, "login.html", {"form": form})


@login_required(login_url="login")
def perfil(request):
    form = PerfilForm(request.POST or None, instance=request.user)
    if request.method == "POST":
        if form.is_valid():
            form.save()
            messages.success(request, "Perfil atualizado com sucesso.")
            return redirect("perfil")
        messages.error(request, "Não foi possível atualizar o perfil. Revise os campos.")

    return render(request, "perfil.html", {"form": form})


@login_required(login_url="login")
@user_passes_test(superuser_required, login_url="login")
def cadastro_funcionario(request):
    if request.method == "POST":
        firstname = request.POST.get("firstname")
        lastname = request.POST.get("lastname")
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        errors = []

        if not firstname:
            errors.append("O primeiro nome é obrigatório.")
        if not lastname:
            errors.append("O sobrenome é obrigatório.")

        if not username:
            errors.append("O nome de usuário é obrigatório.")
        elif User.objects.filter(username=username).exists():
            errors.append("Nome de usuário já existe.")

        if not email:
            errors.append("O e-mail é obrigatório.")
        else:
            try:
                validate_email(email)
            except ValidationError:
                errors.append("O e-mail informado é inválido.")

        if not password:
            errors.append("A senha é obrigatória.")
        elif password != confirm_password:
            errors.append("As senhas não coincidem.")

        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, "cadastro_funcionario.html")

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=firstname,
            last_name=lastname,
        )

        user.is_superuser = "is_admin" in request.POST
        user.is_staff = "is_staff" in request.POST
        user.save()

        messages.success(request, "Usuário criado com sucesso.")
        return redirect("cadastro_funcionario")

    return render(request, "cadastro_funcionario.html")


def nossa_historia(request):
    return render(request, "nossa_historia.html")


@login_required(login_url="login")
def cadastrar_familia(request):
    if request.method == "POST":
        codigo_raw = request.POST.get("codigo", "").strip()
        tem_filhos = request.POST.get("tem_filhos") == "sim"
        qt_filhos = _parse_int(request.POST.get("qt_filhos") if tem_filhos else 0)

        familia_data = {
            "lider_familia": request.POST.get("lider_familia"),
            "dt_nasc_lider": parse_date(request.POST.get("data_nasc_lider")),
            "cidade_estado_nasc_lider": request.POST.get("cidade_estado_nasc_lider"),
            "profissao_lider": request.POST.get("profissao_lider"),
            "escolaridade_lider": request.POST.get("escolaridade_lider"),
            "cpf_lider": request.POST.get("cpf_lider"),
            "rg_lider": request.POST.get("rg_lider"),
            "conjuge": request.POST.get("conjuge"),
            "dt_nasc_conjuge": parse_date(request.POST.get("data_nasc_conj")),
            "cidade_estado_nasc_conjuge": request.POST.get("cidade_estado_nasc_conj"),
            "profissao_conjuge": request.POST.get("profissao_conj"),
            "escolaridade_conjuge": request.POST.get("escolaridade_conj"),
            "cpf_conjuge": request.POST.get("cpf_conj"),
            "rg_conjuge": request.POST.get("rg_conj"),
            "estado_civil": request.POST.get("estado_civil"),
            "religiao": request.POST.get("religiao"),
            "bolsa_familia": request.POST.get("bolsa_familia") == "sim",
            "outro_beneficio": request.POST.get("outro_beneficio") == "sim",
            "renda_familiar": _parse_decimal(request.POST.get("renda_familiar")),
            "tempo_bairro": request.POST.get("tempo_bairro"),
            "tempo_cidade": request.POST.get("tempo_cidade"),
            "residencia": request.POST.get("residencia"),
            "qt_dependentes": _parse_int(request.POST.get("qt_dependentes")),
            "carteira_vacinacao": request.POST.get("vacina_em_dia") == "sim",
            "doenca_cronica": request.POST.get("doenca_cronica"),
            "qt_outros_moradores": _parse_int(request.POST.get("qt_moradores")),
            "contato": request.POST.get("contato"),
            "endereco": request.POST.get("endereco"),
            "tel_fixo": request.POST.get("tel_fixo"),
            "celular": request.POST.get("celular"),
            "email": request.POST.get("email"),
            "observacoes": request.POST.get("obs"),
            "data_visita": parse_date(request.POST.get("data_visita")),
            "responsavel_visita": request.POST.get("responsavel_visita"),
            "tem_filhos": tem_filhos,
            "qt_filhos": qt_filhos,
        }

        if codigo_raw.isdigit():
            familia_data["codigo"] = int(codigo_raw)

        try:
            familia = Familia.objects.create(**familia_data)
        except Exception:
            messages.error(request, "Não foi possível cadastrar a família. Revise os dados.")
            return render(request, "cadastrar_familia.html")

        for i in range(qt_filhos):
            nome_filho = request.POST.get(f"nome{i}")
            dt_nasc_filho = parse_date(request.POST.get(f"data_nascimento{i}"))
            escola_filho = request.POST.get(f"escola{i}")
            serie_filho = request.POST.get(f"serie{i}")

            if nome_filho and dt_nasc_filho and escola_filho and serie_filho:
                Filho.objects.create(
                    familia=familia,
                    nome=nome_filho,
                    dt_nasc_filho=dt_nasc_filho,
                    escola=escola_filho,
                    serie=serie_filho,
                )

        messages.success(request, "Família cadastrada com sucesso.")
        return redirect("cadastrar_familia")

    return render(request, "cadastrar_familia.html")


@login_required(login_url="login")
def alterar_cadastro(request):
    mensagem = None
    cadastros = None
    form = FamiliaForm()

    if request.method == "POST":
        codigo = request.POST.get("codigo", "").strip()
        if not codigo:
            mensagem = "Código não pode estar vazio."
        else:
            try:
                familia = Familia.objects.get(codigo=codigo)
                form = FamiliaForm(request.POST, instance=familia)
                if form.is_valid():
                    familia = form.save()
                    Filho.objects.filter(familia=familia).delete()

                    for i in range(familia.qt_filhos or 0):
                        nome_filho = request.POST.get(f"nome{i}")
                        dt_nasc_filho = parse_date(request.POST.get(f"data_nascimento{i}"))
                        escola_filho = request.POST.get(f"escola{i}")
                        serie_filho = request.POST.get(f"serie{i}")

                        if nome_filho and dt_nasc_filho and escola_filho and serie_filho:
                            Filho.objects.create(
                                familia=familia,
                                nome=nome_filho,
                                dt_nasc_filho=dt_nasc_filho,
                                escola=escola_filho,
                                serie=serie_filho,
                            )

                    messages.success(request, "Cadastro alterado com sucesso.")
                    return redirect("alterar_cadastro")

                mensagem = "Erro ao atualizar cadastro. Verifique os dados."
                cadastros = [familia]
            except Familia.DoesNotExist:
                mensagem = "Cadastro não encontrado."
    else:
        codigo = request.GET.get("codigo", "").strip()
        if codigo:
            try:
                familia = Familia.objects.get(codigo=codigo)
                form = FamiliaForm(instance=familia)
                cadastros = [familia]
            except Familia.DoesNotExist:
                mensagem = "Cadastro não encontrado."

    return render(
        request,
        "alterar_cadastro.html",
        {"form": form, "mensagem": mensagem, "cadastros": cadastros},
    )


@login_required(login_url="login")
def buscar_cadastro(request):
    termo = request.GET.get("term", "").strip()
    codigo = request.GET.get("codigo", "").strip()

    if codigo.isdigit():
        cadastros = Familia.objects.filter(codigo=int(codigo))
    elif termo:
        cadastros = Familia.objects.filter(lider_familia__icontains=termo)
    else:
        cadastros = Familia.objects.none()

    return render(request, "buscar_cadastro.html", {"cadastros": cadastros})


@login_required(login_url="login")
def buscar_cadastro_ajax(request):
    termo = request.GET.get("term", "").strip()
    if not termo:
        return JsonResponse([], safe=False)

    filtros = Q(lider_familia__icontains=termo)
    if termo.isdigit():
        filtros |= Q(codigo=int(termo))

    resultados = (
        Familia.objects.filter(filtros)
        .order_by("lider_familia")
        .values("codigo", "lider_familia")[:10]
    )
    return JsonResponse(list(resultados), safe=False)


@login_required(login_url="login")
def doacoes(request):
    form = DoacaoForm(request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            try:
                with transaction.atomic():
                    doacao = form.save(commit=False)
                    doacao.registrada_por = request.user
                    doacao.save()
                    EstoqueItem.registrar_entrada(
                        produto=doacao.produto,
                        quantidade=doacao.quantidade,
                        unidade=doacao.unidade,
                        data_validade=doacao.data_validade,
                        doacao=doacao,
                    )
                messages.success(request, "Doação registrada com sucesso.")
                return redirect("doacoes")
            except ValidationError as exc:
                form.add_error(None, exc.messages[0])
        messages.error(request, "Não foi possível registrar a doação. Revise os dados.")

    ultimas_doacoes = Doacao.objects.all()[:20]
    return render(
        request,
        "doacoes.html",
        {
            "form": form,
            "ultimas_doacoes": ultimas_doacoes,
            "estoque_itens": _estoque_resumo(),
            "produtos_pereciveis": list(Doacao.produtos_pereciveis()),
        },
    )


def _contexto_repasses(form, **extra):
    contexto = {
        "form": form,
        "ultimos_repasses": Repasse.objects.select_related("familia", "doacao").all()[:20],
        "estoque_itens": _estoque_resumo(),
        "mostrar_confirmacao_vencido": False,
        "payload_confirmacao_vencido": [],
        "produto_bloqueado_nome": "",
        "data_validade_bloqueada": None,
    }
    contexto.update(extra)
    return contexto


def _payload_confirmacao_vencido(post_data):
    payload = []
    for chave, valores in post_data.lists():
        if chave in {"csrfmiddlewaretoken", "confirmar_doacao_vencida", "senha_confirmacao"}:
            continue
        for valor in valores:
            payload.append({"chave": chave, "valor": valor})
    return payload


@login_required(login_url="login")
def repasses(request):
    form = RepasseForm(request.POST or None)
    if request.method == "POST":
        confirmar_doacao_vencida = request.POST.get("confirmar_doacao_vencida") == "1"
        senha_confirmacao = request.POST.get("senha_confirmacao", "").strip()

        if form.is_valid():
            try:
                with transaction.atomic():
                    repasse = form.save(commit=False)
                    repasse.responsavel = request.user
                    permitir_vencido = False
                    lote_vencido = None

                    if repasse.status == Repasse.Status.ENTREGUE and Doacao.is_produto_perecivel(repasse.produto):
                        lote_vencido = (
                            EstoqueLote.lotes_ativos()
                            .filter(produto=repasse.produto, data_validade__lt=date.today())
                            .order_by("data_validade", "id")
                            .first()
                        )
                        if lote_vencido and not confirmar_doacao_vencida:
                            registrar_auditoria_validade(
                                evento=AuditoriaEstoqueValidade.Evento.BLOQUEIO_DOACAO_VENCIDO,
                                mensagem="Tentativa bloqueada de repasse com item vencido.",
                                usuario=request.user,
                                produto=repasse.produto,
                                data_validade=lote_vencido.data_validade,
                                detalhes={"quantidade_solicitada": repasse.quantidade},
                            )
                            messages.error(request, "Você está doando produto vencido.")
                            return render(
                                request,
                                "repasses.html",
                                _contexto_repasses(
                                    form,
                                    mostrar_confirmacao_vencido=True,
                                    payload_confirmacao_vencido=_payload_confirmacao_vencido(request.POST),
                                    produto_bloqueado_nome=lote_vencido.descricao_alerta,
                                    data_validade_bloqueada=lote_vencido.data_validade,
                                ),
                            )

                        if lote_vencido and confirmar_doacao_vencida:
                            usuario_confirmado = authenticate(
                                request,
                                username=request.user.username,
                                password=senha_confirmacao,
                            )
                            if usuario_confirmado is None:
                                registrar_auditoria_validade(
                                    evento=AuditoriaEstoqueValidade.Evento.REAUTENTICACAO_FALHA,
                                    mensagem="Reautenticação inválida para liberar repasse de produto vencido.",
                                    usuario=request.user,
                                    produto=repasse.produto,
                                    data_validade=lote_vencido.data_validade,
                                )
                                messages.error(request, "Você está doando produto vencido.")
                                form.add_error(None, "Senha inválida para confirmar repasse de produto vencido.")
                                return render(
                                    request,
                                    "repasses.html",
                                    _contexto_repasses(
                                        form,
                                        mostrar_confirmacao_vencido=True,
                                        payload_confirmacao_vencido=_payload_confirmacao_vencido(request.POST),
                                        produto_bloqueado_nome=lote_vencido.descricao_alerta,
                                        data_validade_bloqueada=lote_vencido.data_validade,
                                    ),
                                )

                            registrar_auditoria_validade(
                                evento=AuditoriaEstoqueValidade.Evento.REAUTENTICACAO_SUCESSO,
                                mensagem="Reautenticação concluída para repasse de produto vencido.",
                                usuario=request.user,
                                produto=repasse.produto,
                                data_validade=lote_vencido.data_validade,
                                detalhes={"quantidade_solicitada": repasse.quantidade},
                            )
                            permitir_vencido = True

                    if repasse.status == Repasse.Status.ENTREGUE:
                        EstoqueItem.registrar_saida(
                            produto=repasse.produto,
                            quantidade=repasse.quantidade,
                            unidade=repasse.unidade,
                            permitir_vencido=permitir_vencido,
                        )
                    repasse.save()
                    if permitir_vencido:
                        registrar_auditoria_validade(
                            evento=AuditoriaEstoqueValidade.Evento.REPASSE_VENCIDO_CONFIRMADO,
                            mensagem="Repasse de produto vencido autorizado mediante senha.",
                            usuario=request.user,
                            produto=repasse.produto,
                            data_validade=lote_vencido.data_validade if lote_vencido else None,
                            detalhes={"repasse_id": repasse.id, "quantidade": repasse.quantidade},
                        )
                messages.success(request, "Repasse registrado com sucesso.")
                return redirect("repasses")
            except ValidationError as exc:
                form.add_error(None, exc.messages[0])
        messages.error(request, "Não foi possível registrar o repasse. Revise os dados.")

    return render(request, "repasses.html", _contexto_repasses(form))


@login_required(login_url="login")
def estoque(request):
    return render(request, "estoque.html", {"estoque_itens": _estoque_resumo()})


@login_required(login_url="login")
def alertas_validade(request):
    return render(request, "alertas_validade.html", {"alertas": obter_alertas_validade()})
