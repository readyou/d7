# -*- coding: utf-8 -*-

import json
from typing import List, Text

import yaml

from d7.core.builtin import get_uuid
from d7.core.logger import get_task_log_file, get_task_logger
from d7.steps.task import Task


def create_task(task_name: Text, configs: List[dict]) -> Task:
    uuid = get_uuid()
    log_file = get_task_log_file(uuid)
    logger = get_task_logger(log_file=log_file, level='DEBUG', name=uuid)
    return Task(name=task_name, logger=logger, log_file=log_file, configs=configs)


def create_task_from_json(task_name: Text, json_config: str) -> Task:
    configs = json.loads(json_config)
    return create_task(task_name, configs)


def create_task_from_yaml(task_name: Text, yaml_config: str) -> Task:
    configs = yaml.load(yaml_config, Loader=yaml.Loader)
    return create_task(task_name, configs)
