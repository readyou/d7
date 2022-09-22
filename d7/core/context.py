# -*- coding: utf-8 -*-


from typing import Dict, Text, Any, Callable

from d7.core import loader
from d7.core.builtin import get_uuid
from d7.core.parser import parse_variables_mapping, parse_string, parse_data, get_mapping_function, \
    get_mapping_variable


class Context(object):

    _variables_map: Dict[Text, Any] = {}
    _functions_map: Dict[Text, Callable] = {}

    def __init__(self) -> None:
        self._functions_map = loader.load_builtin_functions()

    def load_script(self, script_str: Text):
        self._functions_map.update(**loader.load_functions_from_script(script_str, get_uuid()))

    def extract_variables(self, variables: Dict[Text, Any]):
        if variables is None:
            return
        for key in variables:
            self._variables_map[key] = self.parse_data(variables[key])
        self._variables_map.update(parse_variables_mapping(self._variables_map, self._functions_map))

    def parse_string(self, raw_string: Text) -> Any:
        return parse_string(raw_string, self._variables_map, self._functions_map)

    def parse_data(self, raw_data: Any) -> Any:
        return parse_data(raw_data, self._variables_map, self._functions_map)

    def set_variable(self, key: Text, value: Any):
        self._variables_map[key] = value

    def set_variables(self, variables: Dict[Text, Any] = {}):
        self._variables_map.update(**variables)

    def get_variable(self, name: Text) -> Callable:
        return get_mapping_variable(name, self._variables_map, self._functions_map)

    def get_function(self, name: Text) -> Callable:
        return get_mapping_function(name, self._functions_map)
