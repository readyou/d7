# -*- coding: utf-8 -*-

import datetime
import random
import string
import time
import uuid
from typing import List


def rand_str(str_len: int, prefix: str = '', suffix: str = ''):
    """generate random string with specified length"""
    s = "".join(
        random.choice(string.ascii_letters + string.digits) for _ in range(str_len)
    )
    return f'{prefix}{s}{suffix}'


def split(s: str, spliter: str = ',') -> List[str]:
    return s.split(spliter)


def rand_int(a: int, b: int) -> int:
    return random.randint(a, b)


def get_timestamp(str_len=13):
    """get timestamp string, length can only between 0 and 16"""
    if isinstance(str_len, int) and 0 < str_len < 17:
        return str(time.time()).replace(".", "")[:str_len]

    raise Exception("timestamp length can only between 0 and 16.")


def get_uuid() -> str:
    return str(uuid.uuid4()).replace("-", "")


def unix_now() -> int:
    return datetime.datetime.now().timestamp()


def short_str_now() -> str:
    now = datetime.datetime.now()
    return now.strftime("%Y%m%d_%H%M%S")


def str_now() -> str:
    now = datetime.datetime.now()
    return now.strftime("%Y-%m-%d %H:%M:%S")


def str_today(fmt="%Y-%m-%d"):
    """get current date, default format is %Y-%m-%d"""
    return datetime.datetime.now().strftime(fmt)
