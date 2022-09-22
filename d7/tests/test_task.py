# -*- coding: utf-8 -*-

import json
import sys
import unittest
from typing import List, Text

import pymysql
from d7.core.builtin import get_uuid, unix_now
from d7.steps.step import StepTypeEnum
from d7.steps.step_http import content_type_form, content_type_json
from d7.steps.task import Task, TaskSummary
from d7.steps.util import get_metaconfig_db
from d7.task_maker import create_task, create_task_from_json


def run_task(task_name: Text, configs: List[dict]) -> (Task, TaskSummary):
    task = create_task(task_name, configs)
    task_summary = task.execute()
    return task, task_summary


class TaskTestCase(unittest.TestCase):
    def test_param_set_success(self):
        task_name = sys._getframe().f_code.co_name
        configs = [{
            'name': 'step1',
            # 下面两种传参方式都行
            # 'type': StepTypeEnum.p_SET,
            'type': 'PARAM_SET',
            'config': {
                'p1': '0',
                'p2': 'v2',
                'p3': {
                    'p4': 'v4'
                },
                'p4': [{
                    'p5': 'v5'
                }]
            }
        }]
        task, task_summary = run_task(task_name, configs)
        self.assertTrue(task_summary.success)
        self.assertEqual('0', task.ctx.get_variable('p1'))
        self.assertEqual('v2', task.ctx.get_variable('p2'))
        self.assertEqual('v4', task.ctx.get_variable('p3')['p4'])
        self.assertEqual('v4', task.ctx.get_variable('p3.p4'))
        self.assertEqual('v5', task.ctx.get_variable('p4.$p1.p5'))

    def test_task_init_failed_invalid_type(self):
        task_name = sys._getframe().f_code.co_name
        configs = [{
            'name': 'test set param',
            'type': 'not_exist_type',
            'config': {
                'param1': 'value1',
                'param2': 'value2'
            }
        }]
        task, task_summary = run_task(task_name, configs)
        self.assertFalse(task_summary.success)

    def test_task_init_failed_no_config(self):
        task_name = sys._getframe().f_code.co_name
        configs = [{
            'name': 'test set param',
            'type': StepTypeEnum.PARAM_SET,
            # 'config': {
            #     'param1': 'value1',
            #     'param2': 'value2'
            # }
        }]
        task, task_summary = run_task(task_name, configs)
        self.assertFalse(task_summary.success)

    def test_task_init_failed_empty_config(self):
        task_name = sys._getframe().f_code.co_name
        configs = [{
            'name': 'test set param',
            'type': StepTypeEnum.PARAM_SET,
            'config': {
                #     'param1': 'value1',
                #     'param2': 'value2'
            }
        }]
        task, task_summary = run_task(task_name, configs)
        self.assertFalse(task_summary.success)

    def test_task_sql_insert_success(self):
        task_name = sys._getframe().f_code.co_name
        nickname = 'nickname:' + get_uuid()
        meta_id = 1
        configs = [{
            'name': 'test_step_sql_insert_success',
            'type': StepTypeEnum.SQL_INSERT,
            'config': {
                'meta_id': meta_id,
                'table': 'user_tab',
                'insert_fields': {
                    'username': nickname,
                    'nickname': nickname,
                    'encrypted_password': nickname,
                    'create_time': unix_now(),
                    'update_time': unix_now(),
                },
            }
        }]
        task, task_summary = run_task(task_name, configs)
        self.assertTrue(task_summary.success)
        return nickname

    def test_task_sql_insert_fail_of_invalid_args(self):
        task_name = sys._getframe().f_code.co_name
        nickname = 'nickname:' + get_uuid()
        meta_id = 1
        configs = [{
            'name': 'test_step_sql_insert_fail',
            'type': StepTypeEnum.SQL_INSERT,
            'config': {
                'meta_id': meta_id,
                'table': 'user_tab',
                'insert_fields': {
                    # 'username': nickname, 模拟必填字段没有的场景
                    'nickname': nickname,
                },
            }
        }]
        task, task_summary = run_task(task_name, configs)
        self.assertFalse(task_summary.success)

    def test_task_sql_update_success(self):
        """
        CREATE TABLE `user_tab` (
          `id` bigint NOT NULL AUTO_INCREMENT,
          `username` varchar(64) NOT NULL COMMENT '用户名（全局唯一）',
          `nickname` varchar(64) NOT NULL DEFAULT '' COMMENT '昵称',
          `avatar` varchar(512) NOT NULL DEFAULT '' COMMENT '头像URL',
          `encrypted_password` varchar(64) NOT NULL COMMENT '加密之后的密码',
          `create_time` bigint unsigned NOT NULL COMMENT '创建时间',
          `update_time` bigint unsigned NOT NULL COMMENT '更新时间',
          PRIMARY KEY (`id`),
          UNIQUE KEY `uidx_username` (`username`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
        """
        task_name = sys._getframe().f_code.co_name
        nickname = 'nickname:' + get_uuid()
        meta_id = 1
        configs = [{
            'name': 'test_step_sql_insert_success',
            'type': StepTypeEnum.SQL_INSERT,
            'config': {
                'meta_id': meta_id,
                'table': 'user_tab',
                'insert_fields': {
                    'username': nickname,
                    'nickname': nickname,
                    'encrypted_password': nickname,
                    'create_time': unix_now(),
                    'update_time': unix_now(),
                },
                'extract_result_to': 'user_id'
            }
        }, {
            'name': 'test sql_update',
            'type': StepTypeEnum.SQL_UPDATE,
            'config': {
                'meta_id': meta_id,
                'table': 'user_tab',
                'update_fields': {
                    'username': nickname + '_new',
                    'nickname': nickname + '_new',
                },
                'where': 'id = %(id)s AND username = :username',
                'where_args': {
                    'id': '$user_id',
                    'username': nickname
                },
                'limit': 1
            }
        }]
        task, task_summary = run_task(task_name, configs)
        self.assertTrue(task_summary.success)

        meta_config = get_metaconfig_db(meta_id)
        connection = pymysql.connect(host=meta_config.host,
                                     user=meta_config.username,
                                     password=meta_config.password,
                                     database=meta_config.database,
                                     cursorclass=pymysql.cursors.DictCursor)
        with connection:
            with connection.cursor() as cursor:
                cursor.execute('SELECT * from user_tab ORDER BY id DESC')
                row = cursor.fetchone()
                self.assertEqual(nickname + '_new', row['nickname'])
                self.assertEqual(nickname + '_new', row['username'])

    def test_task_sql_update_fail_of_invalid_args(self):
        task_name = sys._getframe().f_code.co_name
        nickname = 'nickname:' + get_uuid()
        meta_id = 1
        configs = [{
            'name': 'test sql_update',
            'type': StepTypeEnum.SQL_UPDATE,
            'config': {
                'meta_id': meta_id,
                'table': 'user_tab',
                'update_fields': {
                    'username': 'user1',  # 这里模拟update_fields和where_args重名的情况
                    'nickname': nickname,
                },
                'where': 'id = :id AND username = %(username)s',
                'where_args': {
                    # 'id': 1,
                    'username': 'user1'
                },
                'limit': 1
            }
        }]
        task, task_summary = run_task(task_name, configs)
        self.assertFalse(task_summary.success)

    def test_task_sql_select(self):
        task_name = sys._getframe().f_code.co_name
        nickname = 'nickname:' + get_uuid()
        meta_id = 1
        configs = [{
            'name': 'test_step_sql_insert_success',
            'type': StepTypeEnum.SQL_INSERT,
            'config': {
                'meta_id': meta_id,
                'table': 'user_tab',
                'insert_fields': {
                    'username': nickname,
                    'nickname': nickname,
                    'encrypted_password': nickname,
                    'create_time': unix_now(),
                    'update_time': unix_now(),
                },
            }
        }, {
            'name': 'test sql_select',
            'type': StepTypeEnum.SQL_SELECT,
            'config': {
                'meta_id': meta_id,
                'table': 'user_tab',
                'where': 'username = %(username)s',
                'where_args': {
                    'username': nickname
                },
                'limit': 10,
                'extract_result_to': 'user_info'
            }
        }]
        task, task_summary = run_task(task_name, configs)
        self.assertTrue(task_summary.success)

    def test_task_sql_delete_success(self):
        task_name = sys._getframe().f_code.co_name
        nickname = 'nickname:' + get_uuid()
        meta_id = 1
        configs = [{
            'name': 'test_step_sql_insert_success',
            'type': StepTypeEnum.SQL_INSERT,
            'config': {
                'meta_id': meta_id,
                'table': 'user_tab',
                'insert_fields': {
                    'username': nickname,
                    'nickname': nickname,
                    'encrypted_password': nickname,
                    'create_time': unix_now(),
                    'update_time': unix_now(),
                },
            }
        }, {
            'name': 'test sql_delete',
            'type': StepTypeEnum.SQL_DELETE,
            'config': {
                'meta_id': meta_id,
                'table': 'user_tab',
                'where': 'username = %(username)s',
                'where_args': {
                    'username': nickname
                },
                'limit': 1
            }
        }]
        task, task_summary = run_task(task_name, configs)
        self.assertTrue(task_summary.success)

    def test_task_sql_delete_fail_of_not_found(self):
        task_name = sys._getframe().f_code.co_name
        meta_id = 1
        configs = [{
            'name': 'test sql_delete',
            'type': StepTypeEnum.SQL_DELETE,
            'config': {
                'meta_id': meta_id,
                'table': 'user_tab',
                'where': 'username = %(username)s',
                'where_args': {
                    'username': 'abc'
                },
                'limit': 1
            }
        }]
        task, task_summary = run_task(task_name, configs)
        self.assertFalse(task_summary.success)

    def test_continue_when_failed(self):
        task_name = sys._getframe().f_code.co_name
        meta_id = 1
        configs = [{
            'name': 'test sql_delete fail',
            'type': StepTypeEnum.SQL_DELETE,
            'config': {
                'meta_id': meta_id,
                'table': 'user_tab',
                'where': 'username = %(username)s',
                'where_args': {
                    'username': 'abc'
                },
                'limit': 1
            }
        }, {
            'name': 'test param_set success',
            'type': StepTypeEnum.PARAM_SET,
            'config': {
                'param1': 'value1',
                'param2': 'value2'
            }
        }]
        task, task_summary = run_task(task_name, configs)
        self.assertFalse(task_summary.success)
        self.assertEqual(1, len(task_summary.step_results))

        configs[0]['continue_when_failed'] = True
        task, task_summary = run_task(task_name, configs)
        self.assertTrue(task_summary.success)
        self.assertEqual(2, len(task_summary.step_results))
        self.assertTrue(task_summary.step_results[1].success)

    def test_task_redis_set_success(self):
        task_name = sys._getframe().f_code.co_name
        meta_id = 1
        configs = [{
            'name': 'test_step_redis_set_success',
            'type': StepTypeEnum.REDIS_SET,
            'config': {
                'meta_id': meta_id,
                'key': 'test_key',
                'value': 'test_value',
                'expire_seconds': 100,
            }
        }]
        task, task_summary = run_task(task_name, configs)
        self.assertTrue(task_summary.success)

    def test_task_redis_get_success(self):
        task_name = sys._getframe().f_code.co_name
        meta_id = 1
        key = 'test_key'
        value = 'test_value'
        configs = [{
            'name': 'test_step_redis_set_success',
            'type': StepTypeEnum.REDIS_SET,
            'config': {
                'meta_id': meta_id,
                'key': key,
                'value': value,
                'expire_seconds': 100,
            }
        }, {
            'name': 'test_step_redis_get_success',
            'type': StepTypeEnum.REDIS_GET,
            'config': {
                'meta_id': meta_id,
                'key': key,
                'extract_result_to': 'user_info'
            }
        }]
        task, task_summary = run_task(task_name, configs)
        self.assertTrue(task_summary.success)

    def test_task_redis_delete_success(self):
        task_name = sys._getframe().f_code.co_name
        meta_id = 1
        key = 'test_key'
        value = 'test_value'
        configs = [{
            'name': 'test_step_redis_set_success',
            'type': StepTypeEnum.REDIS_SET,
            'config': {
                'meta_id': meta_id,
                'key': key,
                'value': value,
                'expire_seconds': 100,
            }
        }, {
            'name': 'test_step_redis_delete_success',
            'type': StepTypeEnum.REDIS_DELETE,
            'config': {
                'meta_id': meta_id,
                'key': key
            }
        }]
        task, task_summary = run_task(task_name, configs)
        self.assertTrue(task_summary.success)

    def test_task_http_get_success(self):
        task_name = sys._getframe().f_code.co_name
        configs = [{
            'name': 'test_step_http_get',
            'type': StepTypeEnum.HTTP,
            'config': {
                'method': 'GET',
                'url': 'http://httpbin.org/get',
                'params': {
                    'p1': 'x1',
                    'p2': 'x2',
                },
                'use_err_code': ''
            }
        }]
        task, task_summary = run_task(task_name, configs)
        self.assertTrue(task_summary.success)

    def test_task_http_post_form_success(self):
        task_name = sys._getframe().f_code.co_name
        configs = [{
            'name': 'test_step_http_post_form',
            'type': StepTypeEnum.HTTP,
            'config': {
                'method': 'POST',
                'url': 'http://httpbin.org/post',
                'data': {
                    'p1': 'x1',
                    'p2': 'x2',
                },
                'headers': {
                    'content-type': content_type_form
                },
                'use_err_code': ''
            }
        }]
        task, task_summary = run_task(task_name, configs)
        self.assertTrue(task_summary.success)

    def test_task_http_post_json_success(self):
        task_name = sys._getframe().f_code.co_name
        configs = [{
            'name': 'test_step_http_post_json',
            'type': 'HTTP',
            'config': {
                'method': 'POST',
                'url': 'http://httpbin.org/post',
                'data': {
                    'p1': 'x1',
                    'p2': 'x2',
                },
                'headers': {
                    'content-type': content_type_json
                },
                'use_err_code': ''
            }
        }]
        task, task_summary = run_task(task_name, configs)
        self.assertTrue(task_summary.success)

    def test_task_multi_steps_success(self):
        task_name = sys._getframe().f_code.co_name
        nickname = 'nickname:' + get_uuid()
        meta_id = 1
        configs = [{
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
        task, task_summary = run_task(task_name, configs)
        self.assertTrue(task_summary.success)
        user_info = json.loads(task.ctx.get_variable('user_info2'))
        self.assertEqual(nickname, user_info['username'])
        self.assertEqual('nick', user_info['nickname'])

    def test_task_step_loop_success(self):
        task_name = sys._getframe().f_code.co_name
        configs = [{
            'name': 'step loop1',
            'type': StepTypeEnum.LOOP,
            'config': {
                'loop_from': '${range(2)}',
                'children': [{
                    'name': 'step http get1',
                    'type': StepTypeEnum.HTTP,
                    'config': {
                        'method': 'GET',
                        'url': 'http://httpbin.org/get',
                        'params': {
                            'index': '$loop_index',
                            'param': '$loop_param',
                        },
                        'use_err_code': ''
                    }
                }, {
                    'name': 'step loop2',
                    'type': 'LOOP',
                    'config':
                        {
                            'loop_from': '${range(3)}',
                            'children': [{
                                'name': 'step http_get2',
                                'type': StepTypeEnum.HTTP,
                                'config': {
                                    'method': 'GET',
                                    'url': 'http://httpbin.org/get',
                                    'params': {
                                        'index': '$loop_index',
                                        'param': '$loop_param',
                                    },
                                    'use_err_code': ''
                                }
                            }]
                        }
                }]
            }
        }]
        task, task_summary = run_task(task_name, configs)
        self.assertTrue(task_summary.success)
        log = task.get_task_log()
        print(task_summary.log)
        self.assertEqual(task_summary.log, log)

    def test_load_script(self):
        task_name = sys._getframe().f_code.co_name
        configs = [{
            "name": "test load script",
            "type": "SCRIPT_LOAD",
            "config": {
                "script": "def add(a, b):\n  return a + b"
            }
        }]
        task = create_task(task_name, configs)
        summary = task.execute()
        self.assertTrue(summary.success)
        add = task.ctx.get_function("add")
        self.assertEqual(3, add(1, 2))

    def test_config_from_schema(self):
        task_name = sys._getframe().f_code.co_name
        js = '''
        [{
        "name": "test loop",
        "type": "LOOP",
        "continue_when_failed": false,
        "config": {
            "loop_from": "${range(2)}",
            "children": [
                {
                    "type": "HTTP",
                    "name": "test step http",
                    "continue_when_failed": false,
                    "config": {
                        "url": "http://httpbin.org/get",
                        "method": "GET",
                        "params": {
                            "a": "A",
                            "b": "B"
                        },
                        "headers": {
                            "h1": "H1",
                            "h2": "H2"
                        },
                        "use_err_code": "",
                        "extract_result_to": "resp"
                    }
                }
            ]
        }
    }]
        '''
        task = create_task_from_json(task_name, js)
        summary = task.execute()
        self.assertTrue(summary.success)
        resp = task.ctx.get_variable("resp")
        self.assertIsNotNone(resp)
        self.assertEqual(1, task.ctx.get_variable("loop_index"))
        print(resp)
