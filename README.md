## Introduction

批改网写作助手，根据配置自动生成并提交英语作文。

## Requirements

- google-chrome
- Python3.7+

## Usage

> 项目依赖 google-chrome 运行，请确保你的计算机已装有谷歌浏览器。

1. 配置启动参数

    直接运行 `main.py` 初始化项目，在 `/src/config.yaml` 中配置账号信息。

    - 必须填写用户名、密码与作文号，信息填写有误或残缺将无法正常启动项目；
    - `class_name` 为可选项，班级名不存在不影响作文提交，只是成绩不记录排行榜。

    ```yaml
    users:
      - user:
          # 登陆账号：邮箱或者手机号:字符串
          username: 'your username'
          # 账号密码：字符串
          password: 'your password'
          # 班级，请自行打开批改网，看看自己的班级全称
          class_name: your class name
          # 作文号，支持多篇作文并发，pids len ∈[1,∞) List[str]
          pids: [ '1586732' ]
    ```

2. 确保网络通畅，拉取项目第三方依赖

    ```shell
    # PigAI_GPT2/
    pip install -r requirements.txt
    ```

3. 运行项目

    进入到项目下的 `src/` 目录执行如下指令，或直接运行 `main.py `。

    ```bash
    # PigAI_GPT2/src
    python main.py
    ```

## Advanced

1. 操作历史

   首次运行后，可在工程目录下的 `database/action_history.csv` 中查看格式化的操作历史数据。

2. 评测快照

   首次运行后，程序会保存评测页面二点快照，可将页面中的所有富文本信息保存成 `.mhtml` 文件并存储在工程目录下的 `databse/paper_score/`。该格式文件可用主流的浏览器访问。

3. 文本长度

   在 `src/config.py` 文件中可修改变量 `TEXT_LENGTH` 的数值，其表示文章长度的左区间值，既文本生成后，文章长度会超过20 至 80 个词。`TEXT_LENGTH` 的默认值为 320。
