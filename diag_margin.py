"""诊断：打印所有 margin 的宽度和背景色。"""
import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QColor, QFont
from PyQt6.Qsci import QsciScintilla

app = QApplication(sys.argv)
ed = QsciScintilla()

# 用跟 gui.py 完全相同的 margin 配置
ed.setMarginType(0, QsciScintilla.MarginType.NumberMargin)
ed.setMarginWidth(0, "00000")
ed.setMarginType(1, QsciScintilla.MarginType.SymbolMargin)
ed.setMarginWidth(1, 0)
ed.setMarginWidth(2, 14)
ed.setFolding(QsciScintilla.FoldStyle.PlainFoldStyle, 2)

# 设成显眼的颜色，方便看哪一层是哪一层
colors = {
    0: QColor("#FF0000"),   # 红 = 行号栏
    1: QColor("#00FF00"),   # 绿 = 符号栏
    2: QColor("#0000FF"),   # 蓝 = 折叠栏
    3: QColor("#FFFF00"),   # 黄
    4: QColor("#FF00FF"),   # 紫
}
for i, c in colors.items():
    ed.SendScintilla(QsciScintilla.SCI_SETMARGINBACKN, i, c.rgb() & 0xFFFFFF)

ed.setText("line1\nline2\n")
ed.resize(400, 200)
ed.show()

# 打印每个 margin 的实际宽度和颜色
print("=== margin 实际状态 ===")
for i in range(5):
    width = ed.SendScintilla(QsciScintilla.SCI_GETMARGINWIDTHN, i)
    back = ed.SendScintilla(QsciScintilla.SCI_GETMARGINBACKN, i)
    c = QColor(back & 0xFFFFFF)
    print(f"margin {i}: width={width:3d}px  bg={c.name()}")

# 打印行号栏专用 style 的颜色
style_ln = getattr(QsciScintilla, "STYLE_LINENUMBER", 33)
print(f"STYLE_LINENUMBER({style_ln}) "
      f"fore={QColor(ed.SendScintilla(QsciScintilla.SCI_STYLEGETFORE, style_ln) & 0xFFFFFF).name()} "
      f"back={QColor(ed.SendScintilla(QsciScintilla.SCI_STYLEGETBACK, style_ln) & 0xFFFFFF).name()}")

# 窗口关掉再退出，避免占住终端
sys.exit(0)