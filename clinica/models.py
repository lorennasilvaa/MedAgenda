from django.db import models
from django.contrib.auth.models import AbstractUser
from .interfaces import IValidadorAcesso
from .services.services import AuditoriaService

import uuid

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

class Prontuario(models.Model):
    # o campo ID utiliza UUID ao invés de números sequenciais para garantir que os IDs dos registros não possuam conexão entre eles
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # atributos do tipo list<string> mapeados com JSONField
    historico_diagnosticos = models.JSONField(default=list, blank=True)
    prescricoes = models.JSONField(default=list, blank=True)
    alergias = models.JSONField(default=list, blank=True)

    def __str__(self):
        return f"Prontuário: {self.id}"

    # retorna o historico de diagnosticos se o usuario tiver permissao
    def ler_historico(self, usuario: UsuarioClinica) -> list:
        if not usuario.validar_acesso("prontuario:ler"):
            raise PermissionError("O usuário não possui permissão para ler o prontuário.")
        return self.historico_diagnosticos

    # Registra um atendimento adicionando diagnóstico e prescrição
    def registrar_atendimento(self, usuario: UsuarioClinica, diagnostico: str, prescricao: str) -> None:
        if not usuario.validar_acesso("prontuario:escrever"):
            raise PermissionError("O usuário não possui permissão para escrever no prontuário.")
        
        if diagnostico:
            self.historico_diagnosticos.append(diagnostico)
        if prescricao:
            self.prescricoes.append(prescricao)
        self.save()

    # Adiciona uma alergia à lista se o usuário tiver permissão de escrita
    def adicionar_alergia(self, usuario: UsuarioClinica, alergia: str) -> None:
        if not usuario.validar_acesso("prontuario:escrever"):
            raise PermissionError("O usuário não possui permissão para alterar as alergias no prontuário.")
        
        if alergia and alergia not in self.alergias:
            self.alergias.append(alergia)
            self.save()

        # adiciona log 
        AuditoriaService.registrar_log(evento=f"Alergia {alergia} adicionada ao prontuário: {self.id}.", usuario=usuario)
    
class Paciente(models.Model):
    nome = models.CharField(max_length=255)
    cpf = models.CharField(max_length=14, unique=True)
    telefone = models.CharField(max_length=20, blank=True, null=True)

    # Relação de composição com o Prontuário (1 para 1)
    # on_delete=models.CASCADE garante que se o paciente for apagado, o prontuário vinculado também será.
    prontuario = models.OneToOneField(
        'Prontuario', 
        on_delete=models.CASCADE, 
        related_name='paciente'
    )

    def __str__(self):
        return f"{self.nome} (CPF: {self.cpf})"

    # Retorna o prontuário associado a este paciente
    def get_prontuario(self) -> Prontuario:
        return self.prontuario

    @staticmethod
    def cadastrar_paciente(nome, cpf, telefone) -> Paciente:
        # Cria um prontuário para o novo paciente
        prontuario = Prontuario.objects.create()
        prontuario.save()
        paciente = Paciente.objects.create(nome=nome, cpf=cpf, telefone=telefone, prontuario=prontuario)
        paciente.save()
        return paciente

class StatusConsulta(models.TextChoices):
    AGENDADA = 'AGENDADA', 'Agendada'
    REALIZADA = 'REALIZADA', 'Realizada'
    CANCELADA = 'CANCELADA', 'Cancelada'

class Consulta(models.Model):
    paciente = models.ForeignKey('Paciente', on_delete=models.CASCADE, related_name='consultas')
    medico = models.ForeignKey('Medico', on_delete=models.PROTECT, related_name='consultas')
    data_hora = models.DateTimeField()
    observacoes_recepcao = models.TextField(blank=True, null=True)

    status = models.CharField(
        max_length=20,
        choices=StatusConsulta.choices,
        default=StatusConsulta.AGENDADA
    )

    def __str__(self):
        return f"Consulta de {self.paciente.nome} com Dr(a). {self.medico.nome} em {self.data_hora}"

    # agenda a consulta após validar o acesso do usuário
    def agendar(self, usuario: UsuarioClinica) -> None:
        if not usuario.validar_acesso("consulta:agendar"):
            raise PermissionError("O usuário não possui permissão para agendar consultas.")
        
        self.status = StatusConsulta.AGENDADA
        self.save()

    # cancela a consulta registrando o motivo
    def cancelar(self, usuario: UsuarioClinica, motivo: str) -> None:
        # Exemplo de validação de permissão opcional
        if not usuario.validar_acesso("consulta:agendar"):
            raise PermissionError("O usuário não possui permissão para cancelar consultas.")
        
        self.status = StatusConsulta.CANCELADA
        self.observacoes_recepcao = f"Consulta cancelada. Motivo: {motivo}"
        # Se desejar salvar o motivo, você pode criar um campo de texto extra na model para armazená-lo.
        self.save()

        # registrar log
        AuditoriaService.registrar_log(evento=f"Consulta cancelada. Médico responsável: {self.medico}. Paciente: {self.paciente}. Motivo: {motivo}", usuario=usuario)

    # finaliza o atendimento registrando o diagnóstico e a prescrição no prontuario
    def finalizar_atendimento(self, medico: Medico, diagnostico: str, prescricao: str) -> None:
        # Valida se o usuário logado é um médico e tem permissão de escrita
        if not medico.validar_acesso("prontuario:escrever"):
            raise PermissionError("Apenas médicos autorizados podem finalizar o atendimento.")

        self.status = StatusConsulta.REALIZADA
        self.save()

        # Integração automática com o prontuário do paciente vinculado
        if self.paciente and self.paciente.prontuario:
            self.paciente.prontuario.registrar_atendimento(
                usuario=medico,
                diagnostico=diagnostico,
                prescricao=prescricao
            )

        # registra log
        AuditoriaService.registrar_log(evento=f"Atendimento finalizado. Médico responsável: {self.medico}. Paciente: {self.paciente}.", usuario=medico)

    # retorna um resumo administrativo da consulta
    def get_resumo_administrativo(self) -> str:
        return (
            f"Consulta ID: {self.id} | Paciente: {self.paciente.nome} | "
            f"Médico: {self.medico.nome} | Status: {self.status}"
        )