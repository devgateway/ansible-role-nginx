#!/usr/bin/python3
# Convert Nginx conf.d files to YAML structures

# Copyright 2018, Development Gateway

# This program is free software: you can redistribute it and/or modify it under the terms of the
# GNU General Public License as published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without
# even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with this program.
# If not, see <https://www.gnu.org/licenses/>.

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
                    self.kwargs[key] = [self._parse_scalar(v) for v in value.split(':')]
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
        elif scalar.isdigit():
            result = int(scalar)
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
                        data[name]['args'] = this_directive.args
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
                    data[name] = [[get_args(d) for d in directives]]

        for directive_name, contexts in self.children.items():
            context_data = []
            for context in contexts:
                child_data = context.get_data()
                if directive_name == 'if':
                    # remove parentheses from condition
                    child_data[directive_name] = ' '.join(context.args)[1:-1]
                elif directive_name != 'server':
                    # add context name, e.g.: "location: /"
                    child_data[directive_name] = ' '.join(context.args)
                context_data.append(child_data)
            data[directive_name + 's'] = context_data

        return data

def get_logger():
    """Configure logging."""

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
    return logging.getLogger(sys.argv[0])

class ConfFile():
    # match single or double quoted strings, parenthesized expressions, and barewords
    tokenizer = re.compile(r'(?:\'[^\']*\')|(?:"[^"]*")|(?:\([^)]+\))|(?:[^\'"\s]+)')

    @classmethod
    def read_config(cls, file_name):
        log.info('Parsing %s' % file_name)
        http = Context('http')

        with open(file_name, 'r') as config:
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
                        tokens = cls.tokenizer.findall(line[:-1])
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

        return http.get_data()

    def __init__(self, file_name):
        self.http_data = self.read_config(file_name)
        self.servers = self.http_data['servers']
        del self.http_data['servers']

    def __iter__(self):
        for server in self.servers:
            try:
                server_name = server['server_name']
            except KeyError:
                server_name = '<no server name>'
            log.info(server_name)
            site = {'site': {'server': server}}
            if self.http_data:
                site['site']['http'] = self.http_data

            yield site

log = get_logger()
conf = ConfFile(sys.argv[1])
for site in conf:
    print(yaml.dump(
        site,
        Dumper = Dumper,
        default_flow_style = False,
        explicit_start = True
        ))
