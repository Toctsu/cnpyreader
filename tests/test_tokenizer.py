"""测试 tokenizer 的核心翻译行为。"""

from cnpyreader.tokenizer import translate_source


def test_keyword_def_translated():
    src = "def foo():\n    pass\n"
    out = translate_source(src)
    assert "定义" in out
    assert "通过" in out
    assert "def" not in out


def test_builtin_print_translated():
    src = 'print("hi")\n'
    out = translate_source(src)
    assert "打印" in out
    assert "print" not in out


def test_string_literal_not_translated():
    """字符串里的内容绝对不能动——这是 tokenize 方案的核心优势。"""
    src = 'print("print def class")\n'
    out = translate_source(src)
    # 外层的 print 被翻译，但字符串内部的 print / def / class 原样保留
    assert '打印("print def class")' in out


def test_unknown_identifier_kept():
    """词典里没有的标识符原样保留，不强行翻译。"""
    src = "foo_bar = 1\n"
    out = translate_source(src)
    assert "foo_bar" in out

def test_full_roundtrip():
    """英文源码 -> 中文代码 -> 英文源码，关键部分应完整还原。"""
    from cnpyreader.tokenizer import translate_source, translate_back

    src = (
        "def hello(name):\n"
        "    if name:\n"
        "        print(\"Hello, \" + name)\n"
        "    else:\n"
        "        print(\"Hello, world\")\n"
    )
    cn = translate_source(src)
    back = translate_back(cn)

    assert "def hello(name):" in back
    assert "if name:" in back
    assert "print(" in back
    assert "else:" in back