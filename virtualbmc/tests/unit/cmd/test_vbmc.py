# Copyright 2016 Red Hat, Inc.
# All Rights Reserved.
#
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

import io
import json
import sys
from unittest import mock

import zmq

from virtualbmc.cmd import vbmc
from virtualbmc.tests.unit import base


@mock.patch.object(sys, 'exit', lambda _: None)
class VBMCTestCase(base.TestCase):

    @mock.patch.object(zmq, 'Context')
    @mock.patch.object(zmq, 'Poller')
    def test_server_timeout(self, mock_zmq_poller, mock_zmq_context):
        expected_rc = 1
        expected_output = (
            'Failed to connect to the vbmcd server on port 50891, error: '
            'Server response timed out\n')

        mock_zmq_poller = mock_zmq_poller.return_value
        mock_zmq_poller.poll.return_value = {}

        with mock.patch.object(sys, 'stderr', io.StringIO()) as output:
            rc = vbmc.main(['--no-daemon',
                            'add', '--username', 'ironic', 'bar'])

            self.assertEqual(expected_rc, rc)
            self.assertEqual(expected_output, output.getvalue())

    @mock.patch.object(zmq, 'Context')
    @mock.patch.object(zmq, 'Poller')
    def test_main_add(self, mock_zmq_poller, mock_zmq_context):
        expected_rc = 0
        expected_output = ''

        srv_rsp = {
            'rc': expected_rc,
            'msg': ['OK']
        }

        mock_zmq_context = mock_zmq_context.return_value
        mock_zmq_socket = mock_zmq_context.socket.return_value
        mock_zmq_socket.recv.return_value = json.dumps(srv_rsp).encode()
        mock_zmq_poller = mock_zmq_poller.return_value
        mock_zmq_poller.poll.return_value = {
            mock_zmq_socket: zmq.POLLIN
        }

        with mock.patch.object(sys, 'stdout', io.StringIO()) as output:
            rc = vbmc.main(['add', '--bmc-type', 'libvirt',
                            '--libvirt-domain-name', 'foo', 'bar'])

            query = json.loads(mock_zmq_socket.send.call_args[0][0].decode())

            expected_query = {
                'command': 'add',
                'name': 'bar',
                'bmc_type': 'libvirt',
                'enabled': False,
                'host_ip': '127.0.0.1',
                'port': 1623,
                'username': 'admin',
                'password': 'password',
                'libvirt': {
                    'sasl_username': None,
                    'sasl_password': None,
                    'uri': 'qemu:///system',
                    'domain_name': 'foo',
                }
            }

            self.assertEqual(expected_query, query)

            self.assertEqual(expected_rc, rc)
            self.assertEqual(expected_output, output.getvalue())

    @mock.patch.object(zmq, 'Context')
    @mock.patch.object(zmq, 'Poller')
    def test_main_delete(self, mock_zmq_poller, mock_zmq_context):
        expected_rc = 0
        expected_output = ''

        srv_rsp = {
            'rc': expected_rc,
            'msg': ['OK']
        }

        mock_zmq_context = mock_zmq_context.return_value
        mock_zmq_socket = mock_zmq_context.socket.return_value
        mock_zmq_socket.recv.return_value = json.dumps(srv_rsp).encode()
        mock_zmq_poller = mock_zmq_poller.return_value
        mock_zmq_poller.poll.return_value = {
            mock_zmq_socket: zmq.POLLIN
        }

        with mock.patch.object(sys, 'stdout', io.StringIO()) as output:

            rc = vbmc.main(['delete', 'foo', 'bar'])

            query = json.loads(mock_zmq_socket.send.call_args[0][0].decode())

            expected_query = {
                "domain_names": ["foo", "bar"],
                "command": "delete",
            }

            self.assertEqual(expected_query, query)

            self.assertEqual(expected_rc, rc)
            self.assertEqual(expected_output, output.getvalue())

    @mock.patch.object(zmq, 'Context')
    @mock.patch.object(zmq, 'Poller')
    def test_main_start(self, mock_zmq_poller, mock_zmq_context):
        expected_rc = 0
        expected_output = ''

        srv_rsp = {
            'rc': expected_rc,
            'msg': ['OK']
        }

        mock_zmq_context = mock_zmq_context.return_value
        mock_zmq_socket = mock_zmq_context.socket.return_value
        mock_zmq_socket.recv.return_value = json.dumps(srv_rsp).encode()
        mock_zmq_poller = mock_zmq_poller.return_value
        mock_zmq_poller.poll.return_value = {
            mock_zmq_socket: zmq.POLLIN
        }

        with mock.patch.object(sys, 'stdout', io.StringIO()) as output:

            rc = vbmc.main(['start', 'foo', 'bar'])

            query = json.loads(mock_zmq_socket.send.call_args[0][0].decode())

            expected_query = {
                'command': 'start',
                'domain_names': ['foo', 'bar']
            }

            self.assertEqual(expected_query, query)

            self.assertEqual(expected_rc, rc)
            self.assertEqual(expected_output, output.getvalue())

    @mock.patch.object(zmq, 'Context')
    @mock.patch.object(zmq, 'Poller')
    def test_main_stop(self, mock_zmq_poller, mock_zmq_context):
        expected_rc = 0
        expected_output = ''

        srv_rsp = {
            'rc': expected_rc,
            'msg': ['OK']
        }

        mock_zmq_context = mock_zmq_context.return_value
        mock_zmq_socket = mock_zmq_context.socket.return_value
        mock_zmq_socket.recv.return_value = json.dumps(srv_rsp).encode()
        mock_zmq_poller = mock_zmq_poller.return_value
        mock_zmq_poller.poll.return_value = {
            mock_zmq_socket: zmq.POLLIN
        }

        with mock.patch.object(sys, 'stdout', io.StringIO()) as output:

            rc = vbmc.main(['stop', 'foo', 'bar'])

            query = json.loads(mock_zmq_socket.send.call_args[0][0].decode())

            expected_query = {
                'command': 'stop',
                'domain_names': ['foo', 'bar']
            }

            self.assertEqual(expected_query, query)

            self.assertEqual(expected_rc, rc)
            self.assertEqual(expected_output, output.getvalue())

    @mock.patch.object(zmq, 'Context')
    @mock.patch.object(zmq, 'Poller')
    def test_main_list(self, mock_zmq_poller, mock_zmq_context):
        expected_rc = 0
        expected_output = """+-------+-------+
| col1  | col2  |
+-------+-------+
| cell1 | cell2 |
| cell3 | cell4 |
+-------+-------+
"""

        srv_rsp = {
            'rc': expected_rc,
            'header': ['col1', 'col2'],
            'rows': [['cell1', 'cell2'],
                     ['cell3', 'cell4']],
        }

        mock_zmq_context = mock_zmq_context.return_value
        mock_zmq_socket = mock_zmq_context.socket.return_value
        mock_zmq_socket.recv.return_value = json.dumps(srv_rsp).encode()
        mock_zmq_poller = mock_zmq_poller.return_value
        mock_zmq_poller.poll.return_value = {
            mock_zmq_socket: zmq.POLLIN
        }

        with mock.patch.object(sys, 'stdout', io.StringIO()) as output:

            rc = vbmc.main(['list'])

            query = json.loads(mock_zmq_socket.send.call_args[0][0].decode())

            expected_query = {
                "command": "list",
            }

            # Cliff adds some extra args to the query
            query = {key: query[key] for key in query
                     if key in expected_query}

            self.assertEqual(expected_query, query)

            self.assertEqual(expected_rc, rc)
            self.assertEqual(expected_output, output.getvalue())

    @mock.patch.object(zmq, 'Context')
    @mock.patch.object(zmq, 'Poller')
    def test_main_show(self, mock_zmq_poller, mock_zmq_context):
        expected_rc = 0

        expected_output = """+-------+-------+
| col1  | col2  |
+-------+-------+
| cell1 | cell2 |
| cell3 | cell4 |
+-------+-------+
"""

        srv_rsp = {
            'rc': expected_rc,
            'header': ['col1', 'col2'],
            'rows': [['cell1', 'cell2'],
                     ['cell3', 'cell4']]
        }

        mock_zmq_context = mock_zmq_context.return_value
        mock_zmq_socket = mock_zmq_context.socket.return_value
        mock_zmq_socket.recv.return_value = json.dumps(srv_rsp).encode()
        mock_zmq_poller = mock_zmq_poller.return_value
        mock_zmq_poller.poll.return_value = {
            mock_zmq_socket: zmq.POLLIN
        }

        with mock.patch.object(sys, 'stdout', io.StringIO()) as output:

            rc = vbmc.main(['show', 'domain0'])

            query = json.loads(mock_zmq_socket.send.call_args[0][0].decode())

            expected_query = {
                "domain_name": "domain0",
                "command": "show",
            }

            # Cliff adds some extra args to the query
            query = {key: query[key] for key in query
                     if key in expected_query}

            self.assertEqual(expected_query, query)

            self.assertEqual(expected_rc, rc)
            self.assertEqual(expected_output, output.getvalue())
