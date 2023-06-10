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

import os

from oslo_config import cfg


default_opts = [
    cfg.BoolOpt('enable_libvirt', default=True),
    cfg.BoolOpt('enable_ironic', default=True),
    cfg.BoolOpt('show_passwords', default=False),
    cfg.StrOpt(
        'config_dir',
        default=os.path.join(os.path.expanduser('~'), '.vbmc')
    ),
    cfg.StrOpt(
        'pid_file',
        default=os.path.join(os.path.expanduser('~'), '.vbmc', 'master.pid')
    ),
    cfg.PortOpt('server_port', default=50891),
    cfg.IntOpt('server_response_timeout', default=10000, help='(value in ms)'),
    cfg.IntOpt('server_spawn_wait', default=3000, help='(value in ms)'),
]

log_opts = [
    cfg.StrOpt('logfile', default=None),
    cfg.StrOpt('level', default='DEBUG',
               choices=('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')),
    cfg.BoolOpt('use_stderr', default=True),
]

ipmi_opts = [
    cfg.IntOpt(
        'session_timeout',
        default=1,
        help='Maximum time (in seconds) to wait for the data to come across'
    ),
]


def register_opts(conf):
    conf.register_opts(default_opts)
    conf.register_opts(log_opts, group='log')
    conf.register_opts(ipmi_opts, group='ipmi')
