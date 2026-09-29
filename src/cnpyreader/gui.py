"""图形界面：打开 Python 文件，左边英文，右边中文。"""

import sys
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor, QAction
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QSplitter, QFileDialog, QMessageBox,
    QDialog, QDialogButtonBox, QFormLayout, QLineEdit, QSpinBox,
    QComboBox, QCheckBox, QColorDialog,
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



        # 行号 margin（跟颜色无关，只设一次）
        self.setMarginType(0, QsciScintilla.MarginType.NumberMargin)
        self.setMarginWidth(0, "00000")
        
        # 折叠栏（段落指示条）：在行号右边
        # margin 1 是符号栏，margin 2 是折叠栏
        self.setMarginType(1, QsciScintilla.MarginType.SymbolMargin)
        self.setMarginWidth(1, 0)   # 符号栏先不用
        # 折叠栏。PyQt6 的 QScintilla 没导出 FoldMargin 枚举，
        # 但 setFolding 只吃 margin 编号，不吃枚举。
        # 直接给 margin 2 挂折叠：
        self.setMarginWidth(2, 14)
        self.setFolding(QsciScintilla.FoldStyle.PlainFoldStyle, 2)

        # 两侧都挂 lexer：它是唯一能可靠控制文本字体的途径。
        # 但只有左侧（use_lexer=True）才配置语法高亮颜色。
        lexer = QsciLexerPython()
        lexer.setDefaultFont(font)
        lexer.setDefaultColor(QColor("#ABB2BF"))
        lexer.setDefaultPaper(QColor("#282C34"))
        lexer.setFoldComments(True)
        lexer.setFoldQuotes(False)

        if use_lexer:
            lexer.setColor(QColor("#C678DD"), QsciLexerPython.Keyword)
            lexer.setColor(QColor("#98C379"), QsciLexerPython.DoubleQuotedString)
            lexer.setColor(QColor("#98C379"), QsciLexerPython.SingleQuotedString)
            lexer.setColor(QColor("#5C6370"), QsciLexerPython.Comment)
            lexer.setColor(QColor("#5C6370"), QsciLexerPython.CommentBlock)
            lexer.setColor(QColor("#D19A66"), QsciLexerPython.Number)
            lexer.setColor(QColor("#61AFEF"), QsciLexerPython.FunctionMethodName)
            lexer.setColor(QColor("#61AFEF"), QsciLexerPython.ClassName)
            lexer.setColor(QColor("#E5C07B"), QsciLexerPython.Decorator)

        self.setLexer(lexer)
        self._lexer = lexer

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

        # 所有 margin 配置好后，再上主题（顺序很重要）
        self.apply_theme()
        
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

    def apply_theme(self, settings: dict | None = None):
        """按配置重设颜色和字体。可在运行时随时调用，立即生效。"""
        from .settings import load_settings
        from PyQt6.QtGui import QFontDatabase, QPalette

        if settings is None:
            settings = load_settings()

        # ---- 颜色 ----
        bg = QColor(settings.get("editor_bg", "#282C34"))
        fg = QColor(settings.get("editor_fg", "#ABB2BF"))
        margin_bg = QColor(settings.get("margin_bg", "#353B47"))
        margin_fg = QColor(settings.get("margin_fg", "#D0D4DC"))
        sel_bg = QColor("#3E4451")

        # ---- 字体 ----
        available = QFontDatabase.families()
        chosen = settings.get("font_family", "Sarasa Mono SC")
        if chosen not in available:
            for fb in ["Sarasa Mono SC", "Source Han Sans CN Normal",
                       "Noto Sans Mono CJK SC", "Microsoft YaHei", "Consolas"]:
                if fb in available:
                    chosen = fb
                    break
            else:
                chosen = "Microsoft YaHei"

        font_size = settings.get("font_size", 11)
        font = QFont(chosen, font_size)
        font.setFixedPitch(True)
        self.setFont(font)
        self.setMarginsFont(font)

        # ---- 编辑器背景和文字 ----
        self.setColor(fg)
        self.setPaper(bg)
        self.setCaretForegroundColor(fg)
        self.setSelectionBackgroundColor(sel_bg)
        self.setSelectionForegroundColor(fg)
        self.setCaretLineBackgroundColor(bg.lighter(115))
        self.setUnmatchedBraceForegroundColor(QColor("#E06C75"))

        # ---- 更新 lexer（注意：不调用 setLexer！它会重置 margin）----
        if getattr(self, "_lexer", None) is not None:
            self._lexer.setDefaultFont(font)
            self._lexer.setDefaultColor(fg)
            self._lexer.setDefaultPaper(bg)
            for style in range(128):
                self._lexer.setFont(font, style)

        # ---- 高亮 indicator ----
        fill = QColor(settings.get("highlight_fill", "#2C3E50"))
        text = QColor(settings.get("highlight_text", "#5DADE2"))
        if not hasattr(self, "_fill_indicator"):
            self._fill_indicator = 8
            self.indicatorDefine(
                QsciScintilla.IndicatorStyle.StraightBoxIndicator,
                self._fill_indicator,
            )
            self.setIndicatorDrawUnder(True, self._fill_indicator)
            self._text_indicator = 9
            self.indicatorDefine(
                QsciScintilla.IndicatorStyle.TextColorIndicator,
                self._text_indicator,
            )
        self.setIndicatorForegroundColor(fill, self._fill_indicator)
        self.setIndicatorForegroundColor(text, self._text_indicator)

        # ---- 行号栏（放在最后，保证不被覆盖）----
        self.setMarginsBackgroundColor(margin_bg)
        self.setMarginsForegroundColor(margin_fg)
        # 折叠栏背景也设成同一色（覆盖之前残留的棕色）
        self.setFoldMarginColors(margin_bg, margin_bg)
        # 符号栏、折叠栏的底层背景也统一刷一遍
        for i in range(5):
            self.SendScintilla(
                QsciScintilla.SCI_SETMARGINBACKN, i,
                margin_bg.rgb() & 0xFFFFFF,
            )
        style_ln = getattr(QsciScintilla, "STYLE_LINENUMBER", 33)
        self.SendScintilla(
            QsciScintilla.SCI_STYLESETFORE, style_ln,
            margin_fg.rgb() & 0xFFFFFF,
        )
        self.SendScintilla(
            QsciScintilla.SCI_STYLESETBACK, style_ln,
            margin_bg.rgb() & 0xFFFFFF,
        )

        # ---- Qt palette（放最后，覆盖 viewport 白边）----
        pal = self.palette()
        pal.setColor(QPalette.ColorRole.Base, bg)
        pal.setColor(QPalette.ColorRole.Window, bg)
        self.setPalette(pal)

        self.recolor()
        self.update()
        
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
        settings_btn = QPushButton("设置")
        settings_btn.clicked.connect(self.open_settings)
        tb_layout.addWidget(settings_btn)
        
        # 主区域：左右两个编辑器
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # 启动时读一次配置，应用到编辑器
        from .settings import load_settings
        self._settings = load_settings()

        self.left_editor = CodeEditor(readonly=True, use_lexer=True)
        self.right_editor = CodeEditor(readonly=True, use_lexer=False)
        self.left_editor.apply_theme(self._settings)
        self.right_editor.apply_theme(self._settings)
        
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
        from .settings import load_settings
        default_dir = load_settings().get("default_open_dir", "").strip()

        path, _ = QFileDialog.getOpenFileName(
            self, "打开 Python 文件", default_dir,
            "Python 文件 (*.py);;所有文件 (*)"
        )
        if not path:
            return
        self.current_path = Path(path)
        self.path_label.setText(str(self.current_path))
        self.load_file()

        # 记住用户这次打开文件所在目录，下次默认用它
        self._remember_last_dir(path)

    def _remember_last_dir(self, file_path: str):
        """把用户刚刚访问的文件目录记入配置，下次打开对话框默认用它。

        仅在用户没手动设置 default_open_dir 时才自动更新——
        否则会覆盖用户明确指定的目录。
        """
        from .settings import load_settings, save_settings
        s = load_settings()
        # 用户明确设过目录 → 不自动覆盖
        if s.get("default_open_dir", "").strip():
            return
        new_dir = str(Path(file_path).parent)
        s["default_open_dir"] = new_dir
        save_settings(s)

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
        self._apply_background()

    def _apply_background(self):
        """按配置决定是否给左右编辑器打奇偶行底色。"""
        from .settings import load_settings
        s = load_settings()

        if not s.get("zebra_stripes", False):
            # 关掉奇偶 → 把之前画过的 marker 全清掉
            for ed in (self.left_editor, self.right_editor):
                for i in range(ed.lines()):
                    ed.markerDelete(i, 0)
            return

        line_count = max(
            self.left_editor.lines(),
            self.right_editor.lines(),
        )
        stripe = QColor(s.get("zebra_color", "#323842"))

        colors = []
        for i in range(line_count):
            colors.append(stripe if i % 2 == 0 else None)

        self.left_editor.set_line_colors(colors)
        self.right_editor.set_line_colors(colors)

    def open_settings(self):
        dlg = SettingsDialog(self)
        if dlg.exec():
            # 对话框返回 1（Accepted）：立即应用到两个编辑器
            from .settings import load_settings
            s = load_settings()
            self.left_editor.apply_theme(s)
            self.right_editor.apply_theme(s)
            self._apply_background()
            # 高亮模式也同步
            self.highlight_mode = s.get("highlight_mode", "both")
            labels = {
                "both":  "高亮：双边",
                "same":  "高亮：单边同侧",
                "other": "高亮：单边对侧",
            }
            self.highlight_btn.setText(labels[self.highlight_mode])

