"""核心：用 tokenize 解析 Python 源码，按词典替换名字，再拼回源码。"""

import tokenize
from io import BytesIO

from .dictionaries import KEYWORDS, BUILTINS, IDENTIFIER_WORDS


def _split_camel(part: str):
    """把驼峰词拆成小段。getLogger -> ["get", "Logger"]。

    规则：
    - 全大写（如 ERROR、HTTP）不拆，整词保留
    - 全小写（如 logger）不拆
    - 混合（如 getLogger）按大写边界拆
    """
    if not part:
        return []
    # 全大写或全小写：不拆
    if part.isupper() or part.islower():
        return [part]

    words = []
    buf = ""
    for ch in part:
        if ch.isupper() and buf:
            words.append(buf)
            buf = ch
        else:
            buf += ch
    if buf:
        words.append(buf)
    return words


def _translate_identifier(name: str) -> str:
    """翻译标识符：按 '_' 和驼峰拆词，逐词查表，未命中的词原样保留。

    策略：部分命中时，命中的翻、未命中的留英文，用 '_' 拼回。
    这样 get_user_unknown -> 获取_用户_unknown，比整个保留更有信息量。
    """
    # 先按 '_' 拆
    parts = [p for p in name.split("_") if p]

    # 每个部分再按驼峰拆
    all_words = []
    for p in parts:
        all_words.extend(_split_camel(p))

    translated = []
    for w in all_words:
        low = w.lower()
        if w in IDENTIFIER_WORDS:
            translated.append(IDENTIFIER_WORDS[w])
        elif low in IDENTIFIER_WORDS:
            translated.append(IDENTIFIER_WORDS[low])
        else:
            translated.append(w)   # 未命中的词原样保留
    return "_".join(translated)


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