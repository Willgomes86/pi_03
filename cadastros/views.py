from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.contrib.auth.decorators import login_required, user_passes_test
from .forms import FamiliaForm
from .models import Familia, Filho
from django.utils.dateparse import parse_date
from django.http import JsonResponse


def superuser_required(user):
    return user.is_superuser


@login_required(login_url="login")
@user_passes_test(superuser_required, login_url="login")
def cadastro_funcionario(request):
    if not request.user.is_superuser:
        messages.error(request, "Você não tem acesso à página solicitada.")
        return redirect("login")

    if request.method == "POST":
        firstname = request.POST.get("firstname")
        lastname = request.POST.get("lastname")
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        errors = []

        # Validação do primeiro nome
        if not firstname:
            errors.append("O primeiro nome é obrigatório.")

        # Validação do sobrenome
        if not lastname:
            errors.append("O sobrenome é obrigatório.")

        # Validação do nome de usuário
        if not username:
            errors.append("O nome de usuário é obrigatório.")
        elif User.objects.filter(username=username).exists():
            errors.append("Nome de usuário já existe.")

        # Validação do e-mail
        if not email:
            errors.append("O e-mail é obrigatório.")
        else:
            try:
                validate_email(email)
            except ValidationError:
                errors.append("O e-mail informado é inválido.")

        # Validação da senha
        if not password:
            errors.append("A senha é obrigatória.")
        elif password != confirm_password:
            errors.append("As senhas não coincidem.")

        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, "cadastro_funcionario.html")

        # Criação do usuário
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=firstname,
            last_name=lastname,
        )

        # Verifica se as checkboxes estão marcadas
        is_admin = "is_admin" in request.POST
        is_staff = "is_staff" in request.POST

        # Atualiza os campos do usuário com base nos valores das checkboxes
        if is_admin:
            user.is_superuser = True  # Define o usuário como superuser se marcado
        user.is_staff = is_staff  # Define o usuário como staff se marcado

        user.save()

        # Autentica e loga o usuário imediatamente após a criação (opcional)
        user = authenticate(username=username, password=password)
        if user is not None:
            auth_login(request, user)

        messages.success(request, "Usuário criado com sucesso.")
        return redirect(
            "login"
        )  # Redireciona para a página de login ou outra apropriada

    return render(request, "cadastro_funcionario.html")


def home(request):
    return render(request, "home.html")


def login(request):
    if request.method == "GET":
        if request.user.is_authenticated:
            return redirect("home")  # Redireciona para a home se já estiver logado
        return render(request, "login.html")

    elif request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            auth_login(request, user)
            return redirect("cadastrar_familia")  # Redireciona para a home após o login
        else:
            messages.error(request, "Nome de usuário ou senha inválidos.")
            return render(request, "login.html")


def nossa_historia(request):
    return render(request, "nossa_historia.html")

def printNumbers():
    for i in range(10001):
        print(i)
