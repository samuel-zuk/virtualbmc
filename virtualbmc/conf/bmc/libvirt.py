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


libvirt_opts = [
    cfg.StrOpt(
        'uri',
        default='qemu:///system',
        help='The libvirt connection URI to use',
    ),
    cfg.StrOpt(
        'domain-name',
        default=None,
        help='The name of the libvirt domain/virtual machine to control. '
             'Defaults to the same name as the BMC',
    ),
    cfg.StrOpt(
        'sasl-username',
        default=None,
        help='The libvirt SASL username to use',
    ),
    cfg.StrOpt(
        'sasl-password',
        default=None,
        help='The libvirt SASL password to use',
    ),
]


def register_opts(conf):
    conf.register_cli_opts(libvirt_opts, group='libvirt')
    conf.register_opts(libvirt_opts, group='libvirt')
