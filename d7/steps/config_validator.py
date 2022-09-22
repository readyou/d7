# -*- coding: utf-8 -*-

import json

from d7.core.context import Context
from d7.core.exceptions import ParamsError
from d7.core.logger import logger
from d7.steps.step import StepConfigBase, StepTypeEnum
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
from d7.steps.task import LoopConfig, Task, TaskType


def validate_step_config_of_json(json_config: str):
    """validate config of step.

    try:
        validate_step_config_of_json(config)
    catch Exception as e:
        do something when validate failed
    do something when validate succeed

    :param json_config: json format config to be validated
    :return: None
    """
    assert json_config, 'config of json should not be empty'
    try:
        config = json.loads(json_config)
    except Exception as e:
        logger.exception('parse json error: %s', e)
        raise ParamsError(e)
    validate_step_config(config)


def validate_step_config(config: dict):
    """validate config of step.

    try:
        validate_step_config(config)
    catch Exception as e:
        do something when validate failed
    do something when validate succeed

    :param config: config object to be validated
    :return: None
    """
    assert config, 'config should not be None'
    try:
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
                        logger=logger,
                        log_file='',
                        loop_config=loop_config,
                        task_type=TaskType.LOOP,
                        ctx=Context()
                        )
        else:
            raise ParamsError(f"invalid step type: {cfg.type}")
        step.init(config=cfg, log_file='', logger=logger, ctx=Context())
    except Exception as e:
        logger.exception('build and init step instance error: %s', e)
        raise ParamsError(e)
