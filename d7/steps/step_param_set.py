# -*- coding: utf-8 -*-

import logging
from typing import Dict, Text, Any

from d7.core.context import Context
from d7.steps.step import StepBase, StepConfigBase, StepResult


class StepParamSet(StepBase):
    config: Dict[Text, Any] = {}

    def init(self, config: StepConfigBase, logger: logging.Logger, log_file: str, ctx: Context):
        self.config = config.config
        super().init(config, logger, log_file, ctx)

    def run(self) -> StepResult:
        super().run()
        self.ctx.set_variables(self.config)
        self.step_result.success = True
        return self.step_result

    def validate_config(self):
        assert self.config, 'config should not be empty'

    def validate_result(self):
        pass
