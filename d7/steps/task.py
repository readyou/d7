# -*- coding: utf-8 -*-

import json
import logging
from enum import Enum
from typing import List, Iterable, Dict, Text, Any, Optional

from pydantic import validator, BaseModel

from d7.core.builtin import unix_now, str_now
from d7.core.context import Context
from d7.core.exceptions import ParamsError
from d7.core.logger import get_task_logger
from d7.core.model_validators import not_empty
from d7.core.utils import read_file
from d7.steps.step import StepBase, StepConfigBase, StepTypeEnum, StepResult, INDENT, TimeStat
from d7.steps.step_http import StepHttp
from d7.steps.step_param_set import StepParamSet
from d7.steps.step_redis_delete import StepRedisDelete
from d7.steps.step_redis_get import StepRedisGet
from d7.steps.step_redis_set import StepRedisSet
from d7.steps.step_script_load import StepScriptLoad
from d7.steps.step_sql_delete import StepSqlDelete
from d7.steps.step_sql_insert import StepSqlInsert
from d7.steps.step_sql_select import StepSqlSelect
from d7.steps.step_sql_update import StepSqlUpdate


class TaskSummary(BaseModel):
    type: Text
    name: Text
    success: bool = False
    time_stat: TimeStat = TimeStat()
    log: Text = ""
    error: Text = ""
    step_results: List[StepResult] = []
    indent = 0

    def __str__(self):
        step_result_str = '\n'.join([str(step_result) for step_result in self.step_results])
        indent_str = ' ' * self.indent
        task_summary_str = f"""
{indent_str}success: {self.success}
{indent_str}name: {self.name}
{indent_str}type: {self.type}
{indent_str}start_time: {self.time_stat.start_at_str}
{indent_str}end_time: {self.time_stat.end_at_str}
{indent_str}elapsed: {self.time_stat.end_at - self.time_stat.start_at:.2f}s
{indent_str}step_results:
{indent_str}{step_result_str}
"""
        if self.error:
            task_summary_str += f'error: {self.error}\n'
        return task_summary_str


class LoopConfig(BaseModel):
    loop_from: Iterable
    children: List[Dict[Text, Any]]

    # validators
    _loop_from = validator('loop_from', allow_reuse=True)(not_empty)
    _children = validator('children', allow_reuse=True)(not_empty)


class TaskType(Text, Enum):
    TASK = 'task'
    LOOP = 'loop'


def _get_result_str(success: bool):
    if success:
        return 'success'
    else:
        return 'failed'


def get_task_log(log_file) -> Text:
    return read_file(log_file)


