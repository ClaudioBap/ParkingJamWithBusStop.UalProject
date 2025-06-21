# ficheiro: Projeto/plataforma.py

class PlataformaEmbarque:
    def __init__(self, id_plataforma, x, y, cor):
        """
        Inicializa uma plataforma de embarque.
        :param id_plataforma: Identificador único da plataforma.
        :param x: Posição X da plataforma no tabuleiro.
        :param y: Posição Y da plataforma no tabuleiro.
        :param cor: Cor associada a esta plataforma (e aos seus passageiros).
        """
        self.id = id_plataforma
        self.x = x
        self.y = y
        self.cor = cor
        self.ocupada_por = None # Guarda a referência do Autocarro que a ocupa, ou None

    def esta_livre(self):
        """Verifica se a plataforma não está ocupada."""
        return self.ocupada_por is None

    def ocupar(self, autocarro):
        """Marca a plataforma como ocupada por um autocarro."""
        if self.esta_livre():
            self.ocupada_por = autocarro
            return True
        return False # Já estava ocupada

    def libertar(self):
        """Marca a plataforma como livre."""
        autocarro_anterior = self.ocupada_por
        self.ocupada_por = None
        return autocarro_anterior # Retorna quem a estava a ocupar (pode ser útil)

    def __repr__(self):
        estado = "Livre" if self.esta_livre() else f"Ocupada por {self.ocupada_por.cor}"
        return f"Plataforma({self.id}, Cor:{self.cor}, Pos:({self.x},{self.y}), Estado:{estado})"