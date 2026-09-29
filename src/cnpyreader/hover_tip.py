"""悬停气泡：按住修饰键 + 鼠标停在词上，弹出该词的解释。"""

from PyQt6.QtCore import Qt, QPoint, QTimer
from PyQt6.QtGui import QCursor
from PyQt6.QtWidgets import QLabel, QWidget


class HoverTip(QLabel):
    """一个跟随鼠标的小气泡，显示词的说明。"""

    def __init__(self, parent):
        super().__init__(parent, Qt.WindowType.ToolTip)
        self.setWordWrap(True)
        self.setMaximumWidth(360)
        self.setStyleSheet("""
            QLabel {
                background-color: #2C313A;
                color: #E0E0E0;
                border: 1px solid #5C6370;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 13px;
            }
        """)
        self.hide()

    def show_text(self, text: str):
        self.setText(text)
        self.adjustSize()
        pos = QCursor.pos()
        # 弹在鼠标右下方，避免遮挡代码
        self.move(pos.x() + 12, pos.y() + 12)
        self.show()
        self.raise_()