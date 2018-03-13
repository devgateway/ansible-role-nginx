#!/usr/bin/python3
import sys, re, logging

logging.basicConfig(level = 'DEBUG')
log = logging.getLogger(sys.argv[0])

class Directive:
    def __init__(self, tokens):
        self.args = []
        self.kwargs = {}
        for token in tokens:
            pass

        # bare statement, e.g. "ip_hash"
        if not tokens:
            self.args.append(True)

class Context:
    def __init__(self, name, args = None):
        self.args = args
        self.name = name
        self.parent = None
        self.directives = {}
        self.children = {}

    @staticmethod
    def _add_item(_dict, item, name):
        if name not in _dict:
            _dict[name] = []
        _dict[name].append(item)

    def add_directive(self, name, tokens):
        log.debug('\tDirective %s' % name)
        directive = Directive(tokens)
        self._add_item(self.directives, directive, name)

    def add_context(self, child):
        child.parent = self
        self._add_item(self.children, child, child.name)

# match single or double quoted strings and barewords
tokenizer = re.compile(r'(?:\'[^\']*\')|(?:"[^"]*")|(?:\([^)]+\))|(?:[^\'"\s]+)')

http = Context('http')

with open(sys.argv[1], 'r') as config:
    log.debug('Enter context http')
    curr_ctx = http
    for dirty_line in config:
        line = dirty_line.lstrip().rstrip()
        if not line or line[0] == '#':
            # skip blanks and comments
            continue
        else:
            if line[-1] == '}':
                # exit child context
                log.debug('Exit context %s' % curr_ctx.name)
                curr_ctx = curr_ctx.parent
            else:
                tokens = tokenizer.findall(line[:-1])
                if line[-1] == ';':
                    # add directive at current context
                    curr_ctx.add_directive(name = tokens[0], tokens = tokens[1:])
                elif line[-1] == '{':
                    # add child context
                    child = Context(name = tokens[0], args = tokens[1:])
                    curr_ctx.add_context(child)
                    log.debug('Enter context %s' % child.name)
                    curr_ctx = child
                else:
                    raise RuntimeError('Line wrapping not supported. Fix it.\n' + line)
