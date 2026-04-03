from django.core.management.base import BaseCommand

from cadastros.validade import enviar_alertas_validade_email


class Command(BaseCommand):
    help = "Envia alertas de validade (vencidos e próximos) por e-mail."

    def add_arguments(self, parser):
        parser.add_argument(
            "--forcar",
            action="store_true",
            help="Ignora intervalo de envio e dispara o alerta imediatamente.",
        )

    def handle(self, *args, **options):
        resultado = enviar_alertas_validade_email(force=options["forcar"])
        if resultado.get("enviado"):
            self.stdout.write(
                self.style.SUCCESS(
                    f"Alerta enviado para {', '.join(resultado.get('destinatarios', []))}."
                )
            )
            return

        motivo = resultado.get("motivo", "desconhecido")
        if motivo == "sem_destinatarios":
            self.stdout.write(
                self.style.WARNING(
                    "Nenhum destinatário configurado. Defina ESTOQUE_ALERTA_EMAIL_DESTINATARIOS."
                )
            )
        elif motivo == "sem_alertas":
            self.stdout.write(self.style.SUCCESS("Sem alertas de validade pendentes."))
        elif motivo == "intervalo":
            self.stdout.write(self.style.WARNING("Intervalo mínimo de envio ainda não foi atingido."))
        else:
            erro = resultado.get("erro", "erro não informado")
            self.stdout.write(self.style.ERROR(f"Falha ao enviar alerta: {erro}"))
