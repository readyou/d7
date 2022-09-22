# -*- coding: utf-8 -*-

import logging
from typing import Text, Any, Dict

from pydantic import BaseModel, validator

from d7.core.context import Context
from d7.core.model_validators import not_empty, validator_chain, gte
from d7.steps.step import StepBase, StepConfigBase, StepResult
from d7.steps.util import normalize_where, format_sql_raw, get_mysql_cursor


class SqlDeleteConfig(BaseModel):
    meta_id: int
    table: Text
    where: Text
    where_args: Dict[Text, Any]
    limit: int = 1

    # validators
    _meta_id = validator('meta_id', allow_reuse=True)(not_empty)
    _table = validator('table', allow_reuse=True)(not_empty)
    _where = validator('where', allow_reuse=True)(not_empty)
    _where_args = validator('where_args', allow_reuse=True)(not_empty)
    _limit = validator('limit', allow_reuse=True)(validator_chain(gte(1)))


class StepSqlDelete(StepBase):
    sql_delete_config: SqlDeleteConfig
    sql: str

    def init(self, config: StepConfigBase, logger: logging.Logger, log_file: str, ctx: Context):
        self.sql_delete_config = SqlDeleteConfig(**config.config)
        self.sql_delete_config.where = normalize_where(self.sql_delete_config.where)
        self.sql = self._get_sql()
        logger.debug('%s', self.sql)
        super().init(config, logger, log_file, ctx)

    def _get_sql(self):
        sql = f'DELETE FROM {self.sql_delete_config.table} WHERE {self.sql_delete_config.where} LIMIT {self.sql_delete_config.limit}'
        formatted_sql = format_sql_raw(self.sql_delete_config.meta_id, sql, self.sql_delete_config.where_args)
        return formatted_sql

    def run(self) -> StepResult:
        super().run()
        with get_mysql_cursor(self.sql_delete_config.meta_id) as cursor:
            cursor.execute(self.sql)
            self.logger.debug('cursor.rowcount=%s, cursor.lastrowid=%s', cursor.rowcount, cursor.lastrowid)
            if cursor.rowcount != self.sql_delete_config.limit:
                self.logger.error('delete row count[%d] != limit[%d]', cursor.rowcount,
                                  self.sql_delete_config.limit)
                self.step_result.success = False
            else:
                self.step_result.success = True
        return self.step_result

    def validate_config(self):
        pass

    def validate_result(self):
        pass
