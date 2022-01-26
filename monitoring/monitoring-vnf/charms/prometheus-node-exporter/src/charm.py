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
import os
import subprocess
import logging

# Logger
logger = logging.getLogger(__name__)

def install_dependencies():
    python_requirements = ["packaging==21.3"]

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
install_dependencies()
# now we can import the SSHProxyCharm class
from charms.osm.sshproxy import SSHProxyCharm


class SampleProxyCharm(SSHProxyCharm):
    def __init__(self, framework, key):
        super().__init__(framework, key)

        # Listen to charm events
        self.framework.observe(self.on.config_changed, self.on_config_changed)
        self.framework.observe(self.on.install, self.on_install)
        self.framework.observe(self.on.start, self.on_start)
        self.framework.observe(self.on.upgrade_charm, self.on_upgrade_charm)

        # Listen to the touch action event
        self.framework.observe(self.on.configure_remote_action, self.configure_remote)
        self.framework.observe(self.on.start_service_action, self.start_service)

        # Custom actions 
        self.framework.observe(self.on.start_prometheus_exporter_action, self.on_start_prometheus_exporter)
        self.framework.observe(self.on.stop_prometheus_exporter_action, self.on_stop_prometheus_exporter)

        # OSM actions (primitives)
        self.framework.observe(self.on.start_action, self.on_start_action)
        self.framework.observe(self.on.stop_action, self.on_stop_action)
        self.framework.observe(self.on.restart_action, self.on_restart_action)
        self.framework.observe(self.on.reboot_action, self.on_reboot_action)
        self.framework.observe(self.on.upgrade_action, self.on_upgrade_action)


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
        self.on_start_prometheus_exporter(event)


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
    def on_start_prometheus_exporter(self, event):
        logger.info("Starting Prometheus")
        self._get_prometheus_exporter(event)
        self._create_prometheus_exporter_service(event)
        self._run_prometheus_exporter(event)
    

    def on_stop_prometheus_exporter(self, event):
        logger.info("Stopping Prometheus")
        self._stop_prometheus_exporter(event)


    ##########################
    #        Functions       #
    ##########################

    def _get_prometheus_exporter(self, event):
        logger.info("Obtainning Prometheus Exporter")
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
            self.unit.status = MaintenanceStatus(commands[i]["initial_status"])
            try:
                proxy = self.get_ssh_proxy()
                result, error = proxy.run(commands[i]["command"])
                logger.info({"output": result, "errors": error})
                print(commands[i]["ok_status"])
                self.unit.status = MaintenanceStatus(commands[i]["ok_status"])
            except Exception as e:
                logger.error("[Unable to Get the Prometheus Exporter Binary] Action failed {}. Stderr: {}".format(e, error))
                self.unit.status = BlockedStatus(commands[i]["error_status"])
                return False
            
        self.unit.status = ActiveStatus("Prometheus Exporter Binary Obtained With Success")
        logger.info("Obtained Prometheus Exporter")
        return True


    def _create_prometheus_exporter_service(self, event):
        logger.info("Creating Prometheus Exporter Service")
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
            self.unit.status = MaintenanceStatus(commands[i]["initial_status"])
            try:
                proxy = self.get_ssh_proxy()
                result, error = proxy.run(commands[i]["command"])
                logger.info({"output": result, "errors": error})
                print(commands[i]["ok_status"])
                self.unit.status = MaintenanceStatus(commands[i]["ok_status"])
            except Exception as e:
                logger.error("[Unable to Create Prometheus Exporter Service With Success] Action failed {}. Stderr: {}".format(e, error))
                self.unit.status = BlockedStatus(commands[i]["error_status"])
                return False

        self.unit.status = ActiveStatus("Created Prometheus Exporter Service With Success")
        logger.info("Created Prometheus Exporter Service")
        return True
 

    def _run_prometheus_exporter(self, event):
        logger.info("Running Prometheus Exporter Service")
        self.unit.status = MaintenanceStatus("Starting Prometheus Exporter Service...")
        try:
            proxy = self.get_ssh_proxy()
            result, error = proxy.run("sudo service node_exporter start")
            logger.info({"output": result, "errors": error})
            print("Started Prometheus Exporter Service...")
            self.unit.status = MaintenanceStatus("Started Prometheus Exporter Service...")
        except Exception as e:
            logger.error("[Couldn't Start Prometheus Exporter Service] Action failed {}. Stderr: {}".format(e, error))
            self.unit.status = BlockedStatus("Couldn't Start Prometheus Exporter Service...")
            return False

        self.unit.status = MaintenanceStatus("Checking if Prometheus Exporter Service is Running")
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
            self.unit.status = BlockedStatus("Prometheus Exporter Service is not Running")
            return False

        logger.info("Prometheus Exporter Service is Running")
        self.unit.status = ActiveStatus("Prometheus Exporter Service is Running")
        return True


    def _stop_prometheus_exporter(self, event):
        self.unit.status = MaintenanceStatus("Stopping Prometheus Exporter Service...")
        try:
            proxy = self.get_ssh_proxy()
            result, error = proxy.run("sudo service node_exporter stop")
            logger.info({"output": result, "errors": error})
            logger.info("Stopped Prometheus Exporter Service")
            self.unit.status = MaintenanceStatus("Stopped Prometheus Exporter Service")
        except Exception as e:
            logger.error("[Couldn't Stop Prometheus Exporter Service] Action failed {}. Stderr: {}".format(e, error))
            self.unit.status = BlockedStatus("Couldn't Stop Prometheus Exporter Service")
            return False
            
        self.unit.status = ActiveStatus("Prometheus Exporter Service was Stopped")
        return True
   

if __name__ == "__main__":
    main(SampleProxyCharm)