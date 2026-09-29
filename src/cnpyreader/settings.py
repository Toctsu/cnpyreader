"""cnpyreader 的用户配置：读写 ~/.cnpyreader/settings.json。"""

import json
from pathlib import Path

CONFIG_DIR = Path.home() / ".cnpyreader"
CONFIG_FILE = CONFIG_DIR / "settings.json"

#: 默认配置。新增字段时这里加一条，老配置文件自动补齐。
DEFAULTS = {
    "editor_bg": "#282C34",         # 编辑器背景色
    "editor_fg": "#ABB2BF",         # 编辑器默认文字色
    "margin_bg": "#768299",         # 行号栏背景（比编辑器亮一档，有区分）
    "margin_fg": "#5b657a",         # 行号栏数字颜色（浅灰白）
    "highlight_fill": "#2C3E50",    # 联动高亮：填充底色
    "highlight_text": "#5DADE2",    # 联动高亮：文字色
    "zebra_stripes": False,         # 是否启用奇偶行交替底色
    "zebra_color": "#323842",       # 奇偶底色的浅色（启用时用）
    "highlight_mode": "both",       # both / same / other
    "font_family": "Sarasa Mono SC",  # 编辑器字体（推荐更纱黑体等宽版）
    "font_size": 11,
    "default_open_dir": "",           # 打开文件对话框的默认目录，空 = 用系统默认
}


def load_settings() -> dict:
    """读配置，缺失字段用默认值补齐。读失败也返回默认值。"""
    if not CONFIG_FILE.exists():
        return dict(DEFAULTS)
    try:
        text = CONFIG_FILE.read_text(encoding="utf-8-sig")
        data = json.loads(text)
        merged = dict(DEFAULTS)
        merged.update(data)
        return merged
    except Exception as e:
        print(f"[设置] 读取失败：{e}")
        return dict(DEFAULTS)


def save_settings(settings: dict) -> bool:
    """保存配置。返回 True 表示成功，False 表示失败。"""
    try:
        CONFIG_DIR.mkdir(exist_ok=True)
        CONFIG_FILE.write_text(
            json.dumps(settings, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return True
    except Exception as e:
        print(f"[设置] 保存失败：{e}")
        return False

def reset_settings() -> dict:
    """把配置文件重置为默认值，并返回默认字典。

    调用后写盘，下次 load_settings() 会读到全新的默认值。
    """
    defaults = dict(DEFAULTS)
    save_settings(defaults)
    return defaults