from abc import ABC, abstractmethod

class IValidadorAcesso(ABC):
    @abstractmethod
    def validar_acesso(self, permissao: str) -> bool:
        pass