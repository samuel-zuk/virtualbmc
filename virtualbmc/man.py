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
import multiprocessing
import os
import signal

from virtualbmc.cfg import bmc as bmc_cfg
from virtualbmc.cfg import CONF
from virtualbmc import exception
from virtualbmc import log
from virtualbmc import utils
from virtualbmc import vbmc

LOG = log.get_logger()

RUNNING = 'running'
DOWN = 'down'
ERROR = 'error'

DEFAULT_SECTION = 'VirtualBMC'


class VirtualBMCManager(object):
    def __init__(self):
        self.config_dir = CONF['default']['config_dir']
        self._running_instances = {}

    def _read_bmc_config(self, name):
        config_path = os.path.join(self.config_dir, name, 'config')
        if not os.path.exists(config_path):
            raise exception.NotFound(name=name)

    def sync_vbmc_states(self, shutdown=False):
        def vbmc_runner(bmc_config):
            # The manager process installs a signal handler for SIGTERM to
            # propagate it to children. Return to the default handler.
            signal.signal(signal.SIGTERM, signal.SIG_DFL)

            try:
                bmc = vbmc.libvirt.LibvirtVbmc(**bmc_config)
            except Exception as e:
                LOG.exception(f'Error running vBMC: {str(e)}\nWith config:')
                bmc_config.log_opt_values(LOG, logging.EXCEPTION)
                return

            try:
                bmc.listen(timeout=CONF['ipmi']['session_timeout'])
            except Exception as e:
                LOG.exception(
                    'Error listening on %(typ)s vBMC %(name)s: %(err)s',
                    {'typ': bmc_config['bmc_type'],
                     'name': bmc_config['name'],
                     'err': str(e)}
                )
                return

        for name in os.listdir(self.config_dir):
            if not os.path.isdir(os.path.join(self.config_dir, name)):
                continue

            try:
                bmc_config = bmc_cfg.read_config(name, self.config_dir)
            except exception.NotFound:
                continue

            bmc_type = bmc_config['bmc_type']
            should_enable = False if shutdown else bmc_config['enabled']
            instance = self._running_bmcs.get(name)

            if should_enable:
                if not instance or not instance.is_alive():
                    instance = multiprocessing.Process(
                        name=f'vbmcd-managing-{bmc_type}-{name}',
                        target=vbmc_runner,
                        args=(bmc_config,)
                    )
                    instance.daemon = True
                    instance.start()
                    self._running_instances[name] = instance
                    LOG.info(f'Started {bmc_type} vBMC instance {name}')

                if not instance.is_alive():
                    LOG.debug(f'Found dead {bmc_type} vBMC instance {name} '
                              f'(rc: {instance.exitcode})')
            else:
                if instance and instance.is_alive():
                    instance.terminate()
                    LOG.info(f'Terminated {bmc_type} instance {name}')
                    self._running_instances.pop(name, None)

    def periodic(self, shutdown=False):
        self.sync_vbmc_states(shutdown)

    def add(self, bmc_type, name, username, password, address, port):
        path = os.path.join(self.config_dir, name)

        try:
            os.makedirs(path)
        except OSError as ex:
            # path already exists
            if ex.errno == errno.EEXIST:
                return 1, str(ex)
            else:
                msg = (f'Failed to create {bmc_type} vBMC {name}. '
                       f'Error: {str(ex)}')
                LOG.error(msg)
                return 1, msg

    def add_libvirt(self, domain_name, username, password, address, port,
                    libvirt_uri, sasl_username, sasl_password):
        utils.check_libvirt_connection_and_domain(libvirt_uri, domain_name,
                                                  sasl_username, sasl_password)
