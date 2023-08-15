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

from unittest import mock

from virtualbmc import exception
from virtualbmc.tests.unit import base
from virtualbmc.vbmc import base as vbmc_base
from virtualbmc.vbmc import constants


# the VbmcBase class is meant to be subclassed, so we do that here.
class TestVbmc(vbmc_base.VbmcBase):
    bmc_cmd = vbmc_base.VbmcBase.bmc_cmd
    vbmc_type = 'test vbmc'

    @bmc_cmd
    def do_nothing(self, *args, **kwargs):
        return 0

    @bmc_cmd(fail_ok=False)
    def do_nothing_loudly(self, *args, **kwargs):
        return 0

    @bmc_cmd
    def do_bad_silently(self, *args, **kwargs):
        raise RuntimeError('Oh no!')

    @bmc_cmd(fail_ok=False)
    def do_bad_loudly(self, *args, **kwargs):
        raise RuntimeError('Uh oh!')


class VirtualBMCBaseTestCase(base.TestCase):
    def setUp(self):
        super().setUp()
        bmc_init_patcher = mock.patch('pyghmi.ipmi.bmc.Bmc.__init__')
        self.mock_bmc_init = bmc_init_patcher.start()
        self.addCleanup(bmc_init_patcher.stop)
        self.vbmc = TestVbmc('foobar', 'foo', 'bar', '0.0.0.0', 623)

    def _assertLogs(self, level, no_logs):
        cm = self.assertNoLogs if no_logs else self.assertLogs
        return cm(self.get_logger(), level)

    def assertDebugLogs(self, no_logs=False):
        return self._assertLogs('DEBUG', no_logs)

    def assertErrorLogs(self, no_logs=False):
        return self._assertLogs('ERROR', no_logs)

    def test_new(self):
        self.mock_bmc_init.assert_called_once_with(
            authdata={'foo': 'bar'}, port=623, address='0.0.0.0'
        )
        self.assertEqual(self.vbmc.name, 'foobar')

    def test_bmc_cmd_no_args(self):
        with self.assertDebugLogs() as logs:
            self.assertEqual(self.vbmc.do_nothing('ahhh!'), 0)
            output = '\n'.join(logs.output)
            for info in ('do_nothing', 'foobar', 'test vbmc', 'ahhh!'):
                self.assertIn(info, output)

        with self.assertErrorLogs(no_logs=True):
            self.assertEqual(self.vbmc.do_nothing('ahhh!'), 0)

    def test_bmc_cmd_error_no_args(self):
        with self.assertDebugLogs() as logs:
            self.assertEqual(self.vbmc.do_bad_silently('ahhh!'),
                             constants.IPMI_COMMAND_NODE_BUSY)
            output = '\n'.join(logs.output)
            for info in ('do_bad_silently', 'foobar', 'test vbmc', 'ahhh!'):
                self.assertIn(info, output)

        with self.assertErrorLogs() as logs:
            self.assertEqual(self.vbmc.do_bad_silently('ahhh!'),
                             constants.IPMI_COMMAND_NODE_BUSY)
            output = '\n'.join(logs.output)
            for info in ('RuntimeError', 'do_bad_silently', 'foobar', 'ahhh!'):
                self.assertIn(info, output)

    def test_bmc_cmd_with_args(self):
        with self.assertDebugLogs() as logs:
            self.assertEqual(self.vbmc.do_nothing_loudly('ahhh!'), 0)
            output = '\n'.join(logs.output)
            for info in ('do_nothing_loudly', 'foobar', 'test vbmc', 'ahhh!'):
                self.assertIn(info, output)

        with self.assertErrorLogs(no_logs=True):
            self.assertEqual(self.vbmc.do_nothing_loudly('ahhh!'), 0)

    def test_bmc_cmd_error_with_args(self):
        with self.assertDebugLogs() as logs:
            self.assertRaises(exception.VirtualBMCError,
                              self.vbmc.do_bad_loudly, 'ahhh!')
            output = '\n'.join(logs.output)
            for info in ('do_bad_loudly', 'foobar', 'test vbmc', 'ahhh!'):
                self.assertIn(info, output)

        with self.assertErrorLogs() as logs:
            self.assertRaises(exception.VirtualBMCError,
                              self.vbmc.do_bad_loudly, 'ahhh!')
            output = '\n'.join(logs.output)
            for info in ('RuntimeError', 'do_bad_loudly', 'foobar', 'ahhh!'):
                self.assertIn(info, output)
