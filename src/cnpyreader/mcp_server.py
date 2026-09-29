"""MCP server：把 cnpyreader 的工具暴露给模型。

使用方式（在模型的 MCP 配置里）：
    {
      "mcpServers": {
        "cnpyreader": {
          "command": "cnpyreader-mcp"
        }
      }
    }
"""

import logging
from pathlib import Path

from mcp.server.mcpserver import MCPServer

from .tools import (
    translate_code,
    get_structure,
    translate_symbol,
    get_snippet,
)

# ---- 日志：写到 ~/.cnpyreader/mcp.log，方便掉线时排查 ----
_log_dir = Path.home() / ".cnpyreader"
_log_dir.mkdir(exist_ok=True)
logging.basicConfig(
    filename=str(_log_dir / "mcp.log"),
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger("cnpyreader.mcp")
logger.info("MCP server 启动")

mcp = MCPServer("cnpyreader")


@mcp.tool()
def translate_code_tool(source: str, direction: str = "to_chinese") -> str:
    """把 Python 源码在中英文之间翻译。

    direction:
      - "to_chinese"：英文 -> 中文，帮助中文用户阅读
      - "to_english"：中文 -> 英文，翻回后可以正常运行

    翻译是可逆的。中文代码虽然不能直接跑，但用 to_english 翻回去
    就是可运行的 Python。

    注意：不要对整份大文件直接调本工具。先 get_structure_tool
    拿结构、get_snippet_tool 取片段，再翻片段。
    """
    logger.info(f"translate_code_tool: direction={direction}, "
                f"len(source)={len(source)}")
    return translate_code(source, direction)


@mcp.tool()
def get_structure_tool(source: str) -> dict:
    """解析 Python 源码，返回递归结构树。

    推荐工作流：大段代码不要直接丢给 translate_code_tool。
    先调本工具拿到结构树，再挑出关心的节点，
    用 get_snippet_tool 只取那几行，最后翻那几行。
    这样能显著减少 token 消耗。
    """
    logger.info(f"get_structure_tool: len(source)={len(source)}")
    return get_structure(source)


@mcp.tool()
def get_snippet_tool(source: str, start: int, end: int) -> str:
    """按行号取一段源码（1-based，包含 start 和 end）。

    典型用法：先调 get_structure_tool 拿到结构树，
    再对关心的节点调本工具，只取那几行，避免读整份代码。
    """
    logger.info(f"get_snippet_tool: start={start}, end={end}, "
                f"len(source)={len(source)}")
    return get_snippet(source, start, end)


@mcp.tool()
def translate_symbol_tool(name: str) -> str:
    """翻译单个标识符或关键字，返回中文名。未命中则原样返回。

    适合模型只想知道某个变量名/函数名是什么意思，
    不需要读整段代码的场景。
    """
    logger.info(f"translate_symbol_tool: name={name}")
    return translate_symbol(name)


def main():
    mcp.run()


if __name__ == "__main__":
    main()