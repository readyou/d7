# -*- coding: utf-8 -*-

import logging
import os
from datetime import datetime
from functools import lru_cache

logger: logging.Logger = logging.getLogger()


def init_logger(log: logging.Logger):
    global logger
    logger = log


_seq = 0


@lru_cache(maxsize=10000)
def get_task_log_file(uuid: str) -> str:
    if not os.path.isdir('log'):
        try:
            os.mkdir('log')
        except:
            pass
    now = datetime.now()
    now_str = now.strftime("%Y%m%d_%H%M%S")
    global _seq
    _seq += 1
    return f'log/{now_str}_{_seq}_{uuid}.log'


def get_task_file_handler(log_file: str, level: str) -> logging.FileHandler:
    handler = logging.FileHandler(filename=log_file)
    handler.setLevel(level)
    formatter = logging.Formatter(
        fmt='{asctime}|{levelname}|{module}|{filename}:{lineno}|{message}', style='{')
    handler.setFormatter(formatter)
    return handler


def get_task_logger(log_file: str, level: str, name: str) -> logging.Logger:
    _logger = logging.getLogger(name)
    _logger.setLevel(level)
    handler = get_task_file_handler(log_file, level)
    _logger.addHandler(handler)

    return _logger
