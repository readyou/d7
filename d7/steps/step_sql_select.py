# -*- coding: utf-8 -*-

import logging
from typing import Text, Any, Dict, Optional

from pydantic import BaseModel, validator

from d7.core.context import Context
from d7.core.model_validators import not_empty, validator_chain, gte, lte
from d7.steps.step import StepBase, StepConfigBase, StepResult
from d7.steps.util import normalize_where, format_sql_raw, \
    get_mysql_cursor


class SqlSelectConfig(BaseModel):
    meta_id: int
    table: Text
    where: Text
    where_args: Dict[Text, Any]
    limit: int = 1
    extract_result_to: Optional[Text]

    # validators
    _meta_id = validator('meta_id', allow_reuse=True)(not_empty)
    _table = validator('table', allow_reuse=True)(not_empty)
    _where = validator('where', allow_reuse=True)(not_empty)
    _where_args = validator('where_args', allow_reuse=True)(not_empty)
    _limit = validator('limit', allow_reuse=True)(validator_chain(gte(1), lte(2000)))


class StepSqlSelect(StepBase):
    sql_select_config: SqlSelectConfig
    sql: str

    def init(self, config: StepConfigBase, logger: logging.Logger, log_file: str, ctx: Context):
        self.sql_select_config = SqlSelectConfig(**config.config)
        self.sql_select_config.where = normalize_where(self.sql_select_config.where)
        self.sql = self._get_sql()
        logger.debug('%s', self.sql)
        super().init(config, logger, log_file, ctx)

    def _get_sql(self):
        sql = f'SELECT * FROM {self.sql_select_config.table} WHERE {self.sql_select_config.where} LIMIT {self.sql_select_config.limit}'
        formatted_sql = format_sql_raw(self.sql_select_config.meta_id, sql, self.sql_select_config.where_args)
        return formatted_sql

    def run(self) -> StepResult:
        super().run()
        with get_mysql_cursor(self.sql_select_config.meta_id) as cursor:
            cursor.execute(self.sql)
            self.logger.debug('cursor.rowcount=%s, cursor.lastrowid=%s', cursor.rowcount, cursor.lastrowid)
            if self.sql_select_config.limit == 1:
                result = cursor.fetchone()
            else:
                result = cursor.fetchmany()
            self.logger.debug('select result:\n%s', result)
            if self.sql_select_config.extract_result_to:
                self.ctx.set_variable(self.sql_select_config.extract_result_to, result)
        self.step_result.success = result is not None
        return self.step_result

    def validate_config(self):
        pass

    def validate_result(self):
        pass
