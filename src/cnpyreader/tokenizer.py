"""核心：用 tokenize 解析 Python 源码，按词典替换名字，再拼回源码。"""

import tokenize
from io import BytesIO

from .dictionaries import KEYWORDS, BUILTINS, IDENTIFIER_WORDS


def _split_identifier(name: str) -> list:
    """把蛇形或驼峰标识符拆成词列表。

    append_to_message -> ["append", "to", "message"]
    appendToMessage   -> ["append", "To", "Message"]
    """
    words = []
    for part in name.split("_"):
        if not part:
            continue
        # 处理驼峰
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
    """翻译标识符：拆词后逐词查表，查不到的词保留原文。"""
    words = _split_identifier(name)
    if not words:
        return name
    translated = []
    for w in words:
        lower = w.lower()
        if lower in IDENTIFIER_WORDS:
            translated.append(IDENTIFIER_WORDS[lower])
        elif w in IDENTIFIER_WORDS:
            translated.append(IDENTIFIER_WORDS[w])
        else:
            translated.append(w)
    return "".join(translated)


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