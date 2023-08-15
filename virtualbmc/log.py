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

import errno
import logging
import sys

from virtualbmc.conf import CONF

__all__ = ['get_logger']

DEFAULT_LOG_FORMAT = ('%(asctime)s %(process)d %(levelname)s '
                      '%(name)s [-] %(message)s')
LOGGER = None


class VirtualBMCLogger(logging.Logger):

    def __init__(self, level=logging.INFO, logfile=None, use_stderr=False):
        super().__init__('VirtualBMC')
        try:
            self.formatter = logging.Formatter(DEFAULT_LOG_FORMAT)
            self.handlers = []
            if logfile is not None:
                self.handlers.append(logging.FileHandler(logfile))
            if use_stderr:
                self.handlers.append(logging.StreamHandler(sys.stderr))
            if len(self.handlers) == 0:
                self.handlers.append(logging.NullHandler())

            for handler in self.handlers:
                handler.setFormatter(self.formatter)
                self.addHandler(handler)

            self.setLevel(getattr(logging, level))
        except IOError as e:
            if e.errno == errno.EACCES:
                pass


def get_logger():
    global LOGGER
    if LOGGER is None:
        log_conf = CONF['log']
        LOGGER = VirtualBMCLogger(level=log_conf['level'],
                                  logfile=log_conf['logfile'],
                                  use_stderr=log_conf['use_stderr'])

    return LOGGER
