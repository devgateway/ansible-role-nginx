#!/usr/bin/python3
import sys

class Context:
    def __init__(self, ctx_type, name = None):
        self.name = name
        self.ctx_type = ctx_type
        self.directives = []

    def add_directive(self, directive, args):
        pass
