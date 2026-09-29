# 用 MCP 让模型调用 cnpyreader

cnpyreader 把自己包装成一个 **MCP server**，任何支持 MCP 的模型客户端（Cherry Studio、Claude Desktop、Cursor 等）都能挂载它。挂上后，模型遇到看不懂的 Python 代码，会主动调这个工具，**按需翻译片段，而不是把整份代码塞进上下文**。

## 暴露了哪些工具

| 工具名 | 作用 | 输入 | 输出 |
|---|---|---|---|
| `get_structure_tool` | 解析源码，返回递归结构树 | `source`（源码字符串） | 结构树 JSON |
| `get_snippet_tool` | 按行号取一段源码 | `source`, `start`, `end` | 片段字符串 |
| `translate_code_tool` | 把源码翻成中文或翻回英文 | `source`, `direction` | 翻译后的源码 |
| `translate_symbol_tool` | 翻译单个标识符 | `name` | 中文名 |

## 推荐工作流

**不要**直接把整份代码丢给 `translate_code_tool`。正确做法是分三步：

1. **`get_structure_tool(source)`** → 拿到结构树，看清有哪些类、函数、控制流，以及它们在第几行
2. **`get_snippet_tool(source, start, end)`** → 只取你关心的那几行
3. **`translate_code_tool(片段)`** → 只翻那一小段

这么做的好处：**模型读的 token 大幅减少**。一份 600 行的文件，模型只需要读它关心的 20 行，而不是整份。

## 结构树返回什么

`get_structure_tool` 返回类似：

```json
{
  "imports": [
    {"module": "os", "line": 1}
  ],
  "top_level": [
    {
      "name": "Greeter",
      "type": "ClassDef",
      "line_start": 1,
      "line_end": 6,
      "children": [
        {
          "name": "hello",
          "type": "FunctionDef",
          "line_start": 2,
          "line_end": 6,
          "args": ["self", "name"],
          "is_async": false,
          "children": [
            {"name": null, "type": "If", "line_start": 3, "line_end": 6}
          ]
        }
      ]
    }
  ],
  "total_lines": 6
}
```
## 已知问题

某些 MCP 客户端（如 Cherry Studio）在长时间会话或重启后，
可能出现“显示已连接但工具不可调用”的状态不同步问题。

特征：客户端 UI 显示 `cnpyreader` 已连接，但模型调用任何工具
都返回 `unknown tool`。此时检查 `~/.cnpyreader/mcp.log`，
如果只有 `MCP server 启动`、没有任何工具调用记录，说明
客户端根本没连上，问题在客户端侧。

遇到时：**完全退出并重启客户端**（不只是关窗口）。
这不是 cnpyreader 的 bug。