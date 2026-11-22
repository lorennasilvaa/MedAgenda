from pathlib import Path
import tempfile
from django.test import TestCase
from django.utils import timezone
from ..interfaces import IValidadorAcesso
from ..models import( 
    Medico, Recepcionista, Paciente, Prontuario, Consulta, StatusConsulta, 
    UsuarioClinica, AdministradorTI
)
from ..services.services import AuditoriaService

class ClinicaWorkflowTestCase(TestCase):
    
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.log_path = Path(self.temp_dir.name) / "test_auditoria.log"

        # Garante que o AuditoriaService escreva no arquivo temporário deste teste
        self.auditoria = AuditoriaService()
        self.auditoria.caminho_log = str(self.log_path)

        # criando um usuário medico
        self.medico = Medico.objects.create_user(
            username="drhouse",
            password="password123",
            nome="Dr. House",
            cpf="111.111.111-11",
            crm="12345-SP"
        )

        # criando um usuario recepcionista
        self.recepcionista = Recepcionista.objects.create_user(
            username="carmem",
            password="password123",
            nome="Carmem Recepção",
            cpf="222.222.222-22"
        )

        # criando o prontuário e o paciente
        self.prontuario = Prontuario.objects.create()
        self.paciente = Paciente.objects.create(
            nome="Carlos Silva",
            cpf="333.333.333-33",
            telefone="(11) 98888-7777",
            prontuario=self.prontuario
        )

    def test_relacao_paciente_prontuario(self):
        # Testa se o paciente está corretamente vinculado ao prontuário e vice-versa
        self.assertEqual(self.paciente.get_prontuario(), self.prontuario)
        self.assertEqual(self.prontuario.paciente, self.paciente)

    def test_fluxo_agendamento_e_atendimento_consulta(self):
        # Testa o ciclo de vida de uma consulta e a integração com o prontuário
        
        # Criar a consulta agendada
        consulta = Consulta.objects.create(
            paciente=self.paciente,
            medico=self.medico,
            data_hora=timezone.now(),
            observacoes_recepcao="Paciente com febre leve.",
            status=StatusConsulta.AGENDADA
        )
        
        self.assertEqual(consulta.status, StatusConsulta.AGENDADA)
        
        # Testar o método de agendamento validando permissão da recepcionista
        consulta.agendar(usuario=self.recepcionista)
        self.assertEqual(consulta.status, StatusConsulta.AGENDADA)

        # Finalizar o atendimento médico (deve atualizar o status e injetar dados no prontuário)
        diagnostico_teste = "Virose leve"
        prescricao_teste = "Paracetamol 500mg de 8 em 8 horas"
        
        consulta.finalizar_atendimento(
            medico=self.medico,
            diagnostico=diagnostico_teste,
            prescricao=prescricao_teste
        )
        
        # Verificar se a consulta mudou para realizada
        self.assertEqual(consulta.status, StatusConsulta.REALIZADA)
        
        # Verificar se os dados caíram automaticamente no prontuário do paciente
        self.assertIn(diagnostico_teste, self.prontuario.historico_diagnosticos)
        self.assertIn(prescricao_teste, self.prontuario.prescricoes)

    def test_permissao_negada_prontuario(self):
        # Testa se uma recepcionista é bloqueada ao tentar escrever diretamente no prontuário
        with self.assertRaises(PermissionError):
            self.prontuario.registrar_atendimento(
                usuario=self.recepcionista, 
                diagnostico="Tentativa Indevida", 
                prescricao="Nenhuma"
            )

class InterfaceEModelosRBACTestCase(TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.log_path = Path(self.temp_dir.name) / "test_auditoria.log"

        # Garante que o AuditoriaService escreva no arquivo temporário deste teste
        self.auditoria = AuditoriaService()
        self.auditoria.caminho_log = str(self.log_path)

        self.recepcionista = Recepcionista.objects.create_user(
            username="ana_rec",
            password="123",
            nome="Ana Paula",
            cpf="111.111.111-11",
            cargo=UsuarioClinica.TipoCargo.RECEPCIONISTA,
        )
        self.medico = Medico.objects.create_user(
            username="dr_silva",
            password="123",
            nome="Dr. Carlos Silva",
            cpf="222.222.222-22",
            cargo=UsuarioClinica.TipoCargo.MEDICO,
            crm="CRM-RN 1234",
        )
        self.admin_ti = AdministradorTI.objects.create_user(
            username="joao_ti",
            password="123",
            nome="João Souza",
            cpf="333.333.333-33",
            cargo=UsuarioClinica.TipoCargo.TI,
        )

    def test_interface_registrada_nos_modelos(self):
        self.assertTrue(issubclass(UsuarioClinica, IValidadorAcesso))
        self.assertTrue(issubclass(Recepcionista, IValidadorAcesso))
        self.assertTrue(issubclass(Medico, IValidadorAcesso))
        self.assertTrue(issubclass(AdministradorTI, IValidadorAcesso))
        self.assertIsInstance(self.medico, IValidadorAcesso)

    def test_permissoes_recepcionista(self):
        self.assertTrue(self.recepcionista.validar_acesso("consulta:agendar"))
        self.assertTrue(self.recepcionista.validar_acesso("paciente:cadastrar"))
        self.assertFalse(self.recepcionista.validar_acesso("prontuario:ler"))
        self.assertFalse(self.recepcionista.validar_acesso("prontuario:escrever"))
        self.assertFalse(self.recepcionista.validar_acesso("sistema:gerenciar"))

    def test_permissoes_medico(self):
        self.assertTrue(self.medico.validar_acesso("prontuario:ler"))
        self.assertTrue(self.medico.validar_acesso("prontuario:escrever"))
        self.assertTrue(self.medico.validar_acesso("consulta:visualizar"))
        self.assertFalse(self.medico.validar_acesso("consulta:agendar"))
        self.assertFalse(self.medico.validar_acesso("sistema:gerenciar"))
        self.assertEqual(self.medico.crm, "CRM-RN 1234")

    def test_permissoes_administrador_ti(self):
        self.assertTrue(self.admin_ti.validar_acesso("sistema:gerenciar"))
        self.assertTrue(self.admin_ti.validar_acesso("auditoria:ler"))
        self.assertFalse(self.admin_ti.validar_acesso("prontuario:ler"))
        self.assertFalse(self.admin_ti.validar_acesso("consulta:agendar"))

    def test_usuario_base_sem_subclasse_levanta_erro_em_obter_permissoes(self):
        usuario_base = UsuarioClinica.objects.create_user(
            username="base_user",
            password="123",
            nome="Usuário Base",
            cpf="444.444.444-44",
        )
        self.assertEqual(usuario_base.obter_permissoes(), set())