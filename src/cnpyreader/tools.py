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


def _node_to_dict(node: ast.AST) -> dict:
    """把一个 AST 节点转成结构字典（递归）。"""
    result = {
        "name": getattr(node, "name", None),
        "line_start": node.lineno,
        "line_end": getattr(node, "end_lineno", node.lineno),
        "type": type(node).__name__,
    }

    # 参数（函数才有）
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        result["args"] = [a.arg for a in node.args.args]
        result["is_async"] = isinstance(node, ast.AsyncFunctionDef)

    # 子节点
    children = []
    for child in ast.iter_child_nodes(node):
        if isinstance(child, (ast.ClassDef, ast.FunctionDef,
                              ast.AsyncFunctionDef)):
            children.append(_node_to_dict(child))
        elif isinstance(child, (ast.If, ast.For, ast.While,
                                 ast.Try, ast.With)):
            # 控制流节点也暴露出来，但不递归进它的子函数
            children.append({
                "name": None,
                "line_start": child.lineno,
                "line_end": getattr(child, "end_lineno", child.lineno),
                "type": type(child).__name__,
            })
    if children:
        result["children"] = children

    return result


def get_structure(source: str) -> dict:
    """解析 Python 源码，返回递归结构树。

    每个节点包含：
      - name: 类名 / 函数名（控制流节点为 None）
      - type: 节点类型，如 ClassDef / FunctionDef / If / For / While
      - line_start / line_end: 起止行号（1-based）
      - args: 函数参数（仅函数）
      - is_async: 是否异步函数（仅函数）
      - children: 子节点列表

    解析失败时返回 {"error": "..."}。
    """
    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        return {"error": f"语法错误: {e}"}

    imports = []
    top_level = []

    for node in tree.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append({"module": alias.name, "line": node.lineno})
        elif isinstance(node, ast.ImportFrom):
            imports.append({"module": node.module or "", "line": node.lineno})
        elif isinstance(node, (ast.ClassDef, ast.FunctionDef,
                               ast.AsyncFunctionDef)):
            top_level.append(_node_to_dict(node))
        elif isinstance(node, (ast.If, ast.For, ast.While,
                               ast.Try, ast.With)):
            top_level.append({
                "name": None,
                "line_start": node.lineno,
                "line_end": getattr(node, "end_lineno", node.lineno),
                "type": type(node).__name__,
            })

    return {
        "imports": imports,
        "top_level": top_level,
        "total_lines": len(source.splitlines()),
    }


def get_snippet(source: str, start: int, end: int) -> str:
    """按行号取一段源码（1-based，包含 start 和 end）。

    用于模型按结构树取片段，避免读整份代码。
    """
    lines = source.splitlines()
    # 容错：越界就夹紧
    start = max(1, start)
    end = min(len(lines), end)
    if start > end:
        return ""
    return "\n".join(lines[start - 1:end])


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