#!/usr/bin/env python3
import sys

sys.path.append("lib")

from ops.main import main
from ops.model import (
    ActiveStatus,
    MaintenanceStatus,
    BlockedStatus,
    WaitingStatus,
    ModelError,
)

import logging
# Logger
logger = logging.getLogger(__name__)

import os
import subprocess

def install_dependencies():
    python_requirements = ["packaging==21.3", "wgconfig==0.2.2"]

    # Update the apt cache
    logger.info("Updating packages...")
    subprocess.check_call(["sudo", "apt-get", "update"])

    # Make sure Python3 + PIP are available
    if not os.path.exists("/usr/bin/python3") or not os.path.exists("/usr/bin/pip3"):
        # This is needed when running as a k8s charm, as the ubuntu:latest
        # image doesn't include either package.
        # Install the Python3 package
        subprocess.check_call(["sudo", "apt-get", "install", "-y", "python3", "python3-pip"])

    # Install the build dependencies for our requirements (paramiko)
    logger.info("Installing libffi-dev and libssl-dev ...")
    subprocess.check_call(["sudo", "apt-get", "install", "-y", "libffi-dev", "libssl-dev"])

    if len(python_requirements) > 0:
        logger.info("Installing python3 modules")
        subprocess.check_call(["sudo", "python3", "-m", "pip", "install"] + python_requirements)

# start by installing all the required dependencies
try: 
    from charms.osm.sshproxy import SSHProxyCharm
    from wg.toolkit import WGToolkit
except:
    install_dependencies()

# now we can import the SSHProxyCharm class
from charms.osm.sshproxy import SSHProxyCharm
from wg.toolkit import WGToolkit


