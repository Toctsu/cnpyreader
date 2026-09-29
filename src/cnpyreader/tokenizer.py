"""核心：用 tokenize 解析 Python 源码，按词典替换名字，再拼回源码。"""

import tokenize
from io import BytesIO

from .dictionaries import KEYWORDS, BUILTINS, IDENTIFIER_WORDS


def _translate_identifier(name: str) -> str:
    """翻译标识符：拆词后逐词查表，查不到的词保留原文。

    策略（保守）：
    - 如果标识符里有下划线：拆成词，只有全部词都命中词典时才翻译，
      并用下划线拼回；任何一个词没命中，整个标识符原样保留。
    - 如果没有下划线：整个名字小写后查表，命中就翻译，否则原样保留。

    这样不会出现 foo_bar -> foobar 这种吞掉下划线的破坏。
    """
    if "_" in name:
        parts = [p for p in name.split("_") if p]
        translated = []
        for p in parts:
            low = p.lower()
            if low in IDENTIFIER_WORDS:
                translated.append(IDENTIFIER_WORDS[low])
            else:
                # 有一个词没命中，整个保留，不翻译
                return name
        return "_".join(translated)

    # 没有下划线：整个名字查表
    low = name.lower()
    if low in IDENTIFIER_WORDS:
        return IDENTIFIER_WORDS[low]
    return name


def _translate_name(name: str) -> str:
    """按 关键字 -> 内置 -> 标识符 的顺序翻译一个名字。"""
    if name in KEYWORDS:
        return KEYWORDS[name]
    if name in BUILTINS:
        return BUILTINS[name]
    return _translate_identifier(name)


def translate_source(source: str) -> str:
    """把一段 Python 源码翻译为中文代码。"""
    tokens = []
    for tok in tokenize.tokenize(BytesIO(source.encode("utf-8")).readline):
        if tok.type == tokenize.NAME:
            new_name = _translate_name(tok.string)
            if new_name != tok.string:
                tok = tokenize.TokenInfo(
                    tok.type, new_name, tok.start, tok.end, tok.line
                )
        tokens.append(tok)
    return tokenize.untokenize(tokens).decode("utf-8")


def _translate_back_name(name: str) -> str:
    """把一个名字从中文翻回英文。

    顺序：关键字 -> 内置 -> 标识符词表。
    标识符层按 '_' 拆词逐段翻，未命中的段原样保留。
    """
    from .dictionaries import (
        REVERSE_KEYWORDS, REVERSE_BUILTINS, REVERSE_IDENTIFIER_WORDS,
    )

    if name in REVERSE_KEYWORDS:
        return REVERSE_KEYWORDS[name]
    if name in REVERSE_BUILTINS:
        return REVERSE_BUILTINS[name]

    if "_" in name:
        parts = [p for p in name.split("_") if p]
        out = []
        for p in parts:
            if p in REVERSE_IDENTIFIER_WORDS:
                out.append(REVERSE_IDENTIFIER_WORDS[p])
            else:
                out.append(p)
        return "_".join(out)

    if name in REVERSE_IDENTIFIER_WORDS:
        return REVERSE_IDENTIFIER_WORDS[name]
    return name


def translate_back(source: str) -> str:
    """把中文代码翻译回 Python 英文源码。"""
    tokens = []
    for tok in tokenize.tokenize(BytesIO(source.encode("utf-8")).readline):
        if tok.type == tokenize.NAME:
            new_name = _translate_back_name(tok.string)
            if new_name != tok.string:
                tok = tokenize.TokenInfo(
                    tok.type, new_name, tok.start, tok.end, tok.line
                )
        tokens.append(tok)
    return tokenize.untokenize(tokens).decode("utf-8")