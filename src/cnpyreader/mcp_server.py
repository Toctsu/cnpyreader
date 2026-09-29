"""MCP server：把 cnpyreader 的三个工具暴露给模型。

使用方式（在模型的 MCP 配置里）：
    {
      "mcpServers": {
        "cnpyreader": {
          "command": "cnpyreader-mcp"
        }
      }
    }
"""

from mcp.server.mcpserver import MCPServer

from .tools import translate_code, get_structure, translate_symbol, get_snippet

mcp = MCPServer("cnpyreader")


@mcp.tool()
def translate_code_tool(source: str, direction: str = "to_chinese") -> str:
    """把 Python 源码在中英文之间翻译。

    direction:
      - "to_chinese"：英文 -> 中文，帮助中文用户阅读
      - "to_english"：中文 -> 英文，翻回后可以正常运行

    翻译是可逆的。中文代码虽然不能直接跑，但用 to_english 翻回去
    就是可运行的 Python。
    """
    return translate_code(source, direction)


@mcp.tool()
def get_structure_tool(source: str) -> dict:
    """解析 Python 源码，返回类、函数、导入的结构树 JSON。"""
    return get_structure(source)


@mcp.tool()
def get_snippet_tool(source: str, start: int, end: int) -> str:
    """按行号取一段源码（1-based，包含 start 和 end）。

    典型用法：先调 get_structure_tool 拿到结构树，
    再对关心的节点调本工具，只取那几行，避免读整份代码。
    """
    return get_snippet(source, start, end)


def main():
    mcp.run()


if __name__ == "__main__":
    main()