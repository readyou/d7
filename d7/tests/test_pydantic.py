# -*- coding: utf-8 -*-

import unittest
from typing import Text

from pydantic import BaseModel, validator

from d7.core.model_validators import not_empty


class ModelA(BaseModel):
    name: Text
    _name = validator('name', allow_reuse=True)(not_empty)


class PydanticTestCase(unittest.TestCase):

    def test_required_field(self):
        with self.assertRaises(Exception) as e:
            a = ModelA(name='')
        self.assertIsNotNone(e)
        self.assertTrue(str(e.exception).find('should not be empty') >= 0)
