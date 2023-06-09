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

import xml.etree.ElementTree as ET

import libvirt

from virtualbmc import log
from virtualbmc import utils
from virtualbmc.vbmc import base
from virtualbmc.vbmc import constants

LOG = log.get_logger()


class LibvirtVbmc(base.VbmcBase):

    vbmc_type = 'libvirt domain'

    def __init__(self, name, username, password, host_address, port,
                 libvirt_uri, libvirt_sasl_username=None,
                 libvirt_sasl_password=None, **kwargs):
        super().__init__(address, port, ident, password, name)
        self._conn_args = {'uri': libvirt_uri,
                           'sasl_username': libvirt_sasl_username,
                           'sasl_password': libvirt_sasl_password}

    # Copied from nova/virt/libvirt/guest.py
    def get_xml_desc(self, domain, dump_sensitive=False):
        """Returns xml description of guest.

        :param domain: The libvirt domain to call
        :param dump_sensitive: Dump security sensitive information
        :returns string: XML description of the guest
        """
        flags = dump_sensitive and libvirt.VIR_DOMAIN_XML_SECURE or 0
        return domain.XMLDesc(flags=flags)

    def _remove_boot_elements(self, parent_element):
        for boot_element in parent_element.findall('boot'):
            parent_element.remove(boot_element)

    @base.VbmcBase.bmc_cmd
    def get_boot_device(self):
        with utils.libvirt_open(readonly=True, **self._conn_args) as conn:
            domain = utils.get_libvirt_domain(conn, self.name)
            boot_element = ET.fromstring(domain.XMLDesc()).find('.//os/boot')
            boot_dev = None
            if boot_element is not None:
                boot_dev = boot_element.attrib.get('dev')
        return constants.GET_BOOT_DEVICES_MAP.get(boot_dev, 0)

    @base.VbmcBase.bmc_cmd
    def set_boot_device(self, bootdevice):
        device = constants.SET_BOOT_DEVICES_MAP.get(bootdevice)
        if device is None:
            # Invalid data field in request
            return constants.IPMI_INVALID_DATA

        with utils.libvirt_open(**self._conn_args) as conn:
            domain = utils.get_libvirt_domain(conn, self.name)
            tree = ET.fromstring(
                self.get_xml_desc(domain, dump_sensitive=True))

            # Remove all "boot" element under "devices"
            # They are mutually exclusive with "os/boot"
            for device_element in tree.findall('devices/*'):
                self._remove_boot_elements(device_element)

            for os_element in tree.findall('os'):
                # Remove all "boot" elements under "os"
                self._remove_boot_elements(os_element)

                # Add a new boot element with the request boot device
                boot_element = ET.SubElement(os_element, 'boot')
                boot_element.set('dev', device)

            conn.defineXML(ET.tostring(tree, encoding="unicode"))

    @base.VbmcBase.bmc_cmd(fail_ok=False)
    def get_power_state(self):
        with utils.libvirt_open(readonly=True, **self._conn_args) as conn:
            domain = utils.get_libvirt_domain(conn, self.name)
            if domain.isActive():
                return constants.POWERON
            else:
                return constants.POWEROFF

    @base.VbmcBase.bmc_cmd
    def pulse_diag(self):
        with utils.libvirt_open(**self._conn_args) as conn:
            domain = utils.get_libvirt_domain(conn, self.name)
            if domain.isActive():
                domain.injectNMI()

    @base.VbmcBase.bmc_cmd
    def power_off(self):
        with utils.libvirt_open(**self._conn_args) as conn:
            domain = utils.get_libvirt_domain(conn, self.name)
            if domain.isActive():
                domain.destroy()

    @base.VbmcBase.bmc_cmd
    def power_on(self):
        with utils.libvirt_open(**self._conn_args) as conn:
            domain = utils.get_libvirt_domain(conn, self.name)
            if not domain.isActive():
                domain.create()

    @base.VbmcBase.bmc_cmd
    def power_shutdown(self):
        with utils.libvirt_open(**self._conn_args) as conn:
            domain = utils.get_libvirt_domain(conn, self.name)
            if domain.isActive():
                domain.shutdown()

    @base.VbmcBase.bmc_cmd
    def power_reset(self):
        with utils.libvirt_open(**self._conn_args) as conn:
            domain = utils.get_libvirt_domain(conn, self.name)
            if domain.isActive():
                domain.reset()
