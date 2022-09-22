# -*- coding: utf-8 -*-

import logging
# Enabling debugging at http.client level (requests->urllib3->http.client)
# you will see the REQUEST, including HEADERS and DATA, and RESPONSE with HEADERS but without DATA.
# the only thing missing will be the response.body which is not logged.
from enum import Enum
from typing import Text, Dict, Any, Optional

import requests
from pydantic import BaseModel, validator, root_validator

from d7.core.context import Context
from d7.core.model_validators import not_empty
from d7.steps.step import StepBase, StepConfigBase, StepResult

content_type_form = 'application/x-www-form-urlencoded'
content_type_json = 'application/json'


class MethodEnum(Text, Enum):
    GET = "GET"
    POST = "POST"
    # PUT = "PUT"
    # DELETE = "DELETE"
    # HEAD = "HEAD"
    # OPTIONS = "OPTIONS"
    # PATCH = "PATCH"


class HttpConfig(BaseModel):
    url: Text
    method: MethodEnum
    headers: Optional[Dict[Text, Any]]
    cookies: Optional[Dict[Text, Any]]
    params: Optional[Dict[Text, Any]]
    data: Optional[Dict[Text, Any]]
    use_err_code: Text = 'err_code'
    extract_result_to: Optional[Text]
    content_type: Optional[Text]

    # validators
    _url = validator('url', allow_reuse=True)(not_empty)

    @root_validator(pre=False)
    def check_config(cls, values):
        url = str(values['url'])
        assert url.startswith('http://') or url.startswith('https://'), f'url must starts with http'

        if values.get('method') == MethodEnum.GET:
            # GET方法没有什么需要额外校验的参数
            return values

        # POST请求，至少需要headers，指定请求参数是怎样的格式
        headers = values.get('headers')
        assert headers, 'headers should not be empty'
        content_type = get_header_ignore_case(headers, 'content-type')
        assert content_type, 'header "content-type" should not be empty'
        support_types = [content_type_form, content_type_json]
        assert content_type in support_types, f'content-type only support "{content_type_form}" or "{content_type_json}"'

        values['content_type'] = content_type
        return values


class StepHttp(StepBase):
    http_config: HttpConfig

    def init(self, config: StepConfigBase, logger: logging.Logger, log_file: str, ctx: Context):
        self.http_config = HttpConfig(**config.config)
        super().init(config, logger, log_file, ctx)

    def run(self) -> StepResult:
        super().run()

        if self.http_config.method == MethodEnum.GET:
            response = requests.request(method=self.http_config.method, url=self.http_config.url,
                                        headers=self.http_config.headers, cookies=self.http_config.cookies,
                                        params=self.http_config.params)
        elif self.http_config.content_type == content_type_form:
            response = requests.request(method=self.http_config.method, url=self.http_config.url,
                                        headers=self.http_config.headers, cookies=self.http_config.cookies,
                                        data=self.http_config.data)
        else:
            response = requests.request(method=self.http_config.method, url=self.http_config.url,
                                        headers=self.http_config.headers, cookies=self.http_config.cookies,
                                        json=self.http_config.data)

        self.logger.info(f'''
------------request-----------
{response.request.method} {response.request.url}
headers: {response.request.headers}
body: {response.request.body}
------------response----------
status_code: {response.status_code}
headers: {response.headers}
cookies: {response.cookies}
text: {response.text}
------------------------------''')
        # TODO: 自定义结果校验器
        # 约定接口都返回json，且包含：err_code字段
        # 这里不再判断status_code=200，反正json()方法出错，会被外层按失败处理
        if self.http_config.use_err_code:
            js = response.json()
            self.step_result.success = js[self.http_config.use_err_code] == 0
            if self.step_result.success and self.http_config.extract_result_to:
                self.ctx.set_variable(self.http_config.extract_result_to, js)
        else:
            self.step_result.success = response.status_code == 200
            if self.step_result.success and self.http_config.extract_result_to:
                self.ctx.set_variable(self.http_config.extract_result_to, response.text)
        return self.step_result

    def validate_config(self):
        pass

    def validate_result(self):
        pass


def get_header_ignore_case(headers, header_key):
    for key in headers:
        if key.lower() == header_key:
            return headers[key]
