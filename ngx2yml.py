#!/usr/bin/python3
import sys, re
import pprint

class Context:
    def __init__(self, name, args = None):
        self.args = args
        self.name = name
        self.parent = None
        self.directives = []
        self.child_lists = {}

    def add_directive(self, name, args):
        pass

    def add_context(self, child):
        child.parent = self
        self.child_lists[child.name].append(child)

# match single or double quoted strings and barewords; strip quotes
tokenizer = re.compile(r'(?:(?<=\')[^\']*(?=\'))|(?:(?<=")[^"]*(?="))|(?:\([^)]+\))|(?:[^\'"\s]+)')

http = Context('http')

with open(sys.argv[1], 'r') as config:
    curr_ctx = http
    for dirty_line in config:
        line = dirty_line.lstrip().rstrip()
        if not line or line[0] == '#':
            # skip blanks and comments
            continue
        else:
            if line[-1] == '}':
                # exit child context
                curr_ctx = curr_ctx.parent
            else:
                tokens = tokenizer.findall(line[:-1])
                if line[-1] == ';':
                    # add directive at current context
                    curr_ctx.add_directive(name = tokens[0], args = tokens[1:])
                elif line[-1] == '{':
                    # add child context
                    child = Context(name = tokens[0], args = tokens[1:])
                    curr_ctx.add_context(child)
