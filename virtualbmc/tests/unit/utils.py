# Copyright 2016 Red Hat, Inc.
# All Rights Reserved.
#
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

import contextlib
from functools import wraps
from unittest import mock


# obtain a reference to builtins.open on import (before patching)
__builtins_open = open


def mock_existence(*args, return_value=True):
    existence_functions = [
        'os.path.exists',
        'os.path.isdir',
        'os.path.isfile',
    ]

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            with contextlib.ExitStack() as mock_stack:
                mocks = {}
                for target in existence_functions:
                    mocks[target] = mock.patch(target,
                                               return_value=return_value)
                    mock_stack.enter_context(mocks[target])
                return func(*args, mocks, **kwargs)
        return wrapper
    return decorator if len(args) == 0 else decorator(args[0])


def mock_open_file(file_name, read_data=None):
    def mock_open(*args, **kwargs):
        if args[0] == file_name:
            return mock.mock_open(read_data=read_data)(*args, **kwargs)
        else:
            return __builtins_open(*args, **kwargs)
    return mock_open
