import csv
import os
import re
import time
from datetime import datetime
from hashlib import sha256
from typing import Optional, Union, List

import requests
import yaml
from loguru import logger
from selenium.common.exceptions import (
    NoSuchElementException,
    NoAlertPresentException,
    TimeoutException,
    InvalidCookieDomainException,
)
from selenium.webdriver import Chrome
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from .exceptions import LoginTimeoutException, AuthException
from .utils import ToolBox, get_ctx

# ---------------------------------------------------
# 工程目录定位
# ---------------------------------------------------
PROJECT_ROOT = os.path.dirname(__file__)
PROJECT_DATABASE = os.path.join(PROJECT_ROOT, "database")
DIR_PAPER_SCORE = os.path.join(PROJECT_DATABASE, "paper_score")
DIR_COOKIES = os.path.join(PROJECT_DATABASE, "cookies")
PATH_CORPUS = os.path.join(PROJECT_ROOT, "corpus.yaml")
PATH_ACTION_MEMORY = os.path.join(PROJECT_DATABASE, "action_history.csv")
PATH_CTX_COOKIES = os.path.join(DIR_COOKIES, "ctx_cookies.yaml")

# ---------------------------------------------------
# 路径补全
# ---------------------------------------------------
for _trace in [PROJECT_DATABASE, DIR_PAPER_SCORE, DIR_COOKIES]:
    if not os.path.exists(_trace):
        os.mkdir(_trace)


class CookieManager:
    """管理上下文身份令牌"""

    URL_LOGIN = "http://www.pigai.org/"
    URL_ACCOUNT_PERSONAL = "http://www.pigai.org/index.php?a=modifyPassword&type=t11"

    def __init__(
        self, username: str, password: str = None, path_ctx_cookies: Optional[str] = None
    ):
        self.username = username
        self.password = "" if password is None else password
        self.path_ctx_cookies = (
            "ctx_cookies.yaml" if path_ctx_cookies is None else path_ctx_cookies
        )

    def _t(self) -> str:
        return (
            sha256(self.username[-3::-1].encode("utf-8")).hexdigest()
            if self.username
            else ""
        )

    def _login(self, ctx: Chrome) -> None:
        ctx.get(self.URL_LOGIN)

        actions = ActionChains(ctx)

        # 输入账号
        WebDriverWait(ctx, 10).until(
            EC.presence_of_element_located((By.ID, "username"))
        ).send_keys(self.username)

        # 去除遮挡
        try:
            ctx.find_element(By.ID, "lg_header").click()
        except NoSuchElementException:
            actions.send_keys(Keys.TAB)
            actions.perform()

        # 输入密码
        WebDriverWait(ctx, 10).until(
            EC.presence_of_element_located((By.ID, "password"))
        ).send_keys(self.password)

        # 登录
        try:
            ctx.find_element(By.ID, "ulogin").click()
        except NoSuchElementException:
            actions.send_keys(Keys.ENTER)
            actions.perform()

    def load_ctx_cookies(self) -> Optional[List[dict]]:
        """
        载入本地缓存的身份令牌。

        :return:
        """
        if not os.path.exists(self.path_ctx_cookies):
            return []

        with open(self.path_ctx_cookies, "r", encoding="utf8") as file:
            data: dict = yaml.safe_load(file)

        ctx_cookies = data.get(self._t(), []) if isinstance(data, dict) else []
        if not ctx_cookies:
            return []

        return ctx_cookies

    def save_ctx_cookies(self, ctx_cookies: List[dict]) -> None:
        """
        在本地缓存身份令牌。

        :param ctx_cookies:
        :return:
        """
        _data = {}

        if os.path.exists(self.path_ctx_cookies):
            with open(self.path_ctx_cookies, "r", encoding="utf8") as file:
                stream: dict = yaml.safe_load(file)
                _data = _data if not isinstance(stream, dict) else stream

        _data.update({self._t(): ctx_cookies})

        with open(self.path_ctx_cookies, "w", encoding="utf8") as file:
            yaml.dump(_data, file)

    def is_available_cookie(self, ctx_cookies: Optional[List[dict]] = None) -> bool:
        """
        检测 COOKIE 是否有效

        :param ctx_cookies: 若不指定则将工作目录 cookies 视为 ctx_cookies
        :return:
        """
        ctx_cookies = self.load_ctx_cookies() if ctx_cookies is None else ctx_cookies
        if not ctx_cookies:
            return False

        headers = {"cookie": ToolBox.transfer_cookies(ctx_cookies)}
        proxies = {"http": None, "https": None}
        response = requests.get(
            self.URL_ACCOUNT_PERSONAL,
            headers=headers,
            allow_redirects=False,
            proxies=proxies,
        )

        if "账号绑定" in response.text:
            return True
        return False

    def refresh_ctx_cookies(
        self, silence: bool = True, _ctx_session=None
    ) -> Optional[bool]:
        """
        更新上下文身份信息

        :param _ctx_session: 泛型开发者参数
        :param silence:
        :return:
        """
        # {{< Check Context Cookie Validity >}}
        if self.is_available_cookie():
            return True
        # {{< Done >}}

        # {{< Insert Challenger Context >}}
        ctx = get_ctx(silence=silence) if _ctx_session is None else _ctx_session
        try:
            self._login(ctx)

            # 登录状态判断
            try:
                WebDriverWait(ctx, 35).until(EC.url_changes(self.URL_LOGIN))
            except TimeoutException as err:
                raise LoginTimeoutException from err
            else:
                if "psw_error" in ctx.current_url:
                    raise AuthException("账号信息错误")
                logger.debug("登录成功")

        except (AuthException, LoginTimeoutException):
            return False
        else:
            self.save_ctx_cookies(ctx_cookies=ctx.get_cookies())
            return self.is_available_cookie(ctx_cookies=ctx.get_cookies())
        finally:
            if _ctx_session is None:
                ctx.quit()
        # {{< Done >}}