class SettingsDialog(QDialog):
    """设置对话框：颜色 + 字体 + 奇偶行 + 高亮模式。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.resize(420, 480)

        from .settings import load_settings
        self.s = load_settings()

        form = QFormLayout(self)

        # 颜色选择按钮：点击弹出取色器
        self.bg_btn = self._make_color_button("editor_bg")
        self.fg_btn = self._make_color_button("editor_fg")
        self.fill_btn = self._make_color_button("highlight_fill")
        self.text_btn = self._make_color_button("highlight_text")
        self.zebra_color_btn = self._make_color_button("zebra_color")

        form.addRow("编辑器背景", self.bg_btn)
        form.addRow("编辑器文字", self.fg_btn)
        form.addRow("高亮填充色", self.fill_btn)
        form.addRow("高亮文字色", self.text_btn)
        form.addRow("奇偶行浅色", self.zebra_color_btn)

        # 编辑器字体：Scintilla 只支持单一字体，中英不分离
        from PyQt6.QtGui import QFontDatabase
        families = sorted(QFontDatabase.families())

        self.font_combo = QComboBox()
        self.font_combo.setEditable(True)
        self.font_combo.addItems(families)
        self._select_combo(
            self.font_combo,
            self.s.get("font_family", "Sarasa Mono SC")
        )
        form.addRow("编辑器字体", self.font_combo)

        self.size_spin = QSpinBox()
        self.size_spin.setRange(8, 32)
        self.size_spin.setValue(self.s.get("font_size", 11))
        form.addRow("字号", self.size_spin)
        
        # 默认打开目录
        dir_row = QWidget()
        dir_layout = QHBoxLayout(dir_row)
        dir_layout.setContentsMargins(0, 0, 0, 0)

        self.dir_edit = QLineEdit(self.s.get("default_open_dir", ""))
        self.dir_edit.setPlaceholderText("留空则自动记住上次打开的目录")
        dir_layout.addWidget(self.dir_edit, stretch=1)

        browse_btn = QPushButton("浏览…")
        browse_btn.setFixedWidth(72)
        browse_btn.clicked.connect(self._pick_dir)
        dir_layout.addWidget(browse_btn)

        form.addRow("默认打开目录", dir_row)

        # 奇偶行开关
        self.zebra_cb = QCheckBox("启用奇偶行交替底色")
        self.zebra_cb.setChecked(self.s.get("zebra_stripes", False))
        form.addRow("", self.zebra_cb)

        # 高亮模式
        self.mode_combo = QComboBox()
        self.mode_combo.addItem("双边", "both")
        self.mode_combo.addItem("单边同侧", "same")
        self.mode_combo.addItem("单边对侧", "other")
        cur_mode = self.s.get("highlight_mode", "both")
        for i in range(self.mode_combo.count()):
            if self.mode_combo.itemData(i) == cur_mode:
                self.mode_combo.setCurrentIndex(i)
                break
        form.addRow("高亮模式", self.mode_combo)

        # 底部按钮：恢复默认 + OK + Cancel
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        reset_btn = buttons.addButton(
            "恢复默认",
            QDialogButtonBox.ButtonRole.ResetRole,
        )
        reset_btn.clicked.connect(self._restore_defaults)

        buttons.accepted.connect(self.save_and_accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def _select_combo(self, combo: QComboBox, value: str):
        """把下拉框选中到指定值。找不到就设到可编辑文本里。"""
        idx = combo.findText(value)
        if idx >= 0:
            combo.setCurrentIndex(idx)
        else:
            combo.setEditText(value)

    def _pick_dir(self):
        """弹出目录选择框，把选中目录写进输入框。"""
        current = self.dir_edit.text().strip()
        chosen = QFileDialog.getExistingDirectory(
            self, "选择默认打开目录", current
        )
        if chosen:
            self.dir_edit.setText(chosen)

    def _make_color_button(self, key: str) -> QPushButton:
        """做一个显示当前颜色的按钮，点击弹取色器。统一显示小写。"""
        btn = QPushButton()
        hex_lower = self.s.get(key, "#000000").lower()
        btn.setStyleSheet(
            f"background-color: {hex_lower}; min-height: 24px;"
        )
        btn.setText(hex_lower)
        btn.clicked.connect(lambda: self._pick_color(key, btn))
        return btn

    def _pick_color(self, key: str, btn: QPushButton):
        current = QColor(self.s.get(key, "#000000"))
        chosen = QColorDialog.getColor(current, self, "选择颜色")
        if chosen.isValid():
            hex_lower = chosen.name().lower()
            self.s[key] = hex_lower
            btn.setStyleSheet(
                f"background-color: {hex_lower}; min-height: 24px;"
            )
            btn.setText(hex_lower)

    def _restore_defaults(self):
        """把对话框里所有控件恢复成默认值。不写盘——用户仍需点 OK 才生效。"""
        from .settings import DEFAULTS
        d = DEFAULTS

        # 颜色按钮：改回默认色
        self._set_color_button("editor_bg", self.bg_btn, d["editor_bg"])
        self._set_color_button("editor_fg", self.fg_btn, d["editor_fg"])
        self._set_color_button("highlight_fill", self.fill_btn, d["highlight_fill"])
        self._set_color_button("highlight_text", self.text_btn, d["highlight_text"])
        self._set_color_button("zebra_color", self.zebra_color_btn, d["zebra_color"])

        # 字体、字号
        self._select_combo(self.font_combo, d["font_family"])
        self.size_spin.setValue(d["font_size"])

        # 开关和下拉
        self.zebra_cb.setChecked(d["zebra_stripes"])
        for i in range(self.mode_combo.count()):
            if self.mode_combo.itemData(i) == d["highlight_mode"]:
                self.mode_combo.setCurrentIndex(i)
                break
        # 默认打开目录
        self.dir_edit.setText(d.get("default_open_dir", ""))

    def _set_color_button(self, key: str, btn: QPushButton, color_hex: str):
        """把颜色按钮的显示和内部状态改成指定色。统一存小写。"""
        color_hex = color_hex.lower()
        self.s[key] = color_hex
        btn.setStyleSheet(
            f"background-color: {color_hex}; min-height: 24px;"
        )
        btn.setText(color_hex)

    def save_and_accept(self):
        """把对话框里的值写回配置并保存。"""
        self.s["font_family"] = (
            self.font_combo.currentText().strip()
            or "Sarasa Mono SC"
        )
        self.s["font_size"] = self.size_spin.value()
        self.s["zebra_stripes"] = self.zebra_cb.isChecked()
        self.s["highlight_mode"] = self.mode_combo.currentData()
        self.s["default_open_dir"] = self.dir_edit.text().strip()

        from .settings import save_settings
        if save_settings(self.s):
            self.accept()
        else:
            QMessageBox.warning(self, "保存失败", "无法写入配置文件。")

def main():
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()