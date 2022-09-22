# -*- coding: utf-8 -*-

import logging
from typing import Text

from pydantic import BaseModel, validator
from redis import *

from d7.core.context import Context
from d7.core.model_validators import not_empty
from d7.steps.step import StepBase, StepConfigBase, StepResult
from d7.steps.util import get_metaconfig_redis


class RedisSetConfig(BaseModel):
    meta_id: int
    key: Text
    value: Text
    expire_seconds: int

    # validators
    _meta_id = validator('meta_id', allow_reuse=True)(not_empty)
    _key = validator('key', allow_reuse=True)(not_empty)
    _value = validator('value', allow_reuse=True)(not_empty)


class StepRedisSet(StepBase):
    redis_delete_config: RedisSetConfig

    def init(self, config: StepConfigBase, logger: logging.Logger, log_file: str, ctx: Context):
        self.redis_delete_config = RedisSetConfig(**config.config)
        super().init(config, logger, log_file, ctx)

    def run(self) -> StepResult:
        super().run()
        meta_config = get_metaconfig_redis(self.redis_delete_config.meta_id)
        r = Redis(host=meta_config.host, port=meta_config.port, db=meta_config.db, password=meta_config.password)
        response = r.set(name=self.redis_delete_config.key, value=self.redis_delete_config.value,
                         ex=self.redis_delete_config.expire_seconds)
        self.logger.info(
            f'set to redis: key={self.redis_delete_config.key}, value={self.redis_delete_config.value}, response={response}')
        self.step_result.success = response
        return self.step_result

    def validate_config(self):
        pass

    def validate_result(self):
        pass
