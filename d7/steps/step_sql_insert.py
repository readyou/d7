# -*- coding: utf-8 -*-

import logging
from typing import Text, Any, Dict, Optional

from pydantic import BaseModel, validator

from d7.core.context import Context
from d7.core.model_validators import not_empty
from d7.steps.step import StepBase, StepConfigBase, StepResult
from d7.steps.util import format_sql_raw, get_mysql_cursor


class SqlInsertConfig(BaseModel):
    meta_id: int
    table: Text
    insert_fields: Dict[Text, Any]
    extract_result_to: Optional[Text]

    # validators
    _meta_id = validator('meta_id', allow_reuse=True)(not_empty)
    _table = validator('table', allow_reuse=True)(not_empty)
    _insert_fields = validator('insert_fields', allow_reuse=True)(not_empty)


class StepSqlInsert(StepBase):
    sql_insert_config: SqlInsertConfig
    sql: str

    def init(self, config: StepConfigBase, logger: logging.Logger, log_file: str, ctx: Context):
        self.sql_insert_config = SqlInsertConfig(**config.config)
        self.sql = self._get_sql()
        logger.debug('%s', self.sql)
        super().init(config, logger, log_file, ctx)

    def _get_sql(self):
        args = {}
        sql = f'INSERT INTO {self.sql_insert_config.table} ('
        for field in self.sql_insert_config.insert_fields:
            sql += f'{field},'
        sql = sql.rstrip(',')
        sql += ') VALUES ('
        for field in self.sql_insert_config.insert_fields:
            field_name = f'##{field}'
            args[field_name] = self.sql_insert_config.insert_fields[field]
            sql += f'%({field_name})s,'
        sql = sql.rstrip(',')
        sql += ')'
        formatted_sql = format_sql_raw(self.sql_insert_config.meta_id, sql, args)
        return formatted_sql

    def run(self) -> StepResult:
        super().run()
        with get_mysql_cursor(self.sql_insert_config.meta_id) as cursor:
            cursor.execute(self.sql)
            self.logger.debug('cursor.rowcount=%s, cursor.lastrowid=%s', cursor.rowcount, cursor.lastrowid)
            if self.sql_insert_config.extract_result_to:
                self.ctx.set_variable(self.sql_insert_config.extract_result_to, cursor.lastrowid)
        self.step_result.success = True
        return self.step_result

    def validate_config(self):
        pass

    def validate_result(self):
        pass
