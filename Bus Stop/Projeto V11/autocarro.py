# ficheiro: Projeto/autocarro.py

class Autocarro:
    def __init__(self, x, y, direcao, capacidade, cor):
        """
        Inicializa um autocarro.
        :param x: Posição inicial no eixo X (da "cabeça" do autocarro).
        :param y: Posição inicial no eixo Y (da "cabeça" do autocarro).
        :param direcao: "H" para horizontal, "V" para vertical.
        :param capacidade: Número de lugares/espaços (2, 4, 6, 8 ou 12).
        :param cor: Cor do autocarro.
        """
        # Validação capacidades [2, 4, 6, 8, 12]
        capacidades_validas = [2, 4, 6, 8, 12]
        if capacidade not in capacidades_validas:
            raise ValueError(f"Capacidade inválida: {capacidade}. Deve ser uma de {capacidades_validas}")

        self.x = x
        self.y = y
        if direcao not in ["H", "V"]:
             raise ValueError(f"Direção inválida: {direcao}. Deve ser 'H' ou 'V'")
        self.direcao = direcao
        self.capacidade = capacidade
        self.cor = cor

    def obter_posicoes_ocupadas(self):
        """Retorna uma lista das posições (x, y) ocupadas pelo autocarro."""
        posicoes = []
        for i in range(self.capacidade):
            if self.direcao == "H":
                posicoes.append((self.x + i, self.y))
            else: # Direção "V"
                posicoes.append((self.x, self.y + i))
        return posicoes

    def __repr__(self):
        """Representação textual do objeto Autocarro."""
        return f"Autocarro(Cor:{self.cor}, Pos:({self.x},{self.y}), Dir:{self.direcao}, Cap:{self.capacidade})"