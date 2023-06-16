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


ironic_opts = [
    cfg.StrOpt(
        'node-uuid',
        default=None,
        help='The UUID of the Ironic node',
    ),
    cfg.StrOpt(
        'cloud',
        default='overcloud',
        help='The name of the OpenStack cloud to connect to',
    ),
    cfg.StrOpt(
        'region',
        default='regionOne',
        help='The OpenStack identity region of this node',
    ),
]


def register_opts(conf):
    conf.register_cli_opts(ironic_opts, group='ironic')
    conf.register_opts(ironic_opts, group='ironic')
