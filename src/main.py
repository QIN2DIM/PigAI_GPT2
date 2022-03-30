from gevent import monkey

monkey.patch_all()

import os
import re
import csv
import time
from datetime import datetime

import gevent
from gevent.queue import Queue
from yaml.parser import ParserError
from concurrent.futures import ThreadPoolExecutor
from selenium.webdriver import Chrome, ChromeOptions
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import (
    WebDriverException,
    NoSuchElementException,
    NoAlertPresentException,
    TimeoutException,
    UnknownMethodException,
    SessionNotCreatedException,
)
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from config import *


class ActionTraceSpider:
    """Selenium action module"""

    def __init__(self):

        # target
        self.url = "http://www.pigai.org/"

        # 浏览器无/有头启动
        self.silence: bool = False

        # 模型定义信息
        self.username, self.password, self.pid, self.text, self.class_name = [""] * 5

        # 批改网用户信息
        self.score, self.title, self.stu_num, self.stu_name = [""] * 4

        # eid
        self.end_html = ""

    def load_params(self, username, password, pid, text, class_name=""):
        self.username = username
        self.password = password
        self.pid = pid
        self.text = text
        self.class_name = class_name

    @staticmethod
    def wait(api: Chrome, timeout: float, tag_xpath_str):
        if tag_xpath_str == "all":
            time.sleep(1)
            WebDriverWait(api, timeout).until(EC.presence_of_all_elements_located)
        else:
            WebDriverWait(api, timeout).until(
                EC.presence_of_element_located((By.XPATH, tag_xpath_str))
            )

    def set_options(self):
        """浏览器初始化"""
        options = ChromeOptions()

        options.add_argument("--no-sandbox")
        options.add_argument("--incognito")
        options.add_argument("--disk-cache")
        options.add_argument("--lang=zh")
        options.add_argument("--no-proxy-server")
        if self.silence is True or "linux" in sys.platform:
            options.add_argument("--headless")

        service = Service(ChromeDriverManager(log_level=0).install())
        return Chrome(options=options, service=service)  # noqa

    @staticmethod
    def save_cookies(api: Chrome):
        pending = False
        try:
            cookies = api.get_cookies()
            import json

            with open("database/cookies.txt", "w", encoding="utf-8") as f:
                f.write(json.dumps(cookies))
            pending = True
        finally:
            logger.debug(
                ">>> Task over: save cookies "
                if pending
                else ">>> Task failed: save cookie"
            )

    def login(self, api: Chrome, url, username, password):
        try:
            api.get(url)
        except WebDriverException:
            logger.warning(">>> [ERROR] 任务强制结束 || function login :api.get(url) panic")
            return None

        self.wait(api, 5, "all")
        api.find_element(By.ID, "username").send_keys(username)
        api.find_element(By.ID, "lg_header").click()
        api.find_element(By.ID, "password").send_keys(password)
        api.find_element(By.ID, "ulogin").click()

        logger.debug("登录成功")

    def switch_workspace(self, api: Chrome, work_id: str):

        self.wait(api, 5, "all")
        api.find_element(By.NAME, "rid").click()
        api.find_element(By.NAME, "rid").send_keys(work_id)
        api.find_element(By.CLASS_NAME, "sf_right").click()

        logger.debug(f"切换至写作页面 pid={work_id}")

    def input_content(self, api: Chrome, text: str):
        self.wait(api, 5, "all")

        data_frame = api.find_element(By.ID, "contents")
        data_frame.clear()

        logger.debug("正在写作...")
        for ch in text.split(" "):
            data_frame.send_keys("{} ".format(ch))

    def show_workspace_info(self, api: Chrome):
        try:
            self.title = api.find_element(By.XPATH, "//input[@id='title']").get_attribute(
                "value"
            )
            info = api.find_element(
                By.XPATH, "//div[@style]//div[contains(@style,'float:')]"
            ).text
            self.stu_num = [
                i.split(":")[-1] for i in re.split("[，。]", info) if "学号" in i
            ][0]
            self.stu_name = api.find_element(By.ID, "pigai_name").text
        except NoSuchElementException:
            logger.error(">>> [ERROR] No paper number || Get student info failed.")

    def submit(self, api: Chrome):
        api.find_element(By.ID, "dafen").click()
        self.smash_the_popup(api, smash_type="alert")

        logger.debug("提交文章")

    def select_student_class(self, api: Chrome, class_name: str or bool):

        if class_name:
            try:
                api.find_element(By.XPATH, "//select[@id='stu_class']").click()
                time.sleep(1)
                api.find_element(By.XPATH, f"//option[@value='{class_name}']").click()
                time.sleep(1)
                api.find_element(By.ID, "icibaWinBotton").find_element(
                    By.TAG_NAME, "input"
                ).click()
                logger.debug(">>> 选择班级 class={}".format(class_name))
            except NoSuchElementException:
                logger.warning(f">>> 当前作文不支持班级选择或本班级未布置该篇写作训练.(pid:{self.pid})")

    @staticmethod
    def smash_the_popup(api: Chrome, smash_type: str):
        if smash_type == "alert":
            try:
                alert = api.switch_to.alert
                logger.warning(">>> {}".format(alert.text))
                alert.accept()
            except NoAlertPresentException:
                pass

    def get_paper_score(self, api: Chrome):
        try:
            api.maximize_window()
            self.wait(api, 10, "//div[@id='scoreCricle']")
            time.sleep(3)
            self.score = api.find_element(By.XPATH, "//div[@id='scoreCricle']").text
            self.end_html = api.current_url
        except TimeoutException:
            logger.warning("作文提交失败|| 可能原因为：重复提交")
            return None

    def save_action_history(self, api: Chrome):
        capture_pending = False
        add_pending = False

        # 当前时间
        now_ = str(datetime.now()).split(".")[0]
        # 范式一：数据漏采--token替换
        score = self.score if self.score else "none"
        stu_name = self.stu_name if self.stu_name else "none"
        stu_num = self.stu_num if self.stu_num else "none"
        # 范式二：捕获评分页面--输出地址
        end_html = "《{}》_{}_{}.mhtml".format(
            self.title, self.end_html.split("=")[-1], now_.replace(":", "-")
        )
        filename_mhtml = os.path.join(DIR_PAPER_SCORE, end_html)
        try:
            if not os.path.exists(PATH_ACTION_MEMORY):
                with open(PATH_ACTION_MEMORY, "w", encoding="utf-8", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow(
                        [
                            "publish_time",
                            "stu_name",
                            "stu_num",
                            "pid",
                            "title",
                            "score",
                            "end_html",
                        ]
                    )
                    logger.debug(">>> Task over: create action_history.")
        except FileNotFoundError as ef:
            logger.exception(ef)
            return None

        try:
            res = api.execute_cdp_cmd("Page.captureSnapshot", {})

            with open(filename_mhtml, "w", newline="") as f:
                html = res.get("data")
                if html:
                    f.write(html)
                    capture_pending = True
                else:
                    # error_msg = ' The  MTH message is empty: {}'.format(self.pid)
                    pass
        finally:
            task_name = ">>> Task {}: capture end_rid paper score."
            logger.debug(
                task_name.format("over")
                if capture_pending
                else task_name.format("failed")
            )

        try:
            with open(
                    PATH_ACTION_MEMORY, "a", encoding="utf8", newline="", errors="ignore"
            ) as f:
                writer = csv.writer(f)

                writer.writerow(
                    [now_, stu_name, stu_num, self.pid, self.title, score, filename_mhtml]
                )
            add_pending = True
        finally:
            task_name = ">>> Task {}: update actions history."
            logger.debug(
                task_name.format("over") if add_pending else task_name.format("failed")
            )

    def over(self, api):
        user = {"username": self.stu_name, "pid": self.title, "user_id": self.stu_num}
        if self.score:
            user.update({"score": self.score})
        else:
            user.update({"message": "作文异常"})

        self.save_cookies(api)
        self.save_action_history(api)

    def run(self):
        with self.set_options() as api:
            logger.debug("窗口最小化")
            api.minimize_window()

            try:

                self.login(api, self.url, self.username, self.password)

                self.switch_workspace(api, self.pid)

                self.show_workspace_info(api)

                self.input_content(api, self.text)

                self.select_student_class(api, self.class_name)

                self.submit(api)

                self.get_paper_score(api)

                self.over(api)

            except NoSuchElementException:
                logger.critical(">>> 提交异常")
            finally:
                api.quit()
                logger.success(">>> 工作栈已释放完毕")


class PigAI:
    """NLP module"""

    def __init__(self, use_gpt2: bool = False):
        self.use_gpt2 = use_gpt2

    def __str__(self):
        logger.info(self.youdao_cn2en("您好，欢迎使用PigAI！"))

    @staticmethod
    def load_model(path: str = None):
        pass

    def generate_text(self) -> str:
        """

        :return:
        """
        if self.use_gpt2:
            return "Use_AI_Model"
        else:
            return "Use_Default_Model"

    @staticmethod
    def youdao_cn2en(cn_word: str) -> str or None:
        """
        备选方案，逆向有道翻译接口实现文本翻译
        :param cn_word:
        :return:
        """
        import requests
        import hashlib
        import time
        import random
        import json

        # JavaScript Reverse
        timestamp = time.time() * 1000
        salt = "{}{}".format(timestamp, random.randint(1, 10))
        temp = "fanyideskweb" + cn_word + salt + "]BjuETDhU)zqSxf-=B#7m"
        sign = hashlib.md5(temp.encode("utf-8")).hexdigest()

        # Post target
        url = "http://fanyi.youdao.com/translate?smartresult=dict&smartresult=rule"

        # Form data
        data = {
            "i": cn_word,
            "from": "AUTO",
            "to": "AUTO",
            "smartresult": "dict",
            "client": "fanyideskweb",
            "salt": salt,
            "sign": sign,
            "lts": timestamp,
            "bv": "23a17424f135105a1b57871cc3d87452",
            "doctype": "json",
            "version": "2.1",
            "keyfrom": "fanyi.web",
            "action": "FY_BY_REALTlME",
        }

        # Requests headers
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36 Edg/86.0.622.51",
            "Referer": "http://fanyi.youdao.com/",
            "Host": "fanyi.youdao.com",
            "Origin": "http://fanyi.youdao.com",
        }

        # {'PigAI_GPT2_src': '蜘蛛', 'tgt': 'The spider'}
        response = requests.post(url, headers=headers, data=data)
        try:
            len(response.json())
            return response.json()["translateResult"][0][0]
        except json.JSONDecodeError:
            return None


