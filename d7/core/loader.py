# -*- coding: utf-8 -*-
import csv
import importlib
import importlib.machinery
import importlib.util
import os
import tempfile
import types
from typing import Dict, Callable, Text, List

from d7.core import builtin, exceptions


def load_module_functions(module) -> Dict[Text, Callable]:
    """load python module functions.

    Args:
        module: python module

    Returns:
        dict: functions mapping for specified python module

            {
                "func1_name": func1,
                "func2_name": func2
            }
    """
    module_functions = {}

    for name, item in vars(module).items():
        if isinstance(item, types.FunctionType):
            module_functions[name] = item

    return module_functions


def load_builtin_functions() -> Dict[Text, Callable]:
    """load builtin module functions"""
    return load_module_functions(builtin)


def load_functions_from_script(script: Text, module_name: Text) -> Dict[Text, Callable]:
    """
    load functions from script

    :param script: code source str
    :param module_name: unique module name
    :return:
    """
    """load functions from script

    Returns:
        dict: functions mapping
            {
                "func1_name": func1,
                "func2_name": func2
            }
    """

    with tempfile.NamedTemporaryFile() as temp:
        temp.write(bytes(script, 'utf-8'))
        temp.flush()
        return load_from_file(temp.name, module_name)


def load_from_file(filepath: str, module_fullname: str):
    loader = importlib.machinery.SourceFileLoader(module_fullname, filepath)
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return load_module_functions(module)


def load_csv_file(csv_file: Text) -> List[Dict]:
    """load csv file and check file content format

    Args:
        csv_file (str): csv file path, csv file content is like below:

    Returns:
        list: list of parameters, each parameter is in dict format

    Examples:
        >>> cat csv_file
        username,password
        test1,111111
        test2,222222
        test3,333333

        >>> load_csv_file(csv_file)
        [
            {'username': 'test1', 'password': '111111'},
            {'username': 'test2', 'password': '222222'},
            {'username': 'test3', 'password': '333333'}
        ]

    """
    csv_content_list = []

    if not os.path.isfile(csv_file):
        # file path not exist
        raise exceptions.CSVNotFound(csv_file)
    with open(csv_file, encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            csv_content_list.append(row)

    return csv_content_list
