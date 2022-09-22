# -*- coding: utf-8 -*-

import unittest

from d7.core.exceptions import ParamsError
from d7.steps.config_validator import validate_step_config, validate_step_config_of_json


class StepConfigValidatorTestCase(unittest.TestCase):
    def test_validate_failed_no_json_str(self):
        with self.assertRaises(Exception) as cm:
            validate_step_config_of_json('')
        self.assertTrue(cm.exception.__str__().__contains__("config of json should not be empty"))

        with self.assertRaises(Exception) as cm:
            validate_step_config(None)
        self.assertTrue(cm.exception.__str__().__contains__("config should not be None"))

    def test_validate_failed_invalid_type(self):
        config = {
            'name': 'test set param',
            'type': 'not_exist_type',
            'config': {
                'param1': 'value1',
                'param2': 'value2'
            }
        }
        with self.assertRaises(ParamsError) as cm:
            validate_step_config(config)
        self.assertIsNotNone(cm)

    def test_validate_failed_no_config(self):
        config = {
            'name': 'test set param',
            'type': 'PARAM_SET',
            # 'config': {
            #     'param1': 'value1',
            #     'param2': 'value2'
            # }
        }
        with self.assertRaises(ParamsError) as cm:
            validate_step_config(config)
        self.assertIsNotNone(cm)

    def test_validate_failed_empty_config(self):
        config = {
            'name': 'test set param',
            'type': 'not_exist_type',
            'config': {
                # 'param1': 'value1',
                # 'param2': 'value2'
            }
        }
        with self.assertRaises(ParamsError) as cm:
            validate_step_config(config)
        self.assertIsNotNone(cm)

    def test_validate_failed_invalid_sql(self):
        config = {
            'name': 'test sql_select',
            'type': 'SQL_SELECT',
            'config': {
                'meta_id': 1,
                'table': 'user_tab',
                'where': 'id = :id AND username = :username',
                'where_args': {
                    # 'id': 1, # id not exists, should raise error
                    'username': 'xxx'
                },
                'limit': 1,
                'extract_result_to': 'user_info'
            }
        }
        with self.assertRaises(ParamsError) as cm:
            validate_step_config(config)
        self.assertTrue(cm.exception.__str__().__contains__("invalid param 'id', please check your sql or args"))
