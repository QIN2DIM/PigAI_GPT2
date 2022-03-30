import os
import sys

import yaml
from loguru import logger

"""
======================== ʕ•ﻌ•ʔ ========================
(·▽·)欢迎使用PigAI，请跟随提示合理配置项目启动参数
======================== ʕ•ﻌ•ʔ ========================
"""
# (√) 强制填写；(*)可选项
# ---------------------------------------------------
# TODO (√)TexLen -- 文本词数区间起点
# 合成的文章词数不会小于TexLen，一般情况下会超出20至80个词。
# 建议区间 TEXT_LENGTH∈[120, 460]
# ---------------------------------------------------
TEXT_LENGTH = 320

# ---------------------------------------------------
# TODO (√)CHROMEDRIVER_PATH -- ChromeDriver的路径
# 1.本项目内置的ChromeDriver可能与您的Chrome版本不适配。若您发现内置的ChromeDriver不能驱动项目，请根据下方提供的链接下载对应版本的文件
# 推荐`driver随chrome`，既根据现用的Chrome版本找对应的driver而不是对Chrome随意地升降版本(特别是linux环境)
# >> http://npm.taobao.org/mirrors/chromedriver/

# 2.本项目内置了Linux版本和Windows版本的ChromeDriver；显然您需要根据具体的部署环境下载相应的ChromeDriver
# 并将下载好的文件替换掉`./PigAI_GPT2_src/middleware/` 下的`chromedriver.exe`或`chromedriver`

# 3.本项目基于Windows10环境开发，Linux环境测试，可正常运行
# 若您的系统基于MacOS或其他，~可能~无法正常运行本项目
# ---------------------------------------------------

"""
========================== ʕ•ﻌ•ʔ ==========================
如果您并非<PigAI>项目开发者 请勿修改以下变量的默认参数
========================== ʕ•ﻌ•ʔ ==========================

                                  Enjoy it -> ♂main.py
"""
# ---------------------------------------------------
# 服务器工程目录,基于Windows10
# ---------------------------------------------------

# 工程根目录::Windows10写法
PROJECT_ROOT = os.path.dirname(__file__)

# 数据文件路径
PROJECT_DATABASE = os.path.join(PROJECT_ROOT, "database")

# 用户信息配置文件
PATH_CONFIG = os.path.join(PROJECT_ROOT, "config.yaml")

# 操作历史
PATH_ACTION_MEMORY = os.path.join(PROJECT_DATABASE, "action_history.csv")

# 提交结果持久化目录（用于存放.mhtml文件）
DIR_PAPER_SCORE = os.path.join(PROJECT_DATABASE, "paper_score")

# 替代方案: 语料集
DIR_FAKE_CORPUS = os.path.join(PROJECT_DATABASE, "fake_corpus")
PATH_FAKE_CORPUS = os.path.join(DIR_FAKE_CORPUS, "Beyond Good and Evil.txt")

# 日志路径
ROOT_DIR_LOGS = os.path.join(PROJECT_DATABASE, "logs")
logger.add(os.path.join(ROOT_DIR_LOGS, "runtime.log"), level="DEBUG", encoding="utf8")
logger.add(os.path.join(ROOT_DIR_LOGS, "error.log"), encoding="utf8")

# 路径补全
for _trace in [PROJECT_DATABASE, DIR_PAPER_SCORE, DIR_FAKE_CORPUS]:
    if not os.path.exists(_trace):
        os.mkdir(_trace)

_CONFIG_SAMPLE = {
    "users": [
        {
            "user": {
                "username": "8848520",
                "password": "8848520",
                "class_name": "春田花花幼稚园",
                "pids": ["2283917"],
            }
        }
    ]
}
if not os.path.exists(PATH_CONFIG):
    with open(PATH_CONFIG, "w", encoding="utf8") as file:
        yaml.dump(_CONFIG_SAMPLE, file, allow_unicode=True)
    print("配置初始化成功，请重启项目")
    sys.exit()
