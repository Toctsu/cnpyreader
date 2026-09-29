# cnpyreader

将Python 源码翻译为中文代码，帮助中文用户阅读代码。

## 特性

- 纯规则实现，无需大模型
- 基于 Python 标准库 `tokenize`，不会误伤字符串和注释
- 本地运行，零成本，结果确定
- 未命中的标识符原样保留，可逐步扩充词典

## 安装

```bash
pip install -e .