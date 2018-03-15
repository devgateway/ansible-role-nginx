#!/usr/bin/python3
import sys, re, logging, yaml, os
try:
    from yaml import CDumper as Dumper
except ImportError:
    from yaml import Dumper

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
                self.args.append(token[1:-1])
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
        def get_args(directive):
            if len(directive.args) == 1:
                return directive.args[0]
            else:
                return directive.args

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
                    data[name] = get_args(this_directive)
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
                    data[name] = [get_args(d) for d in directives]

        for directive_name, contexts in self.children.items():
            context_data = []
            for context in contexts:
                child_data = context.get_data()
                child_data[directive_name] = context.args
                context_data.append(child_data)
            data[directive_name + 's'] = context_data

        return data

# configure logging
valid_levels = ["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"]
try:
    env_level = os.environ["LOG_LEVEL"]
    valid_levels.remove(env_level)
    level = getattr(logging, env_level)
except KeyError:
    level = logging.WARNING
except ValueError:
    msg = "Expected log level: %s, got: %s. Using default level WARNING." \
            % ("|".join(valid_levels), env_level)
    print(msg, file = sys.stderr)
    level = logging.WARNING
logging.basicConfig(level = level)
log = logging.getLogger(sys.argv[0])

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

print(yaml.dump(http.get_data(), Dumper = Dumper))