@login_required()
def cadastrar_familia(request):
    if request.method == "POST":
        # Recupera os dados do POST
        codigo = request.POST.get("codigo")
        lider_familia = request.POST.get("lider_familia")
        data_nasc_lider = request.POST.get("data_nasc_lider")
        cidade_estado_nasc_lider = request.POST.get("cidade_estado_nasc_lider")
        profissao_lider = request.POST.get("profissao_lider")
        escolaridade_lider = request.POST.get("escolaridade_lider")
        cpf_lider = request.POST.get("cpf_lider")
        rg_lider = request.POST.get("rg_lider")
        conjuge = request.POST.get("conjuge")
        data_nasc_conj = request.POST.get("data_nasc_conj")
        cidade_estado_nasc_conj = request.POST.get("cidade_estado_nasc_conj")
        profissao_conj = request.POST.get("profissao_conj")
        escolaridade_conj = request.POST.get("escolaridade_conj")
        cpf_conj = request.POST.get("cpf_conj")
        rg_conj = request.POST.get("rg_conj")
        estado_civil = request.POST.get("estado_civil")
        religiao = request.POST.get("religiao")
        bolsa_familia = request.POST.get("bolsa_familia") == "sim"
        outro_beneficio = request.POST.get("outro_beneficio") == "sim"
        renda_familiar = request.POST.get("renda_familiar")
        tempo_bairro = request.POST.get("tempo_bairro")
        tempo_cidade = request.POST.get("tempo_cidade")
        residencia = request.POST.get("residencia")
        qt_dependentes = request.POST.get("qt_dependentes")
        vacina_em_dia = request.POST.get("vacina_em_dia") == "sim"
        doenca_cronica = request.POST.get("doenca_cronica")
        qt_moradores = request.POST.get("qt_moradores")
        contato = request.POST.get("contato")
        endereco = request.POST.get("endereco")
        tel_fixo = request.POST.get("tel_fixo")
        celular = request.POST.get("celular")
        email = request.POST.get("email")
        obs = request.POST.get("obs")
        data_visita = request.POST.get("data_visita")
        responsavel_visita = request.POST.get("responsavel_visita")
        tem_filhos = request.POST.get("tem_filhos") == "sim"

        # Certifique-se de que qt_filhos seja definida antes de ser convertida
        qt_filhos = request.POST.get("qt_filhos") if tem_filhos else 0

        # Funções para converter dados
        def convert_to_float(value):
            try:
                return float(value.replace(",", ".")) if value else None
            except (ValueError, AttributeError):
                return None

        def convert_to_int(value):
            try:
                return int(value) if value else 0
            except (ValueError, TypeError):
                return 0

        renda_familiar = convert_to_float(renda_familiar)
        qt_dependentes = convert_to_int(qt_dependentes)
        qt_moradores = convert_to_int(qt_moradores)
        qt_filhos = convert_to_int(qt_filhos)

        # Converte datas
        def parse_date_safe(date_str):
            try:
                return parse_date(date_str)
            except (ValueError, TypeError):
                return None

        data_nasc_lider = parse_date_safe(data_nasc_lider)
        data_nasc_conj = parse_date_safe(data_nasc_conj)
        data_visita = parse_date_safe(data_visita)

        # Cria a instância da família
        familia = Familia.objects.create(
            codigo=codigo,
            lider_familia=lider_familia,
            dt_nasc_lider=data_nasc_lider,
            cidade_estado_nasc_lider=cidade_estado_nasc_lider,
            profissao_lider=profissao_lider,
            escolaridade_lider=escolaridade_lider,
            cpf_lider=cpf_lider,
            rg_lider=rg_lider,
            conjuge=conjuge,
            dt_nasc_conjuge=data_nasc_conj,
            cidade_estado_nasc_conjuge=cidade_estado_nasc_conj,
            profissao_conjuge=profissao_conj,
            escolaridade_conjuge=escolaridade_conj,
            cpf_conjuge=cpf_conj,
            rg_conjuge=rg_conj,
            estado_civil=estado_civil,
            religiao=religiao,
            bolsa_familia=bolsa_familia,
            outro_beneficio=outro_beneficio,
            renda_familiar=renda_familiar,
            tempo_bairro=tempo_bairro,
            tempo_cidade=tempo_cidade,
            residencia=residencia,
            qt_dependentes=qt_dependentes,
            carteira_vacinacao=vacina_em_dia,
            doenca_cronica=doenca_cronica,
            qt_outros_moradores=qt_moradores,
            contato=contato,
            endereco=endereco,
            tel_fixo=tel_fixo,
            celular=celular,
            email=email,
            observacoes=obs,
            data_visita=data_visita,
            responsavel_visita=responsavel_visita,
            tem_filhos=tem_filhos,
            qt_filhos=qt_filhos,
        )

        # Se a família tiver filhos, cria as instâncias correspondentes
        for i in range(qt_filhos):
            nome_filho = request.POST.get(f"nome{i}")
            dt_nasc_filho = parse_date_safe(request.POST.get(f"data_nascimento{i}"))
            escola_filho = request.POST.get(f"escola{i}")
            serie_filho = request.POST.get(f"serie{i}")

            print(f"Processing child {i + 1}:")
            print(f"Nome: {nome_filho}")
            print(f"Data de Nascimento: {dt_nasc_filho}")
            print(f"Escola: {escola_filho}")
            print(f"Série: {serie_filho}")

            if nome_filho and dt_nasc_filho and escola_filho and serie_filho:
                Filho.objects.create(
                    familia=familia,
                    nome=nome_filho,
                    dt_nasc_filho=dt_nasc_filho,
                    escola=escola_filho,
                    serie=serie_filho,
                )
            else:
                print(f"Dados inválidos para o filho {i + 1}")

        messages.success(request, "Família cadastrada com sucesso.")
        return redirect("cadastrar_familia")

    # # Calcula o próximo código
    # ultimo_codigo = Familia.objects.order_by('-codigo').first()
    # proximo_codigo = ultimo_codigo.codigo + 1 if ultimo_codigo else 1

    # return render(request, "cadastrar_familia.html", {'proximo_codigo': proximo_codigo})
    return render(request, "cadastrar_familia.html")


