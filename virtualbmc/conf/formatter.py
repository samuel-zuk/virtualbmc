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

# largely taken from:
# https://opendev.org/openstack/oslo.config/src/branch/master/oslo_config/generator.py

formatter_opts = [
    cfg.StrOpt(
        'output_file',
        help='Path of the file to write to.',
    ),
    cfg.IntOpt(
        'wrap_width',
        default=79,
        min=0,
        help='The maximum length of help lines',
    ),
    cfg.BoolOpt(
        'minimal',
        default=True,
        help='Generate a minimal required configuration',
    ),
    cfg.BoolOpt(
        'summarize',
        default=False,
        help='Only output summaries of help text to config files',
    ),
    cfg.StrOpt(
        'format',
        help='Desired format for the output.',
        default='ini',
        choices=(
            ('ini', 'The only format that can be used directly with '
             'oslo.config.'),
            ('json', 'Intended for third-party tools that want to write '
             'config files based on the sample config data.'),
            ('yaml', 'Same as json'),
            ('rst', 'Can be used to dump the text given to Sphinx when '
             'building documentation using the Sphinx extension. '
             'Useful for debugging,')
        ),
    ),
]


def register_opts(conf):
    conf.register_opts(formatter_opts, group='formatter')
