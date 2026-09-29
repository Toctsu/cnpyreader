"""命令行入口：cnpyreader <文件.py>"""

import argparse
import sys
from pathlib import Path

from .tokenizer import translate_source, translate_back


def main():
    parser = argparse.ArgumentParser(
        prog="cnpyreader",
        description="将 Python 源码翻译为中文代码，或把中文代码翻回英文。",
    )
    parser.add_argument("file", help="要翻译的 Python 文件")
    parser.add_argument(
        "-o", "--output", help="输出文件（默认打印到终端）"
    )
    parser.add_argument(
        "--back", action="store_true",
        help="把中文代码翻译回英文（反向）"
    )
    args = parser.parse_args()

    path = Path(args.file)
    if not path.exists():
        print(f"文件不存在: {path}", file=sys.stderr)
        sys.exit(1)

    source = path.read_text(encoding="utf-8-sig")

    if args.back:
        translated = translate_back(source)
    else:
        translated = translate_source(source)

    if args.output:
        Path(args.output).write_text(translated, encoding="utf-8")
        print(f"已写入 {args.output}")
    else:
        print(translated)


if __name__ == "__main__":
    main()