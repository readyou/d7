# -*- coding: utf-8 -*-

import json
import sys
import unittest

import yaml

from d7.core.builtin import get_uuid, unix_now
from d7.steps.step import StepTypeEnum
from d7.task_maker import create_task_from_yaml


class TaskFactoryTestCase(unittest.TestCase):
    def get_configs(self):
        nickname = 'nickname:' + get_uuid()
        meta_id = 1
        return nickname, [{
            'name': 'test set param',
            'type': StepTypeEnum.PARAM_SET,
            'config': {
                'username': nickname,
                'nickname': nickname
            }
        }, {
            'name': 'test sql_insert',
            'type': StepTypeEnum.SQL_INSERT,
            'config': {
                'meta_id': meta_id,
                'table': 'user_tab',
                'insert_fields': {
                    'username': '$username',
                    'nickname': '$nickname',
                    'encrypted_password': 'password',
                    'create_time': unix_now(),
                    'update_time': unix_now(),
                },
                'extract_result_to': 'user_id',
            }
        }, {
            'name': 'test sql_update',
            'type': StepTypeEnum.SQL_UPDATE,
            'config': {
                'meta_id': meta_id,
                'table': 'user_tab',
                'update_fields': {
                    'nickname': 'nick',
                },
                'where': 'id = :id',
                'where_args': {
                    'id': '$user_id',
                },
                'limit': 1,
            }
        }, {
            'name': 'test sql_select',
            'type': StepTypeEnum.SQL_SELECT,
            'config': {
                'meta_id': meta_id,
                'table': 'user_tab',
                'where': 'id = :id',
                'where_args': {
                    'id': '$user_id',
                },
                'limit': 1,
                'extract_result_to': 'user_info',
            }
        }, {
            'name': 'test redis set',
            'type': StepTypeEnum.REDIS_SET,
            'config': {
                'meta_id': meta_id,
                'key': 'user_info_${user_id}',
                'value': '${json_dumps($user_info)}',
                'expire_seconds': 100,
            }
        }, {
            'name': 'test redis get',
            'type': StepTypeEnum.REDIS_GET,
            'config': {
                'meta_id': meta_id,
                'key': 'user_info_${user_id}',
                'extract_result_to': 'user_info2',
            }
        }]

    def test_yaml_config(self):
        task_name = sys._getframe().f_code.co_name
        nickname, configs = self.get_configs()
        yaml_config = yaml.dump(configs)
        print(yaml_config)
        task = create_task_from_yaml(task_name, yaml_config)
        summary = task.execute()
        print(summary)
        self.assertTrue(summary.success)

    def test_json_config(self):
        task_name = sys._getframe().f_code.co_name
        nickname, configs = self.get_configs()
        json_config = json.dumps(configs)
        print(json_config)
        task = create_task_from_yaml(task_name, json_config)
        summary = task.execute()
        print(summary)
        self.assertTrue(summary.success)
