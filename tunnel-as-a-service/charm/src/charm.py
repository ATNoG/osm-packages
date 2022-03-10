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
    python_requirements = ["packaging==21.3", "pyrsistent==0.18.0", "wgconfig==0.2.2"]

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
        self.framework.observe(self.on.update_wg_ip_action, self.update_wg_ip)



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

    def update_wg_ip(self, event):
        return self.wg_toolkit.base.update_wg_ip(event)


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


if __name__ == "__main__":
    main(SampleProxyCharm)