# Copyright 2020 David Garcia
# See LICENSE file for licensing details.

import unittest
from unittest.mock import Mock, call

from ops.testing import Harness
from charm import SshproxyCharm


class TestCharm(unittest.TestCase):
    @unittest.mock.patch("charms.osm.sshproxy.SSHProxy.run")
    def test_touch_action(self, mock_ssh_proxy):
        mock_ssh_proxy.return_value = ("stdout", None)
        harness = Harness(SshproxyCharm)
        harness.set_leader(is_leader=True)
        harness.begin()
        action_event = Mock(params={"filename": "/home/ubuntu/asd"})
        harness.charm.on_touch_action(action_event)

        self.assertTrue(action_event.set_results.called)
        self.assertEqual(
            action_event.set_results.call_args,
            call({"output": "stdout"}),
        )

    def test_touch_action_fail(self):
        harness = Harness(SshproxyCharm)
        harness.set_leader(is_leader=False)
        harness.begin()
        action_event = Mock(params={"filename": "/home/ubuntu/asd"})
        harness.charm.on_touch_action(action_event)

        self.assertEqual(action_event.fail.call_args, [("Unit is not leader",)])
