# cnpyreader

将 Python 源码翻译为中文代码，帮助中文用户阅读代码。

## 特性

- 纯规则实现，无需大模型
- 基于 Python 标准库 tokenize，不会误伤字符串和注释
- 本地运行，零成本，结果确定
- 未命中的标识符原样保留，可逐步扩充词典
- 支持反向翻译：中文代码可以翻回可运行的英文 Python
- 词典外置为 TOML，用户不改源码就能加词

## 安装

pip install -e .

需要 Python 3.9 及以上。Python 3.10 及以下会自动安装 tomli 作为 TOML 解析器。

## 用法

# 英文 -> 中文
cnpyreader examples/hello.py

# 中文 -> 英文（反向）
cnpyreader my_cn.py --back

# 结果写到文件
cnpyreader examples/hello.py -o out_cn.py

## 示例

输入：

def hello(name):
    if name:
        print("Hello, " + name)
    else:
        print("Hello, world")

输出：

定义 hello(name):
    如果 name:
        打印("Hello, " + name)
    否则:
        打印("Hello, world")

## 自定义词典

用户可以在 ~/.cnpyreader/dictionaries/ 下放自己的 TOML 词表，程序启动时会自动加载，同名键会覆盖内置词表。

示例 ~/.cnpyreader/dictionaries/my.toml：

[identifiers]
hello = "问候"
my_custom_func = "我的函数"

三个可用的表：

- [keywords]：Python 关键字
- [builtins]：内置函数
- [identifiers]：标识符拆词词表

Windows 下用户目录是 C:\Users\<你的用户名>\.cnpyreader\dictionaries\。

## 词典约定

反向映射要求中文名唯一。如果想让两个英文词映射到同一个中文词（比如 message 和 msg 都叫“消息”），应把全称写在缩写前面，反向映射会取第一个出现的英文词作为还原目标。

## 贡献

欢迎提交词典条目和新的语言规则。词典位于 src/cnpyreader/dictionaries/*.toml。

## 许可证

MIT