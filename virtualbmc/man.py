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

import signal

from virtualbmc import config as vbmc_config
from virtualbmc import log
from virtualbmc import vbmc

LOG = log.get_logger()

RUNNING = 'running'
DOWN = 'down'
ERROR = 'error'

DEFAULT_SECTION = 'VirtualBMC'

CONF = vbmc_config.get_config()


class VirtualBMCManager(object):
    def __init__(self):
        self.config_dir = CONF['default']['config_dir']
        self._running_domains = {}

    @staticmethod
    def censor_passwords(dictionary, secret='***'):
        """Replaces passwords in a dictionary with a placeholder value."""
        return {key: (secret if 'password' in key else val)
                for key, val in dictionary}

    def sync_vbmc_states(self, shutdown=False):
        def vbmc_runner(bmc_config):
            # The manager process installs a signal handler for SIGTERM to
            # propagate it to children. Return to the default handler.
            signal.signal(signal.SIGTERM, signal.SIG_DFL)

            show_passwords = CONF['default']['show_passwords']

            show_options = (bmc_config if show_passwords else
                            self.censor_passwords(bmc_config))
            print(bmc_config)

    def periodic(self, shutdown=False):
        self.sync_vbmc_states(shutdown)
