# ficheiro: Projeto/tabuleiro.py

class Tabuleiro:
    def __init__(self, largura, altura):
        """
        Inicializa o tabuleiro (grelha) do jogo.
        Guarda as dimensões e a lista de autocarros presentes.
        :param largura: Número de colunas do tabuleiro.
        :param altura: Número de linhas do tabuleiro.
        """
        self.largura = largura
        self.altura = altura
        self.autocarros = []

    def adicionar_autocarro(self, autocarro):
        """Adiciona um autocarro à lista do tabuleiro."""
        self.autocarros.append(autocarro)
        return True

    def verificar_disponibilidade(self, autocarro_novo):
        """
        Verifica se as posições para um novo autocarro não colidem com os existentes.
        """
        posicoes_ocupadas_existentes = set()
        for a in self.autocarros:
            posicoes_ocupadas_existentes.update(a.obter_posicoes_ocupadas())
        posicoes_novo = set(autocarro_novo.obter_posicoes_ocupadas())
        # Verifica limites
        for x, y in posicoes_novo:
             if not (0 <= x < self.largura and 0 <= y < self.altura): return False
        # Verifica colisão
        if not posicoes_novo.isdisjoint(posicoes_ocupadas_existentes): return False
        return True # Posição válida