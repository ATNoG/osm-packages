from select import select
import sys
sys.path.append(".")
from osm_ssh_proxy import SSHProxy
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


##### MOCKS #####
class Model():
    def __init__(self,unit):
        self.unit = unit
    config = {
        "tunnel_address": "10.100.100.0/24",
        "tunnel_peer_address": "10.100.100.1/24",
        "listen_port": "51820",
        "save_config": "true",
        "forward_interface": "wg0",
        "ssh-hostname": "10.0.12.107",
        "username": "ubuntu",
        "password": "ubuntu",
        "vsi_id": "1",
    }
class Unit():
    def __init__(self):
        pass
    def is_leader(self):
        return True
class Event():
    params = {}
    def __init__(self):
        pass

    def add_param(self, key, value):
        self.params[key] = value

    def set_results(self, x):
        pass
##### END OF MOCKS #####

class TunnelCharm:
    def __init__(self, username, password, hostname):
        self.username = username
        self.password = password
        self.hostname = hostname
        self.ssh_proxy = SSHProxy(hostname, username, password)
        self.model = Model(Unit()) 
        

    def get_ssh_proxy(self):
        return self.ssh_proxy

    def _execute_command(self, command):
        result, error = None, None
        #self.unit.status = MaintenanceStatus(initial_status)
        logging.info(command.initial_status)
        try:
            proxy = self.get_ssh_proxy()
            result, error = proxy.run(command.command)
            logging.info(command.ok_status)
            ret = {"output": result, "errors": error}
            logging.info(ret)
            #self.unit.status = MaintenanceStatus(command.ok_status)
            return ret
        except Exception as e:
            logging.error(command.error_status)
            logging.error("[{}] Action failed {}. Stderr: {}".format(command.command, e, error))
            #self.unit.status = BlockedStatus(command.error_status)
            raise Exception("[{}] Action failed {}. Stderr: {}".format(command.command, e, error))
    

    def _execute_scp(self, source_file, destination_file, initial_status, ok_status, error_status):
        result, error = None, None
        #self.unit.status = MaintenanceStatus(initial_status)
        logging.info(initial_status)
        try:
            proxy = self.get_ssh_proxy()
            proxy.scp(source_file, destination_file)
            logging.info(ok_status)
            ret = {"source": source_file, "destination": destination_file}
            logging.info(ret)
            #self.unit.status = MaintenanceStatus(ok_status)
            return True
        except Exception as e:
            logging.error(error_status)
            logging.error(
                "[SCP {} -> {}] Action failed {}. Stderr: {}".format(source_file, destination_file, e, error))
            #self.unit.status = BlockedStatus(error_status)
            raise Exception("[SCP {} -> {}] Action failed {}. Stderr: {}".format(source_file, destination_file, e, error))


    def _execute_commands_list(self, commands_list):
        for c in commands_list:
            self._execute_command(c)


    def __get_wg_config_to_local(self):
        forward_interface = self.model.config["forward_interface"]
        destination_file_local = "/tmp/wireguard/wg.conf"
        source_file_vnf = "/etc/wireguard/{}.conf".format(forward_interface)

        # 1. Obtain the wg config file from the VNF
        command = Command(
            "sudo cat {} ".format(source_file_vnf),
            "Performing a cat on the wireguard configuration file on the VNF...",
            "Performed a cat on the wireguard configuration file on the VNF",
            "Could not perform a cat on the wireguard configuration file on the VNF"
        )
        ret = self._execute_command(command)

        #2. Write the wg config file to local
        with open(destination_file_local, "w") as f:
                f.write(ret["output"]+"\n")


    def _update_wg_config_on_vnf(self):
        forward_interface = self.model.config["forward_interface"]
        source_file = "/tmp/wireguard/wg.conf"
        destination_file = "~/{}.conf".format(forward_interface)

        # 1 - move config file to vnf's home directory
        try:
            logging.info("Updating wireguard configuration file on VNF...")
            ret = self._execute_scp(
                source_file,
                destination_file,
                "Copying wireguard configuration file to the VNF's home directory...",
                "Copied wireguard configuration file to the VNF's home directory",
                "Could not copy wireguard configuration file to the VNF's home directory!"
            )

            if not ret:
                raise Exception("Could not copy wireguard configuration file to the VNF!")

            # 2 - update config file
            command = Command(
                "sudo mv {} /etc/wireguard/".format(destination_file),
                "Moving wireguard configuration file to /etc/wireguard/...",
                "Moved wireguard configuration file to /etc/wireguard/",
                "Could not move wireguard configuration file to /etc/wireguard/"
            )
            self._execute_command(command)
            logging.info("Updated wireguard configuration file on VNF")
            return True

        except Exception as e:
            logging.error("Unable to update wireguard config on vnf")
            #self.unit.status = BlockedStatus(error_status)
            raise Exception(("Unable to update wireguard config on vnf"))

    def install_packages(self, event):
        if self.model.unit.is_leader():
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

            self._execute_commands_list(commands)

            #self.unit.status = ActiveStatus("<-replace->")
            return True
        else:
            event.fail("Unit is not leader")


    def wireguard_version_check(self, event):
        if self.model.unit.is_leader():
            command = Command(  
                "wg --version",
                "Checking wireguard version...",
                "Wireguard version is correct",
                "Wireguard version is not correct. Maybe it is not installed?",
            )
            self._execute_command(command)
            #self.unit.status = ActiveStatus("<-replace->")
            return True
        else:
            event.fail("Unit is not leader")


    def configuration_keygen(self, event):
        if self.model.unit.is_leader():
            private_key_path = "/etc/wireguard/privatekey"
            public_key_path = "/etc/wireguard/publickey"

            commands = [
                Command(
                    "wg genkey | sudo tee {} | wg pubkey | sudo tee {}".format(private_key_path, public_key_path),
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

            self._execute_commands_list(commands)
  
            #self.unit.status = ActiveStatus("<-replace->")
            return True
        else:
            event.fail("Unit is not leader")


    def wireguard_server_configuration(self, event):
        tunnel_peer_address = self.model.config["tunnel_peer_address"]
        listen_port = self.model.config["listen_port"]
        save_config = self.model.config["save_config"]
        forward_interface = self.model.config["forward_interface"]

        if self.model.unit.is_leader():

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
            ret = self._execute_command(command)

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
            self._update_wg_config_on_vnf()

            # Allow IPv4 forwarding
            command = Command(
                "sudo sysctl -w net.ipv4.ip_forward=1",
                "Allowing IPv4 forwarding on the VNF...",
                "Allowed IPv4 forwarding on the VNF",
                "Could not allow IPv4 forwarding on the VNF!"
            )
            self._execute_command(command)

            # Print WG Configuration
            with open("/tmp/wireguard/wg.conf", "r") as f:
                logging.info("\n<===== Wireguard Configuration File =====>\n" + f.read())

            #self.unit.status = ActiveStatus("<-replace->")
            return True
        else:
            event.fail("Unit is not leader")


    def start_wireguard(self, event):
        forward_interface = self.model.config["forward_interface"]
        if self.model.unit.is_leader():
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
            self._execute_commands_list(commands)
            #self.unit.status = ActiveStatus("<-replace->")
            return True
        else:
            event.fail("Unit is not leader")


    def add_peer(self, event):
        forward_interface = self.model.config["forward_interface"]
        tunnel_address = self.model.config["tunnel_address"]
        peer_key = event.params["peer_key"]
        peer_endpoint = event.params["peer_endpoint"]
        allowed_networks = event.params["allowed_networks"]

        if self.model.unit.is_leader():
            
            # 1. Stop Wireguard
            command = Command(
                "sudo wg-quick down {} || true ".format(forward_interface),
                "Stopping wireguard...",
                "Wireguard stopped",
                "Unable to stop wireguard!",
            )
            self._execute_command(command)

            # 2. Add peer
            # 2.1. Get wg config to local file 
            self.__get_wg_config_to_local()

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
            self._update_wg_config_on_vnf()
            
            command = Command(
                "sudo wg-quick up {}".format(forward_interface),
                "Starting wireguard...",
                "Wireguard started",
                "Unable to start wireguard!",
            )
            self._execute_command(command)
            ##self.unit.status = ActiveStatus("<-replace->")
            return True
        else:
            event.fail("Unit is not leader")

    def get_vnf_ip(self, event):
        if self.model.unit.is_leader():
            forward_interface = self.model.config["forward_interface"]
            vnf_mgmt_ip = self.model.config['ssh-hostname']
            tunnel_peer_address = self.model.config['tunnel_peer_address']
            vsi_id = self.model.config['vsi_id']
            public_key_path = "/etc/wireguard/publickey"

            command = Command(  
                "ls /sys/class/net/",
                "Getting VNF network interfaces...",
                "Got VNF network interfaces",
                "Could not get VNF network interfaces!",
            )
            ret = self._execute_command(command)
            network_interfaces = ret["output"].split("\n")
            logging.info("VNF network interfaces: {}".format(network_interfaces))


            network_interfaces_info = {}
            for net_int in network_interfaces:
                net_int_ip = None
                net_int_mac = None
                command = Command(
                    "ip addr show {} | grep inet | head -n1 | xargs ".format(net_int),
                    "Getting {} Network interface Information (IP)".format(net_int),
                    "Got {} Network interface Information (IP)".format(net_int),
                    "Could not get {} Network interface Information! (IP)".format(net_int),
                )
                ret = self._execute_command(command)
                if len(ret["output"]) != 0:
                    net_int_ip = ret["output"].split(" ")[1].split("/")[0]
                    #logging.info("VNF IP: {}".format(vnfIp))
                
                command = Command(
                    "ip addr show {} | grep ether | xargs".format(net_int),
                    "Getting {} Network interface Information (MAC)".format(net_int),
                    "Got {} Network interface Information (MAC)".format(net_int),
                    "Could not get {} Network interface Information! (MAC)".format(net_int),
                )
                ret = self._execute_command(command)
                if len(ret["output"]) != 0:
                    net_int_mac = ret["output"].split(" ")[1]

                command = Command(
                    "ip addr show {} | grep ether | xargs".format(net_int),
                    "Getting {} Network interface Information (Gateway)".format(net_int),
                    "Got {} Network interface Information (Gateway)".format(net_int),
                    "Could not get {} Network interface Information! (Gateway)".format(
                        net_int),
                )
                ret = self._execute_command(command)
                if len(ret["output"]) != 0:
                    net_int_mac = ret["output"].split(" ")[1]
                
                network_interfaces_info[net_int] = {
                    "ip": net_int_ip,
                    "mac": net_int_mac
                }

            print(network_interfaces_info)

            

            command =  Command(
                "sudo cat {}".format(public_key_path),
                "Checking wireguard public key...",
                "Checked wireguard public key",
                "Could not validate wireguard public key!",
            )
            
            ret = self._execute_command(command)
            public_key = ret["output"]
            
            result = json.dumps({
                "vsiId": vsi_id, 
                "publicKey": public_key, 
                "publicEndpoint": vnf_mgmt_ip,
                "internalEndpoint": vnf_mgmt_ip, 
                "tunnelId": tunnel_peer_address
            })

            logging.info("VNF Network Info: {}".format(result))
            event.set_results({'output': result, "errors": "-"})
            return True
            #self.unit.status = ActiveStatus("<-replace->")
            return True
        else:
            event.fail("Unit is not leader")


    def modify_tunnel(self, event):
        if self.model.unit.is_leader():
            pass
            #self.unit.status = ActiveStatus("<-replace->")
            return True
        else:
            event.fail("Unit is not leader")


    def ip_route_management(self, event):
        network = event.params["network"]
        action = event.params["action"]
        gw_address = event.params["gw_address"]

        if self.model.unit.is_leader():
            
            if action not in ["add", "delete"]:
                logging.error("Action not supported! Allowed actions = [add, delete]")
                #self.unit.status = BlockedStatus(command.error_status)
                raise Exception("Action not supported! Allowed actions = [add, delete]")

            command =  Command(
                "sudo ip r {} {} via {}".format(action, network, gw_address),
                "{}ing route ({} via {})...".format(action, network, gw_address),
                "{}ed route ({} via {})".format(action, network, gw_address),
                "could not {} route ({} via {})".format(action, network, gw_address),
            )
            self._execute_command(command)
            return True
        else:
            event.fail("Unit is not leader")






if __name__ == "__main__":
    tunnel_charm = TunnelCharm("ubuntu", "ubuntu", "10.0.12.107")
    #tunnel_charm.install_packages(None)
    #tunnel_charm.wireguard_version_check(None)
    #tunnel_charm.configuration_keygen(None)
    #tunnel_charm.wireguard_server_configuration(None)
    event = Event()
    event.add_param("peer_key", "U5H6wmmosBhVLLm1A1p/Hbx7M/hhtvpQ8D+20K0ORj0=")
    event.add_param("peer_endpoint", "155.44.99.111:51820")
    event.add_param("allowed_networks", ["10.10.10.0/24", "10.10.11.0/24"])
    #tunnel_charm.addpeer(event)
    #tunnel_charm.get_vnf_ip(event)
    event = Event()
    event.add_param("action", "delete")
    event.add_param("network", "10.0.16.0/23")
    event.add_param("gw_address", "10.0.12.1")
    tunnel_charm.ip_route_management(event)
