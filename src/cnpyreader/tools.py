"""给模型调用的工具函数：翻译、结构提取、符号翻译。

这三个函数是纯函数，输入输出都是基本类型，
方便被 MCP server 或其他 agent 框架直接包装。
"""

import ast

from .tokenizer import translate_source, translate_back
from .dictionaries import KEYWORDS, BUILTINS, IDENTIFIER_WORDS


def translate_code(source: str, direction: str = "to_chinese") -> str:
    """把源码在中英文之间翻译。

    参数：
        source: 源代码字符串
        direction: "to_chinese" 英文->中文；"to_english" 中文->英文

    返回：翻译后的源码字符串。
    """
    # 兜底：有些模型会把换行传成字面 "\n"，先还原成真实换行再翻译
    if "\\n" in source and "\n" not in source:
        source = source.replace("\\n", "\n")

    if direction == "to_chinese":
        return translate_source(source)
    if direction == "to_english":
        return translate_back(source)
    raise ValueError(f"未知方向: {direction}")


def get_structure(source: str) -> dict:
    """解析 Python 源码，返回结构树。

    返回形如：
    {
      "classes": [{"name": "A", "line": 1, "methods": [...]}],
      "functions": [{"name": "f", "line": 10, "args": ["x", "y"]}],
      "imports": [{"module": "os", "line": 1}],
    }

    解析失败时返回 {"error": "..."}。
    """
    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        return {"error": f"语法错误: {e}"}

    classes = []
    functions = []
    imports = []

    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            classes.append({
                "name": node.name,
                "line": node.lineno,
                "methods": [m.name for m in node.body
                            if isinstance(m, ast.FunctionDef)],
            })
        elif isinstance(node, ast.FunctionDef):
            functions.append({
                "name": node.name,
                "line": node.lineno,
                "args": [a.arg for a in node.args.args],
            })
        elif isinstance(node, ast.Import):
            for alias in node.names:
                imports.append({"module": alias.name, "line": node.lineno})
        elif isinstance(node, ast.ImportFrom):
            imports.append({
                "module": node.module or "",
                "line": node.lineno,
            })

    return {"classes": classes, "functions": functions, "imports": imports}


def translate_symbol(name: str) -> str:
    """翻译单个标识符或关键字。

    优先关键字、内置，再按标识符拆词。
    未命中的部分原样保留。
    """
    if name in KEYWORDS:
        return KEYWORDS[name]
    if name in BUILTINS:
        return BUILTINS[name]

    if "_" in name:
        parts = [p for p in name.split("_") if p]
        out = []
        for p in parts:
            low = p.lower()
            if low in IDENTIFIER_WORDS:
                out.append(IDENTIFIER_WORDS[low])
            else:
                out.append(p)
        return "_".join(out)

    low = name.lower()
    if low in IDENTIFIER_WORDS:
        return IDENTIFIER_WORDS[low]
    return name