import os
import sys

# ---------------------------------------------------
# Core system file path.Don't change.
# ::ROOT DATABASE
# ::Linux Google Chrome v85.0.4183.102
# ---------------------------------------------------
ROOT_DIR_PROJECT = os.path.dirname(__file__)
ROOT_DIR_DATABASE = os.path.join(ROOT_DIR_PROJECT, 'dataBase')
ROOT_DIR_MIDDLEWARE = os.path.join(ROOT_DIR_PROJECT, 'middleware')
ROOT_PATH_YAML_CONFIG = os.path.join(ROOT_DIR_DATABASE, 'config.yaml')
ROOT_PATH_SENTENCE_DEFAULT = os.path.join(ROOT_DIR_DATABASE, 'fake_sentence.csv')
ROOT_PATH_SENTENCE_GRT2 = os.path.join(ROOT_DIR_DATABASE, 'generation.csv')
ROOT_PATH_MODEL_GPT2 = os.path.join(ROOT_DIR_MIDDLEWARE, 'gpt2.model')
if 'win' in sys.platform:
    CHROMEDRIVER_PATH = os.path.join(ROOT_DIR_MIDDLEWARE, 'chromedriver.exe')
elif 'linux' in sys.platform:
    CHROMEDRIVER_PATH = os.path.join(ROOT_DIR_MIDDLEWARE, 'chromedriver')

# ---------------------------------------------------
# Engine params.Don't change.
# ::Linux Google Chrome v85.0.4183.102
# ---------------------------------------------------
SILENCE = True if 'linux' in sys.platform else False  # 静默启动：windows环境下默认为False
DEBUG = False  # True时需要手动关闭进程：默认为False
ANTI = True  # 目标网站是否包含高强度反爬虫系统：默认为True
