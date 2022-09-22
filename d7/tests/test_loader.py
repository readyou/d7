# -*- coding: utf-8 -*-

import tempfile
import unittest

from d7.core import loader
from d7.core.builtin import get_uuid
from d7.core.loader import load_functions_from_script, load_builtin_functions


class ImportTestCase(unittest.TestCase):
    def test_import_script(self):
        name = 'func_add'
        script = f'''
def {name}(a, b):
    return a + b
'''
        module_name = get_uuid()
        function_map = load_functions_from_script(script, module_name)
        self.assertTrue(function_map)
        self.assertIsNotNone(function_map[name])
        self.assertEqual(3, function_map[name](1, 2))

    def test_import_builtin(self):
        function_map = load_builtin_functions()
        self.assertTrue(function_map)
        self.assertIsNotNone(function_map['get_timestamp'])
        timestamp = function_map['get_timestamp'](13)
        self.assertEqual(13, len(timestamp))

    def test_load_csv_file_one_parameter(self):
        csv_str = '''username,password
test1,111111
test2,222222
test3,333333
'''
        with tempfile.NamedTemporaryFile() as temp:
            temp.write(bytes(csv_str, 'utf-8'))
            temp.flush()
            csv_content = loader.load_csv_file(temp.name)
            self.assertEqual(
                csv_content,
                [
                    {"username": "test1", "password": "111111"},
                    {"username": "test2", "password": "222222"},
                    {"username": "test3", "password": "333333"},
                ],
            )
