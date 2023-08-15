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

from virtualbmc import conf as config
from virtualbmc.tests.unit import base


class ApplicationConfigTestCase(base.TestCase):
    def setUp(self):
        super().setUp()
        self.CONF = config.CONF

    def test_defaults(self):
        default_values = {
            'enable_libvirt': True,
            'enable_ironic': True,
            'show_passwords': False,
            'pid_file': 'master.pid',
            'server_port': 50891,
            'host_ip': '127.0.0.1',
            'server_response_timeout': 5000,
            'server_spawn_wait': 3000,
        }
        for opt, value in default_values.items():
            self.assertEqual(self.CONF[opt], value)

    def test_ipmi_defaults(self):
        ipmi_defaults = {'session_timeout': 1}
        for opt, value in ipmi_defaults.items():
            self.assertEqual(self.CONF['ipmi'][opt], value)

    def test_log_defaults(self):
        log_defaults = {
            'logfile': None,
            'level': 'INFO',
            'use_stderr': True,
        }

        for opt, value in log_defaults.items():
            self.assertEqual(self.CONF['log'][opt], value)

    def test_formatter_defaults(self):
        formatter_defaults = {
            'wrap_width': 79,
            'minimal': True,
            'summarize': False,
            'format': 'ini',
        }

        for opt, value in formatter_defaults.items():
            self.assertEqual(self.CONF['formatter'][opt], value)
