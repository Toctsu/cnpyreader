"""图形界面：打开 Python 文件，左边英文，右边中文。"""

import sys
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor, QAction
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QSplitter, QFileDialog, QMessageBox,
)
from PyQt6.Qsci import QsciScintilla, QsciLexerPython

from .tokenizer import translate_source, translate_back


class CodeEditor(QsciScintilla):
    """一个带 Python 语法高亮、行号、只读的 QScintilla 编辑器。"""

    def __init__(self, readonly: bool = True, use_lexer: bool = True, parent=None):
        super().__init__(parent)

        # 字体：等宽，中英文都能显示
        font = QFont("Consolas", 11)
        font.setFixedPitch(True)
        font.setFamilies(["Consolas", "Microsoft YaHei", "SimSun"])
        self.setFont(font)
        self.setMarginsFont(font)

        # --- 深色主题（One Dark 配色） ---
        bg_color = QColor("#282C34")
        fg_color = QColor("#ABB2BF")
        selection_bg = QColor("#3E4451")

        # 基础编辑器底色和文字
        self.setColor(fg_color)
        self.setPaper(bg_color)
        self.setMarginsBackgroundColor(bg_color)
        self.setMarginsForegroundColor(QColor("#5C6370"))   # 行号：暗灰色
        self.setCaretForegroundColor(fg_color)
        self.setSelectionBackgroundColor(selection_bg)
        self.setSelectionForegroundColor(fg_color)          # 选中文字保持原色

        # 行号
        self.setMarginType(0, QsciScintilla.MarginType.NumberMargin)
        self.setMarginWidth(0, "00000")

        # Python 语法高亮（只在左侧英文编辑器用，避免中文被误高亮）
        if use_lexer:
            lexer = QsciLexerPython()
            lexer.setDefaultFont(font)
            lexer.setDefaultColor(fg_color)
            lexer.setDefaultPaper(bg_color)

            # 手动指定 Python 语法元素的颜色（One Dark）
            lexer.setColor(QColor("#C678DD"), QsciLexerPython.Keyword)              # 关键字：紫
            lexer.setColor(QColor("#98C379"), QsciLexerPython.DoubleQuotedString)   # 双引号字符串：绿
            lexer.setColor(QColor("#98C379"), QsciLexerPython.SingleQuotedString)   # 单引号字符串：绿
            lexer.setColor(QColor("#5C6370"), QsciLexerPython.Comment)              # 注释：灰
            lexer.setColor(QColor("#5C6370"), QsciLexerPython.CommentBlock)         # 块注释：灰
            lexer.setColor(QColor("#D19A66"), QsciLexerPython.Number)               # 数字：橙
            lexer.setColor(QColor("#61AFEF"), QsciLexerPython.FunctionMethodName)   # 函数名：蓝
            lexer.setColor(QColor("#61AFEF"), QsciLexerPython.ClassName)            # 类名：蓝
            lexer.setColor(QColor("#E5C07B"), QsciLexerPython.Decorator)            # 装饰器：黄

            self.setLexer(lexer)

        # 缩进
        self.setIndentationsUseTabs(False)
        self.setIndentationWidth(4)
        self.setTabWidth(4)

        # 其他
        self.setBraceMatching(QsciScintilla.BraceMatch.SloppyBraceMatch)
        self.setCaretLineVisible(True)
        self.setCaretLineBackgroundColor(QColor("#323842"))
        self.setUnmatchedBraceForegroundColor(QColor("#E06C75"))
        self.setReadOnly(readonly)

        # 联动高亮：两套 indicator 叠加
        #   8 = 整行填充底色（StraightBoxIndicator）
        #   9 = 行内文字变色（TextColorIndicator）
        # 两者都不和奇偶行底色的 marker 冲突。

        # --- 高亮色 ---
        # 调试用高对比色：橙红。逻辑确认后改成柔和的蓝灰。
        fill_color = QColor("#5C2A2A")     # 填充底色：暗红
        text_color = QColor("#FF8A8A")     # 文字色：亮橙红

        # indicator 8：填充整行
        self._fill_indicator = 8
        self.indicatorDefine(
            QsciScintilla.IndicatorStyle.StraightBoxIndicator,
            self._fill_indicator,
        )
        self.setIndicatorForegroundColor(fill_color, self._fill_indicator)
        self.setIndicatorDrawUnder(True, self._fill_indicator)

        # indicator 9：文字变色
        self._text_indicator = 9
        self.indicatorDefine(
            QsciScintilla.IndicatorStyle.TextColorIndicator,
            self._text_indicator,
        )
        self.setIndicatorForegroundColor(text_color, self._text_indicator)
    def set_line_colors(self, colors: list):
        """按行号设置整行背景色。

        colors: 列表，索引对应行号（0-based），元素是 QColor 或 None。
                None 表示不改这一行。
        """
        for i, color in enumerate(colors):
            if color is None:
                continue
            # QScintilla 用 marker 实现整行背景。
            # 先清掉这一行已有的 marker，再画新的。
            self.markerDelete(i, 0)
            marker_id = 0
            self.markerDefine(
                QsciScintilla.MarkerSymbol.Background,
                marker_id,
            )
            self.setMarkerBackgroundColor(color, marker_id)
            self.markerAdd(i, marker_id)

    def set_active_line(self, line: int):
        """用两套 indicator 高亮整行：填充 + 文字变色。"""
        # 先清掉旧的高亮
        self.clearIndicatorRange(0, 0, self.lines(), 0, self._fill_indicator)
        self.clearIndicatorRange(0, 0, self.lines(), 0, self._text_indicator)

        if not (0 <= line < self.lines()):
            return

        line_text = self.text(line)
        end_col = max(len(line_text), 1)   # 空行至少覆盖 1 列

        # 填充
        self.fillIndicatorRange(
            line, 0, line, end_col, self._fill_indicator
        )
        # 文字变色
        self.fillIndicatorRange(
            line, 0, line, end_col, self._text_indicator
        )

    def clear_active_line(self):
        """清除所有联动高亮。"""
        self.clearIndicatorRange(0, 0, self.lines(), 0, self._fill_indicator)
        self.clearIndicatorRange(0, 0, self.lines(), 0, self._text_indicator)
        
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("cnpyreader — Python 中文阅读器")
        self.resize(1200, 760)

        self.current_path: Path | None = None

        # 顶部工具条
        toolbar = QWidget()
        tb_layout = QHBoxLayout(toolbar)
        tb_layout.setContentsMargins(12, 8, 12, 8)

        open_btn = QPushButton("打开文件")
        open_btn.clicked.connect(self.open_file)
        tb_layout.addWidget(open_btn)

        self.path_label = QLabel("（未打开文件）")
        self.path_label.setStyleSheet("color: gray;")
        tb_layout.addWidget(self.path_label, stretch=1)

        # 翻译方向切换
        self.mode_btn = QPushButton("当前：英文 → 中文")
        self.mode_btn.setCheckable(True)
        self.mode_btn.toggled.connect(self.on_mode_toggled)
        tb_layout.addWidget(self.mode_btn)

        # 高亮模式：三态循环
        #   "both"  = 双边高亮（左右都亮）
        #   "same"  = 单边-同侧（只亮当前侧）
        #   "other" = 单边-对侧（只亮对面）
        self.highlight_mode = "both"
        self.highlight_btn = QPushButton("高亮：双边")
        self.highlight_btn.clicked.connect(self.on_highlight_clicked)
        tb_layout.addWidget(self.highlight_btn)
        
        # 主区域：左右两个编辑器
        splitter = QSplitter(Qt.Orientation.Horizontal)

        self.left_editor = CodeEditor(readonly=True, use_lexer=True)
        self.right_editor = CodeEditor(readonly=True, use_lexer=False)
        # 滚动同步：任何一边滚动，把另一边也滚到同一行
        self._syncing = False
        self.left_editor.verticalScrollBar().valueChanged.connect(
            self._on_left_scroll
        )
        self.right_editor.verticalScrollBar().valueChanged.connect(
            self._on_right_scroll
        )

        # 行级联动高亮：任意一边光标行变了，两边同步高亮
        self.left_editor.cursorPositionChanged.connect(
            self._on_left_cursor_moved
        )
        self.right_editor.cursorPositionChanged.connect(
            self._on_right_cursor_moved
        )

        splitter.addWidget(self.left_editor)
        splitter.addWidget(self.right_editor)
        splitter.setSizes([600, 600])

        # 整体布局
        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(toolbar)
        layout.addWidget(splitter, stretch=1)

        self.setCentralWidget(central)

        # 快捷键
        open_action = QAction("打开", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_file)
        self.addAction(open_action)
        
    def _on_left_scroll(self, value: int):
        if self._syncing:
            return
        self._syncing = True
        self.right_editor.verticalScrollBar().setValue(value)
        self._syncing = False

    def _on_right_scroll(self, value: int):
        if self._syncing:
            return
        self._syncing = True
        self.left_editor.verticalScrollBar().setValue(value)
        self._syncing = False

    def _on_left_cursor_moved(self, line: int, _col: int):
        self._apply_highlight(line, source="left")

    def _on_right_cursor_moved(self, line: int, _col: int):
        self._apply_highlight(line, source="right")

    def _apply_highlight(self, line: int, source: str):
        """按当前高亮模式，决定左右两侧如何亮。

        source: "left" 表示光标在左侧，"right" 表示在右侧。
        """
        mode = self.highlight_mode

        # 先清掉两侧
        self.left_editor.clear_active_line()
        self.right_editor.clear_active_line()

        if mode == "both":
            self.left_editor.set_active_line(line)
            self.right_editor.set_active_line(line)

        elif mode == "same":
            # 只亮当前侧
            if source == "left":
                self.left_editor.set_active_line(line)
            else:
                self.right_editor.set_active_line(line)

        elif mode == "other":
            # 只亮对面
            if source == "left":
                self.right_editor.set_active_line(line)
            else:
                self.left_editor.set_active_line(line)

    # ---- 翻译方向 ----
    def on_mode_toggled(self, checked: bool):
        if checked:
            self.mode_btn.setText("当前：中文 → 英文")
        else:
            self.mode_btn.setText("当前：英文 → 中文")
        # 重新翻译当前文件
        if self.current_path is not None:
            self.translate_current()

    def on_highlight_clicked(self):
        # 三态循环：both -> same -> other -> both
        order = ["both", "same", "other"]
        idx = order.index(self.highlight_mode)
        self.highlight_mode = order[(idx + 1) % 3]

        labels = {
            "both":  "高亮：双边",
            "same":  "高亮：单边同侧",
            "other": "高亮：单边对侧",
        }
        self.highlight_btn.setText(labels[self.highlight_mode])

        # 切换后重新触发一次当前光标所在行的高亮
        line, _ = self.left_editor.getCursorPosition()
        self._apply_highlight(line, source="left")

    # ---- 打开文件 ----
    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "打开 Python 文件", "",
            "Python 文件 (*.py);;所有文件 (*)"
        )
        if not path:
            return
        self.current_path = Path(path)
        self.path_label.setText(str(self.current_path))
        self.load_file()

    def load_file(self):
        if self.current_path is None:
            return
        try:
            source = self.current_path.read_text(encoding="utf-8-sig")
        except Exception as e:
            QMessageBox.warning(self, "读取失败", str(e))
            return

        self.left_editor.setText(source)
        self.translate_current()

    def translate_current(self):
        if self.current_path is None:
            return
        source = self.left_editor.text()
        try:
            if self.mode_btn.isChecked():
                # 中文 -> 英文
                result = translate_back(source)
            else:
                # 英文 -> 中文
                result = translate_source(source)
        except Exception as e:
            QMessageBox.warning(self, "翻译失败", str(e))
            return
        self.right_editor.setText(result)
        self._apply_zebra_stripes()

    def _apply_zebra_stripes(self):
        """给左右两个编辑器打奇偶行交替底色，让行行对应更直观。"""
        line_count = max(
            self.left_editor.lines(),
            self.right_editor.lines(),
        )
        odd_color = QColor("#323842")
        even_color = None

        colors = []
        for i in range(line_count):
            if i % 2 == 0:
                colors.append(odd_color)
            else:
                colors.append(even_color)

        self.left_editor.set_line_colors(colors)
        self.right_editor.set_line_colors(colors)

def main():
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()