class Middleware:
    """
    >> System middleware
    1. Manage the multithreading and the multi-coroutine tasks list of the user group
    2. Manage the spider cluster module and the text generation module
    """

    def __init__(self):
        self.account_q = Queue()
        self.work_q = Queue()
        self.account_num: int = 0

    @staticmethod
    def load_sample_text(deep_learning=False) -> str:
        if deep_learning:
            pass
        else:
            from database.fake_corpus.load_fake_data import generate_fake_text

            return generate_fake_text()["text"]

    @staticmethod
    def load_workspace(username, password, workspace: ActionTraceSpider, **kwargs):

        text = kwargs.get("text")

        workspace.load_params(
            username=username,
            password=password,
            pid=kwargs.get("pid"),
            text=text if text else Middleware.load_sample_text(),
            class_name=kwargs.get("class_name"),
        )
        return workspace

    def load_model(self, engine: PigAI, **kwargs):
        """

        :param engine: 将NLP生成模型导入
        :param kwargs: 额外参数，控制生成模式：
        :return:
        """
        pass

    def load_user_config(self, config_path=PATH_CONFIG):
        with open(config_path, "r", encoding="utf-8") as f:
            try:
                data = yaml.load(f, Loader=yaml.FullLoader)
            except ParserError:
                logger.error(">>> [ERROR] config.yaml 配置信息设置出现致命错误！")
                return None
            except FileNotFoundError:
                logger.error(">>> [ERROR] config.yaml 未找到yaml配置文件，请将配置文件放在当前目录下!")

        for i, user in enumerate(data["users"]):
            user: dict
            username = (
                user["user"].get("username")
                if isinstance(user["user"].get("username"), str)
                else None
            )
            password = (
                user["user"].get("password")
                if isinstance(user["user"].get("password"), str)
                else None
            )
            class_name = user["user"].get("class_name")
            pids = user["user"].get("pids")
            try:
                pids = (
                    pids
                    if isinstance(pids, list) and pids[0] and isinstance(pids[0], str)
                    else None
                )
            except IndexError:
                logger.warning(
                    f">>> [ERROR] username:{username} || 作文号填写异常 || pids: ({pids}) <<"
                )

            if not class_name:
                logger.warning(">>> 班级信息为空")

            check = (
                True
                if len([i for i in [username, password, pids] if not i]) < 1
                else False
            )
            if check:
                self.account_q.put_nowait(user)
                self.account_num = self.account_q.qsize()
            else:
                logger.error(f">>> username:{username} || 配置信息输入格式有误  <<")

    def coroutine_engine(self):
        while not self.work_q.empty():
            data = self.work_q.get_nowait()
            logger.success("实例启动成功")
            try:
                self.load_workspace(
                    data["username"],
                    data["password"],
                    ActionTraceSpider(),
                    class_name=data["class_name"],
                    pid=data["pids"],
                ).run()
            except SessionNotCreatedException or WebDriverException:
                logger.info(">>> Coroutine_ID: {} || 任务强制结束 ".format(data["username"]))

    def coroutine_speed_up(self, account_info: dict):
        task_list = []
        pids = account_info.get("user").get("pids")

        if len(pids) > 1:
            for pid in pids:
                account_info.get("user").update({"pids": pid})
                self.work_q.put_nowait(account_info["user"])
        else:
            account_info.get("user").update({"pids": pids[0]})
            self.work_q.put_nowait(account_info["user"])

        for x in range(self.work_q.qsize()):
            task = gevent.spawn(self.coroutine_engine)
            task_list.append(task)
        gevent.joinall(task_list)

    def do_middleware_engine(self):
        if self.account_num > 1:
            with ThreadPoolExecutor(max_workers=self.account_num) as t:
                for x in range(self.account_num):
                    t.submit(self.coroutine_speed_up, self.account_q.get_nowait())
        elif 0 <= self.account_num <= 1:
            if not self.account_q.empty():
                self.coroutine_speed_up(self.account_q.get_nowait())
        else:
            return False

    @logger.catch()
    def run(self, use_model=False):
        try:
            if use_model:
                raise UnknownMethodException
            self.load_user_config()
            self.do_middleware_engine()
        except UnknownMethodException:
            logger.warning(">>> 任务强制结束，未载入文本生成模型！")
        except WebDriverException or SessionNotCreatedException:
            logger.warning(">>> 任务强制结束")


if __name__ == "__main__":
    Middleware().run(use_model=False)
