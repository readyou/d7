# -*- coding: utf-8 -*-

import logging
from typing import Text, Optional

from pydantic import BaseModel, validator
from redis import *

from d7.core.context import Context
from d7.core.model_validators import not_empty
from d7.steps.step import StepBase, StepConfigBase, StepResult
from d7.steps.util import get_metaconfig_redis


class RedisGetConfig(BaseModel):
    meta_id: int
    key: Text
    extract_result_to: Optional[Text]

    # validators
    _meta_id = validator('meta_id', allow_reuse=True)(not_empty)
    _key = validator('key', allow_reuse=True)(not_empty)


class StepRedisGet(StepBase):
    redis_get_config: RedisGetConfig

    def init(self, config: StepConfigBase, logger: logging.Logger, log_file: str, ctx: Context):
        self.redis_get_config = RedisGetConfig(**config.config)
        super().init(config, logger, log_file, ctx)

    def run(self) -> StepResult:
        super().run()
        meta_config = get_metaconfig_redis(self.redis_get_config.meta_id)
        r = Redis(host=meta_config.host, port=meta_config.port, db=meta_config.db, password=meta_config.password)
        result = r.get(self.redis_get_config.key)
        self.logger.info(f'get from redis: key={self.redis_get_config.key}, result={result}')
        if self.redis_get_config.extract_result_to:
            self.ctx.set_variable(self.redis_get_config.extract_result_to, result)
        self.step_result.success = result is not None
        return self.step_result

    def validate_config(self):
        pass

    def validate_result(self):
        pass
