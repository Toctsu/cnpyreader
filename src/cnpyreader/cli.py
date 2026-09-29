"""命令行入口：cnpyreader <文件.py>"""

import argparse
import sys
from pathlib import Path

from .tokenizer import translate_source


def main():
    parser = argparse.ArgumentParser(
        prog="cnpyreader",
        description="将 Python 源码翻译为中文代码。",
    )
    parser.add_argument("file", help="要翻译的 Python 文件")
    parser.add_argument(
        "-o", "--output", help="输出文件（默认打印到终端）"
    )
    args = parser.parse_args()

    path = Path(args.file)
    if not path.exists():
        print(f"文件不存在: {path}", file=sys.stderr)
        sys.exit(1)

    source = path.read_text(encoding="utf-8")
    translated = translate_source(source)

    if args.output:
        Path(args.output).write_text(translated, encoding="utf-8")
        print(f"已写入 {args.output}")
    else:
        print(translated)


if __name__ == "__main__":
    main()