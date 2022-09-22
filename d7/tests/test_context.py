# -*- coding: utf-8 -*-

import unittest

from d7.core.context import Context


class TaskLogTestCase(unittest.TestCase):

    def test_context(self):
        ctx = Context()
        script = '''
def add(a, b):
    return a + b
'''
        ctx.load_script(script)
        add = ctx.get_function('add')
        self.assertIsNotNone(add)
        self.assertTrue(callable(add))
        self.assertEqual(3, add(1, 2))

        # get python builtin function
        add = ctx.get_function('sum')
        self.assertIsNotNone(add)
        self.assertTrue(callable(add))
        self.assertEqual(3, add([1, 2]))

        # extract variables
        ctx.extract_variables({
            'a': 1,
            'b': 2,
            'c': '${add($a, $b)}',
            'd': 'hello',
        })
        b = ctx.parse_data('${add($a, b=$c)}')
        self.assertTrue(isinstance(b, int))
        self.assertEqual(4, b)

        c = ctx.get_variable('c')
        self.assertEqual(3, c)

        d = ctx.get_variable('d')
        self.assertEqual('hello', d)

        ctx.set_variable('c', 9)
        b = ctx.parse_data('${add($a, b=$c)}')
        self.assertTrue(isinstance(b, int))
        self.assertEqual(10, b)
