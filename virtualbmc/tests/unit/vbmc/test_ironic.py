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

from unittest import mock
import uuid

from virtualbmc import exception
from virtualbmc.tests.unit import base
from virtualbmc.vbmc import constants
from virtualbmc.vbmc import ironic as vbmc_ironic


class IronicVirtualBMCTestCase(base.TestCase):
    def setUp(self):
        super().setUp()
        bmc_init_patcher = mock.patch('pyghmi.ipmi.bmc.Bmc.__init__')
        bmc_init_patcher.start()
        self.addCleanup(bmc_init_patcher.stop)

        connection_patcher = mock.patch('openstack.connect')
        self.mock_connection = connection_patcher.start()
        self.addCleanup(connection_patcher.stop)
        self.mock_baremetal = (
            self.mock_connection.return_value.__enter__().baremetal)

        self.node_uuid = str(uuid.uuid4())
        self.cloud = 'test_cloud'
        self.region = 'RegionOne'
        self.vbmc = vbmc_ironic.IronicVbmc(
            'foobar', 'foo', 'bar', '0.0.0.0', 623,
            self.node_uuid, self.cloud, self.region
        )

    def assert_connection_args(self):
        self.mock_connection.assert_called_once_with(
            cloud=self.cloud, region=self.region
        )

    def test_get_boot_device(self):
        mock_get_boot_device = self.mock_baremetal.get_node_boot_device
        # additionally, check that an invalid device returns 0
        GET_BOOT_DEVICES_MAP = dict(vbmc_ironic.GET_BOOT_DEVICES_MAP, foobar=0)

        for dev_ironic, dev_ipmi in GET_BOOT_DEVICES_MAP.items():
            mock_get_boot_device.return_value = {'boot_device': dev_ironic}

            self.assertEqual(self.vbmc.get_boot_device(), dev_ipmi)
            self.assert_connection_args()
            mock_get_boot_device.assert_called_once_with(self.node_uuid)

            self.mock_connection.reset_mock()

    def test_set_boot_device(self):
        mock_set_boot_device = self.mock_baremetal.set_node_boot_device
        for dev_ipmi, dev_ironic in vbmc_ironic.SET_BOOT_DEVICES_MAP.items():
            self.assertEqual(self.vbmc.set_boot_device(dev_ipmi), None)
            self.assert_connection_args()
            mock_set_boot_device.assert_called_once_with(
                self.node_uuid, dev_ironic)

            self.mock_connection.reset_mock()

    def test_set_boot_device_error(self):
        self.assertEqual(self.vbmc.set_boot_device('i dunno'),
                         constants.IPMI_INVALID_DATA)
        self.mock_connection.assert_not_called()
        self.mock_baremetal.assert_not_called()

    def test_get_power_state_on(self):
        mock_find_node = self.mock_baremetal.find_node
        mock_find_node.return_value.power_state = 'power on'

        self.assertEqual(self.vbmc.get_power_state(), constants.POWERON)
        self.assert_connection_args()
        mock_find_node.assert_called_once_with(self.node_uuid)

    def test_get_power_state_off(self):
        mock_find_node = self.mock_baremetal.find_node
        mock_find_node.return_value.power_state = 'power off'

        self.assertEqual(self.vbmc.get_power_state(), constants.POWEROFF)
        self.assert_connection_args()
        mock_find_node.assert_called_once_with(self.node_uuid)

    def test_get_power_state_error(self):
        self.mock_baremetal.find_node.side_effect = Exception('oops!')
        self.assertRaises(exception.VirtualBMCError, self.vbmc.get_power_state)
        self.assert_connection_args()

    def test_pulse_diag(self):
        self.assertEqual(self.vbmc.pulse_diag(),
                         constants.IPMI_COMMAND_NODE_BUSY)

    def test_power_off(self):
        self.assertEqual(self.vbmc.power_off(), None)
        self.assert_connection_args()
        self.mock_baremetal.set_node_power_state.assert_called_once_with(
            self.node_uuid, 'power off')

    def test_power_on(self):
        self.assertEqual(self.vbmc.power_on(), None)
        self.assert_connection_args()
        self.mock_baremetal.set_node_power_state.assert_called_once_with(
            self.node_uuid, 'power on')

    def test_power_shutdown(self):
        self.assertEqual(self.vbmc.power_shutdown(), None)
        self.assert_connection_args()
        self.mock_baremetal.set_node_power_state.assert_called_once_with(
            self.node_uuid, 'power off')

    def test_power_reset(self):
        self.assertEqual(self.vbmc.power_reset(), None)
        self.assert_connection_args()
        self.mock_baremetal.set_node_power_state.assert_called_once_with(
            self.node_uuid, 'rebooting')
