#!/usr/bin/python3
import sys, re, logging

logging.basicConfig(level = 'DEBUG')
log = logging.getLogger(sys.argv[0])

class Statement:
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return self.name

class Directive(Statement):
    def __init__(self, name, tokens):
        super().__init__(name)
        self.args = []
        self.kwargs = {}

        # bare statement, e.g. "ip_hash"
        if not tokens:
            self.args.append(True)

        for token in tokens:
            if token[0] in '\'"':
                # it's a quoted string
                self.args.append(token[1:-2])
            elif '=' in token:
                # it's a keyworded argument
                (key, value) = tuple(token.split('=', maxsplit = 1))
                if ':' in value:
                    # it's a list of values
                    self.kwargs[key] = value.split(':')
                else:
                    # it's a single value
                    self.kwargs[key] = self._parse_scalar(value)
            else:
                # it's a positional argument
                self.args.append(self._parse_scalar(token))

        log.debug('\t%s: %i args, %i kwargs' % (self.name, len(self.args), len(self.kwargs)))

    @staticmethod
    def _parse_scalar(scalar):
        if scalar == 'on':
            result = True
        elif scalar == 'off':
            result = False
        else:
            result = scalar

        return result

class Context(Statement):
    def __init__(self, name, args = None):
        super().__init__(name)
        self.args = args
        self.parent = None
        self.directives = {}
        self.children = {}

    @staticmethod
    def _add_item(_dict, item, name):
        if name not in _dict:
            _dict[name] = []
        _dict[name].append(item)

    def add_directive(self, name, tokens):
        directive = Directive(name, tokens)
        self._add_item(self.directives, directive, name)

    def add_context(self, child):
        child.parent = self
        self._add_item(self.children, child, child.name)

    def get_data(self):
        data = {}
        for name, directives in self.directives.items():
            if len(directives) == 1:
                # single directive in this context
                this_directive = directives[0]
                if this_directive.kwargs:
                    # keyworded args present, make it a dictionary
                    data[name] = {'kwargs': this_directive.kwargs}
                    # if positional args also present, add them as 'args' member
                    if this_directive.args:
                        data[name]['args'] = this_directive.kwargs
                else:
                    data[name] = this_directive.args
            else:
                # multiple directives in this context
                multiple_args = map(lambda d: len(d.args) > 1, directives)
                if all(multiple_args):
                    # make a dict with each first arg as the key
                    data[name] = {}
                    for directive in directives:
                        args = directive.args[:]
                        key = args.pop(0)
                        data[name][key] = args
                else:
                    # array of arrays of arguments
                    data[name] = [d.args for d in directives]

        return data

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
