import logging
from django.utils import timezone

# configura o logger padrão do django
logger = logging.getLogger('clinica_auditoria')

class AuditoriaService:
    # registra um evento de log no sistema com timestamp e usuario responsavel
    @staticmethod
    def registrar_log(evento: str, usuario=None) -> None:
        timestamp = timezone.now().strftime("%Y-%m-%d %H:%M:%S")
        username = usuario.username if usuario else "anônimo"
        cargo = getattr(usuario, "cargo", "SEM_CARGO") if usuario else "N/A"

        mensagem_log = f"[{timestamp}] [AUDITORIA] Usuário: {username} ({cargo}) - Evento: {evento}"

        # grava no log oficial do django - console ou arquivo
        logger.info(mensagem_log)

        # salva em um arquivo dedicado 
        try: 
            with open("logs.log", "a", encoding="utf-8") as arquivo:
                arquivo.write(mensagem_log + "\n")
        except Exception as e:
            logger.error(f"erro ao salvar arquivo de log: {e}")

