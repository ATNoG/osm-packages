import json
import logging
import os

from pyrsistent import v
import wgconfig
from wg.command import Command
import wg.constants as Constants 

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
                    None,
                    "sudo apt-get update",
                    "Updating packages...",
                    "Packages updated",
                    "Could not update packages!",
                ),
                Command(
                    None,
                    "sudo apt install wireguard -y",
                    "Installing wireguard...",
                    "Wireguard installed",
                    "Could not install wireguard!",
                ),
                Command(
                    None,
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
                None,
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
            commands = [
                Command(
                    None,
                    "wg genkey | sudo tee {} | wg pubkey | sudo tee {}".format(
                        Constants.PRIVATE_KEY_FILEPATH,
                        Constants.PUBLIC_KEY_FILEPATH
                        ),
                    "Creating wireguard keys...",
                    "Created wireguard keys",
                    "Could not create wireguard keys!",
                ),
                Command(
                    None,
                    "sudo cat {}".format(Constants.PRIVATE_KEY_FILEPATH),
                    "Checking wireguard private key...",
                    "Checked wireguard private key",
                    "Could not validate wireguard private key!",
                ),
                Command(
                    None,
                    "sudo cat {}".format(Constants.PUBLIC_KEY_FILEPATH),
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
            if not os.path.exists(Constants.WG_CONFIG_LOCAL_FILEPATH):
                if not os.path.exists(Constants.WG_CONFIG_LOCAL_DIR):
                    os.mkdir(Constants.WG_CONFIG_LOCAL_DIR)
                open(Constants.WG_CONFIG_LOCAL_FILEPATH, 'a').close()
            logging.info("Local wireguard configuration file created")

            # define the interface of the wireguard conf file
            m_wgconfig = wgconfig.WGConfig(Constants.WG_CONFIG_LOCAL_FILEPATH)

            command = Command(
                None,
                "sudo cat {}".format(Constants.PRIVATE_KEY_FILEPATH),
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
                None,
                "sudo sysctl -w net.ipv4.ip_forward=1",
                "Allowing IPv4 forwarding on the VNF...",
                "Allowed IPv4 forwarding on the VNF",
                "Could not allow IPv4 forwarding on the VNF!"
            )
            self.wg_aux.execute_command(command)

            # Print WG Configuration
            with open(Constants.WG_CONFIG_LOCAL_FILEPATH, "r") as f:
                logging.info(
                    "\n<===== Wireguard Configuration File =====>\n" + f.read())

            #self.tunnel_charm.unit.status = ActiveStatus("<-replace->")
            return True
        else:
            event.fail("Unit is not leader")


    def start_wireguard(self, event):
        forward_interface = self.tunnel_charm.model.config["forward_interface"]
        if self.tunnel_charm.model.unit.is_leader():
            commands = [
                Command(
                    None,
                    "sudo wg-quick down {} || true ".format(forward_interface),
                    "Stopping wireguard...",
                    "Wireguard stopped",
                    "Unable to stop wireguard!",
                ),
                Command(
                    None,
                    "sudo wg-quick up {}".format(forward_interface),
                    "Starting wireguard...",
                    "Wireguard started",
                    "Unable to start wireguard!",
                ),
                Command(
                    None,
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

    def get_wireguard_base_info(self, event):
        if self.tunnel_charm.model.unit.is_leader():

            # 1. Get public key
            command = Command(
                event,
                "sudo cat {}".format(Constants.PUBLIC_KEY_FILEPATH),
                "Checking wireguard public key...",
                "Checked wireguard public key",
                "Could not validate wireguard public key!",
            )
            
            ret = self.wg_aux.execute_command(command)
            public_key = ret["output"]

            # 2. get address and list port
            self.wg_aux.get_wg_config_to_local()

            logging.info("Updating local wireguard configuration file")
            m_wgconfig = wgconfig.WGConfig(Constants.WG_CONFIG_LOCAL_FILEPATH)
            m_wgconfig.read_file()

            interface_data = dict(m_wgconfig.interface)
            result = json.dumps({
                "address": interface_data["Address"],
                "listen_port": interface_data["ListenPort"],
                "public_key": public_key,
    
            })

            logging.info("WG Base Info: {}".format(result))
            event.set_results({'output': result, "errors": ""})

            ##self.unit.status = ActiveStatus("<-replace->")
            return True
        else:
            event.fail("Unit is not leader")


    def update_wg_ip(self, event):
        if self.tunnel_charm.model.unit.is_leader():
            forward_interface = self.tunnel_charm.model.config["forward_interface"]
            new_ip = event.params["wg_new_ip"]

            # 1. Stop Wireguard
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
            m_wgconfig.del_attr(None, "Address")
            m_wgconfig.add_attr(None, 'Address', new_ip)
            m_wgconfig.write_file()
            # 2. Update wireguard configuration file on VNF
            self.wg_aux.update_wg_config_on_vnf()

            command = Command(
                event,
                "sudo wg-quick up {}".format(forward_interface),
                "Starting wireguard...",
                "Wireguard started",
                "Unable to start wireguard!",
            )
            self.wg_aux.execute_command(command)

            event.set_results({'output': "Wireguard Peer Updated Configuration: " + str(m_wgconfig.interface), "errors": ""})
            logging.info("Peer Updated Configuration:" + str(m_wgconfig.interface))
            return True
        else:
            event.fail("Unit is not leader")