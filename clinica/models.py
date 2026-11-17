from django.db import models
from django.contrib.auth.models import AbstractUser
from .interfaces import IValidadorAcesso

class UsuarioClinica(AbstractUser):
    class TipoCargo(models.TextChoices):
        RECEPCIONISTA = 'REC', 'Recepcionista'
        MEDICO = 'MED', 'Médico'
        TI = 'TI', 'Administrador de TI'

    nome = models.CharField(max_length=50)
    cpf = models.CharField(max_length=14, unique=True)
    cargo = models.CharField(max_length=3, choices=TipoCargo.choices, default=TipoCargo.RECEPCIONISTA)
    
    # Campo específico de médico, mas mantido opcional na base para suportar o Proxy Model
    crm = models.CharField(max_length=15, unique=True, null=True, blank=True)

    def validar_acesso(self, permissao: str) -> bool:
        return permissao in self.obter_permissoes()

    def obter_permissoes(self) -> set:
        return set()
    

# Registra formalmente que a classe do Django implementa a Interface
IValidadorAcesso.register(UsuarioClinica)

class Recepcionista(UsuarioClinica):
    class Meta:
        proxy = True

    def obter_permissoes(self) -> set:
        return {"consulta:agendar", "paciente:cadastrar"}


class Medico(UsuarioClinica):
    class Meta:
        proxy = True

    def obter_permissoes(self) -> set:
        return {"prontuario:ler", "prontuario:escrever", "consulta:visualizar"}


class AdministradorTI(UsuarioClinica):
    class Meta:
        proxy = True

    def obter_permissoes(self) -> set:
        return {"sistema:gerenciar", "auditoria:ler"}