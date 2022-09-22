# -*- coding: utf-8 -*-

import logging
from typing import Text

from pydantic import BaseModel, validator

from d7.core.context import Context
from d7.core.model_validators import not_empty
from d7.steps.step import StepBase, StepConfigBase, StepResult


class ScriptLoadConfig(BaseModel):
    script: Text

    # validators
    _script = validator('script', allow_reuse=True)(not_empty)


class StepScriptLoad(StepBase):
    script_load_config: ScriptLoadConfig

    def init(self, config: StepConfigBase, logger: logging.Logger, log_file: str, ctx: Context):
        self.script_load_config = ScriptLoadConfig(**config.config)
        super().init(config, logger, log_file, ctx)

    def run(self) -> StepResult:
        super().run()
        self.ctx.load_script(self.script_load_config.script)
        self.step_result.success = True
        return self.step_result

    def validate_config(self):
        pass

    def validate_result(self):
        pass
