## Introduction

批改网写作助手，根据配置自动生成并提交英语作文。

## Requirements

- google-chrome
- Python3.7+

## Usage

> 项目依赖 google-chrome 运行，请确保你的计算机已装有谷歌浏览器。

1. 拉取 PyPi Package

   ```bash
   pip install pigai-gpt2
   ```

2. 跨越次元的相遇

   ```python
   from typing import Union, List
   
   from pigai import runner
   
   # [√] 账号信息
   username, password = "", ""
   # [√] 作文号
   pids: Union[str, List[str]] = ["2107818"]
   # [*] 班级名全称 错误或不存在不影响程序运行
   class_name: str = "春田花花幼稚园"
   # [*] 文本词汇量 实际生成量会略多于此值
   content_length: int = 200
   
   if __name__ == '__main__':
       runner(
           username=username,
           password=password,
           pids=pids,
           class_name=class_name,
           content_length=content_length,
           save_action_memory=True,
           check_result=True
       )
   
   ```

## Advanced

1. 操作历史

   首次运行后，可在工程目录下的 `database/action_history.csv` 中查看格式化的操作历史数据。

2. 评测快照

   首次运行后，程序会保存评测页面二点快照，可将页面中的所有富文本信息保存成 `.mhtml` 文件并存储在工程目录下的 `databse/paper_score/`。该格式文件可用主流的浏览器访问。

3. 文本长度

   在 `src/config.py` 文件中可修改变量 `TEXT_LENGTH` 的数值，其表示文章长度的左区间值，既文本生成后，文章长度会超过20 至 80 个词。`TEXT_LENGTH` 的默认值为 320。
