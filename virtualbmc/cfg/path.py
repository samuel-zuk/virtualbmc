#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import os

from oslo_config import cfg
from oslo_config import types as cfg_types


class Path(cfg_types.ConfigType):
    PATH = 'path'
    FILE = 'file'
    DIRECTORY = 'directory'
    PATH_TYPES = [PATH, FILE, DIRECTORY]

    def __init__(self, type_name=PATH, must_exist=True):
        super().__init__(type_name=type_name)
        self.path_type = type_name
        self.must_exist = must_exist

        if self.path_type not in self.PATH_TYPES:
            raise ValueError('Path type must be one of %s, received %s' %
                             str(self.PATH_TYPES), self.path_type)

    def __call__(self, value):
        value = str(value)

        if self.must_exist:

            if not os.path.exists(value):
                raise ValueError(f'Could not find {self.path_type} "{value}"')

            if self.path_type == self.FILE and not os.path.isfile(value):
                raise ValueError(f'"{value}" is not a path to a regular file')
            elif self.path_type == self.DIRECTORY and not os.path.isdir(value):
                raise ValueError(f'"{value}" is not a path to a directory')

        return os.path.abspath(value)

    def __repr__(self):
        return self.path_type.title()

    def __eq__(self, other):
        return all((self.__class__ == other.__class__,
                    self.path_type == other.path_type,
                    self.must_exist == other.must_exist))

    def _formatter(self, value):
        return str(value)


class PathOpt(cfg.Opt):
    def __init__(self, name, path_type=Path.PATH, must_exist=True, **kwargs):
        super().__init__(name,
                         type=Path(path_type, must_exist=must_exist),
                         **kwargs)


class FileOpt(PathOpt):
    def __init__(self, name, must_exist=True, **kwargs):
        super().__init__(name, Path.FILE, must_exist, **kwargs)


class DirectoryOpt(PathOpt):
    def __init__(self, name, must_exist=True, **kwargs):
        super().__init__(name, Path.DIRECTORY, must_exist, **kwargs)