class PigAI:
    """Selenium action module"""

    def __init__(
        self,
        username: str,
        password: str,
        pid: str,
        content: str,
        class_name: str,
        silence: Optional[bool] = None,
    ):
        """

        :param username:账号
        :param password:密码
        :param pid:作文号
        :param content:正文
        :param class_name:班级名
        :param silence:
        """
        self.url = "http://www.pigai.org/index.php?c=write"
        self.silence = bool(silence)

        # 启动信息
        self.username = username
        self.password = password
        self.pid = pid
        self.content = content
        self.class_name = class_name

        # 对象信息
        self.score, self.title, self.stu_num, self.stu_name = [""] * 4

        # eid
        self.end_html = ""

    @staticmethod
    def wait(api: Chrome, timeout: float, tag_xpath_str):
        try:
            if tag_xpath_str == "all":
                time.sleep(1)
                WebDriverWait(api, timeout).until(EC.presence_of_all_elements_located)
            else:
                WebDriverWait(api, timeout).until(
                    EC.presence_of_element_located((By.XPATH, tag_xpath_str))
                )
        except TimeoutException:
            pass

    def _reset_page(self, ctx: Chrome, ctx_cookies):
        ctx.get(self.url)
        for cookie_dict in ctx_cookies:
            try:
                ctx.add_cookie(cookie_dict)
            except InvalidCookieDomainException:
                pass
        ctx.get(self.url)

    def switch_to_workspace(self, api: Chrome):

        self.wait(api, 5, "all")
        api.find_element(By.NAME, "rid").click()
        api.find_element(By.NAME, "rid").send_keys(self.pid)
        api.find_element(By.CLASS_NAME, "sf_right").click()

        logger.debug(f"切换至写作页面 pid={self.pid}")

    def build_content(self, api: Chrome):
        self.wait(api, 5, "all")

        data_frame = api.find_element(By.ID, "contents")
        data_frame.clear()

        for ch in self.content.split(" "):
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

    def select_class(self, api: Chrome, class_name: str or bool):

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
                logger.warning("Alert={}".format(alert.text))
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

    def check_result(self):
        user = {
            "user_id": f"{self.stu_num[:3]}***{self.stu_num[-6:-3]}",
            "pid": self.title,
            "score": str(self.score),
        }

        logger.debug(str(user))

    def run(
        self,
        ctx: Chrome,
        ctx_cookies: List[dict],
        save_action_memory: Optional[bool] = True,
        check_result: Optional[bool] = True,
    ):
        # 重载 COOKIE
        self._reset_page(ctx, ctx_cookies=ctx_cookies)

        self.switch_to_workspace(ctx)

        self.show_workspace_info(ctx)

        self.build_content(ctx)

        self.select_class(ctx, self.class_name)

        self.submit(ctx)

        self.get_paper_score(ctx)

        if check_result:
            self.check_result()

        if save_action_memory:
            self.save_action_history(ctx)


@logger.catch()
def runner(
    username: str,
    password: str,
    pids: Union[str, list],
    class_name: str = None,
    content_length: Optional[int] = 200,
    save_action_memory: Optional[bool] = None,
    check_result: Optional[bool] = None,
):
    """

    :param username:账号
    :param password:密码
    :param pids:作文号
    :param class_name:班级名。不填写影响程序运行，但成绩“无效”。
    :param check_result: 输出执行结果，默认 False。
    :param save_action_memory: 是否存储操作历史，默认 False。
    :param content_length: 文章长度，默认 200。
    """
    if not class_name:
        logger.warning("`class_name`识别错误，无法将作文提交至指定群组。")

    if isinstance(pids, str):
        pids = [pids]

    if not isinstance(content_length, int):
        content_length = 200

    save_action_memory = bool(save_action_memory)
    check_result = bool(check_result)

    manager = CookieManager(username, password, path_ctx_cookies=PATH_CTX_COOKIES)

    if manager.refresh_ctx_cookies(silence=False):
        ctx_cookies = manager.load_ctx_cookies()

        for pid in pids:
            content = ToolBox.generate_fake_text(
                path_corpus=PATH_CORPUS, content_length=content_length
            )
            action = PigAI(
                username=username,
                password=password,
                pid=pid,
                class_name=class_name,
                content=content,
            )

            action.run(
                ctx=get_ctx(silence=False),
                ctx_cookies=ctx_cookies,
                save_action_memory=save_action_memory,
                check_result=check_result,
            )

        logger.success("工作栈已释放完毕")
