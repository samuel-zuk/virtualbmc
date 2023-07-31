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


default_opts = [
    cfg.BoolOpt(
        'enable_libvirt',
        default=True,
        help='Set to enable creating vBMCs for libvirt domains'),
    cfg.BoolOpt(
        'enable_ironic',
        default=True,
        help='Set to enable creating vBMCs for Ironic nodes'),
    cfg.BoolOpt(
        'show_passwords',
        default=False,
        help='Password values will be obfuscated (e.g. replaced with "***") '
             'in logs if False and output normally if True'),
    cfg.StrOpt(
        'pid_file',
        default='master.pid',
        help='Path to the pid file of the vBMC server. Will be created in the '
             'config directory if not otherwise specified.'),
    cfg.HostAddressOpt(
        'host_ip',
        default='127.0.0.1',
        help='The IP address or hostname on which the vBMC server listens'),
    cfg.PortOpt(
        'server_port',
        default=50891,
        help='The TCP port on which the vBMC server listens'),
    cfg.IntOpt(
        'server_response_timeout',
        default=5000,
        help='<FIXME> (time in ms)'),
    cfg.IntOpt(
        'server_spawn_wait',
        default=3000,
        help='<FIXME> (time in ms)'),
]


def register_opts(conf):
    conf.register_opts(default_opts)
