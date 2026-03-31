from django import forms
from django.contrib.auth.models import User

from .models import Doacao, Doador, Familia, Repasse


class StyledModelForm(forms.ModelForm):
    """Aplica classes visuais consistentes aos campos do formulário."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            widget = field.widget
            if isinstance(widget, forms.CheckboxInput):
                widget.attrs["class"] = "form-check-input"
                continue

            css_class = "form-select" if isinstance(widget, forms.Select) else "form-control"
            existing = widget.attrs.get("class", "")
            widget.attrs["class"] = f"{existing} {css_class}".strip()
            if name in {"data_doacao", "data_repasse"}:
                widget.attrs["type"] = "date"


class LoginForm(forms.Form):
    username = forms.CharField(
        label="Usuário",
        max_length=150,
        widget=forms.TextInput(
            attrs={"class": "form-control form-control-lg", "placeholder": "Digite seu usuário"}
        ),
    )
    password = forms.CharField(
        label="Senha",
        widget=forms.PasswordInput(
            attrs={"class": "form-control form-control-lg", "placeholder": "Digite sua senha"}
        ),
    )


class PerfilForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "email"]
        labels = {
            "first_name": "Nome",
            "last_name": "Sobrenome",
            "email": "E-mail",
        }
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Seu nome"}),
            "last_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Seu sobrenome"}),
            "email": forms.EmailInput(attrs={"class": "form-control", "placeholder": "seuemail@exemplo.com"}),
        }


class FamiliaForm(StyledModelForm):
    class Meta:
        model = Familia
        fields = "__all__"


class DoadorForm(StyledModelForm):
    class Meta:
        model = Doador
        fields = ["nome", "documento", "email", "telefone", "ativo"]


class DoacaoForm(StyledModelForm):
    class Meta:
        model = Doacao
        fields = [
            "doador",
            "categoria",
            "descricao",
            "valor",
            "quantidade",
            "unidade",
            "data_doacao",
            "observacoes",
        ]
        widgets = {
            "data_doacao": forms.DateInput(attrs={"type": "date"}),
            "observacoes": forms.Textarea(attrs={"rows": 3}),
        }


class RepasseForm(StyledModelForm):
    class Meta:
        model = Repasse
        fields = [
            "familia",
            "doacao",
            "categoria",
            "descricao",
            "valor_estimado",
            "quantidade",
            "unidade",
            "data_repasse",
            "status",
            "observacoes",
        ]
        widgets = {
            "data_repasse": forms.DateInput(attrs={"type": "date"}),
            "observacoes": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["familia"].queryset = Familia.objects.order_by("lider_familia")
        self.fields["doacao"].queryset = Doacao.objects.select_related("doador").order_by("-data_doacao", "-id")
        self.fields["doacao"].required = False
