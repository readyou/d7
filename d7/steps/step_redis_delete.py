# -*- coding: utf-8 -*-

import logging
from typing import Text

from pydantic import BaseModel, validator
from redis import *

from d7.core.context import Context
from d7.steps.step import StepBase, StepConfigBase, StepResult
from d7.steps.util import get_metaconfig_redis
from d7.core.model_validators import not_empty


class RedisDeleteConfig(BaseModel):
    meta_id: int
    key: Text

    # validators
    _meta_id = validator('meta_id', allow_reuse=True)(not_empty)
    _key = validator('key', allow_reuse=True)(not_empty)


class StepRedisDelete(StepBase):
    redis_delete_config: RedisDeleteConfig

    def init(self, config: StepConfigBase, logger: logging.Logger, log_file: str, ctx: Context):
        self.redis_delete_config = RedisDeleteConfig(**config.config)
        super().init(config, logger, log_file, ctx)

    def run(self) -> StepResult:
        super().run()
        meta_config = get_metaconfig_redis(self.redis_delete_config.meta_id)
        r = Redis(host=meta_config.host, port=meta_config.port, db=meta_config.db, password=meta_config.password)
        response = r.delete(self.redis_delete_config.key)
        self.step_result.success = response == 1
        return self.step_result

    def validate_config(self):
        pass

    def validate_result(self):
        pass
