# -*- coding: utf-8 -*-


def not_empty(obj):
    assert obj, 'should not be empty.'
    return obj


def gt(target):
    def checker(obj):
        assert obj > target, f'should > {target}'
        return obj

    return checker


def gte(target):
    def checker(obj):
        assert obj >= target, f'should >= {target}'
        return obj

    return checker


def lt(target):
    def checker(obj):
        assert obj < target, f'should < {target}'
        return obj

    return checker


def lte(target):
    def checker(obj):
        assert obj <= target
        assert obj <= target, f'should <= {target}'
        return obj

    return checker


def validator_chain(*checkers):
    assert checkers, 'checkers should not be empty'

    def checker(obj):
        for c in checkers:
            assert callable(c), 'should be callable'
            obj = c(obj)
        return obj

    return checker
