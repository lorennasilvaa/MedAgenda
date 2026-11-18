from django.test import TestCase

from django.utils import timezone
from .models import Medico, Recepcionista, Paciente, Prontuario, Consulta, StatusConsulta

class ClinicaWorkflowTestCase(TestCase):
    
    def setUp(self):
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
