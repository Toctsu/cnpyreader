"""最小诊断：QScintilla 什么都不设，看默认颜色。"""
import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.Qsci import QsciScintilla

app = QApplication(sys.argv)

ed = QsciScintilla()
# 只挂行号，其他什么都不设
ed.setMarginType(0, QsciScintilla.MarginType.NumberMargin)
ed.setMarginWidth(0, "00000")
ed.setText("line1\nline2\nline3\n")
ed.resize(600, 300)
ed.show()

print("=== 默认状态（什么都没设）===")
for i in range(5):
    w = ed.SendScintilla(QsciScintilla.SCI_GETMARGINWIDTHN, i)
    if w > 0:
        bg = ed.SendScintilla(QsciScintilla.SCI_GETMARGINBACKN, i)
        print(f"margin {i}: width={w}px  bg={hex(bg)}")

sys.exit(app.exec())