# ficheiro: Projeto/passageiro.py

class Passageiro:
    def __init__(self, id_passageiro, x, y, cor):
        """
        Inicializa um passageiro.
        :param id_passageiro: Identificador único.
        :param x: Posição X (-1 se na estação).
        :param y: Posição Y (-1 se na estação).
        :param cor: Cor do passageiro.
        """
        self.id = id_passageiro
        self.x = x
        self.y = y
        self.cor = cor
        self.estado = "esperando" # 'esperando', 'embarcado'

    def embarcar(self):
        """Muda o estado do passageiro para embarcado."""
        if self.estado == "esperando":
            self.estado = "embarcado"; return True
        return False

    def __repr__(self):
        return f"Passageiro({self.id}, Cor:{self.cor}, Estado:{self.estado})"