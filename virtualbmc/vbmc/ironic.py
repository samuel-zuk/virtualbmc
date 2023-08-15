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

import openstack

from virtualbmc import log
from virtualbmc.vbmc import base
from virtualbmc.vbmc import constants

LOG = log.get_logger()

GET_BOOT_DEVICES_MAP = {
    'pxe': 4,
    'disk': 8,
    'cdrom': 0x14,
}

SET_BOOT_DEVICES_MAP = {
    'network': 'pxe',
    'hd': 'disk',
    'optical': 'cdrom',
}


class IronicVbmc(base.VbmcBase):
    bmc_cmd = base.VbmcBase.bmc_cmd
    vbmc_type = 'ironic node'

    def __init__(self, name, username, password, host_ip, port,
                 node_uuid, cloud, region, **kwargs):
        super().__init__(name, username, password, host_ip, port)
        self.node_uuid = node_uuid
        self._conn_args = {'cloud': cloud, 'region': region}

    @bmc_cmd
    def get_boot_device(self):
        with openstack.connect(**self._conn_args) as conn:
            device = conn.baremetal.get_node_boot_device(self.node_uuid)
            return GET_BOOT_DEVICES_MAP.get(device.get('boot_device', None), 0)

    @bmc_cmd
    def set_boot_device(self, bootdevice):
        device = SET_BOOT_DEVICES_MAP.get(bootdevice)
        if device is None:
            # Invalid data field in request
            return constants.IPMI_INVALID_DATA

        with openstack.connect(**self._conn_args) as conn:
            conn.baremetal.set_node_boot_device(self.node_uuid, device)

    @bmc_cmd(fail_ok=False)
    def get_power_state(self):
        with openstack.connect(**self._conn_args) as conn:
            node = conn.baremetal.find_node(self.node_uuid)
            if node.power_state == 'power on':
                return constants.POWERON
            else:
                return constants.POWEROFF

    @bmc_cmd
    def pulse_diag(self):
        return constants.IPMI_COMMAND_NODE_BUSY

    @bmc_cmd
    def power_off(self):
        with openstack.connect(**self._conn_args) as conn:
            conn.baremetal.set_node_power_state(self.node_uuid, 'power off')

    @bmc_cmd
    def power_on(self):
        with openstack.connect(**self._conn_args) as conn:
            conn.baremetal.set_node_power_state(self.node_uuid, 'power on')

    @bmc_cmd
    def power_shutdown(self):
        with openstack.connect(**self._conn_args) as conn:
            conn.baremetal.set_node_power_state(self.node_uuid, 'power off')

    @bmc_cmd
    def power_reset(self):
        with openstack.connect(**self._conn_args) as conn:
            conn.baremetal.set_node_power_state(self.node_uuid, 'rebooting')
