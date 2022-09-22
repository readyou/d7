# -*- coding: utf-8 -*-

import contextlib
import json
import re
import string
from typing import Optional
from typing import Text

import pymysql
from pydantic import BaseModel
from pymysql import cursors

from d7.core.logger import logger
from d7.steps.uncurl import parse


class MetaConfigRedis(BaseModel):
    host: Text
    port: int = 3306
    db: Text
    password: Optional[Text]


_fetch_meta_func = None


def set_fetch_meta_func(fetch_meta):
    global _fetch_meta_func
    _fetch_meta_func = fetch_meta


def get_metaconfig_redis(meta_id: int) -> MetaConfigRedis:
    config = {
        'host': '127.0.0.1',
        'port': 6379,
        'db': 0,
    }
    global _fetch_meta_func
    if _fetch_meta_func is None:
        logger.info('_fetch_meta_func is None, use default config')
        return MetaConfigRedis(**config)
    c, err = _fetch_meta_func(meta_id=meta_id)
    if err is not None:
        logger.error('fetch_meta error: %s, use default config', err)
        return MetaConfigRedis(**config)

    c = json.loads(c.config)
    if type(c) == type([]):
        return MetaConfigRedis(**c[0])
    if type(c) == type({}):
        return MetaConfigRedis(**c)
    logger.info("meta type is: %s", type(c))

    return MetaConfigRedis(**config)


class MetaConfigDB(BaseModel):
    username: Text
    password: Text
    host: Text
    port: int = 3306
    database: Text


def get_metaconfig_db(meta_id: int) -> MetaConfigDB:
    config = {
        'username': 'root',
        'password': 'root',
        'host': '127.0.0.1',
        'port': 3306,
        'database': 'test',
    }

    global _fetch_meta_func
    if _fetch_meta_func is None:
        logger.info('_fetch_meta_func is None, use default config')
        return MetaConfigDB(**config)
    c, err = _fetch_meta_func(meta_id=meta_id)
    if err is not None:
        logger.error('fetch_meta error: %s, use default config', err)
        return MetaConfigDB(**config)

    c = json.loads(c.config)
    if type(c) == type([]):
        return MetaConfigDB(**c[0])
    if type(c) == type({}):
        return MetaConfigDB(**c)
    logger.info("meta type is: %s", type(c))

    return MetaConfigDB(**config)


def normalize_where(where: str) -> str:
    where = where.replace(':', '$')
    args = re.findall('\$\S+', where)
    for arg in args:
        normalize_arg = '%(' + ('' + arg).lstrip('$') + ')s'
        where = where.replace(arg, normalize_arg)
    return where


def format_sql_raw(meta_id, sql, args) -> string:
    meta_config = get_metaconfig_db(meta_id)
    connection = pymysql.connect(host=meta_config.host,
                                 port=meta_config.port,
                                 user=meta_config.username,
                                 password=meta_config.password,
                                 database=meta_config.database,
                                 cursorclass=pymysql.cursors.DictCursor)
    with connection:
        with connection.cursor() as cursor:
            return format_sql(cursor, sql, args)


def format_sql(cursor, sql, args) -> string:
    try:
        formatted_sql = cursor.mogrify(query=sql, args=args)
    except KeyError as e:
        field = str(e).replace('##', '')
        raise Exception(f'invalid param {field}, please check your sql or args') from None
    return formatted_sql


@contextlib.contextmanager
def get_mysql_cursor(meta_id: int) -> cursors.Cursor:
    assert meta_id, 'meta_id should not be empty'
    meta_config = get_metaconfig_db(meta_id)
    connection = pymysql.connect(host=meta_config.host,
                                 port=meta_config.port,
                                 user=meta_config.username,
                                 password=meta_config.password,
                                 database=meta_config.database,
                                 cursorclass=pymysql.cursors.DictCursor)
    with connection:
        has_err = False
        with connection.cursor() as cursor:
            try:
                yield cursor
            except Exception as e:
                logger.exception('cursor execute error: %s', e)
                has_err = True
                connection.rollback()
                raise e
            finally:
                if not has_err:
                    connection.commit()


def parse_curl_to_step_config(curl_command: str) -> object:
    # 删除不支持的参数
    curl_command = curl_command.replace('--location', '')
    ctx = parse(curl_command)
    obj = {
        'method': ctx.method.upper(),
        'url': ctx.url,
        'headers': ctx.headers,
        'cookies': ctx.cookies,
        'params': ctx.params,
        'data': ctx.data,
    }
    return obj
