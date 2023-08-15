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
from unittest import mock

from virtualbmc import exception
from virtualbmc.tests.unit import base
from virtualbmc.vbmc import constants
from virtualbmc.vbmc import libvirt as vbmc_libvirt


DOMAIN_XML_TEMPLATE = """\
<domain type='qemu'>
  <os>
    <type arch='x86_64' machine='pc-1.0'>hvm</type>
    <boot dev='%s'/>
    <bootmenu enable='no'/>
    <bios useserial='yes'/>
  </os>
  <devices>
    <disk type='block' device='disk'>
      <boot order='2'/>
    </disk>
    <interface type='network'>
      <boot order='1'/>
    </interface>
  </devices>
</domain>
"""


class LibvirtVirtualBMCTestCase(base.TestCase):
    def setUp(self):
        super().setUp()
        bmc_init_patcher = mock.patch('pyghmi.ipmi.bmc.Bmc.__init__')
        bmc_init_patcher.start()
        self.addCleanup(bmc_init_patcher.stop)

        connection_patcher = mock.patch('virtualbmc.utils.libvirt_open')
        self.mock_connection_manager = connection_patcher.start()
        self.addCleanup(connection_patcher.stop)
        self.mock_connection = (
            self.mock_connection_manager.return_value.__enter__())

        get_domain_patcher = mock.patch('virtualbmc.utils.get_libvirt_domain')
        self.mock_get_domain = get_domain_patcher.start()
        self.addCleanup(get_domain_patcher.stop)

        self.uri = 'qemu:///system'
        self.domain_name = 'test_domain'
        self.sasl_username = 'admin'
        self.sasl_password = 'password'

        self.vbmc = vbmc_libvirt.LibvirtVbmc(
            'foobar', 'foo', 'bar', '0.0.0.0', 623,
            self.uri, self.domain_name, 'admin', 'password'
        )

    def assert_connection_args(self, readonly=False):
        kwargs = {'uri': self.uri, 'sasl_username': self.sasl_username,
                  'sasl_password': self.sasl_password}
        if readonly:
            kwargs['readonly'] = True

        self.mock_connection_manager.assert_called_once_with(**kwargs)
        self.mock_get_domain.assert_called_once_with(
            mock.ANY, self.domain_name)

    @staticmethod
    def power_test(*args, domain_active=None):
        def decorator(func):
            @wraps(func)
            def wrapper(self, *args, **kwargs):
                mock_domain = self.mock_get_domain.return_value
                mock_domain.isActive.return_value = domain_active

                func(self, mock_domain, *args, **kwargs)

                self.assert_connection_args()
            return wrapper
        return decorator if not args else decorator(args[0])

    def test_get_boot_device(self):
        # additionally, check that an invalid device returns 0
        GET_BOOT_DEVICES_MAP = dict(vbmc_libvirt.GET_BOOT_DEVICES_MAP, trash=0)
        mock_domain_xml = self.mock_get_domain.return_value.XMLDesc

        for dev_libvirt, dev_ipmi in GET_BOOT_DEVICES_MAP.items():
            mock_domain_xml.return_value = DOMAIN_XML_TEMPLATE % dev_libvirt

            self.assertEqual(self.vbmc.get_boot_device(), dev_ipmi)
            self.assert_connection_args(readonly=True)

            self.mock_connection_manager.reset_mock()
            self.mock_get_domain.reset_mock()

    def test_set_boot_device(self):
        self.mock_get_domain.return_value.XMLDesc.return_value = (
            DOMAIN_XML_TEMPLATE % 'nonsense')

        for dev_ipmi, dev_libvirt in vbmc_libvirt.SET_BOOT_DEVICES_MAP.items():
            self.assertEqual(self.vbmc.set_boot_device(dev_ipmi), None)
            self.assert_connection_args()

            new_domain_xml = str(self.mock_connection.defineXML.call_args)
            self.assertIn(f'<boot dev="{dev_libvirt}" />', new_domain_xml)
            self.assertEqual(1, new_domain_xml.count('<boot '))

            self.mock_connection_manager.reset_mock()
            self.mock_get_domain.reset_mock()

    def test_set_boot_device_invalid(self):
        self.assertEqual(self.vbmc.set_boot_device('whatever'),
                         constants.IPMI_INVALID_DATA)
        self.mock_connection_manager.assert_not_called()
        self.mock_get_domain.assert_not_called()

    def test_get_power_state_domain_active(self):
        self.mock_get_domain.return_value.isActive.return_value = True
        self.assertEqual(self.vbmc.get_power_state(), constants.POWERON)
        self.assert_connection_args(readonly=True)

    def test_get_power_state_domain_inactive(self):
        self.mock_get_domain.return_value.isActive.return_value = False
        self.assertEqual(self.vbmc.get_power_state(), constants.POWEROFF)
        self.assert_connection_args(readonly=True)

    def test_get_power_state_error(self):
        self.mock_get_domain.side_effect = Exception('oops!')
        self.assertRaises(exception.VirtualBMCError, self.vbmc.get_power_state)
        self.assert_connection_args(readonly=True)

    @power_test(domain_active=True)
    def test_pulse_diag_domain_active(self, mock_domain):
        self.assertEqual(self.vbmc.pulse_diag(), None)
        mock_domain.injectNMI.assert_called_once_with()

    @power_test(domain_active=False)
    def test_pulse_diag_domain_inactive(self, mock_domain):
        self.assertEqual(self.vbmc.pulse_diag(), None)
        mock_domain.injectNMI.assert_not_called()

    @power_test(domain_active=True)
    def test_power_off_domain_active(self, mock_domain):
        self.assertEqual(self.vbmc.power_off(), None)
        mock_domain.destroy.assert_called_once_with()

    @power_test(domain_active=False)
    def test_power_off_domain_inactive(self, mock_domain):
        self.assertEqual(self.vbmc.power_off(), None)
        mock_domain.destroy.assert_not_called()

    @power_test(domain_active=True)
    def test_power_on_domain_active(self, mock_domain):
        self.assertEqual(self.vbmc.power_on(), None)
        mock_domain.create.assert_not_called()

    @power_test(domain_active=False)
    def test_power_on_domain_inactive(self, mock_domain):
        self.assertEqual(self.vbmc.power_on(), None)
        mock_domain.create.assert_called_once_with()

    @power_test(domain_active=True)
    def test_power_shutdown_domain_active(self, mock_domain):
        self.assertEqual(self.vbmc.power_shutdown(), None)
        mock_domain.shutdown.assert_called_once_with()

    @power_test(domain_active=False)
    def test_power_shutdown_domain_inactive(self, mock_domain):
        self.assertEqual(self.vbmc.power_shutdown(), None)
        mock_domain.shutdown.assert_not_called()

    @power_test(domain_active=True)
    def test_power_reset_domain_active(self, mock_domain):
        self.assertEqual(self.vbmc.power_reset(), None)
        mock_domain.reset.assert_called_once_with()

    @power_test(domain_active=False)
    def test_power_reset_domain_inactive(self, mock_domain):
        self.assertEqual(self.vbmc.power_on(), None)
        mock_domain.reset.assert_not_called()
