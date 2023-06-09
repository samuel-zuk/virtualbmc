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
import shutil

from virtualbmc.conf import bmc as cfg
from virtualbmc.conf import CONF
from virtualbmc import exception
from virtualbmc import log
from virtualbmc import utils
from virtualbmc import vbmc

LOG = log.get_logger()

# BMC status
RUNNING = 'running'
DOWN = 'down'
ERROR = 'error'


class VirtualBMCManager(object):
    def __init__(self):
        self.config_dir = CONF['default']['config_dir']
        self._running_instances = {}

    def _bmc_exists(self, name):
        bmc_config_dir = os.path.join(self.config_dir, name)
        return (
            os.path.isdir(bmc_config_dir)
            and os.path.isfile(os.path.join(bmc_config_dir, 'vbmc.conf'))
        )

    def sync_vbmc_states(self, shutdown=False):
        def vbmc_runner(bmc_config):
            # The manager process installs a signal handler for SIGTERM to
            # propagate it to children. Return to the default handler.
            signal.signal(signal.SIGTERM, signal.SIG_DFL)

            try:
                if bmc_config['bmc_type'] == 'libvirt':
                    bmc = vbmc.libvirt.LibvirtVbmc(**bmc_config)
                else:
                    bmc = vbmc.base.VbmcBase(**bmc_config)
                bmc.listen(timeout=CONF['ipmi']['session_timeout'])
            except Exception as e:
                LOG.exception(
                    'Error running %(typ)s vBMC %(name)s: %(err)s\n'
                    'With config:' % {'typ': bmc_config['bmc_type'],
                                      'name': bmc_config['name'],
                                      'err': str(e)}
                )
                bmc_config.log_opt_values(LOG, logging.EXCEPTION)

        for name in os.listdir(self.config_dir):
            if not self._bmc_exists(name):
                continue

            bmc_config = cfg.BMCConfig(name, self.config_dir).CONF
            bmc_type = bmc_config['bmc_type']
            should_enable = False if shutdown else bmc_config['enabled']
            instance = self._running_instances.get(name)

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

    def add_libvirt(self, name, domain_name, bmc_username, bmc_password,
                    address, port, libvirt_uri, sasl_username, sasl_password):
        if os.path.exists(os.path.join(os.path.config_dir, name)):
            msg = f'Error creating vBMC {name}: config dir already exists'
            LOG.error(msg)
            return 1, msg

        utils.check_libvirt_connection_and_domain(
            libvirt_uri, domain_name, sasl_username, sasl_password)

        try:
            cfg.BMCConfig(bmc_type='libvirt',
                          name=name,
                          conf_dir=self.config_dir,
                          enabled=enabled,
                          host_address=host_address,
                          port=port,
                          username=bmc_username,
                          password=bmc_password,
                          domain_name=domain_name,
                          libvirt_uri=libvirt_uri,
                          sasl_username=sasl_username,
                          sasl_password=sasl_passsword)
            cfg.write()
        except Exception as ex:
            self.delete(name)
            msg = f'Error creating vBMC {name}: {str(ex)}'
            LOG.error(msg)
            return 1, msg

        return 0, ''

    def delete(self, name):
        if not self._bmc_exists(name):
            raise exception.NotFound(name=name)

        try:
            self.stop(name)
        except exception.VirtualBMCError:
            pass

        shutil.rmtree(os.path.join(self.config_dir, name))

        return 0, ''

    def start(self, name):
        if not self._bmc_exists(name):
            raise exception.NotFound(name=name)

        bmc_config = cfg.BMCConfig(name, self.config_dir)

        if name in self._running_instances:
            self.sync_vbmc_states()
            if name in self._running_instances:
                LOG.warning(f'BMC instance {name} already running, ignoring '
                            '"start" command')
                return 0, ''
        
        try:
            if not bmc_config.CONF.get('enabled', None):
                bmc_config.set('enabled', True)
                bmc_config.write()
        except Exception as ex:
            msg = ('Error running %(typ)s vBMC %(name)s: %(err)s\n' %
                   {'typ': bmc_config['bmc_type'], 'name': name, 'err': ex})
            LOG.exception(msg)
            return 1, msg

        self.sync_vbmc_states()
        return 0, ''

    def stop(self, name):
        if not self._bmc_exists(name):
            raise exception.NotFound(name=name)

        bmc_config = cfg.BMCConfig(name, self.config_dir)

        try:
            if bmc_config.CONF.get('enabled', None):
                bmc_config.set('enabled', False)
                bmc_config.write()
        except Exception as ex:
            msg = ('Error stopping %(typ)s vBMC %(name)s: %(err)s\n' %
                   {'typ': bmc_config['bmc_type'], 'name': name, 'err': ex})
            LOG.exception(msg)
            return 1, msg

        self.sync_vbmc_states()
        return 0, ''
        
    def list(self):
        rc = 0
        tables = []
        try:
            for name in os.listdir(self.config_dir):
                if _bmc_exists(name):
                    tables.append(self._get_as_dict(name))
        except OSError as ex:
            if ex.errno == errno.EEXIST:
                rc = 1

        return rc, tables

    def _get_as_dict(self, name):
        bmc_config = cfg.BMCConfig(name, self.config_dir)
        show_options = bmc_config.as_dict()
        
        instance = self._running_instances.get(name)

        if instance and instance.is_alive():
            show_options['status'] = RUNNING
        elif instance and not instance.is_alive():
            show_options['status'] = ERROR
        else:
            show_options['status'] = DOWN

        return show_options

    def show(self, name):
        return 0, list(self._get_as_dict(name).items())
