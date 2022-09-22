# -*- coding: utf-8 -*-

import logging
from enum import Enum
from typing import Optional, Text, List

from pydantic import BaseModel, validator

from d7.core.builtin import unix_now, str_now
from d7.core.context import Context
from d7.core.model_validators import not_empty
from d7.core.types import Config


class StepTypeEnum(Text, Enum):
    SCRIPT_LOAD = "SCRIPT_LOAD"
    PARAM_SET = "PARAM_SET"
    SQL_UPDATE = "SQL_UPDATE"
    SQL_DELETE = "SQL_DELETE"
    SQL_INSERT = "SQL_INSERT"
    SQL_SELECT = "SQL_SELECT"
    REDIS_GET = "REDIS_GET"
    REDIS_SET = "REDIS_SET"
    REDIS_DELETE = "REDIS_DELETE"
    HTTP = "HTTP"
    LOOP = "LOOP"
    TASK = "TASK"


class TimeStat(BaseModel):
    start_at: float = 0
    start_at_str: Text = ""
    end_at: float = 0
    end_at_str: Text = ""
    elapsed: float = 0


INDENT = 4


class StepResult(BaseModel):
    name: Text = ""
    indent: int = 0
    type: Text = "UNKNOWN"
    time_stat: TimeStat = TimeStat()
    children: List['StepResult'] = {}
    success: bool = False
    config_error: Text = ""
    execute_error: Text = ""

    def __str__(self) -> str:
        ret = " " * self.indent
        started = self.time_stat.start_at > 0
        if self.success:
            ret += "[√] "
        elif started:
            ret += "[x] "
        else:
            ret += '[-] '
        ret += f'[{self.type}][{self.name}]'
        if self.config_error:
            ret = ret + ', config_error=' + self.config_error
        if started:
            ret += f', elapsed={self.time_stat.end_at - self.time_stat.start_at:.2f}s, start_time={self.time_stat.start_at_str}'
        if self.execute_error:
            ret = ret + ', execute_error=' + self.execute_error
        if self.children:
            ret += ', children:\n'
            for child in self.children:
                child.indent = self.indent + INDENT
            ret += '\n'.join([str(i) for i in self.children])

        return ret


StepResult.update_forward_refs()


class StepConfigBase(BaseModel):
    name: Text
    type: StepTypeEnum
    config: Config
    continue_when_failed: bool = False

    # validators
    _name = validator('name', allow_reuse=True)(not_empty)
    _type = validator('type', allow_reuse=True)(not_empty)
    _config = validator('config', allow_reuse=True)(not_empty)


class StepBase(object):
    name: Text
    type: StepTypeEnum
    config: Config
    log_file: str
    logger: logging.Logger
    continue_when_failed: bool = False
    ctx: Context
    step_result: StepResult
    parent: Optional['StepBase']

    def get_name(self) -> Text:
        return self.name

    def get_type(self) -> StepTypeEnum:
        return self.type

    def get_logger(self) -> logging.Logger:
        return self.logger

    def init(self, config: StepConfigBase, logger: logging.Logger, log_file: str, ctx: Context):
        # subclass should override this method and call super().init()
        self.name = config.name
        self.type = config.type
        self.config = config.config
        self.log_file = log_file
        self.logger = logger
        self.continue_when_failed = config.continue_when_failed
        self.ctx = ctx
        self.validate_config()

    def run(self) -> StepResult:
        # subclass should override this method and call super().init()
        self.step_result = StepResult(name=self.name, type=self.type)
        self.step_result.time_stat.start_at = unix_now()
        self.step_result.time_stat.start_at_str = str_now()

    def validate_config(self):
        # subclass should override this method
        pass

    def validate_result(self):
        # subclass should override this method
        pass

    def get_full_path(self):
        path = self.name
        parent = self.parent
        while parent:
            path = f'{parent.name} > ' + path
            parent = parent.parent
        return path