@login_required
def alterar_cadastro(request):
    mensagem = None
    cadastros = None

    if request.method == "POST":
        codigo = request.POST.get("codigo", "").strip()

        if codigo:
            try:
                familia = Familia.objects.get(codigo=codigo)
                form = FamiliaForm(request.POST, instance=familia)

                if form.is_valid():
                    familia = form.save()

                    # Atualiza ou remove os filhos existentes
                    Filho.objects.filter(familia=familia).delete()
                    for i in range(familia.qt_filhos):
                        nome_filho = request.POST.get(f"nome{i}")
                        dt_nasc_filho = parse_date(
                            request.POST.get(f"data_nascimento{i}")
                        )
                        escola_filho = request.POST.get(f"escola{i}")
                        serie_filho = request.POST.get(f"serie{i}")

                        if (
                            nome_filho
                            and dt_nasc_filho
                            and escola_filho
                            and serie_filho
                        ):
                            Filho.objects.create(
                                familia=familia,
                                nome=nome_filho,
                                dt_nasc_filho=dt_nasc_filho,
                                escola=escola_filho,
                                serie=serie_filho,
                            )

                    messages.success(request, "Cadastro alterado com sucesso.")
                    return redirect(
                        "alterar_cadastro"
                    )  # Redireciona para evitar reenvio de formulário
                else:
                    mensagem = "Erro ao atualizar cadastro. Verifique os dados."
                    print(form.errors)  # Adicione isso para depurar erros do formulário

                cadastros = [familia]
            except Familia.DoesNotExist:
                mensagem = "Cadastro não encontrado"
                form = FamiliaForm()
        else:
            mensagem = "Código não pode estar vazio"
            form = FamiliaForm()
    else:
        codigo = request.GET.get("codigo", "").strip()
        if codigo:
            try:
                familia = Familia.objects.get(codigo=codigo)
                form = FamiliaForm(instance=familia)
                cadastros = [familia]
            except Familia.DoesNotExist:
                mensagem = "Cadastro não encontrado"
                form = FamiliaForm()
        else:
            form = FamiliaForm()

    return render(
        request,
        "alterar_cadastro.html",
        {"form": form, "mensagem": mensagem, "cadastros": cadastros},
    )


def buscar_cadastro(request):
    termo = request.GET.get("term", "")
    cadastros = (
        Familia.objects.filter(lider_familia__icontains=termo)
        if termo
        else Familia.objects.none()
    )
    return render(request, "buscar_cadastro.html", {"cadastros": cadastros})