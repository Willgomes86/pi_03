from django import forms
from django.contrib.auth.models import User

from .models import Doacao, Doador, EstoqueItem, Familia, Repasse


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
            if name in {"data_doacao", "data_repasse", "data_validade"}:
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
            "categoria",
            "produto",
            "descricao",
            "valor",
            "quantidade",
            "unidade",
            "data_doacao",
            "data_validade",
            "observacoes",
        ]
        widgets = {
            "data_doacao": forms.DateInput(attrs={"type": "date"}),
            "data_validade": forms.DateInput(attrs={"type": "date"}),
            "observacoes": forms.Textarea(attrs={"rows": 3}),
        }

    def clean(self):
        cleaned_data = super().clean()
        categoria = cleaned_data.get("categoria")
        produto = cleaned_data.get("produto")

        if categoria == Doacao.Categoria.FINANCEIRA:
            cleaned_data["produto"] = Doacao.Produto.NAO_APLICAVEL
            cleaned_data["data_validade"] = None
            return cleaned_data

        if produto == Doacao.Produto.NAO_APLICAVEL:
            self.add_error("produto", "Selecione um produto para registrar doação de itens.")
            cleaned_data["data_validade"] = None
            return cleaned_data

        data_validade = cleaned_data.get("data_validade")
        if Doacao.is_produto_perecivel(produto) and not data_validade:
            self.add_error("data_validade", "Informe a data de validade para produtos perecíveis.")
        if not Doacao.is_produto_perecivel(produto):
            cleaned_data["data_validade"] = None

        return cleaned_data


class RepasseForm(StyledModelForm):
    class Meta:
        model = Repasse
        fields = [
            "familia",
            "doacao",
            "categoria",
            "produto",
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
        self.fields["doacao"].queryset = Doacao.objects.order_by("-data_doacao", "-id")
        self.fields["doacao"].required = False

    def clean(self):
        cleaned_data = super().clean()
        categoria = cleaned_data.get("categoria")
        produto = cleaned_data.get("produto")
        quantidade = cleaned_data.get("quantidade") or 0
        status = cleaned_data.get("status")

        if categoria == Doacao.Categoria.FINANCEIRA:
            cleaned_data["produto"] = Doacao.Produto.NAO_APLICAVEL
            return cleaned_data

        if produto == Doacao.Produto.NAO_APLICAVEL:
            self.add_error("produto", "Selecione um produto para repassar itens.")
            return cleaned_data

        if status == Repasse.Status.ENTREGUE and quantidade > 0:
            saldo = EstoqueItem.objects.filter(produto=produto).values_list("quantidade", flat=True).first() or 0
            if quantidade > saldo:
                produto_nome = dict(Doacao.Produto.choices).get(produto, produto)
                self.add_error(
                    "quantidade",
                    f"Estoque insuficiente para {produto_nome}. Disponível: {saldo}.",
                )

        return cleaned_data
