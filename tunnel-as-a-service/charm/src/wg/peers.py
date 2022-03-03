import wgconfig
import os
from wg.command import Command
import json
import wg.constants as Constants 

import logging
# Logger
logging.basicConfig(
    format="%(module)-15s:%(levelname)-10s| %(message)s",
    level=logging.INFO
)
class WGPeers:

    def __init__(self, tunnel_charm, wg_aux):
        self.tunnel_charm = tunnel_charm
        self.wg_aux = wg_aux

    def add_peer(self, event):
        forward_interface = self.tunnel_charm.model.config["forward_interface"]
        tunnel_address = self.tunnel_charm.model.config["tunnel_address"]
        peer_key = event.params["peer_public_key"]
        peer_endpoint = event.params["peer_endpoint"]

        allowed_networks = []
        if "allowed_networks" in event.params and event.params.get["allowed_networks"] != "null":
            allowed_networks = [net.strip() for net in list(allowed_networks.split(","))]

        if self.tunnel_charm.model.unit.is_leader():
            # 1. Stop Wireguard
            command = Command(
                event,
                "sudo wg-quick down {} || true ".format(forward_interface),
                "Stopping wireguard...",
                "Wireguard stopped",
                "Unable to stop wireguard!",
            )
            self.wg_aux.execute_command(command)

            # 2. Add peer
            # 2.1. Get wg config to local file
            self.wg_aux.get_wg_config_to_local()

            # 2.2. Add peer to wg local config
            logging.info("Updating local wireguard configuration file")
            m_wgconfig = wgconfig.WGConfig(Constants.WG_CONFIG_LOCAL_FILEPATH)
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
            self.wg_aux.update_wg_config_on_vnf()

            command = Command(
                event,
                "sudo wg-quick up {}".format(forward_interface),
                "Starting wireguard...",
                "Wireguard started",
                "Unable to start wireguard!",
            )
            self.wg_aux.execute_command(command)
            
            event.set_results({'output': "Peer added with success", "errors": ""})
            ##self.unit.status = ActiveStatus("<-replace->")
            return True
        else:
            event.fail("Unit is not leader")

    def get_peers(self, event):
        if self.tunnel_charm.model.unit.is_leader():
            # 1. Get wg config to local file
            self.wg_aux.get_wg_config_to_local()

            # 2. Add peer to wg local config
            logging.info("Updating local wireguard configuration file")
            m_wgconfig = wgconfig.WGConfig(Constants.WG_CONFIG_LOCAL_FILEPATH)
            m_wgconfig.read_file()

            # 3. Get peers from wg config
            wg_existing_peers = m_wgconfig.peers
            result_peers = None
            if "peer_public_key" in event.params and event.params["peer_public_key"] != "null":
                peer_public_key = event.params["peer_public_key"]
                result_peers = wg_existing_peers.get(peer_public_key, None)
            elif "peer_endpoint_ip" in event.params and event.params["peer_endpoint_ip"] != "null":
                peer_endpoint_ip = event.params["peer_endpoint_ip"]
                for peer_data in wg_existing_peers.values():
                    if peer_endpoint_ip in peer_data["Endpoint"]:
                        result_peers = peer_data
                        break
            else:
                result_peers = wg_existing_peers

            logging.info("Existing/Filtered peers: {}".format(result_peers))

            event.set_results({'output': str(result_peers), "errors": ""})
            return True
        else:
            event.fail("Unit is not leader")


    def update_peer_endpoint(self, event):
        if self.tunnel_charm.model.unit.is_leader():
            tunnel_address = self.tunnel_charm.model.config["tunnel_address"]
            forward_interface = self.tunnel_charm.model.config["forward_interface"]
            new_endpoint = event.params["new_endpoint"]

            public_key, endpoint_ip = event.params.get("peer_public_key", None), event.params.get("peer_endpoint_ip", None)
            if public_key == "null":
                public_key = None
            if endpoint_ip == "null":
                endpoint_ip = None
            peer_info = self.wg_aux.get_peer_given_public_key(event, public_key, endpoint_ip)

            # 2. Stop Wireguard
            command = Command(
                event,
                "sudo wg-quick down {} || true ".format(forward_interface),
                "Stopping wireguard...",
                "Wireguard stopped",
                "Unable to stop wireguard!",
            )
            self.wg_aux.execute_command(command)

            m_wgconfig = wgconfig.WGConfig(Constants.WG_CONFIG_LOCAL_FILEPATH)
            m_wgconfig.read_file()
            m_wgconfig.del_attr(peer_info["PublicKey"], "Endpoint")
            m_wgconfig.add_attr(
                peer_info["PublicKey"], "Endpoint", new_endpoint)
            m_wgconfig.write_file()
            # 3. Update wireguard configuration file on VNF
            self.wg_aux.update_wg_config_on_vnf()

            command = Command(
                event,
                "sudo wg-quick up {}".format(forward_interface),
                "Starting wireguard...",
                "Wireguard started",
                "Unable to start wireguard!",
            )
            self.wg_aux.execute_command(command)

            event.set_results({'output': "Peer updated with success: " + str(m_wgconfig.peers[peer_info["PublicKey"]]), "errors": ""})
            logging.info("Updated peer:" +str(m_wgconfig.peers[peer_info["PublicKey"]]))
            return True
        else:
            event.fail("Unit is not leader")


    def update_peer_allowed_ips(self, event):
        if self.tunnel_charm.model.unit.is_leader():
            forward_interface = self.tunnel_charm.model.config["forward_interface"]
            action = event.params["action"]
            new_network = event.params["network"]

            if action not in ["add", "delete"]:
                logging.error( "Action not supported! Allowed actions = [add, delete]")
                raise Exception( "Action not supported! Allowed actions = [add, delete]")

            public_key, endpoint_ip = event.params.get("peer_public_key", None), event.params.get("peer_endpoint_ip", None)
            if public_key == "null":
                public_key = None
            if endpoint_ip == "null":
                endpoint_ip = None
            peer_info = self.wg_aux.get_peer_given_public_key(event, public_key, endpoint_ip)

            # 2. Stop Wireguard
            command = Command(
                event,
                "sudo wg-quick down {} || true ".format(forward_interface),
                "Stopping wireguard...",
                "Wireguard stopped",
                "Unable to stop wireguard!",
            )
            self.wg_aux.execute_command(command)

            m_wgconfig = wgconfig.WGConfig(Constants.WG_CONFIG_LOCAL_FILEPATH)
            m_wgconfig.read_file()

            if action == "add":
                m_wgconfig.add_attr(peer_info["PublicKey"], "AllowedIPs", new_network)
            elif action == "delete":
                m_wgconfig.del_attr( peer_info["PublicKey"], "AllowedIPs", new_network)

            m_wgconfig.write_file()

            # 3. Update wireguard configuration file on VNF
            self.wg_aux.update_wg_config_on_vnf()

            command = Command(
                event,
                "sudo wg-quick up {}".format(forward_interface),
                "Starting wireguard...",
                "Wireguard started",
                "Unable to start wireguard!",
            )
            self.wg_aux.execute_command(command)

            event.set_results({'output': "Peer updated with success:" + str(m_wgconfig.peers[peer_info["PublicKey"]]), "errors": ""})
            logging.info("Updated peer:" + str(m_wgconfig.peers[peer_info["PublicKey"]]))
            return True
        else:
            event.fail("Unit is not leader")


    def delete_peer(self, event):
        if self.tunnel_charm.model.unit.is_leader():
            forward_interface = self.tunnel_charm.model.config["forward_interface"]

            public_key, endpoint_ip = event.params.get("peer_public_key", None), event.params.get("peer_endpoint_ip", None)
            if public_key == "null":
                public_key = None
            if endpoint_ip == "null":
                endpoint_ip = None
            peer_info = self.wg_aux.get_peer_given_public_key(event, public_key, endpoint_ip)

            # 2. Stop Wireguard
            command = Command(
                event,
                "sudo wg-quick down {} || true ".format(forward_interface),
                "Stopping wireguard...",
                "Wireguard stopped",
                "Unable to stop wireguard!",
            )
            self.wg_aux.execute_command(command)

            m_wgconfig = wgconfig.WGConfig(Constants.WG_CONFIG_LOCAL_FILEPATH)
            m_wgconfig.read_file()
            m_wgconfig.del_peer(peer_info["PublicKey"])
            m_wgconfig.write_file()

            # 3. Update wireguard configuration file on VNF
            self.wg_aux.update_wg_config_on_vnf()

            command = Command(
                event,
                "sudo wg-quick up {}".format(forward_interface),
                "Starting wireguard...",
                "Wireguard started",
                "Unable to start wireguard!",
            )
            self.wg_aux.execute_command(command)

            event.set_results( {'output': "Peer deleted with success! Current peers:" + str(m_wgconfig.peers), "errors": ""})
            logging.info("Current peers:" + str(m_wgconfig.peers))
            return True
        else:
            event.fail("Unit is not leader")
