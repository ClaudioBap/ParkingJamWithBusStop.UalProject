# ficheiro: Projeto/jogogui.py

# --- Imports ---
from PyQt6.QtWidgets import (QApplication, QGraphicsScene, QPushButton, QHBoxLayout,
                             QVBoxLayout, QWidget, QMessageBox, QGraphicsTextItem,
                             QGraphicsRectItem, QGraphicsEllipseItem)
from PyQt6.QtGui import QFont, QColor, QBrush, QPen, QPixmap, QScreen # Importa QScreen
from PyQt6.QtCore import (Qt, QPointF, QTimer, QPropertyAnimation,
                          QEasingCurve, QAbstractAnimation, pyqtProperty)
import sys # Importa o módulo sys
import math
import random

from jogo import Jogo
from autocarro import Autocarro
from passageiro import Passageiro
# Usa a versão de AutocarroGrafico que desenha o retângulo + highlight
from autocarrografico import AutocarroGrafico
from qgraphicsview import CustomGraphicsView

# --- Classe Principal da GUI ---
class JogoGUI(QWidget):
    TAMANHO_CELULA = AutocarroGrafico.TAMANHO_CELULA # Usa tamanho 30

    def __init__(self):
        """Inicializador da janela principal do jogo."""
        super().__init__()
        # Usa a versão de Jogo com geração aleatória 12x12
        self.jogo = Jogo()
        self.autocarros_graficos = {} # Dicionário para autocarros no tabuleiro principal
        # NOVO: Dicionário para manter referências de autocarros gráficos na área de estacionamento
        self.autocarros_graficos_estacionados = {}
        self.autocarro_selecionado = None
        self.animation = None # Referência para a animação em curso
        # Setup Autoplay
        self.autoplay_ativo = False
        self.autoplay_timer = QTimer(self); self.autoplay_timer.timeout.connect(self.passo_autoplay)

        # --- MODIFICAÇÕES PARA DIMENSÕES E POSICIONAMENTO DA JANELA ---

        # Define Dimensões Base das Áreas
        self.altura_estacao_px = 4 * self.TAMANHO_CELULA
        self.altura_tabuleiro_px = self.jogo.tabuleiro.altura * self.TAMANHO_CELULA
        self.largura_tabuleiro_px = self.jogo.tabuleiro.largura * self.TAMANHO_CELULA
        self.altura_fila_px = 5 * self.TAMANHO_CELULA # Altura para a área da fila aleatória

        # NOVO: Altura REDUZIDA para a área de estacionamento por cor
        # Ajuste este valor conforme necessário para garantir que os botões são visíveis
        self.altura_estacionamento_px = 3 * self.TAMANHO_CELULA # Reduzido de 6 para 3 células de altura (exemplo)

        # Calcula a altura total da área gráfica (vista)
        self.altura_total_area_grafica_px = self.altura_estacao_px + self.altura_tabuleiro_px + self.altura_fila_px + self.altura_estacionamento_px

        margem = self.TAMANHO_CELULA # Margem usada para o layout da view

        # Define a largura da janela (mantida do ajuste anterior)
        self.largura_janela = self.largura_tabuleiro_px + margem

        # Obtém a geometria DISPONÍVEL do ecrã primário (exclui barras do sistema)
        available_geometry = QApplication.primaryScreen().availableGeometry()
        available_width = available_geometry.width()
        available_height = available_geometry.height()
        pos_x_available = available_geometry.x() # Posição inicial X disponível
        pos_y_available = available_geometry.y() # Posição inicial Y disponível (após barras do sistema)


        # Define a altura da janela para a altura DISPONÍVEL do ecrã
        self.altura_janela = available_height

        # Calcula a posição X para centrar a janela horizontalmente dentro da área disponível
        # Usa a posição inicial X disponível + metade do espaço restante horizontal
        pos_x_centro = pos_x_available + (available_width - self.largura_janela) // 2

        # A posição Y inicial da janela será a posição inicial Y disponível
        pos_y_topo = pos_y_available

        # Configura Janela
        self.setWindowTitle("Parking Jam + Estação")
        # Define a geometria da janela (posição e tamanho) usando a área disponível
        self.setGeometry(pos_x_centro, pos_y_topo, self.largura_janela, self.altura_janela)

        # --- FIM DAS MODIFICAÇÕES (Corrigido) ---

        # Configura Cena e Vista
        # A cena define a área total de desenho, a vista exibe uma parte dela.
        # A cena precisa ter a altura total de todas as áreas desenhadas.
        self.scene=QGraphicsScene(0,0,self.largura_tabuleiro_px,self.altura_total_area_grafica_px);
        self.view=CustomGraphicsView(self.scene,self)

        # Ajusta o tamanho fixo da view para a altura total das áreas gráficas.
        # Como a janela tem a altura total do ecrã e o layout principal é QVBoxLayout,
        # a view ocupará a altura necessária e os botões ficarão abaixo dela, visíveis.
        self.view.setFixedSize(self.largura_janela,self.altura_total_area_grafica_px + margem); # Adiciona margem à altura da view

        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        # Setup Botões e Layout
        self.botao_reiniciar=QPushButton("Reiniciar",self); self.botao_reiniciar.clicked.connect(self.reiniciar_jogo)
        self.botao_autoplay=QPushButton("Jogar Auto",self); self.botao_autoplay.setCheckable(True); self.botao_autoplay.toggled.connect(self.toggle_autoplay)
        # +++ NOVO BOTÃO SUGESTÃO +++
        self.botao_sugestao = QPushButton("Sugestão", self)
        self.botao_sugestao.clicked.connect(self.sugerir_jogada)
        # +++++++++++++++++++++++++++

        # +++ NOVO BOTÃO SAIR +++
        self.botao_sair = QPushButton("Exit Game", self)
        self.botao_sair.clicked.connect(self.sair_jogo) # Conecta o sinal clicked ao novo slot
        # +++++++++++++++++++++++

        layout_botoes=QHBoxLayout(); layout_botoes.addWidget(self.botao_reiniciar); layout_botoes.addWidget(self.botao_autoplay)
        # +++ ADICIONAR BOTÃO SUGESTÃO AO LAYOUT +++
        layout_botoes.addWidget(self.botao_sugestao)
        # ++++++++++++++++++++++++++++++++++++++++++
        # +++ ADICIONAR BOTÃO SAIR AO LAYOUT +++
        layout_botoes.addWidget(self.botao_sair)
        # ++++++++++++++++++++++++++++++++++++++
        layout_principal=QVBoxLayout(); layout_principal.addWidget(self.view); layout_principal.addLayout(layout_botoes); self.setLayout(layout_principal)

        # +++ NOVOS ATRIBUTOS para gerir o piscar da sugestão +++
        self._current_blinking_autocarro_grafico = None
        self._blinking_animation = None # Referência para a animação QPropertyAnimation
        # +++++++++++++++++++++++++++++++++++++++++++++++++++++++

        # Desenhar o estado inicial do jogo
        self.desenhar_estado_jogo()
        self.setFocus()

    # --- Métodos de Desenho ---
    def desenhar_estado_jogo(self):
        """Limpa a cena, os dicts de refs e redesenha ESTAÇÃO, PARQUE, FILA e ESTACIONAMENTO."""
        # Limpa a cena e as referências gráficas
        self.autocarros_graficos.clear() # Referências para autocarros no tabuleiro principal
        self.autocarros_graficos_estacionados.clear() # Referências para autocarros na área de estacionamento
        self.scene.clear()

        # Define os offsets verticais para cada área
        y_inicio_grelha = self.altura_estacao_px
        y_inicio_fila = self.altura_estacao_px + self.altura_tabuleiro_px
        y_inicio_estacionamento = y_inicio_fila + self.altura_fila_px # Novo início da área de estacionamento

        # 1. Fundo Estação (Área superior onde se vê a contagem de passageiros por cor)
        cor_fundo_estacao=QColor("#D0D0D0"); fundo_estacao=QGraphicsRectItem(0,0,self.largura_tabuleiro_px, y_inicio_grelha); fundo_estacao.setBrush(QBrush(cor_fundo_estacao)); pen_fundo=QPen(); pen_fundo.setStyle(Qt.PenStyle.NoPen); fundo_estacao.setPen(pen_fundo); fundo_estacao.setZValue(-3); self.scene.addItem(fundo_estacao)

        # 2. Grelha Parque (Área central onde os autocarros se movem)
        largura_px=self.largura_tabuleiro_px; altura_parque_px = self.altura_tabuleiro_px; cor_grelha=QColor("lightgray");
        # Desenha as linhas verticais da grelha do parque
        for x in range(0,largura_px+1,self.TAMANHO_CELULA): self.scene.addLine(x,y_inicio_grelha,x,y_inicio_fila,cor_grelha)
        # Desenha as linhas horizontais da grelha do parque
        for y in range(y_inicio_grelha,y_inicio_fila+1,self.TAMANHO_CELULA): self.scene.addLine(0,y,largura_px,y,cor_grelha)

        # 3. Zonas e Contagem de Passageiros na Estação
        if hasattr(self.jogo,'cores_ativas') and self.jogo.cores_ativas:
            num_zonas=len(self.jogo.cores_ativas)
            if num_zonas > 0:
                largura_zona=self.largura_tabuleiro_px/num_zonas; altura_zona=self.altura_estacao_px*0.7; y_zona=self.altura_estacao_px*0.15
                # Tamanho menor para a representação visual de passageiro na estação (se necessário desenhar)
                # diametro_passageiro_estacao = self.TAMANHO_CELULA/3;
                # pen_passageiro=QPen(Qt.GlobalColor.darkGray)
                for i, cor in enumerate(self.jogo.cores_ativas):
                    x_zona=i*largura_zona; zona_rect=QGraphicsRectItem(x_zona,y_zona,largura_zona,altura_zona)
                    try: cor_zona=QColor(cor); cor_fundo_zona=QColor(cor_zona); cor_fundo_zona.setAlpha(60); pen_zona=QPen(cor_zona.darker(120)); pen_zona.setWidth(2); zona_rect.setBrush(QBrush(cor_fundo_zona)); zona_rect.setPen(pen_zona)
                    except ValueError: zona_rect.setBrush(QBrush(Qt.GlobalColor.lightGray)); zona_rect.setPen(QPen(Qt.GlobalColor.black))
                    zona_rect.setZValue(-1); self.scene.addItem(zona_rect)

                    # Desenhar o nome da cor na zona da estação
                    texto_cor_item=QGraphicsTextItem(cor.upper()); texto_cor_item.setFont(QFont("Arial",7,QFont.Weight.Bold));
                    try: texto_cor_item.setDefaultTextColor(QColor(cor).darker(150))
                    except ValueError: texto_cor_item.setDefaultTextColor(Qt.GlobalColor.black)
                    rect_texto_cor=texto_cor_item.boundingRect(); texto_cor_item.setPos(x_zona+(largura_zona-rect_texto_cor.width())/2, y_zona+1); self.scene.addItem(texto_cor_item)

                    # ALTERADO: Obter contagem de passageiros *esperando* desta cor
                    # Agora contamos do total de passageiros (self.jogo.passageiros)
                    passageiros_esperando_desta_cor = [p for p in self.jogo.passageiros if p.cor == cor and p.estado == 'esperando']
                    contagem=len(passageiros_esperando_desta_cor) # Usar contagem do total de passageiros esperando

                    # Desenhar a contagem de passageiros esperando
                    if contagem>=0:
                        texto_contagem=QGraphicsTextItem(f"({contagem})"); fonte_contagem=QFont("Arial",8,QFont.Weight.Bold); texto_contagem.setFont(fonte_contagem)
                        try: texto_contagem.setDefaultTextColor(QColor(cor).darker(200))
                        except ValueError: texto_contagem.setDefaultTextColor(Qt.GlobalColor.black)
                        rect_contagem=texto_contagem.boundingRect(); pos_x_cont=x_zona+largura_zona-rect_contagem.width()-3; pos_y_cont=y_zona+3
                        texto_contagem.setPos(pos_x_cont,pos_y_cont); texto_contagem.setZValue(1); self.scene.addItem(texto_contagem)

        # 4. Desenhar Autocarros (principalmente no Parque)
        y_offset_parque = self.altura_estacao_px
        for autocarro in self.jogo.tabuleiro.autocarros:
             # Desenha cada autocarro no offset correto do parque
             # A função desenhar_autocarro agora verifica se o autocarro está no tabuleiro principal
             self.desenhar_autocarro(autocarro, y_offset_parque)


        # 5. Desenhar a Fila Aleatória (AGORA DINÂMICA)
        self.desenhar_fila_aleatoria(y_inicio_fila)

        # 6. Desenhar a Área de Estacionamento por Cor (COM AUTOCARROS ESTACIONADOS)
        self.desenhar_area_estacionamento(y_inicio_estacionamento)


    # --- Função Modificada: ADICIONA TEXTO DE CAPACIDADE e SETA como FILHOS ---
    def desenhar_autocarro(self, autocarro, y_offset=0):
        """Cria item gráfico PAI, e seta/texto de capacidade como FILHOS."""
        # 1. Cria o item gráfico do autocarro (o pai)
        # Verifica se o autocarro está no tabuleiro principal antes de desenhar aqui
        if autocarro not in self.jogo.tabuleiro.autocarros:
             # Não desenha autocarros que não estão no tabuleiro principal aqui.
             # A função desenhar_area_estacionamento cuida da visualização dos estacionados.
             return


        item_grafico = AutocarroGrafico(autocarro) # Este será o PAI
        pos_x_na_cena = autocarro.x * self.TAMANHO_CELULA
        pos_y_na_cena = (autocarro.y * self.TAMANHO_CELULA) + y_offset # Offset do parque

        item_grafico.setPos(pos_x_na_cena, pos_y_na_cena) # Define a posição do PAI na cena

        # Adiciona o PAI à cena e ao dicionário de autocarros no tabuleiro principal
        self.scene.addItem(item_grafico)
        self.autocarros_graficos[autocarro] = item_grafico

        # --- 2. SETA DE DIREÇÃO (FILHO de item_grafico) ---
        seta_char = "→" if autocarro.direcao == "H" else "↓"
        # Define item_grafico como PAI aqui:
        seta = QGraphicsTextItem(seta_char, parent=item_grafico) # <--- PAI DEFINIDO
        # +++ DEFINIR OBJECT NAME para a seta +++
        seta.setObjectName("arrowItem") # Nome para identificação
        # +++++++++++++++++++++++++++++++++++++++
        seta_font = QFont("Arial", 12, QFont.Weight.Bold); seta.setFont(seta_font)
        seta.setDefaultTextColor(Qt.GlobalColor.black)

        # Calcula posição RELATIVA AO PAI (item_grafico)
        rect_bus_local = item_grafico.boundingRect() # Limites locais do pai (0,0 a width,height)
        seta_rect = seta.boundingRect() # Limites do texto da seta
        # Centro X e Y dentro das coordenadas LOCAIS do pai
        pos_x_centro_local = rect_bus_local.width() / 2
        pos_y_centro_local = rect_y_centro_local = rect_bus_local.height() / 2
        # Posição da seta para ficar centrada LOCALMENTe
        pos_x_seta_local = pos_x_centro_local - seta_rect.width() / 2
        pos_y_seta_local = pos_y_centro_local - seta_rect.height() / 2
        seta.setPos(pos_x_seta_local, pos_y_seta_local) # Define posição LOCAL

        # ZValue para ficar por cima do desenho base do pai
        seta.setZValue(1)
        # NÃO adicionar à cena separadamente: self.scene.addItem(seta) # <--- REMOVER/COMENTAR

        # --- 3. TEXTO DE CAPACIDADE (FILHO de item_grafico) ---
        try:
            # Mostrar capacidade total se estiver no tabuleiro
            texto_cap_str = f"C:{autocarro.capacidade}"
            font_weight = QFont.Weight.Normal

            cap_text_item = QGraphicsTextItem(texto_cap_str, parent=item_grafico) # <--- PAI DEFINIDO
            cap_font = QFont("Arial", 8, font_weight)
            cap_text_item.setFont(cap_font)
            cap_text_item.setDefaultTextColor(Qt.GlobalColor.black)

            # Calcular posição LOCAL "atrás" da seta (usando posições locais da seta)
            cap_rect = cap_text_item.boundingRect()
            spacing = 2

            if autocarro.direcao == "H": # Seta →, texto à Esquerda
                 # X local = X local da seta - largura do texto - espaço
                pos_x_cap_local = pos_x_seta_local - cap_rect.width() - spacing
                 # Y local = Y local da seta + ajuste vertical
                pos_y_cap_local = pos_y_seta_local + (seta_rect.height() - cap_rect.height()) / 2
            else: # Seta ↓, texto Acima
                 # X local = X local da seta + ajuste horizontal
                pos_x_cap_local = pos_x_seta_local + (seta_rect.width() - cap_rect.width()) / 2
                 # Y local = Y local da seta - altura do texto - espaço
                pos_y_cap_local = pos_y_seta_local - cap_rect.height() - spacing

            cap_text_item.setPos(pos_x_cap_local, pos_y_cap_local) # Define posição LOCAL

            # ZValue para ficar por cima do desenho base do pai (na mesma camada da seta)
            cap_text_item.setZValue(1)
            # NÃO adicionar à cena separadamente: self.scene.addItem(cap_text_item) # <--- REMOVER/COMENTAR

        except Exception as e:
            print(f"Erro ao desenhar capacidade para {autocarro}: {e}")
        # --- FIM TEXTO CAPACIDADE ---


    # NOVO MÉTODO: Desenhar a fila aleatória (AGORA DINÂMICA)
    def desenhar_fila_aleatoria(self, y_offset):
        """Desenha a fila dinâmica de passageiros na parte inferior,
           mostrando apenas os passageiros que ainda estão esperando."""
        # Fundo para a área da fila
        cor_fundo_fila = QColor("#E0D0C0") # Cor cinza claro/ocre
        fundo_fila = QGraphicsRectItem(0, y_offset, self.largura_tabuleiro_px, self.altura_fila_px)
        fundo_fila.setBrush(QBrush(cor_fundo_fila))
        pen_fundo_fila = QPen(Qt.GlobalColor.darkGray)
        pen_fundo_fila.setWidth(1)
        fundo_fila.setPen(pen_fundo_fila)
        fundo_fila.setZValue(-2) # Abaixo dos autocarros
        self.scene.addItem(fundo_fila)

        # Título para a fila
        titulo_fila = QGraphicsTextItem("Fila de Espera:") # Texto alterado
        titulo_fila.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        titulo_fila.setDefaultTextColor(Qt.GlobalColor.black)
        titulo_fila.setPos(5, y_offset + 5) # Posição dentro da área da fila
        titulo_fila.setZValue(1)
        self.scene.addItem(titulo_fila)

        # --- NOVO: Filtrar e desenhar APENAS passageiros esperando da fila aleatória ---
        # Obter a lista de passageiros que AINDA ESTÃO ESPERANDO da lista original da fila
        # Filtramos mantendo a ordem original da fila_aleatoria
        passageiros_esperando_na_fila = [p for p in self.jogo.fila_aleatoria if p.estado == 'esperando']

        diametro_passageiro = self.TAMANHO_CELULA / 2.5 # Um pouco maior para visibilidade na fila
        espaco_horizontal = diametro_passageiro * 1.3 # Ajustado espaçamento
        espaco_vertical = diametro_passageiro * 1.3   # Ajustado espaçamento
        offset_x_inicial = 5 + titulo_fila.boundingRect().width() + 10 # Espaço após o título
        y_start_drawing_pax = y_offset + titulo_fila.boundingRect().height() + 10 # Início do desenho dos passageiros

        # Calcule o número máximo de colunas que cabem na largura disponível
        max_cols = math.floor((self.largura_tabuleiro_px - offset_x_inicial) / espaco_horizontal)
        if max_cols <= 0: max_cols = 1 # Garante pelo menos uma coluna

        # Itera sobre a lista FILTRADA de passageiros esperando na ordem original da fila
        for idx, passenger in enumerate(passageiros_esperando_na_fila):
            linha = idx // max_cols
            col = idx % max_cols

            px = offset_x_inicial + (col * espaco_horizontal)
            py = y_start_drawing_pax + (linha * espaco_vertical)

            # Verificar se ainda há espaço na área da fila
            limite_inferior_area_fila = y_offset + self.altura_fila_px - 5 # 5px de margem inferior

            if (py + diametro_passageiro) > limite_inferior_area_fila:
                 # Se não couber completamente na área visível, paramos de desenhar.
                 # Isso simula a fila "saindo" da área de visualização se for muito longa.
                 break # Sai do loop
                 # continue # Usar continue para desenhar os que couberem, mesmo que a fila lógica seja mais longa

            ellipse_item = QGraphicsEllipseItem(px, py, diametro_passageiro, diametro_passageiro)
            try: ellipse_item.setBrush(QBrush(QColor(passenger.cor)))
            except ValueError: ellipse_item.setBrush(QBrush(Qt.GlobalColor.gray)) # Cor cinza se a cor for inválida
            ellipse_item.setPen(QPen(Qt.GlobalColor.darkGray))
            ellipse_item.setZValue(1)
            self.scene.addItem(ellipse_item)

        # --- FIM NOVO ---


    # NOVO MÉTODO: Desenhar a Área de Estacionamento por Cor (COM AUTOCARROS ESTACIONADOS)
    def desenhar_area_estacionamento(self, y_offset):
        """Desenha a área de estacionamento organizada por cor na parte inferior,
           incluindo a visualização dos autocarros estacionados."""
        # Fundo para a área de estacionamento
        cor_fundo_estacionamento = QColor("#C0C0C0") # Cor cinza um pouco mais escuro
        fundo_estacionamento = QGraphicsRectItem(0, y_offset, self.largura_tabuleiro_px, self.altura_estacionamento_px)
        fundo_estacionamento.setBrush(QBrush(cor_fundo_estacionamento))
        pen_fundo_estacionamento = QPen(Qt.GlobalColor.darkGray)
        pen_fundo_estacionamento.setWidth(1)
        fundo_estacionamento.setPen(pen_fundo_estacionamento)
        fundo_estacionamento.setZValue(-2) # Abaixo dos autocarros e da fila
        self.scene.addItem(fundo_estacionamento)

        # Título para a área de estacionamento
        titulo_estacionamento = QGraphicsTextItem("Estacionamento por Cor:")
        titulo_estacionamento.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        titulo_estacionamento.setDefaultTextColor(Qt.GlobalColor.black)
        titulo_estacionamento.setPos(5, y_offset + 5) # Posição dentro da área
        titulo_estacionamento.setZValue(1)
        self.scene.addItem(titulo_estacionamento)

        # Desenhar as áreas para cada cor ativa e os autocarros estacionados
        if hasattr(self.jogo, 'cores_ativas') and self.jogo.cores_ativas:
            num_cores = len(self.jogo.cores_ativas)
            if num_cores > 0:
                largura_zona_cor = self.largura_tabuleiro_px / num_cores
                # Ajusta altura para não sobrepor o título e deixar espaço para os autocarros
                altura_zona_cor_fundo = self.altura_estacionamento_px - (titulo_estacionamento.boundingRect().height() + 10)
                y_zona_cor_fundo = y_offset + titulo_estacionamento.boundingRect().height() + 10 # Espaço abaixo do título

                for i, cor in enumerate(self.jogo.cores_ativas):
                    x_zona_cor = i * largura_zona_cor

                    # Desenha o fundo colorido da zona de estacionamento para esta cor
                    zona_cor_rect = QGraphicsRectItem(x_zona_cor, y_zona_cor_fundo, largura_zona_cor, altura_zona_cor_fundo)
                    try:
                        cor_base = QColor(cor)
                        cor_fundo_zona = QColor(cor_base)
                        cor_fundo_zona.setAlpha(40) # Um pouco transparente
                        pen_zona = QPen(cor_base.darker(120))
                        pen_zona.setWidth(1)
                        zona_cor_rect.setBrush(QBrush(cor_fundo_zona))
                        zona_cor_rect.setPen(pen_zona)
                    except ValueError:
                        zona_cor_rect.setBrush(QBrush(Qt.GlobalColor.lightGray))
                        zona_cor_rect.setPen(QPen(Qt.GlobalColor.black))
                    zona_cor_rect.setZValue(-1) # Acima do fundo da área, abaixo dos autocarros estacionados
                    self.scene.addItem(zona_cor_rect)

                    # Texto com o nome da cor na zona de estacionamento
                    texto_cor_estacionamento = QGraphicsTextItem(cor.upper())
                    texto_cor_estacionamento.setFont(QFont("Arial", 7, QFont.Weight.Bold))
                    try:
                        texto_cor_estacionamento.setDefaultTextColor(QColor(cor).darker(150))
                    except ValueError:
                        texto_cor_estacionamento.setDefaultTextColor(Qt.GlobalColor.black)

                    rect_texto_cor_est = texto_cor_estacionamento.boundingRect()
                    pos_x_texto_est = x_zona_cor + (largura_zona_cor - rect_texto_cor_est.width()) / 2
                    pos_y_texto_est = y_zona_cor_fundo + 3 # Pequeno offset
                    texto_cor_estacionamento.setPos(pos_x_texto_est, pos_y_texto_est)
                    texto_cor_estacionamento.setZValue(1)
                    self.scene.addItem(texto_cor_estacionamento)

                    # --- Desenhar Autocarros Estacionados para esta cor ---
                    # Obter a lista de autocarros estacionados para esta cor
                    autocarros_estacionados = self.jogo.estacionamento_por_cor.get(cor, [])
                    # Altura disponível para desenhar autocarros dentro da zona da cor
                    altura_desenho_autocarros = altura_zona_cor_fundo - rect_texto_cor_est.height() - 5 # Espaço abaixo do texto
                    y_start_autocarros = y_zona_cor_fundo + rect_texto_cor_est.height() + 5

                    # Definir um tamanho visual menor para os autocarros estacionados
                    tamanho_visual_autocarro_est = self.TAMANHO_CELULA * 0.4 # Por exemplo, 40% do tamanho normal
                    espaco_h_autocarros = tamanho_visual_autocarro_est * 1.2
                    espaco_v_autocarros = tamanho_visual_autocarro_est * 1.2

                    # Calcular o número máximo de colunas que cabem na largura da zona de cor
                    max_cols_est = math.floor(largura_zona_cor / espaco_h_autocarros)
                    if max_cols_est <= 0: max_cols_est = 1 # Garante pelo menos uma coluna


                    for j, autocarro_est in enumerate(autocarros_estacionados):
                        # Calcular a posição visual do autocarro estacionado
                        linha_est = j // max_cols_est
                        col_est = j % max_cols_est

                        # Posição dentro da zona de cor específica
                        px_est = x_zona_cor + (col_est * espaco_h_autocarros) + 5 # Pequena margem
                        py_est = y_start_autocarros + (linha_est * espaco_v_autocarros)

                        # Verificar se o autocarro estacionado cabe na área de desenho
                        if (py_est + tamanho_visual_autocarro_est) > (y_zona_cor_fundo + altura_zona_cor_fundo - 5): # 5px margem inferior
                            break # Parar de desenhar se não houver mais espaço

                        # Desenhar um retângulo para representar o autocarro estacionado
                        rect_est = QGraphicsRectItem(px_est, py_est, tamanho_visual_autocarro_est, tamanho_visual_autocarro_est * 0.6) # Retângulo mais largo
                        try: rect_est.setBrush(QBrush(QColor(autocarro_est.cor)))
                        except ValueError: rect_est.setBrush(QBrush(Qt.GlobalColor.darkGray))
                        rect_est.setPen(QPen(Qt.GlobalColor.black, 1))
                        rect_est.setZValue(2) # Acima do fundo da zona de cor
                        self.scene.addItem(rect_est)

                        # Desenhar a contagem de passageiros embarcados vs capacidade total
                        # Acessar passageiros embarcados diretamente do objeto autocarro
                        embarcados = len(getattr(autocarro_est, 'passageiros_embarcados', []))
                        capacidade = autocarro_est.capacidade
                        texto_cap_est = QGraphicsTextItem(f"{embarcados}/{capacidade}")

                        fonte_cap_est = QFont("Arial", int(tamanho_visual_autocarro_est * 0.4), QFont.Weight.Bold) # Fonte ligeiramente menor
                        texto_cap_est.setFont(fonte_cap_est)
                        texto_cap_est.setDefaultTextColor(Qt.GlobalColor.white) # Cor branca para destacar
                        # Posicionar o texto no centro do retângulo
                        rect_cap_est = texto_cap_est.boundingRect()
                        pos_x_cap_est = px_est + (tamanho_visual_autocarro_est - rect_cap_est.width()) / 2
                        pos_y_cap_est = py_est + (tamanho_visual_autocarro_est * 0.6 - rect_cap_est.height()) / 2
                        texto_cap_est.setPos(pos_x_cap_est, pos_y_cap_est)
                        texto_cap_est.setZValue(3) # Acima do retângulo do autocarro
                        self.scene.addItem(texto_cap_est)

                        # Adicionar este autocarro gráfico ao dicionário de autocarros gráficos estacionados
                        # Usamos o objeto autocarro lógico como chave.
                        self.autocarros_graficos_estacionados[autocarro_est] = rect_est


    # +++ NOVO SLOT para o botão de Sugestão +++
    def sugerir_jogada(self):
        """Procura uma sugestão de jogada e faz a seta do autocarro piscar."""
        print("Botão Sugestão clicado. A procurar sugestão...")

        # 1. Parar qualquer animação de piscar existente
        self.stop_blinking_suggestion()

        # 2. Obter sugestão da lógica do jogo
        sugestao_autocarro, dx, dy = self.jogo.find_suggestion()

        # 3. Se uma sugestão for encontrada, iniciar o piscar na seta do autocarro gráfico
        if sugestao_autocarro:
            print(f"Sugestão encontrada para autocarro {sugestao_autocarro.cor}")
            # A sugestão é APENAS para autocarros no tabuleiro principal,
            # então procuramos apenas no dicionário de autocarros gráficos do tabuleiro.
            autocarro_grafico = self.autocarros_graficos.get(sugestao_autocarro)
            if autocarro_grafico:
                print(f"A iniciar piscar para {autocarro_grafico.autocarro.cor}")
                autocarro_grafico.start_blinking_arrow()
                # Guardar referência para poder parar depois
                self._current_blinking_autocarro_grafico = autocarro_grafico
            else:
                print(f"Erro: Item gráfico no tabuleiro não encontrado para autocarro sugerido {sugestao_autocarro.cor}")
        else:
            print("Nenhuma sugestão de jogada válida encontrada no tabuleiro principal.")
            # Opcional: Mostrar uma mensagem ao utilizador
            QMessageBox.information(self, "Sugestão", "Nenhuma jogada válida encontrada no tabuleiro principal.")

    # +++ NOVO MÉTODO para parar o piscar +++
    def stop_blinking_suggestion(self):
        """Para a animação de piscar na seta do autocarro sugerido anteriormente."""
        # Verifica se existe uma animação e se está a correr antes de parar
        # A animação de piscar é gerida pelo próprio AutocarroGrafico (usado apenas no tabuleiro principal)
        if self._current_blinking_autocarro_grafico:
             self._current_blinking_autocarro_grafico.stop_blinking_arrow()

        # Limpa a referência para o autocarro gráfico que estava a piscar
        self._current_blinking_autocarro_grafico = None
        # A referência da animação (self._blinking_animation) está dentro do AutocarroGrafico agora.
    # +++++++++++++++++++++++++++++++++++++++


    # +++ NOVO SLOT para limpar referência da animação manual +++
    def _on_animation_finished(self):
        """Slot chamado quando uma animação (self.animation) termina."""
        # Define a referência da animação manual como None para evitar erros de objeto apagado
        self.animation = None
        # NOVO: Processar a fila de embarque APÓS a animação terminar
        print("\n--- Animação terminada. A processar fila de embarque ---")
        self.jogo.processar_fila_embarque() # Chamar a nova função de processamento da fila
        # Redesenhar o estado do jogo
        self.desenhar_estado_jogo()


    # --- Métodos de Interação ---
    def autocarro_foi_clicado(self, autocarro):
        """Processa o clique num autocarro gráfico."""
        # +++ Parar sugestão a piscar quando um autocarro é clicado +++
        self.stop_blinking_suggestion()
        # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

        # Selecionar apenas autocarros no tabuleiro principal
        if autocarro in self.jogo.tabuleiro.autocarros:
            selecao_anterior = self.autocarro_selecionado; self.autocarro_selecionado = autocarro
            print(f"[JogoGUI] Autocarro selecionado: {autocarro}")
            # Atualiza o visual para remover highlight antigo e adicionar novo
            if selecao_anterior:
                 item_antigo = self.autocarros_graficos.get(selecao_anterior)
                 if item_antigo: item_antigo.update() # Pede redesenho (remove highlight)
            if self.autocarro_selecionado:
                item_novo = self.autocarros_graficos.get(self.autocarro_selecionado)
                if item_novo: item_novo.update() # Pede redesenho (adiciona highlight)
        else:
            # Se o autocarro clicado NÃO está no tabuleiro principal (está estacionado),
            # desselecionamos qualquer autocarro que estivesse selecionado.
            if self.autocarro_selecionado:
                 item_antigo = self.autocarros_graficos.get(self.autocarro_selecionado)
                 if item_antigo: item_antigo.update()
                 self.autocarro_selecionado = None
            print(f"[JogoGUI] Autocarro clicado ({autocarro.cor}) não está no tabuleiro principal. Nenhum autocarro selecionado para movimento.")


        self.setFocus() # Garante foco para capturar teclas

    def keyPressEvent(self, event):
        """Processa eventos de tecla para mover o autocarro selecionado."""
        # Ignora teclas se animação estiver a decorrer
        # Verifica primeiro se self.animation existe e não é None antes de aceder a state()
        if self.animation is not None and self.animation.state() == QAbstractAnimation.State.Running:
            # print("Debug: Animação em curso, tecla ignorada.")
            return

        if self.autocarro_selecionado is None:
            # Se nenhum autocarro está selecionado, passa o evento para o widget base
            super().keyPressEvent(event)
            return

        autocarro = self.autocarro_selecionado
        key = event.key()
        dx, dy = 0, 0 # Inicializa dx e dy para o movimento manual

        movimento_mapeado = False
        # Mapeia teclas para movimento APENAS na direção do autocarro
        if autocarro.direcao == "H":
            if key == Qt.Key.Key_Right:
                dx = 1
                movimento_mapeado = True
            elif key == Qt.Key.Key_Left:
                dx = -1
                movimento_mapeado = True  # Movimento para trás
        elif autocarro.direcao == "V":
            if key == Qt.Key.Key_Down:
                dy = 1
                movimento_mapeado = True
            elif key == Qt.Key.Key_Up:
                dy = -1
                movimento_mapeado = True  # Movimento para trás

        # Se a tecla pressionada não corresponde a um movimento mapeado para a direção do autocarro,
        # passa o evento para o widget base.
        if not movimento_mapeado:
            super().keyPressEvent(event)
            return

        # Se o movimento foi mapeado (dx != 0 ou dy != 0)
        if dx != 0 or dy != 0:
            # Verifica se é uma tentativa de saída (apenas para a frente na direção)
            # Uma saída ocorre quando a 'cabeça' do autocarro, movendo-se para a frente,
            # sairia da grelha principal (dimensões do tabuleiro lógico).
            tentativa_saida=False
            largura=self.jogo.tabuleiro.largura
            altura=self.jogo.tabuleiro.altura

            # Calcula o vetor de movimento "para a frente" na direção do autocarro para verificar a saída
            dx_frente_check, dy_frente_check = (1, 0) if autocarro.direcao == "H" else (0, 1)

            # Uma tentativa de saída acontece APENAS se o movimento manual atual for o movimento PARA A FRENTE
            if dx == dx_frente_check and dy == dy_frente_check:
                 # Verifica se a "cauda" do autocarro (com o comprimento) atingiu ou ultrapassou a borda de saída
                 # CORREÇÃO: Verificar a cauda do autocarro para a saída
                 pos_cauda_x = autocarro.x + (autocarro.capacidade - 1 if autocarro.direcao == "H" else 0)
                 pos_cauda_y = autocarro.y + (autocarro.capacidade - 1 if autocarro.direcao == "V" else 0)

                 nova_pos_cauda_x = pos_cauda_x + dx
                 nova_pos_cauda_y = pos_cauda_y + dy

                 if autocarro.direcao=="H" and nova_pos_cauda_x >= largura:
                      tentativa_saida=True
                 elif autocarro.direcao=="V" and nova_pos_cauda_y >= altura:
                      tentativa_saida=True


            if tentativa_saida:
                print(f"Tentativa de SAÍDA detectada para autocarro {autocarro.cor}")
                # Chama a função para processar a saída para a área de estacionamento
                self.process_exit_attempt(autocarro)
            else:
                # É um movimento normal dentro do tabuleiro principal (pode ser para a frente ou para trás)
                # CORREÇÃO: Usar dx e dy para verificar a validade do movimento manual
                if self.jogo.is_move_valid(autocarro, dx, dy):
                    # Encontra o item gráfico correspondente ao autocarro selecionado (deve estar no dicionário do tabuleiro)
                    item_a_mover = self.autocarros_graficos.get(autocarro)
                    if not item_a_mover:
                         print(f"Erro Animação: Item gráfico NÃO encontrado NO TABULEIRO para {autocarro}!");
                         return

                    # Posição inicial e final PARA A ANIMAÇÃO (em coordenadas da cena)
                    start_pos = item_a_mover.pos() # Posição atual do item gráfico na cena

                    # Calcula a posição final LÓGICA (no tabuleiro)
                    nova_x_logica = autocarro.x + dx
                    nova_y_logica = autocarro.y + dy

                    # Calcula a posição final na cena (usando o offset do parque)
                    target_x_cena = nova_x_logica * self.TAMANHO_CELULA
                    target_y_cena = (nova_y_logica * self.TAMANHO_CELULA) + self.altura_estacao_px
                    target_pos = QPointF(target_x_cena, target_y_cena)

                    # >>> ATUALIZA A POSIÇÃO LÓGICA DO AUTOCARRO ANTES DE INICIAR A ANIMAÇÃO <<<
                    autocarro.x = nova_x_logica
                    autocarro.y = nova_y_logica
                    self.jogo.movimentos += 1 # Incrementa contador de movimentos NO OBJETO JOGO
                    print(f"Movimento Válido: {autocarro.cor} movido para ({autocarro.x},{autocarro.y}). Total movimentos: {self.jogo.movimentos}. Animando...")

                    # Cria e configura a animação de movimento
                    self.animation = QPropertyAnimation(item_a_mover, b"pos", self) # Anima a propriedade 'pos' do item gráfico
                    if not self.animation:
                        print("Erro: Falha ao criar QPropertyAnimation!");
                        return
                    self.animation.setDuration(150) # Duração curta (ms)
                    self.animation.setStartValue(start_pos)
                    self.animation.setEndValue(target_pos)
                    curva = QEasingCurve(QEasingCurve.Type.OutQuad) # Curva de easing suave
                    self.animation.setEasingCurve(curva)

                    # >>> CONECTA O SINAL finished DA ANIMAÇÃO <<<
                    # Quando a animação terminar, o slot _on_animation_finished será chamado
                    self.animation.finished.connect(self._on_animation_finished)

                    # Inicia a animação
                    # DeletionPolicy.DeleteWhenStopped garante que o objeto animação é destruído ao terminar.
                    self.animation.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)

                    # +++ Parar sugestão a piscar quando um movimento manual é feito +++
                    self.stop_blinking_suggestion()
                    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

                    # O redesenho completo do estado (para atualizar contagens) acontece AGORA no _on_animation_finished
                    # self.desenhar_estado_jogo() # REMOVER: Redesenhar aqui pode causar problemas com a animação

                    self.setFocus() # Mantem o foco na janela para capturar próximas teclas
                else:
                    print(f"Movimento inválido - Bloqueado por colisão ou limite do tabuleiro.")

        # Se a tecla pressionada não era um movimento mapeado para o autocarro selecionado,
        # o evento é passado adiante pela verificação no início da função.
        # super().keyPressEvent(event) # Esta linha é alcançada se not movimento_mapeado

    def process_exit_attempt(self, autocarro_a_sair: Autocarro):
        """Processa a tentativa de saída de um autocarro do tabuleiro para a área de estacionamento."""
        print(f"Processando saída para autocarro {autocarro_a_sair.cor}...")

        # Remove o item gráfico da cena e do dicionário de referências do tabuleiro principal
        # Usamos pop com default=None para evitar erro se a chave não existir
        # NOTA: O item gráfico para autocarros na área de estacionamento será gerido
        # pelo desenhar_area_estacionamento e mantido em autocarros_graficos_estacionados.
        item_grafico_removido = self.autocarros_graficos.pop(autocarro_a_sair, None)
        if item_grafico_removido:
            # +++ Parar sugestão a piscar se o autocarro sugerido sair +++
            if self._current_blinking_autocarro_grafico == item_grafico_removido:
                self.stop_blinking_suggestion()
            # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++
            self.scene.removeItem(item_grafico_removido) # Remove o item gráfico da cena do tabuleiro
            print(f" -> Item gráfico do autocarro {autocarro_a_sair.cor} removido da cena do tabuleiro.")
        else:
            # Isto pode acontecer se o autocarro já tiver sido removido do tabuleiro lógico
            # mas process_exit_attempt foi chamado por algum motivo.
            print(f" -> Aviso: Item gráfico do autocarro {autocarro_a_sair.cor} não encontrado no dicionário 'autocarros_graficos' do tabuleiro.")


        # Remove o autocarro da lógica do jogo (do tabuleiro) E adiciona-o ao dicionário de estacionamento por cor.
        # A função remove_bus AGORA apenas move o autocarro lógico para a área de estacionamento (se for de cor ativa).
        removido_logico_do_tabuleiro = self.jogo.remove_bus(autocarro_a_sair)

        if removido_logico_do_tabuleiro:
            # Desseleciona o autocarro se este era o autocarro selecionado
            if self.autocarro_selecionado == autocarro_a_sair:
                self.autocarro_selecionado = None

            # NOVO: Após mover o autocarro para a área de estacionamento lógico,
            # processar a fila de embarque para tentar embarcar passageiros em autocarros estacionados.
            print(" -> Autocarro movido para a área de estacionamento lógico (se de cor ativa). A processar fila de embarque...")
            self.jogo.processar_fila_embarque() # Chamar a nova função de processamento da fila


            # ATUALIZA A VISUALIZAÇÃO COMPLETA
            # Essencial para atualizar a contagem de passageiros na estação, a remoção visual do autocarro do tabuleiro,
            # a visualização dos autocarros *na área de estacionamento* (incluindo os que ficam cheios e desaparecem),
            # e a fila de espera (que pode ter passageiros removidos).
            self.desenhar_estado_jogo()
            print("Saída para estacionamento e processamento da fila de embarque concluídos. Estado visual atualizado.")


            # 4. Verifica condição de vitória APÓS atualizar o estado e potencialmente remover autocarros cheios do estacionamento
            if self.jogo.verificar_vitoria():
                print("VITÓRIA!");
                self.parar_autoplay(); # <--- Linha que chama parar_autoplay
                QMessageBox.information(self,"Vitória!","Parabéns! Todos os passageiros foram embarcados.");
                self.reiniciar_jogo() # Reinicia o jogo após a vitória

        else:
            # Se o autocarro não foi encontrado no tabuleiro lógico para remover,
            # apenas redesenha o estado atual.
            print(f"Falha ao processar saída: autocarro {autocarro_a_sair.cor} não encontrado no tabuleiro lógico para remoção.")
            self.desenhar_estado_jogo()


    def toggle_autoplay(self, checked):
        """Inicia ou para o modo de jogo automático."""
        if checked:
            # Cancela animação manual se estiver a decorrer antes de iniciar autoplay
            if self.animation is not None and self.animation.state() == QAbstractAnimation.State.Running:
                 self.animation.stop() # Para a animação imediatamente
                 self.animation = None # Limpa a referência
                 # O slot _on_animation_finished será chamado pelo stop signal,
                 # que tratará do redesenho após a paragem abrupta, se necessário.

            # +++ Parar sugestão a piscar ao iniciar autoplay +++
            self.stop_blinking_suggestion()
            # +++++++++++++++++++++++++++++++++++++++++++++++++++

            self.autoplay_ativo = True
            self.botao_autoplay.setText("Parar Auto") # Mudar texto do botão
            # Define o intervalo entre passos do autoplay (em milissegundos)
            intervalo_ms = 300
            self.autoplay_timer.start(intervalo_ms)
            print(f"Autoplay iniciado com intervalo de {intervalo_ms}ms.")

            # Desseleciona qualquer autocarro que esteja selecionado visualmente
            if self.autocarro_selecionado:
                item_sel = self.autocarros_graficos.get(self.autocarro_selecionado)
                self.autocarro_selecionado = None;
                if item_sel: item_sel.update() # Remove o destaque visual
        else:
            # Se 'checked' é False, parar o autoplay
            self.parar_autoplay()


    def parar_autoplay(self):
        """Para o modo de jogo automático."""
        if self.autoplay_ativo:
            self.autoplay_ativo = False
            self.autoplay_timer.stop() # Para o timer
            self.botao_autoplay.setText("Jogar Auto") # Restaurar texto do botão
            self.botao_autoplay.setChecked(False) # Desmarca o botão
            print("Autoplay parado.")
            # Opcional: garantir que não fica nenhuma animação do autoplay a correr (embora _on_animation_finished deva limpar self.animation)
            # if self.animation is not None and self.animation.state() == QAbstractAnimation.State.Running:
            #    self.animation.stop()


    def passo_autoplay(self):
        """Executa um passo do jogo no modo autoplay (tenta mover um autocarro aleatório ou processar fila de embarque)."""
        # Se o autoplay foi desativado enquanto o timer estava a correr, parar o timer.
        if not self.autoplay_ativo:
            self.autoplay_timer.stop()
            return

        # Verifica se já existe uma animação a decorrer de um passo anterior
        # Usar 'self.animation is not None and ...' para ser mais explícito
        if self.animation is not None and self.animation.state() == QAbstractAnimation.State.Running:
            # Se uma animação estiver em curso, aguardar que termine antes de fazer o próximo movimento.
            # print("Autoplay: Animação em curso, a aguardar para o próximo passo...")
            return # Sai da função, o timer chamará novamente mais tarde

        # Verificar condição de vitória antes de tentar fazer um movimento
        if self.jogo.verificar_vitoria():
            print("Autoplay: Vitória alcançada!");
            self.parar_autoplay();
            # A mensagem de vitória e reinício serão tratadas na função verificar_vitoria
            return

        # --- NOVO: Processar a fila de embarque no início de cada passo do autoplay ---
        # Isso garante que o embarque em autocarros estacionados acontece sempre que possível.
        print("\n--- Passo do Autoplay. A processar fila de embarque ---")
        self.jogo.processar_fila_embarque() # Chamar a nova função de processamento da fila
        # Redesenha para mostrar o estado atual após a tentativa de embarque no estacionamento
        self.desenhar_estado_jogo()
        # Verifica novamente a vitória após o processamento da fila, caso algum embarque complete a condição
        if self.jogo.verificar_vitoria():
            print("Autoplay: Vitória alcançada após processamento da fila de embarque!");
            self.parar_autoplay();
            return
        # --- FIM NOVO ---


        # Tenta encontrar um autocarro que possa mover-se (primeiro para a frente, depois para trás)
        # Baralha a lista de autocarros para tentar movimentos em ordem aleatória
        buses = list(self.jogo.tabuleiro.autocarros); random.shuffle(buses)
        movimento_feito = False

        for autocarro in buses:
            # Tenta mover 1 unidade na sua direção
            dx_frente, dy_frente = (1, 0) if autocarro.direcao == "H" else (0, 1)

            # Verifica se a tentativa para a frente é uma saída
            tentativa_saida=False; largura=self.jogo.tabuleiro.largura; altura=self.jogo.tabuleiro.altura
            # CORREÇÃO: Verificar a cauda do autocarro para a saída no autoplay
            pos_cauda_x = autocarro.x + (autocarro.capacidade - 1 if autocarro.direcao == "H" else 0)
            pos_cauda_y = autocarro.y + (autocarro.capacidade - 1 if autocarro.direcao == "V" else 0)

            nova_pos_cauda_x = pos_cauda_x + dx_frente
            nova_pos_cauda_y = pos_cauda_y + dy_frente

            if autocarro.direcao=="H" and nova_pos_cauda_x >= largura:
                 tentativa_saida=True
            elif autocarro.direcao=="V" and nova_pos_cauda_y >= altura:
                 tentativa_saida=True


            if tentativa_saida:
                print(f"Autoplay: Tentando processar saída com autocarro {autocarro.cor}")
                # process_exit_attempt agora trata de adicionar ao estacionamento e *depois* processar a fila de embarque para todos os estacionados
                self.process_exit_attempt(autocarro)
                movimento_feito = True # Considera a saída como um movimento
                break # Sai do loop for depois de fazer um movimento (saída)

            elif self.jogo.is_move_valid(autocarro, dx_frente, dy_frente):
                # Se não é uma saída e o movimento para a frente é válido
                print(f"Autoplay: Movendo autocarro {autocarro.cor} para a frente.")
                # Busca o item gráfico no dicionário do tabuleiro principal
                item_a_mover = self.autocarros_graficos.get(autocarro)
                if item_a_mover:
                    start_pos=item_a_mover.pos() # Posição atual do item gráfico

                    # Calcula a nova posição lógica e de cena
                    nova_x_logica = autocarro.x + dx_frente
                    nova_y_logica = autocarro.y + dy_frente
                    target_x_cena=(nova_x_logica)*self.TAMANHO_CELULA
                    target_y_cena=((nova_y_logica)*self.TAMANHO_CELULA)+self.altura_estacao_px
                    target_pos=QPointF(target_x_cena, target_y_cena)

                    # >>> ATUALIZA A POSIÇÃO LÓGICA PRIMEIRO <<<
                    autocarro.x = nova_x_logica
                    autocarro.y = nova_y_logica
                    self.jogo.movimentos += 1 # Incrementa contador de movimentos
                    print(f"Autoplay: Autocarro {autocarro.cor} movido para ({autocarro.x},{autocarro.y}). Total movimentos: {self.jogo.movimentos}.")


                    # Cria e configura a animação
                    animation = QPropertyAnimation(item_a_mover, b"pos", self)
                    animation.setDuration(150) # Duração da animação
                    animation.setStartValue(start_pos); animation.setEndValue(target_pos)
                    curva = QEasingCurve(QEasingCurve.Type.OutQuad); animation.setEasingCurve(curva)

                    # Guarda a referência da animação e conecta o sinal finished
                    self.animation = animation # Guarda a referência da animação em self
                    self.animation.finished.connect(self._on_animation_finished)

                    # Inicia a animação
                    self.animation.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)

                    movimento_feito = True
                    break # Sai do loop for depois de fazer um movimento válido para a frente
                else:
                    print(f"Autoplay ERRO: Item gráfico NÃO encontrado NO TABULEIRO para autocarro {autocarro}")

            else:
                # Se o movimento para a frente não é válido e não é uma saída, tenta mover para trás
                dx_tras, dy_tras = (-1, 0) if autocarro.direcao == "H" else (0, -1)
                if self.jogo.is_move_valid(autocarro, dx_tras, dy_tras):
                    print(f"Autoplay: Movendo autocarro {autocarro.cor} para trás.")
                    # Busca o item gráfico no dicionário do tabuleiro principal
                    item_a_mover = self.autocarros_graficos.get(autocarro)
                    if item_a_mover:
                         start_pos=item_a_mover.pos()

                         # Calcula a nova posição lógica e de cena
                         nova_x_logica = autocarro.x + dx_tras
                         nova_y_logica = autocarro.y + dy_tras
                         target_x_cena=(nova_x_logica)*self.TAMANHO_CELULA
                         target_y_cena=((nova_y_logica)*self.TAMANHO_CELULA)+self.altura_estacao_px
                         target_pos=QPointF(target_x_cena, target_y_cena)

                         # >>> ATUALIZA A POSIÇÃO LÓGICA PRIMEIRO <<<
                         autocarro.x = nova_x_logica
                         autocarro.y = nova_y_logica
                         self.jogo.movimentos += 1 # Incrementa contador de movimentos
                         print(f"Autoplay: Autocarro {autocarro.cor} movido para ({autocarro.x},{autocarro.y}). Total movimentos: {self.jogo.movimentos}.")

                         # Cria e configura a animação
                         animation = QPropertyAnimation(item_a_mover, b"pos", self)
                         animation.setDuration(150)
                         animation.setStartValue(start_pos); animation.setEndValue(target_pos)
                         curva = QEasingCurve(QEasingCurve.Type.OutQuad); animation.setEasingCurve(curva)

                         # Guarda a referência da animação e conecta o sinal finished
                         self.animation = animation
                         self.animation.finished.connect(self._on_animation_finished)

                         # Inicia a animação
                         self.animation.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)

                         movimento_feito = True
                         break # Sai do loop for depois de fazer um movimento válido para trás
                    else:
                         print(f"Autoplay ERRO: Item gráfico NÃO encontrado NO TABULEIRO para autocarro {autocarro}")


        # Fim do loop for que tenta mover os autocarros
        if not movimento_feito and self.autoplay_ativo:
            # Se nenhum movimento (para frente ou para trás) ou saída foi possível para *qualquer* autocarro
            # Verifica se é vitória antes de declarar um bloqueio total
            if not self.jogo.verificar_vitoria():
                 print("Autoplay: Nenhum movimento válido ou de saída encontrado para nenhum autocarro.");
                 self.parar_autoplay(); # Para o autoplay
                 QMessageBox.warning(self,"Autoplay Parado","Nenhum movimento válido ou de saída encontrado para nenhum autocarro.")
            else:
                 # Se não houve movimento mas é vitória, apenas para o autoplay (a mensagem de vitória virá de outro lado)
                 print("Autoplay: Vitória alcançada (sem mais movimentos possíveis), parando.")
                 self.parar_autoplay()


    def reiniciar_jogo(self):
        """Reinicia o estado do jogo e a interface gráfica."""
        print("Reiniciando jogo...");
        # Para autoplay e qualquer animação em curso para um reset limpo
        self.parar_autoplay()
        if self.animation is not None and self.animation.state() == QAbstractAnimation.State.Running:
            self.animation.stop() # Para animação imediatamente
            self.animation = None # Limpa a referência

        # +++ Parar sugestão a piscar ao reiniciar +++
        self.stop_blinking_suggestion()
        # +++++++++++++++++++++++++++++++++++++++++++

        # Cria uma nova instância da lógica do jogo (isso gera um novo tabuleiro, passageiros, fila aleatória, etc.)
        self.jogo = Jogo()
        self.autocarro_selecionado = None # Desseleciona qualquer autocarro anterior
        self.autocarros_graficos.clear() # Limpa o dicionário de referências gráficas antigas do tabuleiro principal
        self.autocarros_graficos_estacionados.clear() # Limpa o dicionário de referências gráficas do estacionamento

        # Limpa a cena e redesenha tudo com o novo estado inicial do jogo
        self.desenhar_estado_jogo()
        self.setFocus() # Garante que a janela principal retoma o foco para input do utilizador

    # +++ NOVO SLOT para sair do jogo +++
    def sair_jogo(self):
        """Fecha a aplicação."""
        print("Botão Exit Game clicado. A sair do jogo.")
        QApplication.quit() # ou sys.exit(0)
    # +++++++++++++++++++++++++++++++++++

# --- Ponto de Entrada Principal ---
if __name__ == "__main__":
    # Cria a aplicação QApplication
    app = QApplication(sys.argv)

    # Cria a janela principal do jogo
    janela = JogoGUI()

    # Mostra a janela
    janela.show()

    # Inicia o loop de eventos da aplicação.
    # O aplicativo executa até que QCoreApplication::exit() seja chamado
    # ou o último widget de nível superior seja fechado.
    sys.exit(app.exec())