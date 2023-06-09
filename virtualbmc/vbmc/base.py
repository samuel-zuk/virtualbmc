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

from functools import wraps

import pyghmi.ipmi.bmc as bmc

from virtualbmc import exception
from virtualbmc import log
from virtualbmc.vbmc import constants

LOG = log.get_logger()


class VbmcBase(bmc.Bmc):

    vbmc_type = 'vbmc_base'

    def __init__(self, name, username, password, host_address, port, **kwargs):
        super().__init__(authdata={username: password},
                         port=port,
                         addresss=host_address)
        self.name = name

    @staticmethod
    def bmc_cmd(*args, fail_ok=True):
        """ decorator that handles errors + debugging info for bmc commands """
        def decorator(func):
            @wraps(func)
            def wrapper(self, *args, **kwargs):
                argument_info = ''
                debug_str = (f'Calling {func.__name__} for {self.vbmc_type} '
                             '{self.name}')
                if args or kwargs:
                    if args:
                        args_str = ', '.join(args)
                        argument_info += f' with args "{args_str}"'
                    if kwargs:
                        kwargs_str = ', '.join(map(lambda k, v: f'{k}={v}',
                                                   kwargs.items()))
                        argument_info += ' and ' if args else ' with '
                        argument_info += f'kwargs {kwargs_str}'

                    debug_str += argument_info
                LOG.debug(debug_str)

                try:
                    return func(self, *args, **kwargs)
                except Exception as e:
                    error_str = (f'{func.__name__} failed for {self.vbmc_type}'
                                 ' {self.name}')
                    if args or kwargs:
                        error_str += argument_info
                    error_str += f'\nError: {str(e)}'
                    LOG.error(error_str)

                    if fail_ok:
                        return constants.IPMI_COMMAND_NODE_BUSY
                    else:
                        raise exception.VirtualBMCError(message=error_str)
            return wrapper
        # (szuk) this makes it so the decorator syntax "works" with arguments.
        return decorator if len(args) == 0 else decorator(args[0])
