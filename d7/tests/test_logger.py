# -*- coding: utf-8 -*-

import unittest

from d7.core.builtin import get_uuid
from d7.core.logger import get_task_logger, get_task_log_file


class TaskLogTestCase(unittest.TestCase):
    def test_get_task_logger(self):
        uuid = get_uuid()
        log_file = get_task_log_file(uuid)
        logger = get_task_logger(log_file=log_file, level="DEBUG", name=__file__)
        logger.debug("debug msg")
        logger.info("info msg")
        logger.error("error msg")

    def test_get_multi_times_of_the_same_uuid(self):
        uuid = 'abc'
        file_set = set()
        for i in range(10):
            file_set.add(get_task_log_file(uuid))
        self.assertEqual(1, len(file_set))
