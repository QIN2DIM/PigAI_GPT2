# -*- coding: utf-8 -*-
# Time       : 2022/3/30 18:40
# Author     : QIN2DIM
# Github     : https://github.com/QIN2DIM
# Description:
import os
import random
import sys
from typing import Optional, Union, List, Dict

import requests
import yaml
from selenium.webdriver import Chrome, ChromeOptions
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


class ToolBox:
    @staticmethod
    def generate_fake_text(path_corpus: str, content_length: int = 320):
        if not os.path.exists(path_corpus):
            print("Downloading corpus...")
            url = "https://curly-shape-d178.qinse.workers.dev/https://github.com/QIN2DIM/PigAI_GPT2/releases/download/corpus/corpus.yaml"
            with requests.get(url, stream=True) as response, open(
                path_corpus, "wb"
            ) as file:
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        file.write(chunk)
        with open(path_corpus, "r", encoding="utf8") as file:
            dataset = yaml.load(file, Loader=yaml.Loader)
        corpus: Optional[List[str]] = dataset.get("corpus", [])
        if not corpus:
            return ""
        random.shuffle(corpus)

        content = ""
        while len(content.split(" ")) < content_length:
            content += corpus.pop()
        return content

    @staticmethod
    def transfer_cookies(
        api_cookies: Union[List[Dict[str, str]], str]
    ) -> Union[str, List[Dict[str, str]]]:
        """
        将 cookies 转换为可携带的 Request Header
        :param api_cookies: api.get_cookies() or cookie_body
        :return:
        """
        if isinstance(api_cookies, str):
            return [
                {"name": i.split("=")[0], "value": i.split("=")[1]}
                for i in api_cookies.split("; ")
            ]
        return "; ".join([f"{i['name']}={i['value']}" for i in api_cookies])


def get_ctx(silence: Optional = None):
    options = ChromeOptions()

    options.add_argument("--no-sandbox")
    options.add_argument("--incognito")
    options.add_argument("--disk-cache")
    options.add_argument("--lang=zh")
    options.add_argument("--no-proxy-server")

    if silence is True or "linux" in sys.platform:
        options.add_argument("--headless")

    service = Service(ChromeDriverManager(log_level=0).install())
    return Chrome(options=options, service=service)  # noqa
