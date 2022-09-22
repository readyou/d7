# -*- coding: utf-8 -*-

import argparse
import json
import shlex

from collections import OrderedDict, namedtuple
from urllib.parse import urlparse

ParsedCommand = namedtuple(
    "ParsedCommand",
    [
        "method",
        "url",
        "auth",
        "headers",
        "cookies",
        "params",
        "data",
        "json",
        "verify",
    ],
)

parser = argparse.ArgumentParser()

parser.add_argument("command")
parser.add_argument("url")
parser.add_argument("-A", "--user-agent")
parser.add_argument("-I", "--head")
parser.add_argument("-H", "--header", action="append", default=[])
parser.add_argument("-b", "--cookie", action="append", default=[])
parser.add_argument("-d", "--data", "--data-ascii", "--data-binary", "--data-raw", default=None)
parser.add_argument("-k", "--insecure", action="store_false")
parser.add_argument("-u", "--user", default=())
parser.add_argument("-X", "--request", default="")


def _parse_url(url: str) -> [bool, any]:
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc]), result
    except Exception:
        return False, None


def parse(curl_command: str) -> ParsedCommand:
    cookies = OrderedDict()
    headers = OrderedDict()
    body = None
    method = "GET"

    curl_command = curl_command.replace("\\\n", " ")

    tokens = shlex.split(curl_command)
    parsed_args = parser.parse_args(tokens)

    if parsed_args.command != "curl":
        raise ValueError("Not a valid cURL command")

    [url_valid, parsed_url] = _parse_url(parsed_args.url)
    if not url_valid:
        raise ValueError("Not a valid URL for cURL command")
    short_url = parsed_args.url.replace(f'?{parsed_url.query}', '')
    params = None
    if parsed_url.query:
        params = {}
        param_pairs = parsed_url.query.split('&')
        for i, v in enumerate(param_pairs):
            param_pair = v.split('=')
            if param_pair and len(param_pair) == 2:
                params[param_pair[0]] = param_pair[1]

    data = parsed_args.data
    if data:
        method = "POST"

    if data:
        try:
            body = json.loads(data)
        except json.JSONDecodeError:
            headers["Content-Type"] = "application/x-www-form-urlencoded"
        else:
            headers["Content-Type"] = "application/json"

    if parsed_args.request:
        method = parsed_args.request

    for arg in parsed_args.cookie:
        try:
            key, value = arg.split("=", 1)
        except ValueError:
            pass
        else:
            cookies[key] = value

    for arg in parsed_args.header:
        try:
            key, value = arg.split(":", 1)
        except ValueError:
            pass
        else:
            headers[key] = value

    user = parsed_args.user
    if user:
        user = tuple(user.split(":"))

    return ParsedCommand(
        method=method,
        url=short_url,
        auth=user,
        headers=headers,
        cookies=cookies,
        params=params,
        data=data,
        json=body,
        verify=parsed_args.insecure,
    )
