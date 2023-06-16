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

from oslo_config import cfg

from virtualbmc.conf import CONF


default_opts = {
    'name': cfg.StrOpt(
        'name',
        # positional=True,
        default=None,
        help='The name of this vBMC.'
    ),
    'bmc_type': cfg.StrOpt(
        'bmc-type',
        default=None,
        choices=('libvirt', 'ironic'),
        # positional=True,
        help='The service the vBMC will communicate with',
    ),
    'enabled': cfg.BoolOpt(
        'enabled',
        default=False,
        help='Determines if this should be activated by the vbmcd daemon',
    ),
    'host_ip': cfg.HostAddressOpt(
        'host-ip',
        default='127.0.0.1',
        help='The IP address or hostname on which this vBMC should listen',
    ),
    'port': cfg.PortOpt(
        'port',
        default=1623,
        help='The port on which the vBMC should listen',
    ),
    'username': cfg.StrOpt(
        'username',
        default='admin',
        help='The username to expect from an IPMI client',
    ),
    'password': cfg.StrOpt(
        'password',
        default='password',
        secret=CONF['show_passwords'],
        help='The password to expect from an IPMI client',
    ),
}

_cli_opts = ['name', 'bmc_type', 'host_ip', 'port', 'username', 'password']


def register_opts(conf):
    conf.register_cli_opts(
        [ default_opts[opt_name] for opt_name in _cli_opts ]
    )
    conf.register_opts(default_opts.values())
