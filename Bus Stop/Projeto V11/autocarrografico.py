# ficheiro: Projeto/autocarrografico.py

# --- Imports Atualizados (Inclui animação) ---
from PyQt6.QtCore import Qt, QRectF, QPointF, QPropertyAnimation, QEasingCurve, QAbstractAnimation, pyqtProperty, QTimer
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen, QPixmap, QFont
from PyQt6.QtWidgets import QGraphicsObject, QGraphicsItem, QStyleOptionGraphicsItem, QWidget, QStyle, QGraphicsTextItem
# +++++++++++++++++++++++++++++++++++++++++++++++++++

from autocarro import Autocarro

# --- Classe Gráfica do Autocarro ---
class AutocarroGrafico(QGraphicsObject):
    TAMANHO_CELULA = 30 # Mantém o tamanho menor

    # +++ Propriedade para Animar a Cor da Seta +++
    # Precisamos de uma propriedade dinamicamente acessível para QPropertyAnimation
    def get_arrow_item(self) -> QGraphicsTextItem | None:
        """Procura e retorna o item gráfico da seta entre os childItems()."""
        # Iterar pelos itens filhos gráficos
        for item in self.childItems():
            # Verificar se é um QGraphicsTextItem e se tem o objectName correto
            if isinstance(item, QGraphicsTextItem) and item.objectName() == "arrowItem":
                return item
        return None

    def get_arrow_color(self):
        """Obtém a cor atual do item gráfico da seta usando get_arrow_item()."""
        arrow_item = self.get_arrow_item()
        if arrow_item:
            return arrow_item.defaultTextColor()
        return QColor(Qt.GlobalColor.black) # Cor padrão se não encontrar a seta

    def set_arrow_color(self, color):
        """Define a cor do item gráfico da seta e força um redesenho usando get_arrow_item()."""
        arrow_item = self.get_arrow_item()
        if arrow_item:
            # Define a nova cor (garantindo que é um objeto QColor)
            arrow_item.setDefaultTextColor(QColor(color))
            # Pede ao item gráfico pai (AutocarroGrafico) para se redesenhar
            # Isso garante que a mudança de cor da seta (o filho) é visível
            self.update()

    # Define a propriedade 'arrowColor' que QPropertyAnimation pode usar.
    # O 'b"arrowColor"' cria um QByteArray a partir do nome da propriedade,
    # que é o que o QPropertyAnimation espera.
    arrowColor = pyqtProperty(QColor, get_arrow_color, set_arrow_color)
    # +++++++++++++++++++++++++++++++++++++++++++++++


    def __init__(self, autocarro: Autocarro, parent: QGraphicsItem | None = None):
        super().__init__(parent)
        self.autocarro = autocarro
        self._icon_pixmap = None # Para guardar a imagem do ícone

        # +++ Atributo para a animação de piscar +++
        self._blinking_animation = None
        # ++++++++++++++++++++++++++++++++++++++++

        # Calcula dimensões baseadas nas células
        if self.autocarro.direcao == "H":
            self._width = self.TAMANHO_CELULA * self.autocarro.capacidade
            self._height = self.TAMANHO_CELULA
        else: # Direção "V"
            self._width = self.TAMANHO_CELULA
            self._height = self.TAMANHO_CELULA * self.autocarro.capacidade

        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setData(0, self.autocarro)


    # +++ Métodos para controlar o piscar da seta (AGORA USANDO childItems()) +++
    def start_blinking_arrow(self):
        """Inicia a animação de piscar na seta do autocarro."""

        # --- DEBUG: Verificar filhos gráficos antes de procurar ---
        print(f"DEBUG (start_blinking_arrow): Chamado para Autocarro {self.autocarro.cor}")
        print(f"DEBUG (start_blinking_arrow): A procurar item com objectName 'arrowItem' entre os childItems() de {self.autocarro.cor} ({self.__class__.__name__})")
        # Listar os nomes dos childItems que são QGraphicsTextItem para debug
        child_item_names = [item.objectName() for item in self.childItems() if isinstance(item, QGraphicsTextItem) and hasattr(item, 'objectName')]
        print(f"DEBUG (start_blinking_arrow): ObjectNames dos QGraphicsTextItems childItems encontrados: {child_item_names}")
        # --- FIM DEBUG ---

        # Encontra o item da seta usando o novo método get_arrow_item()
        arrow_item = self.get_arrow_item()

        if not arrow_item:
            print("Erro: Item da seta não encontrado para animar (usando childItems())!")
            return

        # Para qualquer animação anterior nesta seta
        self.stop_blinking_arrow()

        # Cria a animação de cor
        # Anima a propriedade 'arrowColor' que definimos acima
        self._blinking_animation = QPropertyAnimation(self, b"arrowColor", self)
        self._blinking_animation.setDuration(400) # Duração de um ciclo (amarelo -> preto -> amarelo)
        # Define os valores chave para a animação:
        # No início (0.0), a cor é amarela.
        # A meio (0.5), a cor volta à cor original da seta (preto).
        # No fim (1.0), a cor volta a ser amarela.
        self._blinking_animation.setStartValue(QColor("yellow"))
        self._blinking_animation.setKeyValueAt(0.5, QColor(Qt.GlobalColor.black)) # Cor do texto original
        self._blinking_animation.setEndValue(QColor("yellow"))

        self._blinking_animation.setLoopCount(-1) # Repetir indefinidamente
        # Define para apagar a animação quando parar (evita fugas de memória)
        self._blinking_animation.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)

    def stop_blinking_arrow(self):
        """Para a animação de piscar na seta e restaura a cor original."""
        # Verifica se existe uma animação e se está a correr antes de parar
        if self._blinking_animation and self._blinking_animation.state() == QAbstractAnimation.State.Running:
            self._blinking_animation.stop()
            print("Animação de piscar parada.")

        # Garante que a cor da seta volta ao padrão original (preto)
        # Encontra o item da seta usando o novo método get_arrow_item()
        arrow_item = self.get_arrow_item()
        if arrow_item:
             arrow_item.setDefaultTextColor(Qt.GlobalColor.black)
             arrow_item.update() # Redesenha para aplicar a cor padrão

        # Limpa a referência para a animação
        self._blinking_animation = None
    # +++++++++++++++++++++++++++++++++++++++++++++++


    # --- boundingRect (Usa dimensões calculadas) ---
    def boundingRect(self) -> QRectF:
        """Retorna os limites externos do item nas suas coordenadas locais."""
        # Baseia-se nas dimensões calculadas, não na imagem do ícone
        return QRectF(0, 0, self._width, self._height)

    # --- paint (Desenha fundo + ícone) ---
    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: QWidget | None = None) -> None:
        """Desenha o fundo colorido, o ícone, e a borda/highlight."""
        rect = self.boundingRect()

        # --- 1. Desenha o fundo colorido ---
        try: brush = QBrush(QColor(self.autocarro.cor))
        except ValueError: brush = QBrush(Qt.GlobalColor.darkGray) # Fallback cor
        painter.setBrush(brush)
        # Define a Pen BASE (sem highlight aqui, tratado depois)
        pen_base = QPen(Qt.GlobalColor.black); pen_base.setWidth(1)
        painter.setPen(pen_base)
        painter.drawRect(rect) # Desenha o retângulo colorido
        # -----------------------------------

        # --- 2. Desenha o Ícone (se carregado) no Canto Inferior Esquerdo ---
        if self._icon_pixmap:
            margin = 2 # Pequena margem do canto
            icon_width = self._icon_pixmap.width()
            icon_height = self._icon_pixmap.height()
            # Posição X: Canto esquerdo (0 local) + margem
            icon_x = margin
            # Posição Y: Altura total - altura do ícone - margem
            icon_y = rect.height() - icon_height - margin

            # Desenha o pixmap nessa posição local
            painter.drawPixmap(int(icon_x), int(icon_y), self._icon_pixmap)
        # -----------------------------------------------------------------

        # --- 3. Desenha Destaque de Seleção (POR CIMA de tudo) ---
        if option.state & QStyle.StateFlag.State_Selected:
             pen_highlight = QPen(QColor("yellow")) # Cor do destaque
             pen_highlight.setWidth(3) # Espessura do destaque
             painter.setPen(pen_highlight)
             painter.setBrush(Qt.BrushStyle.NoBrush) # Sem preenchimento
             # Desenha retângulo de destaque nos limites externos
             painter.drawRect(rect)
        # ------------------------------------------------------

    # --- mousePressEvent (sem alterações) ---
    def mousePressEvent(self, event):
        # print(f"[AutocarroGrafico] Clicado: {self.autocarro}") # Debug
        try: # Notifica JogoGUI
            # Para o piscar quando o autocarro é clicado
            self.stop_blinking_arrow()
            # Notifica a JogoGUI
            jogo_gui = self.scene().views()[0].parent()
            if hasattr(jogo_gui, 'autocarro_foi_clicado'):
                 jogo_gui.autocarro_foi_clicado(self.autocarro)
        except Exception as e:
             print(f"Erro no mousePressEvent de AutocarroGrafico: {e}")
        super().mousePressEvent(event) # Propaga evento