class SampleProxyCharm(SSHProxyCharm):
    def __init__(self, framework, key):
        super().__init__(framework, key)
        # Custom
        self.wg_toolkit = WGToolkit(self)
        self.wg_aux = self.wg_toolkit.aux


        #-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-#
        #                               Default Events                                #
        #-----------------------------------------------------------------------------#
        # Listen to charm events
        self.framework.observe(self.on.config_changed, self.on_config_changed)
        self.framework.observe(self.on.install, self.on_install)
        self.framework.observe(self.on.start, self.on_start)
        self.framework.observe(self.on.upgrade_charm, self.on_upgrade_charm)

        # Listen to the touch action event
        self.framework.observe(self.on.configure_remote_action, self.configure_remote)
        self.framework.observe(self.on.start_service_action, self.start_service)

        # OSM actions (primitives)
        self.framework.observe(self.on.start_action, self.on_start_action)
        self.framework.observe(self.on.stop_action, self.on_stop_action)
        self.framework.observe(self.on.restart_action, self.on_restart_action)
        self.framework.observe(self.on.reboot_action, self.on_reboot_action)
        self.framework.observe(self.on.upgrade_action, self.on_upgrade_action)

        #-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-#
        #                            End of Default Events                            #
        #-----------------------------------------------------------------------------#



        # Custom actions 
        #self.framework.observe(self.on.start_prometheus_exporter_action, self.on_start_prometheus_exporter)
        #self.framework.observe(self.on.stop_prometheus_exporter_action, self.on_stop_prometheus_exporter)
        self.framework.observe(self.on.get_wireguard_base_info_action, self.get_wireguard_base_info)
        self.framework.observe(self.on.add_peer_action, self.add_peer)
        self.framework.observe(self.on.get_vnf_ip_action, self.get_vnf_ip)
        self.framework.observe(self.on.ip_route_management_action, self.ip_route_management)
        self.framework.observe(self.on.get_peers_action, self.get_peers)
        self.framework.observe(self.on.update_peer_endpoint_action, self.update_peer_endpoint)
        self.framework.observe(self.on.update_peer_allowed_ips_action, self.update_peer_allowed_ips)
        self.framework.observe(self.on.delete_peer_action, self.delete_peer)
        self.framework.observe(self.on.get_ip_routes_action, self.get_ip_routes)


    def on_config_changed(self, event):
        """Handle changes in configuration"""
        super().on_config_changed(event)


    def on_install(self, event):
        """Called when the charm is being installed"""
        super().on_install(event)


    def on_start(self, event):
        """Called when the charm is being started"""
        super().on_start(event)
        # Custom Code
        self.on_start_wireguard(event)


    def on_upgrade_charm(self, event):
        """Upgrade the charm."""
        self.unit.status = MaintenanceStatus("Upgrading charm")
        # Do upgrade related stuff
        self.unit.status = ActiveStatus("Active")


    def configure_remote(self, event):
        """Configure remote action."""
        if self.model.unit.is_leader():
            stderr = None
            try:
                mgmt_ip = self.model.config["ssh-hostname"]
                destination_ip = event.params["destination_ip"]
                cmd = "vnfcli set license {} server {}".format(
                    mgmt_ip,
                    destination_ip
                )
                proxy = self.get_ssh_proxy()
                stdout, stderr = proxy.run(cmd)
                logger.info({"output": stdout})
            except Exception as e:
                logger.error("Action failed {}. Stderr: {}".format(e, stderr))
        else:
            logger.error("Unit is not leader")


    def start_service(self, event):
        """Start service action."""
        if self.model.unit.is_leader():
            stderr = None
            try:
                cmd = "sudo service vnfoper start"
                proxy = self.get_ssh_proxy()
                stdout, stderr = proxy.run(cmd)
                logger.info({"output": stdout})
            except Exception as e:
                logger.error("Action failed {}. Stderr: {}".format(e, stderr))
        else:
            logger.error("Unit is not leader")

    ###############
    # OSM methods #
    ###############
    def on_start_action(self, event):
        """Start the VNF service on the VM."""
        pass

    def on_stop_action(self, event):
        """Stop the VNF service on the VM."""
        pass

    def on_restart_action(self, event):
        """Restart the VNF service on the VM."""
        pass

    def on_reboot_action(self, event):
        """Reboot the VM."""
        if self.unit.is_leader():
          pass

    def on_upgrade_action(self, event):
        """Upgrade the VNF service on the VM."""
        pass


    ##########################
    #     Custom Actions     #
    ##########################
    def on_start_wireguard(self, event):
        self.wg_toolkit.base.install_wg_packages(event)
        self.wg_toolkit.base.wireguard_version_check(event)
        self.wg_toolkit.base.configuration_keygen(event)
        self.wg_toolkit.base.wireguard_server_configuration(event)
        self.wg_toolkit.base.start_wireguard(event)
    



    ##########################
    #        Functions       #
    ##########################
    def get_wireguard_base_info(self, event):
        return self.wg_toolkit.base.get_wireguard_base_info(event)

    
    def add_peer(self, event):
        return self.wg_toolkit.peers.add_peer(event)


    def get_vnf_ip(self, event):
        return self.wg_toolkit.network_mgmt.get_vnf_ip(event)

    def ip_route_management(self, event):
        return self.wg_toolkit.network_mgmt.ip_route_management(event)

    def get_peers(self, event):
        return self.wg_toolkit.peers.get_peers(event)
    
    def update_peer_endpoint(self, event):
        return self.wg_toolkit.peers.update_peer_endpoint(event)

    def update_peer_allowed_ips(self, event):
        return self.wg_toolkit.peers.update_peer_allowed_ips(event)

    def delete_peer(self, event):
        return self.wg_toolkit.peers.delete_peer(event)

    def get_ip_routes(self, event):
        return self.wg_toolkit.network_mgmt.get_ip_routes(event)

    """
    def _get_prometheus_exporter(self, event):
        commands = [
            {
                "command": "wget https://github.com/prometheus/node_exporter/releases/download/v1.3.1/node_exporter-1.3.1.linux-amd64.tar.gz",
                "initial_status": "Getting Prometheus Exporter Bin...",
                "ok_status": "Obtained Prometheus Exporter Tar",
                "error_status": "Couldn't Obtain Prometheus Exporter Tar"
            },
            {
                "command": "tar xvfz node_exporter-1.3.1.linux-amd64.tar.gz",
                "initial_status": "Decompressing Prometheus Exporter Tar...",
                "ok_status": "decompressed Prometheus Exporter Tar",
                "error_status": "Couldn't Decompress Prometheus Exporter Tar"
            },
            {
                "command": "sudo mv node_exporter-1.3.1.linux-amd64/node_exporter /usr/local/bin/ && rm -rf node_exporter-1.3.1.linux-amd64",
                "initial_status": "Moving Prometheus Exporter Bin to the Correct Location...",
                "ok_status": "Moved Prometheus Exporter Bin to /usr/local/bin/",
                "error_status": "Couldn't Move the Prometheus Exporter Bin to /usr/local/bin/"
            },
        ]

        for i in range(len(commands)):
            result, error = None, None
            self.unit.status = MaintenanceStatus(commands[i]["initial_status"])
            try:
                proxy = self.get_ssh_proxy()
                
                result, error = proxy.run(commands[i]["command"])
                logger.info({"output": result, "errors": error})
                logger.info(commands[i]["ok_status"])
                self.unit.status = MaintenanceStatus(commands[i]["ok_status"])
            except Exception as e:
                logger.error("[Unable to Get the Prometheus Exporter Binary] Action failed {}. Stderr: {}".format(e, error))
                raise Exception("[Unable to Get the Prometheus Exporter Binary] Action failed {}. Stderr: {}".format(e, error))
                self.unit.status = BlockedStatus(commands[i]["error_status"])
                return False
            
        self.unit.status = ActiveStatus("Prometheus Exporter Binary Obtained With Success")
        return True


    def _create_prometheus_exporter_service(self, event):
        commands = [
            {
                "command": 'sudo useradd -rs /bin/false node_exporter || true',
                "initial_status": "Adding node_exporter User...",
                "ok_status": "Added node_exporter User...",
                "error_status": "Couldn't Add  node_exporter User...",
            },
            {
                "command": '\"echo -e \\"{}\\" | sudo tee {}\"'.format(
                "[Unit]\nDescription=Node Exporter\nAfter=network.target\n\n[Service]\nUser=node_exporter\nGroup=node_exporter\nType=simple\nExecStart=/usr/local/bin/node_exporter\n\n[Install]\nWantedBy=multi-user.target",
                "/etc/systemd/system/node_exporter.service"),
                "initial_status": "Adding Prometheus Exporter Service to Systemd...",
                "ok_status": "Added Prometheus Exporter Service to Systemd",
                "error_status": "Couldn't Add Prometheus Exporter Service to Systemd",
            },
            {
                "command": 'sudo systemctl daemon-reload && sudo systemctl enable node_exporter',
                "initial_status": "Enabling Prometheus Exporter Service...",
                "ok_status": "Enabled Prometheus Exporter Service...",
                "error_status": "Couldn't Enable Prometheus Exporter Service...",
            },
            
        ]

        for i in range(len(commands)):
            result, error = None, None
            self.unit.status = MaintenanceStatus(commands[i]["initial_status"])
            try:
                proxy = self.get_ssh_proxy()
                
                result, error = proxy.run(commands[i]["command"])
                logger.info({"output": result, "errors": error})
                logger.info(commands[i]["ok_status"])
                self.unit.status = MaintenanceStatus(commands[i]["ok_status"])
            except Exception as e:
                logger.error("[Unable to Create Prometheus Exporter Service With Success] Action failed {}. Stderr: {}".format(e, error))
                raise Exception("[Unable to Create Prometheus Exporter Service With Success] Action failed {}. Stderr: {}".format(e, error))
                self.unit.status = BlockedStatus(commands[i]["error_status"])
                return False

        self.unit.status = ActiveStatus("Created Prometheus Exporter Service With Success")
        return True
 

    def _run_prometheus_exporter(self, event):
        self.unit.status = MaintenanceStatus("Starting Prometheus Exporter Service...")
        result, error = None, None
        try:
            proxy = self.get_ssh_proxy()
            result, error = proxy.run("sudo service node_exporter start")
            logger.info({"output": result, "errors": error})
            logger.info("Started Prometheus Exporter Service...")
            self.unit.status = MaintenanceStatus("Started Prometheus Exporter Service...")
        except Exception as e:
            logger.error("[Couldn't Start Prometheus Exporter Service] Action failed {}. Stderr: {}".format(e, error))
            raise Exception("[Couldn't Start Prometheus Exporter Service] Action failed {}. Stderr: {}".format(e, error))
            self.unit.status = BlockedStatus("Couldn't Start Prometheus Exporter Service...")
            return False

        self.unit.status = MaintenanceStatus("Checking if Prometheus Exporter Service is Running")
        result, error = None, None
        try:
            proxy = self.get_ssh_proxy()
            result, error = proxy.run("curl -Is http://127.0.0.1:9100/metrics | head -1")
            logger.info({"output": result, "errors": error})
            if "200" not in result:
                logger.error("Prometheus Exporter Service is not Running...")
                self.unit.status = BlockedStatus("Prometheus Exporter Service is not Running")
                return False
        except Exception as e:
            logger.error("[Prometheus Exporter Service is not Running] Action failed {}. Stderr: {}".format(e, error))
            raise Exception("[Prometheus Exporter Service is not Running] Action failed {}. Stderr: {}".format(e, error))
            self.unit.status = BlockedStatus("Prometheus Exporter Service is not Running")
            return False

        logger.info("Prometheus Exporter Service is Running")
        self.unit.status = ActiveStatus("Prometheus Exporter Service is Running")
        return True


    def _stop_prometheus_exporter(self, event):
        result, error = None, None
        self.unit.status = MaintenanceStatus("Stopping Prometheus Exporter Service...")
        try:
            proxy = self.get_ssh_proxy()
            result, error = proxy.run("sudo service node_exporter stop")
            logger.info({"output": result, "errors": error})
            logger.info("Stopped Prometheus Exporter Service")
            self.unit.status = MaintenanceStatus("Stopped Prometheus Exporter Service")
        except Exception as e:
            logger.error("[Couldn't Stop Prometheus Exporter Service] Action failed {}. Stderr: {}".format(e, error))
            raise Exception("[Couldn't Stop Prometheus Exporter Service] Action failed {}. Stderr: {}".format(e, error))
            self.unit.status = BlockedStatus("Couldn't Stop Prometheus Exporter Service")
            return False
            
        self.unit.status = ActiveStatus("Prometheus Exporter Service was Stopped")
        return True
   
    """

if __name__ == "__main__":
    main(SampleProxyCharm)