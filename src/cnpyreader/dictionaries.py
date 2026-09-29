"""三层词典：关键字、内置名、标识符词表。

正向：英文 -> 中文（用于阅读）
反向：中文 -> 英文（用于把中文代码翻回可运行的 Python）

反向映射要求中文名唯一，所以词典里不允许出现两个英文词
映射到同一个中文词。dictionaries 末尾的 _invert 会在冲突时直接报错。
"""

# ============ 第一层：Python 关键字 ============
KEYWORDS = {
    "False": "假",
    "None": "空",
    "True": "真",
    "and": "并且",
    "as": "作为",
    "assert": "断言",
    "async": "异步",
    "await": "等待",
    "break": "跳出",
    "class": "类",
    "continue": "继续",
    "def": "定义",
    "del": "删除",
    "elif": "否则如果",
    "else": "否则",
    "except": "异常",
    "finally": "最后",
    "for": "对于",
    "from": "从",
    "global": "全局",
    "if": "如果",
    "import": "导入",
    "in": "在",
    "is": "是",
    "lambda": "匿名函数",
    "nonlocal": "非局部",
    "not": "非",
    "or": "或者",
    "pass": "通过",
    "raise": "抛出",
    "return": "返回",
    "try": "尝试",
    "while": "当",
    "with": "使用",
    "yield": "产出",
}

# ============ 第二层：常用内置名 ============
BUILTINS = {
    "print": "打印",
    "len": "长度",
    "range": "范围",
    "str": "字符串",
    "int": "整数",
    "float": "浮点数",
    "list": "列表",
    "dict": "字典",
    "set": "集合",
    "tuple": "元组",
    "bool": "布尔",
    "self": "自身",
    "append": "追加",
    "extend": "扩展",
    "insert": "插入",
    "remove": "移除",
    "pop": "弹出",
    "get": "获取",
    "keys": "键列表",
    "values": "值列表",
    "items": "项列表",
    "open": "打开",
    "input": "输入",
    "type": "类型",
    "isinstance": "是实例",
    "super": "父类",
    "enumerate": "枚举",
    "zip": "拉链",
    "map": "映射",
    "filter": "过滤",
    "sorted": "排序",
    "sum": "求和",
    "min": "最小",
    "max": "最大",
    "abs": "绝对值",
    "round": "四舍五入",
}

# ============ 第三层：标识符拆词词表 ============
# 注意：中文名必须唯一。缩写和全称要用不同的中文名，
# 比如 message / msg 不能都叫"消息"。
IDENTIFIER_WORDS = {
    # 动词
    "get": "获取",
    "set": "设置",
    "add": "添加",
    "remove": "移除",
    "delete": "删除",
    "update": "更新",
    "create": "创建",
    "load": "加载",
    "save": "保存",
    "read": "读取",
    "write": "写入",
    "open": "打开",
    "close": "关闭",
    "start": "开始",
    "stop": "停止",
    "run": "运行",
    "init": "初始化",
    "main": "主",
    "build": "构建",
    "parse": "解析",
    "render": "渲染",
    "check": "检查",
    "find": "查找",
    "search": "搜索",
    "send": "发送",
    "receive": "接收",
    "push": "推送",
    "pull": "拉取",

    # 名词：消息类
    "message": "消息全称",
    "msg": "消息",
    "information": "信息全称",
    "info": "信息",
    "error": "错误全称",
    "err": "错误",
    "warning": "警告",
    "debug": "调试",
    "notice": "通知",
    "alert": "警报",

    # 名词：配置类
    "config": "配置全称",
    "cfg": "配置",
    "settings": "设置",
    "option": "选项",
    "optionals": "可选项",
    "default": "默认",
    "current": "当前",
    "new": "新",
    "old": "旧",

    # 名词：人 / 对象
    "user": "用户",
    "name": "名字",
    "title": "标题",
    "author": "作者",
    "owner": "所有者",
    "self": "自身",
    "this": "这个",
    "that": "那个",

    # 名词：文件 / 路径
    "path": "路径",
    "file": "文件",
    "dir": "目录",
    "folder": "文件夹",
    "filename": "文件名",
    "dirname": "目录名",

    # 名词：数据
    "text": "文本",
    "content": "内容",
    "data": "数据",
    "result": "结果",
    "value": "值",
    "key": "键",
    "item": "项",
    "list": "列表",
    "dict": "字典",
    "count": "数量",
    "index": "索引",
    "length": "长度",
    "size": "大小",
    "width": "宽",
    "height": "高",
    "color": "颜色",
    "theme": "主题",
    "font": "字体",

    # 介词 / 连词 / 助词
    "to": "到",
    "from": "从",
    "in": "在",
    "out": "出",
    "on": "开",
    "off": "关",
    "is": "是",
    "has": "有",
    "can": "可以",
    "should": "应该",
    "all": "全部",
    "any": "任意",
    "none": "无",
    "empty": "空",
    "valid": "有效",
    "invalid": "无效",
    "true": "真",
    "false": "假",
    "success": "成功",
    "fail": "失败",
    "failed": "已失败",
    "finish": "完成",
    "finished": "已完成",
    "begin": "开始",
    "end": "结束",
    "next": "下一个",
    "prev": "上一个",
    "first": "第一个",
    "last": "最后一个",
}


# ============ 反向词典（中文 -> 英文）============
# 正向允许多对一（message 和 msg 都叫"消息"），
# 反向只保留"全称"作为还原目标，缩写不参与反向。
# 所以反向词典的构造方式是：取每个中文名第一次出现（也就是
# 词典书写顺序里靠前的那个英文词）作为它的英文还原目标。
# 使用者在写词典时，应把全称写在缩写前面，例如先写 message 再写 msg。

def _invert(d):
    """把 {英文: 中文} 翻成 {中文: 英文}。

    允许多对一：多个英文词可以映射到同一个中文词。
    反向时取"第一次出现"的英文词作为还原目标，
    所以词典里应把全称写在缩写前面。
    """
    result = {}
    for en, cn in d.items():
        if cn not in result:
            result[cn] = en
        # 已经有映射了，跳过（缩写不覆盖全称）
    return result


REVERSE_KEYWORDS = _invert(KEYWORDS)
REVERSE_BUILTINS = _invert(BUILTINS)
REVERSE_IDENTIFIER_WORDS = _invert(IDENTIFIER_WORDS)