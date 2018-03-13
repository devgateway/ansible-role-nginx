#!/usr/bin/python3
import sys, re, logging

logging.basicConfig(level = 'DEBUG')
log = logging.getLogger(sys.argv[0])

class Context:
    def __init__(self, name, args = None):
        log.debug('Create context "%s"' % name)
        self.args = args
        self.name = name
        self.parent = None
        self.directives = []
        self.child_lists = {}

    def add_directive(self, name, args):
        log.debug('Add directive "%s"' % name)
        pass

    def add_context(self, child):
        log.debug('Add context "%s->%s"' % (self.name, child.name))
        child.parent = self
        if child.name not in self.child_lists:
            self.child_lists[child.name] = []
        self.child_lists[child.name].append(child)

# match single or double quoted strings and barewords; strip quotes
tokenizer = re.compile(r'(?:(?<=\')[^\']*(?=\'))|(?:(?<=")[^"]*(?="))|(?:\([^)]+\))|(?:[^\'"\s]+)')

http = Context('http')

with open(sys.argv[1], 'r') as config:
    lineno = 0
    curr_ctx = http
    for dirty_line in config:
        lineno = lineno + 1
        line = dirty_line.lstrip().rstrip()
        if not line or line[0] == '#':
            # skip blanks and comments
            log.debug('Line %i: skipping' % lineno)
            continue
        else:
            if line[-1] == '}':
                # exit child context
                log.debug('Line %i: exit context %s' % (lineno, curr_ctx.name))
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
                    curr_ctx = child
                else:
                    raise RuntimeError('Line wrapping not supported. Fix it.')
