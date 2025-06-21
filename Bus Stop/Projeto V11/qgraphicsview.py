# ficheiro: Projeto/qgraphicsview.py

from PyQt6.QtWidgets import QGraphicsView
from PyQt6.QtCore import Qt

class CustomGraphicsView(QGraphicsView):
    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)

    def keyPressEvent(self, event):
        if self.parent() and hasattr(self.parent(), 'keyPressEvent'):
            self.parent().keyPressEvent(event)
        else:
            super().keyPressEvent(event)