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

from importlib import reload as importlib_reload
from io import StringIO
import os.path
from unittest import mock

from oslo_config import cfg as oslo_cfg

from virtualbmc.conf import bmc as bmc_conf
from virtualbmc import exception
from virtualbmc.tests.unit import base
from virtualbmc.tests.unit import utils


class BMCConfigTestCase(base.TestCase):
    _MOCK_CONFIG_PATH = '/path/to/config'

    def setUp(self):
        super().setUp()
        mock_conf = {
            'show_passwords': False,
            'config_dir': [self._MOCK_CONFIG_PATH],
            'formatter': type('', (object,), {
                'output_file': self._MOCK_CONFIG_PATH,
                'wrap_width': 79,
                'minimal': True,
                'summarize': False,
                'format': 'ini',
            })
        }
        app_conf_patcher = mock.patch('virtualbmc.conf.CONF', mock_conf)
        app_conf_patcher.start()
        self.addCleanup(app_conf_patcher.stop)
        importlib_reload(bmc_conf.base)

        self.CONF = bmc_conf.BMCConfig()
        self.default_values = {
            'name': None,
            'bmc_type': None,
            'enabled': False,
            'host_ip': '127.0.0.1',
            'port': 1623,
            'username': 'admin',
            'password': 'password',
        }

    @staticmethod
    def _mk_test_config(bmc_type, name):
        return ('[DEFAULT]\n'
                f'name={name}\n'
                f'bmc_type={bmc_type}\n'
                'enabled=false\n'
                'host_ip=127.0.0.1\n'
                'port=1623\n'
                'username=admin\n'
                'password=password')

    def test_defaults(self):
        for opt, value in self.default_values.items():
            self.assertEqual(self.CONF[opt], value)

    @mock.patch('virtualbmc.conf.bmc.libvirt.register_opts')
    def test_new(self, mock_register_opts):
        bmc_type = 'libvirt'
        name = 'test-bmc'

        self.CONF.new(bmc_type, name)

        expected_values = self.default_values
        expected_values.update({'bmc_type': bmc_type, 'name': name})

        for opt, value in expected_values.items():
            self.assertEqual(self.CONF[opt], value)

        mock_register_opts.assert_called_once()

    @mock.patch('virtualbmc.conf.bmc.libvirt.register_opts')
    def test_new_with_args(self, mock_register_opts):
        expected_values = self.default_values
        expected_values.update({
            'bmc_type': 'libvirt',
            'name': 'test-bmc',
            'host_ip': '10.0.0.1',
            'port': 1234,
            'enabled': True,
        })

        self.CONF.new(**expected_values)
        for opt, value in expected_values.items():
            self.assertEqual(self.CONF[opt], value)

        mock_register_opts.assert_called_once()

    def test_new_invalid_bmc_type(self):
        self.assertRaises(ValueError, self.CONF.new, 'invalid', 'test-bmc')

    @utils.mock_existence(return_value=True)
    def test_load(self, existence_mocks):
        bmc_type = 'libvirt'
        name = 'test-bmc'

        expected_values = self.default_values
        expected_values.update({'bmc_type': bmc_type, 'name': name})

        mock_conf = self._mk_test_config(bmc_type, name)
        mock_path = os.path.join(self._MOCK_CONFIG_PATH, name, 'vbmc.conf')
        mock_open_func = utils.mock_open_file(mock_path, mock_conf)

        with mock.patch('builtins.open',
                        side_effect=mock_open_func) as mock_open:
            self.CONF.load(name)

            for opt, value in expected_values.items():
                self.assertEqual(self.CONF[opt], value)

            mock_open.assert_called_with(mock_path)

    @utils.mock_existence(return_value=False)
    def test_load_not_found(self, existence_mocks):
        self.assertRaises(exception.NotFound, self.CONF.load, 'test-bmc')

    @utils.mock_existence(return_value=True)
    def test_load_invalid_bmc_type(self, existence_mocks):
        bmc_type = 'invalid'
        name = 'test-bmc'

        mock_conf = self._mk_test_config(bmc_type, name)
        mock_path = os.path.join(self._MOCK_CONFIG_PATH, name, 'vbmc.conf')
        mock_open_func = utils.mock_open_file(mock_path, mock_conf)

        with mock.patch('builtins.open',
                        side_effect=mock_open_func) as mock_open:
            self.assertRaises(ValueError, self.CONF.load, name)
            mock_open.assert_called_with(mock_path)

    @utils.mock_existence(return_value=True)
    def test_load_from_write(self, existence_mocks):
        name = 'test-bmc'
        expected_values = self.default_values
        expected_values.update({
            'name': name,
            'bmc_type': 'libvirt',
            'host_ip': '10.0.0.1',
            'port': 1234,
            'enabled': True,
        })

        write_out = StringIO()
        self.CONF.new(**expected_values)
        self.CONF.write(write_out)

        conf_loaded = bmc_conf.BMCConfig()
        mock_path = os.path.join(self._MOCK_CONFIG_PATH, name, 'vbmc.conf')
        mock_open_func = utils.mock_open_file(mock_path, write_out.getvalue())

        with mock.patch('builtins.open',
                        side_effect=mock_open_func) as mock_open:
            conf_loaded.load(name)

            for opt, value in expected_values.items():
                self.assertEqual(self.CONF[opt], value)
                self.assertEqual(conf_loaded[opt], value)

            mock_open.assert_called_with(mock_path)

    def test_as_dict(self):
        self.assertEqual(self.default_values, self.CONF.as_dict())

    def test_get_parser(self):
        self.CONF.init_parser()
        self.assertIsInstance(self.CONF.get_parser(),
                              oslo_cfg._CachedArgumentParser)

    def test_get_uninitialized_parser(self):
        self.assertIsInstance(self.CONF.get_parser(),
                              oslo_cfg._CachedArgumentParser)
