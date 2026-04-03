from datetime import date

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import AuditoriaEstoqueValidade, Doacao, EstoqueItem, EstoqueLote, Familia, Repasse


class FluxoEstoqueTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="tester", password="senha123")
        self.client.login(username="tester", password="senha123")
        self.familia = Familia.objects.create(
            lider_familia="Maria Silva",
            dt_nasc_lider=date(1985, 1, 1),
        )

    def test_doacao_de_item_soma_no_estoque(self):
        response = self.client.post(
            reverse("doacoes"),
            data={
                "categoria": Doacao.Categoria.ALIMENTOS,
                "produto": Doacao.Produto.ARROZ,
                "descricao": "Arroz tipo 1",
                "valor": "",
                "quantidade": 12,
                "unidade": "kg",
                "data_doacao": "2026-04-01",
                "data_validade": "2026-05-01",
                "observacoes": "",
            },
        )

        self.assertEqual(response.status_code, 302)
        item = EstoqueItem.objects.get(produto=Doacao.Produto.ARROZ)
        self.assertEqual(item.quantidade, 12)
        self.assertEqual(item.unidade, "kg")
        lote = EstoqueLote.objects.get(produto=Doacao.Produto.ARROZ, data_validade="2026-05-01")
        self.assertEqual(lote.quantidade, 12)

    def test_repasse_entregue_abate_estoque(self):
        EstoqueItem.objects.create(produto=Doacao.Produto.FEIJAO, quantidade=8, unidade="kg")
        EstoqueLote.objects.create(
            produto=Doacao.Produto.FEIJAO,
            quantidade=8,
            unidade="kg",
            data_validade="2026-05-20",
        )

        response = self.client.post(
            reverse("repasses"),
            data={
                "familia": self.familia.pk,
                "doacao": "",
                "categoria": Doacao.Categoria.ALIMENTOS,
                "produto": Doacao.Produto.FEIJAO,
                "descricao": "Repasse mensal",
                "valor_estimado": "",
                "quantidade": 3,
                "unidade": "kg",
                "data_repasse": "2026-04-01",
                "status": Repasse.Status.ENTREGUE,
                "observacoes": "",
            },
        )

        self.assertEqual(response.status_code, 302)
        item = EstoqueItem.objects.get(produto=Doacao.Produto.FEIJAO)
        self.assertEqual(item.quantidade, 5)
        lote = EstoqueLote.objects.get(produto=Doacao.Produto.FEIJAO, data_validade="2026-05-20")
        self.assertEqual(lote.quantidade, 5)

    def test_repasse_bloqueia_quando_estoque_for_insuficiente(self):
        EstoqueItem.objects.create(produto=Doacao.Produto.CESTA_BASICA, quantidade=1, unidade="un")

        response = self.client.post(
            reverse("repasses"),
            data={
                "familia": self.familia.pk,
                "doacao": "",
                "categoria": Doacao.Categoria.ALIMENTOS,
                "produto": Doacao.Produto.CESTA_BASICA,
                "descricao": "Repasse extra",
                "valor_estimado": "",
                "quantidade": 2,
                "unidade": "un",
                "data_repasse": "2026-04-01",
                "status": Repasse.Status.ENTREGUE,
                "observacoes": "",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("quantidade", response.context["form"].errors)
        self.assertIn("Estoque insuficiente", response.context["form"].errors["quantidade"][0])
        item = EstoqueItem.objects.get(produto=Doacao.Produto.CESTA_BASICA)
        self.assertEqual(item.quantidade, 1)

    def test_doacao_perecivel_sem_validade_retorna_erro(self):
        response = self.client.post(
            reverse("doacoes"),
            data={
                "categoria": Doacao.Categoria.ALIMENTOS,
                "produto": Doacao.Produto.FEIJAO,
                "descricao": "Feijão 1kg",
                "valor": "",
                "quantidade": 5,
                "unidade": "kg",
                "data_doacao": "2026-04-01",
                "data_validade": "",
                "observacoes": "",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("data_validade", response.context["form"].errors)
        self.assertFalse(EstoqueItem.objects.filter(produto=Doacao.Produto.FEIJAO).exists())

    def test_doacao_nao_perecivel_nao_exige_validade(self):
        response = self.client.post(
            reverse("doacoes"),
            data={
                "categoria": Doacao.Categoria.OUTROS,
                "produto": Doacao.Produto.BRINQUEDOS,
                "descricao": "Brinquedos infantis",
                "valor": "",
                "quantidade": 4,
                "unidade": "un",
                "data_doacao": "2026-04-01",
                "data_validade": "",
                "observacoes": "",
            },
        )

        self.assertEqual(response.status_code, 302)
        doacao = Doacao.objects.get(produto=Doacao.Produto.BRINQUEDOS)
        self.assertIsNone(doacao.data_validade)

    def test_repasse_com_produto_vencido_trava_tela(self):
        EstoqueItem.objects.create(produto=Doacao.Produto.FEIJAO, quantidade=3, unidade="kg")
        EstoqueLote.objects.create(
            produto=Doacao.Produto.FEIJAO,
            quantidade=3,
            unidade="kg",
            data_validade="2026-03-01",
        )

        response = self.client.post(
            reverse("repasses"),
            data={
                "familia": self.familia.pk,
                "doacao": "",
                "categoria": Doacao.Categoria.ALIMENTOS,
                "produto": Doacao.Produto.FEIJAO,
                "descricao": "Repasse vencido",
                "valor_estimado": "",
                "quantidade": 1,
                "unidade": "kg",
                "data_repasse": "2026-04-01",
                "status": Repasse.Status.ENTREGUE,
                "observacoes": "",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["mostrar_confirmacao_vencido"])
        self.assertEqual(
            AuditoriaEstoqueValidade.objects.filter(
                evento=AuditoriaEstoqueValidade.Evento.BLOQUEIO_DOACAO_VENCIDO
            ).count(),
            1,
        )

    def test_repasse_vencido_com_senha_valida_registra_auditoria(self):
        EstoqueItem.objects.create(produto=Doacao.Produto.FEIJAO, quantidade=3, unidade="kg")
        EstoqueLote.objects.create(
            produto=Doacao.Produto.FEIJAO,
            quantidade=3,
            unidade="kg",
            data_validade="2026-03-01",
        )

        response = self.client.post(
            reverse("repasses"),
            data={
                "familia": self.familia.pk,
                "doacao": "",
                "categoria": Doacao.Categoria.ALIMENTOS,
                "produto": Doacao.Produto.FEIJAO,
                "descricao": "Repasse vencido autorizado",
                "valor_estimado": "",
                "quantidade": 1,
                "unidade": "kg",
                "data_repasse": "2026-04-01",
                "status": Repasse.Status.ENTREGUE,
                "observacoes": "",
                "confirmar_doacao_vencida": "1",
                "senha_confirmacao": "senha123",
            },
        )

        self.assertEqual(response.status_code, 302)
        item = EstoqueItem.objects.get(produto=Doacao.Produto.FEIJAO)
        self.assertEqual(item.quantidade, 2)
        self.assertTrue(
            AuditoriaEstoqueValidade.objects.filter(
                evento=AuditoriaEstoqueValidade.Evento.REAUTENTICACAO_SUCESSO
            ).exists()
        )
        self.assertTrue(
            AuditoriaEstoqueValidade.objects.filter(
                evento=AuditoriaEstoqueValidade.Evento.REPASSE_VENCIDO_CONFIRMADO
            ).exists()
        )
