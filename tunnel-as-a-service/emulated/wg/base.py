import json
import logging
import os
import wgconfig
from command import Command

# Logger
logging.basicConfig(
    format="%(module)-15s:%(levelname)-10s| %(message)s",
    level=logging.INFO
)
class WGBase:

    def __init__(self, tunnel_charm, wg_aux):
        self.tunnel_charm = tunnel_charm
        self.wg_aux = wg_aux

    def install_wg_packages(self, event):
        if self.tunnel_charm.model.unit.is_leader():
            commands = [
                Command(
                    "sudo apt-get update",
                    "Updating packages...",
                    "Packages updated",
                    "Could not update packages!",
                ),
                Command(
                    "sudo apt install wireguard -y",
                    "Installing wireguard...",
                    "Wireguard installed",
                    "Could not install wireguard!",
                ),
                Command(
                    "sudo apt install net-tools -y",
                    "Installing net-tools...",
                    "net-tools installed",
                    "Could not install net-tools!",
                ),
            ]

            self.wg_aux.execute_commands_list(commands)
            #self.tunnel_charm.unit.status = ActiveStatus("<-replace->")
            return True
        else:
            event.fail("Unit is not leader")


    def wireguard_version_check(self, event):
        if self.tunnel_charm.model.unit.is_leader():
            command = Command(
                "wg --version",
                "Checking wireguard version...",
                "Wireguard version is correct",
                "Wireguard version is not correct. Maybe it is not installed?",
            )
            self.wg_aux.execute_command(command)
            #self.tunnel_charm.unit.status = ActiveStatus("<-replace->")
            return True
        else:
            event.fail("Unit is not leader")


    def configuration_keygen(self, event):
        if self.tunnel_charm.model.unit.is_leader():
            private_key_path = "/etc/wireguard/privatekey"
            public_key_path = "/etc/wireguard/publickey"

            commands = [
                Command(
                    "wg genkey | sudo tee {} | wg pubkey | sudo tee {}".format(
                        private_key_path, public_key_path),
                    "Creating wireguard keys...",
                    "Created wireguard keys",
                    "Could not create wireguard keys!",
                ),
                Command(
                    "sudo cat {}".format(private_key_path),
                    "Checking wireguard private key...",
                    "Checked wireguard private key",
                    "Could not validate wireguard private key!",
                ),
                Command(
                    "sudo cat {}".format(public_key_path),
                    "Checking wireguard public key...",
                    "Checked wireguard public key",
                    "Could not validate wireguard public key!",
                ),
            ]

            self.wg_aux.execute_commands_list(commands)

            #self.tunnel_charm.unit.status = ActiveStatus("<-replace->")
            return True
        else:
            event.fail("Unit is not leader")


    def wireguard_server_configuration(self, event):
        tunnel_peer_address = self.tunnel_charm.model.config["tunnel_peer_address"]
        listen_port = self.tunnel_charm.model.config["listen_port"]
        save_config = self.tunnel_charm.model.config["save_config"]

        if self.tunnel_charm.model.unit.is_leader():

            # create base configuration file
            logging.info("Creating local wireguard configuration file")
            if not os.path.exists("/tmp/wireguard/wg.conf"):
                if not os.path.exists("/tmp/wireguard/"):
                    os.mkdir("/tmp/wireguard")
                open("/tmp/wireguard/wg.conf", 'a').close()
            logging.info("Local wireguard configuration file created")

            # define the interface of the wireguard conf file
            m_wgconfig = wgconfig.WGConfig("/tmp/wireguard/wg.conf")

            command = Command(
                "sudo cat /etc/wireguard/privatekey",
                "Obtaining wireguard private key...",
                "Obtained wireguard private key",
                "Could not obtain wireguard private key!"
            )
            ret = self.wg_aux.execute_command(command)

            try:
                wg_pk = ret["output"].strip()
            except:
                raise Exception("Could not obtain wireguard private key!")

            logging.info("Updating local wireguard configuration file")
            m_wgconfig.add_attr(None, 'Address', tunnel_peer_address)
            m_wgconfig.add_attr(None, 'SaveConfig', save_config)
            m_wgconfig.add_attr(None, 'ListenPort', listen_port)
            m_wgconfig.add_attr(None, 'PrivateKey', wg_pk)
            m_wgconfig.write_file()
            logging.info("Local wireguard configuration file updated")

            # Update wireguard configuration file on VNF
            self.wg_aux.update_wg_config_on_vnf()

            # Allow IPv4 forwarding
            command = Command(
                "sudo sysctl -w net.ipv4.ip_forward=1",
                "Allowing IPv4 forwarding on the VNF...",
                "Allowed IPv4 forwarding on the VNF",
                "Could not allow IPv4 forwarding on the VNF!"
            )
            self.wg_aux.execute_command(command)

            # Print WG Configuration
            with open("/tmp/wireguard/wg.conf", "r") as f:
                logging.info(
                    "\n<===== Wireguard Configuration File =====>\n" + f.read())

            #self.tunnel_charm.unit.status = ActiveStatus("<-replace->")
            return True
        else:
            event.fail("Unit is not leader")


    def start_wireguard(self, event):
        forward_interface = self.model.config["forward_interface"]
        if self.tunnel_charm.model.unit.is_leader():
            commands = [
                Command(
                    "sudo wg-quick down {} || true ".format(forward_interface),
                    "Stopping wireguard...",
                    "Wireguard stopped",
                    "Unable to stop wireguard!",
                ),
                Command(
                    "sudo wg-quick up {}".format(forward_interface),
                    "Starting wireguard...",
                    "Wireguard started",
                    "Unable to start wireguard!",
                ),
                Command(
                    "sudo wg show {}".format(forward_interface),
                    "Checking wireguard configuration...",
                    "Checked wireguard configuration",
                    "Could not check wireguard configuration!",
                )
            ]
            self.wg_aux.execute_commands_list(commands)
            #self.tunnel_charm.unit.status = ActiveStatus("<-replace->")
            return True
        else:
            event.fail("Unit is not leader")