# -*- coding: utf-8 -*-
# Time       : 2022/3/30 18:46
# Author     : QIN2DIM
# Github     : https://github.com/QIN2DIM
# Description:
from typing import Optional, Sequence


class PigAIException(Exception):
    """Armor module basic exception"""

    def __init__(self, msg: Optional[str] = None, stacktrace: Optional[Sequence[str]] = None):
        self.msg = msg
        self.stacktrace = stacktrace
        super().__init__()

    def __str__(self) -> str:
        exception_msg = f"{self.msg}\n"
        if self.stacktrace:
            stacktrace = "\n".join(self.stacktrace)
            exception_msg += f"Stacktrace:\n{stacktrace}"
        return exception_msg


class AuthException(PigAIException):
    """认证错误"""


class LoginTimeoutException(AuthException):
    """登录验证超时"""


class InvalidParamsException(PigAIException):
    """缺少必要的函数参数"""


class OncePaperWarning(PigAIException):
    """当前作文仅能提交一次且已提交，无法继续作业"""


class PaperNotFoundError(PigAIException):
    """作文号不存在或作业尚未发布"""
