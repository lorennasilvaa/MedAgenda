from django.db import models
from django.contrib.auth.models import AbstractUser

class UsuarioClinica(AbstractUser):
    class TipoCargo(models.TextChoices):
        RECEPCIONISTA = 'REC', 'Recepcionista'
        MEDICO = 'MED', 'Médico'
        TI = 'TI', 'Administrador de TI'

    cpf = models.CharField(max_length=14, unique=True)
    cargo = models.CharField(max_length=3, choices=TipoCargo.choices, default=TipoCargo.RECEPCIONISTA)

    def validar_acesso(self, permissao: str) -> bool:
        return permissao in self.obter_permissoes()

    def obter_permissoes(self) -> set:
        return set()