#!/usr/bin/python3
# Split YAML stream into site documents
# Usage: ./splityml.py BIG_YAML OUTPUT_DIR

# Copyright 2018, Development Gateway

# This program is free software: you can redistribute it and/or modify it under the terms of the
# GNU General Public License as published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without
# even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with this program.
# If not, see <https://www.gnu.org/licenses/>.

import sys, yaml, os, uuid, logging
try:
    from yaml import CDumper as Dumper, CBaseLoader as BaseLoader
except ImportError:
    from yaml import Dumper, BaseLoader

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

unique_names = set()

def get_file_name(document):
    global unique_names
    try:
        server_names = document['site']['server']['server_name']
        if type(server_names) is str:
            primary_name = server_names
        else:
            primary_name = server_names[0]
        log.debug('Primary name is %s' % primary_name)

        if primary_name[0] == '.':
            # strip leading dot
            primary_name = primary_name[1:]
            log.debug('Removed leading dot')

        if primary_name in unique_names:
            log.info('Name %s not unique' % primary_name)
            listen = document['site']['server']['listen']
            if type(listen) is list:
                # multiple arguments to listen directive
                ports = listen
            else:
                ports = [listen]

            for port in listen:
                # try appending ports (or other listen args)
                new_name = '%s-%s' % (primary_name, port)
                if new_name not in unique_names:
                    # found a unique name
                    log.info('New unique name %s' % new_name)
                    primary_name = new_name
                    break

            if primary_name in unique_names:
                # still not unique, resort to UUID
                raise KeyError('Can\'t create a unique file name')
        unique_names.add(primary_name)
        base_name = primary_name
    except Exception as e:
        log.warning(str(e))
        base_name = str(uuid.uuid4())
    return os.path.join(sys.argv[2], base_name + '.yml')

with open(sys.argv[1], 'r') as big_file:
    documents = yaml.load_all(big_file, Loader = BaseLoader)
    for document in documents:
        file_name = get_file_name(document)
        with open(file_name, 'x') as small_file:
            yaml.dump(document, stream = small_file, Dumper = Dumper)
