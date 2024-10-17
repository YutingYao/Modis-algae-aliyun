#!/usr/bin/env python
# -*- coding: utf-8 -*-

from abc import abstractmethod, ABCMeta
from aiearth.engine.client.interactive_session import InteractiveSession


class FunctionNode(metaclass=ABCMeta):
    def __init__(self, name, args, var_name=None):
        self.func_name = name
        self.invoke_args = args
        self.var_name = var_name

    def _isVariable(self):
        return self.func_name is None and self.invoke_args is None

    def getInfo(self):
        return InteractiveSession.getInfo(self)
