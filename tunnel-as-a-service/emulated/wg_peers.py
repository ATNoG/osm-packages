import wgconfig
import os
from command import Command
import json

import logging
# Logger
logging.basicConfig(
    format="%(module)-15s:%(levelname)-10s| %(message)s",
    level=logging.INFO
)
class WGPeers:

    def __init__(self, tunnel_charm):
        self.tunnel_charm = tunnel_charm

    def add_peer(self, event):
        forward_interface = self.tunnel_charm.model.config["forward_interface"]
        tunnel_address = self.tunnel_charm.model.config["tunnel_address"]
        peer_key = event.params["peer_key"]
        peer_endpoint = event.params["peer_endpoint"]
        allowed_networks = event.params["allowed_networks"]

        if self.tunnel_charm.model.unit.is_leader():

            # 1. Stop Wireguard
            command = Command(
                "sudo wg-quick down {} || true ".format(forward_interface),
                "Stopping wireguard...",
                "Wireguard stopped",
                "Unable to stop wireguard!",
            )
            self.tunnel_charm.wg_aux.execute_command(command)

            # 2. Add peer
            # 2.1. Get wg config to local file
            self.tunnel_charm.wg_aux.get_wg_config_to_local()

            # 2.2. Add peer to wg local config
            logging.info("Updating local wireguard configuration file")
            m_wgconfig = wgconfig.WGConfig("/tmp/wireguard/wg.conf")
            m_wgconfig.read_file()

            # if peer already exists, remove it
            wg_existing_peers = m_wgconfig.peers
            if peer_key in wg_existing_peers:
                m_wgconfig.del_peer(peer_key)

            m_wgconfig.add_peer(peer_key)
            m_wgconfig.add_attr(
                peer_key,
                'AllowedIPs',
                ", ".join(allowed_networks + [tunnel_address])
            )
            m_wgconfig.add_attr(
                peer_key,
                'Endpoint',
                peer_endpoint
            )
            m_wgconfig.write_file()

            # 3. Update wireguard configuration file on VNF
            self.tunnel_charm.wg_aux.update_wg_config_on_vnf()

            command = Command(
                "sudo wg-quick up {}".format(forward_interface),
                "Starting wireguard...",
                "Wireguard started",
                "Unable to start wireguard!",
            )
            self.tunnel_charm.wg_aux.execute_command(command)
            ##self.unit.status = ActiveStatus("<-replace->")
            return True
        else:
            event.fail("Unit is not leader")
