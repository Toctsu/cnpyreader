"""词典加载器：从内置 TOML 和用户自定义 TOML 合并出三层词典。

目录约定：
- 内置：src/cnpyreader/dictionaries/*.toml
- 用户：~/.cnpyreader/dictionaries/*.toml

加载顺序：内置 -> 用户。用户词表逐键覆盖内置。
"""

from pathlib import Path

try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:
    import tomli as tomllib  # 3.10 及以下


#: 内置词典目录
BUILTIN_DIR = Path(__file__).parent

#: 用户自定义词典目录
USER_DIR = Path.home() / ".cnpyreader" / "dictionaries"


def _load_toml_dir(directory: Path) -> dict:
    """读一个目录下所有 .toml，合并成一个 dict。

    每个 .toml 的顶层应该是三个表：[keywords] [builtins] [identifiers]。
    不在这个结构里的内容会被忽略。
    """
    merged = {"keywords": {}, "builtins": {}, "identifiers": {}}
    if not directory.is_dir():
        return merged
    for path in sorted(directory.glob("*.toml")):
        # 读成文本、剥掉 BOM，再交给 tomllib 解析。
        # 因为 Windows PowerShell 的 Out-File -Encoding utf8 会写 BOM。
        text = path.read_text(encoding="utf-8-sig")
        data = tomllib.loads(text)
        for section in ("keywords", "builtins", "identifiers"):
            if section in data:
                merged[section].update(data[section])
    return merged

def _load_explanations() -> dict:
    """载入 explanations.toml，合并 keywords 和 builtins 两个表。"""
    result = {}
    path = BUILTIN_DIR / "explanations.toml"
    if not path.is_file():
        return result
    try:
        import tomllib
        data = tomllib.loads(path.read_text(encoding="utf-8-sig"))
        for section in ("keywords", "builtins"):
            if section in data:
                result.update(data[section])
    except Exception as e:
        print(f"[解释表] 载入失败：{e}")
    return result


EXPLANATIONS = _load_explanations()

def _merge(builtin: dict, user: dict) -> dict:
    """用户词表覆盖内置词表。"""
    out = {k: dict(v) for k, v in builtin.items()}
    for section, table in user.items():
        if section in out:
            out[section].update(table)
    return out


# 加载并合并
_builtin = _load_toml_dir(BUILTIN_DIR)
_user = _load_toml_dir(USER_DIR)
_merged = _merge(_builtin, _user)

KEYWORDS = _merged["keywords"]
BUILTINS = _merged["builtins"]
IDENTIFIER_WORDS = _merged["identifiers"]


def _invert(d):
    """把 {英文: 中文} 翻成 {中文: 英文}。

    允许多对一：多个英文词可以映射到同一个中文词。
    反向时取"第一次出现"的英文词作为还原目标，
    所以词典里应把全称写在缩写前面。
    """
    result = {}
    for en, cn in d.items():
        if cn not in result:
            result[cn] = en
    return result


REVERSE_KEYWORDS = _invert(KEYWORDS)
REVERSE_BUILTINS = _invert(BUILTINS)
REVERSE_IDENTIFIER_WORDS = _invert(IDENTIFIER_WORDS)