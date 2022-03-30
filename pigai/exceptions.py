# -*- coding: utf-8 -*-
# Time       : 2022/3/30 18:46
# Author     : QIN2DIM
# Github     : https://github.com/QIN2DIM
# Description:
from typing import Optional, Sequence


class PigAIException(Exception):
    """Armor module basic exception"""

    def __init__(
        self, msg: Optional[str] = None, stacktrace: Optional[Sequence[str]] = None
    ):
        self.msg = msg
        self.stacktrace = stacktrace
        super().__init__()

    def __str__(self) -> str:
        exception_msg = f"Message: {self.msg}\n"
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