class Task(StepBase):
    name: str = ''
    task_type: TaskType
    loop_config: Optional[LoopConfig]
    log_file: str
    logger: logging.Logger
    ctx: Context
    indent = 0
    parent = None

    def get_task_log(self) -> Text:
        s = read_file(self.log_file)
        return s

    def execute(self) -> TaskSummary:
        summary = TaskSummary(name=self.name, type='task', indent=self.indent)
        summary.time_stat.start_at = unix_now()
        summary.time_stat.start_at_str = str_now()
        path = self.get_full_path()
        if self.task_type == TaskType.TASK:
            config = json.dumps(self.loop_config.children, indent=2)
            self.logger.info('start run task [%s], config=%s', path, config)
        try:
            self._run(summary)
        except Exception as e:
            self.logger.exception('run task error: %s', e)
            print('run task error: %s' % e)
            summary.error = repr(e)
        summary.time_stat.end_at = unix_now()
        summary.time_stat.end_at_str = str_now()
        if self.task_type == TaskType.TASK:
            self.logger.info('end [%s] [%s]', _get_result_str(summary.success), path)
            self.logger.info('task_summary: %s', summary)
        summary.log = read_file(self.log_file)
        return summary

    def validate_config(self):
        pass

    def validate_result(self):
        pass

    def init(self, config: StepConfigBase, logger: logging.Logger, log_file: str, ctx: Context):
        pass

    def __init__(self,
                 name: str,
                 logger: logging.Logger = None,
                 log_file: str = '',
                 configs: List[dict] = None,
                 loop_config: LoopConfig = None,
                 task_type: TaskType = TaskType.TASK,
                 ctx: Context = None):
        self.task_type = task_type
        self.type = StepTypeEnum.TASK if task_type == TaskType.TASK else StepTypeEnum.LOOP
        self.log_file = log_file
        self.logger = logger or get_task_logger(log_file=self.log_file, level='DEBUG', name=self.log_file)
        if not configs and not loop_config:
            raise ParamsError('configs or loop_config should exists')

        self.name = name
        self.loop_config = loop_config or LoopConfig(loop_from=[1], children=configs)
        self.ctx = ctx or Context()

    def run(self) -> StepResult:
        summary = self.execute()
        step_result = StepResult(name=self.name, type=self.task_type)
        step_result.time_stat = summary.time_stat
        step_result.success = summary.success
        step_result.execute_error = summary.error
        step_result.children = summary.step_results
        return step_result

    def _run(self, summary: TaskSummary):
        loop_from = []
        if isinstance(self.loop_config.loop_from, Dict):
            for key in self.loop_config.loop_from:
                loop_from.append({
                    'loop_index': key,
                    'loop_param': self.loop_config.loop_from[key]
                })
        else:
            for (key, value) in enumerate(self.loop_config.loop_from):
                loop_from.append({
                    'loop_index': key,
                    'loop_param': value
                })
        loop_from = sorted(loop_from, key=lambda a: a['loop_index'])
        single_loop = len(loop_from) == 1
        path = self.get_full_path()
        success = True
        for loop in loop_from:
            self.ctx.set_variables(loop)
            if not single_loop:
                self.logger.info('start [%s] [loop:%s]', path, loop['loop_index'])
            success = self._run_steps(self.loop_config.children, summary)
            if not single_loop:
                self.logger.info('end [%s] [%s] [loop:%s]', _get_result_str(success), path, loop['loop_index'])
            if not success:
                break
        summary.success = success

    def _run_steps(self, children: List[Dict[Text, Any]], summary: TaskSummary) -> bool:
        success = True
        for config in children:
            step_name = config['name']
            path = self.get_full_path() + f' > {step_name}'
            step_result = StepResult()
            step_result.time_stat.start_at = unix_now()
            step_result.time_stat.start_at_str = str_now()
            step_result.name = step_name
            self.logger.info('start [%s]', path)
            try:
                self.logger.debug('config before parsed: %s', config)
                config = self.ctx.parse_data(config)
                self.logger.debug('config after parsed: %s', config)
                step = self.build_step(config=config)
                step_result.type = step.type
            except Exception as e:
                self.logger.exception('build step[%s] error: %r', step_name, e)
                success = False
                step_result.success = False
                step_result.config_error = repr(e)
                step_result.time_stat.end_at = unix_now()
                step_result.time_stat.end_at_str = str_now()
                summary.step_results.append(step_result)
                self.logger.error('end [error:init] [%s]: %r\n', path, e)
                return success

            try:
                step_result = step.run()
                self.logger.info('end [%s] [%s]\n', _get_result_str(step_result.success), path)
                if not step_result.success:
                    if not step.continue_when_failed:
                        success = False
                        break
            except Exception as e:
                step_result.success = False
                step_result.execute_error = repr(e)
                self.logger.exception('end [error:run] [%s]: %r\n', path, e)
                if not step.continue_when_failed:
                    success = False
                    break
            finally:
                step_result.time_stat.end_at = unix_now()
                step_result.time_stat.end_at_str = str_now()
                summary.step_results.append(step_result)
        summary.success = success
        return success

    def build_step(self, config: dict) -> StepBase:
        cfg = StepConfigBase(**config)
        if cfg.type == StepTypeEnum.HTTP:
            step = StepHttp()
        elif cfg.type == StepTypeEnum.SQL_SELECT:
            step = StepSqlSelect()
        elif cfg.type == StepTypeEnum.SQL_UPDATE:
            step = StepSqlUpdate()
        elif cfg.type == StepTypeEnum.SQL_INSERT:
            step = StepSqlInsert()
        elif cfg.type == StepTypeEnum.SQL_DELETE:
            step = StepSqlDelete()
        elif cfg.type == StepTypeEnum.REDIS_GET:
            step = StepRedisGet()
        elif cfg.type == StepTypeEnum.REDIS_SET:
            step = StepRedisSet()
        elif cfg.type == StepTypeEnum.REDIS_DELETE:
            step = StepRedisDelete()
        elif cfg.type == StepTypeEnum.PARAM_SET:
            step = StepParamSet()
        elif cfg.type == StepTypeEnum.SCRIPT_LOAD:
            step = StepScriptLoad()
        elif cfg.type == StepTypeEnum.LOOP:
            loop_config = LoopConfig(**cfg.config)
            step = Task(name=cfg.name,
                        logger=self.logger,
                        log_file=self.log_file,
                        loop_config=loop_config,
                        task_type=TaskType.LOOP,
                        ctx=self.ctx
                        )
            step.indent = self.indent + INDENT
        else:
            raise Exception(f"invalid step type: {cfg.type}")

        step.parent = self
        step.init(config=cfg, logger=self.logger, log_file=self.log_file, ctx=self.ctx)
        step.validate_config()
        return step
