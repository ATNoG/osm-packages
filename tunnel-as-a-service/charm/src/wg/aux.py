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

class WGAux:
    def __init__(self, tunnel_charm):
        self.tunnel_charm = tunnel_charm

    def execute_command(self, command):
        result, error = None, None
        #self.unit.status = MaintenanceStatus(initial_status)
        logging.info(command.initial_status)
        try:
            proxy = self.tunnel_charm.get_ssh_proxy()
            result, error = proxy.run(command.command)
            logging.info(command.ok_status)
            ret = {"output": result, "errors": error}
            logging.info(ret)
            #self.unit.status = MaintenanceStatus(command.ok_status)
            return ret
        except Exception as e:
            logging.error("[{}] Action failed {}. Stderr: {}".format(command.command, e, error))
            if command.event is not None:
                command.event.set_results({'output': "", "errors": "[{}] Action failed {}. Stderr: {}".format(command.command, e, error)})
            #self.unit.status = BlockedStatus(command.error_status)
            raise Exception("[{}] Action failed {}. Stderr: {}".format(command.command, e, error))


    def execute_commands_list(self, commands_list):
        for c in commands_list:
            self.execute_command(c)


    def execute_scp(self, source_file, destination_file, initial_status, ok_status, error_status):
        result, error = None, None
        #self.unit.status = MaintenanceStatus(initial_status)
        logging.info(initial_status)
        try:
            proxy = self.tunnel_charm.get_ssh_proxy()
            proxy.scp(source_file, destination_file)
            logging.info(ok_status)
            ret = {"source": source_file, "destination": destination_file}
            logging.info(ret)
            #self.unit.status = MaintenanceStatus(ok_status)
            return True
        except Exception as e:
            logging.error(error_status)
            logging.error("[SCP {} -> {}] Action failed {}. Stderr: {}".format(source_file, destination_file, e, error))
            #self.unit.status = BlockedStatus(error_status)
            raise Exception("[SCP {} -> {}] Action failed {}. Stderr: {}".format(source_file, destination_file, e, error))

    
    def get_wg_config_to_local(self):
        forward_interface = self.tunnel_charm.model.config["forward_interface"]
        source_file_vnf = "{}/{}.conf".format(Constants.VNF_WG_CONFIG_DESTINATION_DIR,forward_interface)

        # create base configuration file
        logging.info("Creating local wireguard configuration file")
        if not os.path.exists(Constants.WG_CONFIG_LOCAL_FILEPATH):
            if not os.path.exists(Constants.WG_CONFIG_LOCAL_DIR):
                os.mkdir(Constants.WG_CONFIG_LOCAL_DIR)
            open(Constants.WG_CONFIG_LOCAL_FILEPATH, 'a').close()
        logging.info("Local wireguard configuration file created")

        # 1. Obtain the wg config file from the VNF
        command = Command(
            None,
            "sudo cat {} ".format(source_file_vnf),
            "Performing a cat on the wireguard configuration file on the VNF...",
            "Performed a cat on the wireguard configuration file on the VNF",
            "Could not perform a cat on the wireguard configuration file on the VNF"
        )
        ret = self.execute_command(command)

        #2. Write the wg config file to local
        with open(Constants.WG_CONFIG_LOCAL_FILEPATH, "w") as f:
                f.write(ret["output"]+"\n")


    def update_wg_config_on_vnf(self):
        forward_interface = self.tunnel_charm.model.config["forward_interface"]
        source_file = Constants.WG_CONFIG_LOCAL_FILEPATH
        destination_file = "{}/{}.conf".format(Constants.VNF_WG_CONFIG_HOME_DIR, forward_interface)

        # 1 - move config file to vnf's home directory
        try:
            logging.info("Updating wireguard configuration file on VNF...")
            ret = self.execute_scp(
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
                None,
                "sudo mv {} {}".format(destination_file, Constants.VNF_WG_CONFIG_DESTINATION_DIR),
                "Moving wireguard configuration file to {}/...".format(Constants.VNF_WG_CONFIG_DESTINATION_DIR),
                "Moved wireguard configuration file to {}/".format(Constants.VNF_WG_CONFIG_DESTINATION_DIR),
                "Could not move wireguard configuration file to {}/".format(Constants.VNF_WG_CONFIG_DESTINATION_DIR)
            )
            self.execute_command(command)
            logging.info("Updated wireguard configuration file on VNF")
            return True

        except Exception as e:
            logging.error("Unable to update wireguard config on vnf")
            #self.unit.status = BlockedStatus(error_status)
            raise Exception(("Unable to update wireguard config on vnf"))


    def get_peer_given_public_key(self, event, public_key, endpoint_ip):
        if public_key is None and endpoint_ip is None:
            logging.error("Missing peer public key or endpoint IP")
            event.set_results({'output': "", "errors": "Missing peer public key or endpoint IP"})
            raise Exception("Missing peer public key or endpoint IP")

        self.get_wg_config_to_local()
        logging.info("Updating local wireguard configuration file")
        m_wgconfig = wgconfig.WGConfig(Constants.WG_CONFIG_LOCAL_FILEPATH)
        m_wgconfig.read_file()
        wg_existing_peers = m_wgconfig.peers

        m_peer_public_key = None
        if "peer_endpoint_ip" in event.params:
            peer_endpoint_ip = event.params["peer_endpoint_ip"]
            for peer_data in wg_existing_peers.values():
                if peer_endpoint_ip in peer_data["Endpoint"]:
                    m_peer_public_key = peer_data["PublicKey"]
                    break

        if m_peer_public_key is None:
            m_peer_public_key = public_key

        if m_peer_public_key not in wg_existing_peers.keys():
            logging.error("Could not select the desired peer")
            event.set_results({'output': "", "errors": "Could not select the desired peer"})
            raise Exception("Could not select the desired peer")

        return wg_existing_peers[m_peer_public_key]
