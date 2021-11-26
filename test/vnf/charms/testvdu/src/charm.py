#!/usr/bin/env python3
# Copyright 2020 David Garcia
# See LICENSE file for licensing details.

import sys

sys.path.append("lib")

from ops.main import main

from charms.osm.sshproxy import SSHProxyCharm
from ops.model import (
    ActiveStatus,
    MaintenanceStatus,
    BlockedStatus,
    WaitingStatus,
    ModelError,
)

# self.unit.status = MaintenanceStatus("Generating SSH keys...")
# self.unit.status = ActiveStatus()
# self.unit.status = BlockedStatus("Invalid SSH credentials.")

class SshproxyCharm(SSHProxyCharm):
    def __init__(self, *args):
        super().__init__(*args)

        # An example of setting charm state
        # that's persistent across events
        self.state.set_default(is_started=False)

        if not self.state.is_started:
            self.state.is_started = True

        # Register all of the events we want to observe
        # Charm events
        self.framework.observe(self.on.config_changed, self.on_config_changed)
        self.framework.observe(self.on.install, self.on_install)
        self.framework.observe(self.on.start, self.on_start)
        self.framework.observe(self.on.upgrade_charm, self.on_upgrade_charm)
        # Charm actions (primitives)
        self.framework.observe(self.on.touch_action, self.on_touch_action)
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
        super().on_install(event)

    def on_start(self, event):
        """Called when the charm is being installed"""
        super().on_start(event)

    def on_upgrade_charm(self, event):
        """Upgrade the charm."""
        self.unit.status = MaintenanceStatus("Upgrading charm")
        # Do upgrade related stuff
        self.unit.status = ActiveStatus("Active")

    def on_touch_action(self, event):
        """Touch a file."""

        if self.unit.is_leader():
            filename = event.params["filename"]
            proxy = self.get_ssh_proxy()
            stdout, stderr = proxy.run("touch {}".format(filename))
            proxy.scp("/etc/lsb-release", "/home/ubuntu/scp_file")
            event.set_results({"output": stdout})
        else:
            event.fail("Unit is not leader")
            return

    ###############
    # OSM methods #
    ###############
    def on_start_action(self, event):
        """Start the VNF service on the VM."""
        if self.unit.is_leader():
            self.unit.status = MaintenanceStatus("Installing docker")
            proxy = self.get_ssh_proxy()

            # install docker
            proxy.run("sudo apt-get update")
            proxy.run("sudo apt-get -y install apt-transport-https" + 
                                        " ca-certificates" + 
                                        " curl" +
                                        " gnupg" +
                                        " lsb-release")
            proxy.run("curl -fsSL https://download.docker.com/linux/ubuntu/gpg | " +
                        "sudo gpg --yes --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg")
            proxy.run("echo \"deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] " +
                        "https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable\"" + 
                        " | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null")
            proxy.run("sudo apt-get update")
            proxy.run("sudo apt-get -y install docker-ce docker-ce-cli containerd.io")
            proxy.run("sudo systemctl restart docker")

            # install docker-compose
            self.unit.status = MaintenanceStatus("Installing docker-compose")
            try:
                proxy.run("sudo groupadd docker && sudo usermod -aG docker $USER" + 
                                    " && newgrp docker")
            except Exception as e:
                # it means that the group already exists
                proxy.run("newgrp docker")

            proxy.run("sudo curl -L \"https://github.com/docker/compose/releases/latest/download" + 
                "/docker-compose-$(uname -s)-$(uname -m)\" " + 
                "-o /usr/local/bin/docker-compose && sudo chmod +x /usr/local/bin/docker-compose")

            # add directory where the github repository will be pulled
            proxy.run("mkdir ~/github-code")
            
            self.unit.status = ActiveStatus("All required packages installed successfully")
        else:
            event.fail("Unit is not leader")
            return

    def on_stop_action(self, event):
        """Stop the VNF service on the VM."""
        if self.unit.is_leader():
            self.unit.status = MaintenanceStatus("Removing docker")
            proxy = self.get_ssh_proxy()

            # removing docker
            proxy.run("sudo apt-get -y purge docker-ce docker-ce-cli containerd.io")
            proxy.run("sudo rm -rf /var/lib/docker")
            proxy.run("sudo rm -rf /var/lib/containerd")

            self.unit.status = MaintenanceStatus("Removing docker-compose")
            proxy.run("newgrp ubuntu")
            proxy.run("sudo rm /usr/local/bin/docker-compose")

            # remove github code
            proxy.run("rm -rf ~/github-code")

            self.unit.status = ActiveStatus("All the installed packages were removed")
        else:
            event.fail("Unit is not leader")
            return

    def on_restart_action(self, event):
        """Restart the VNF service on the VM."""
        pass

    def on_reboot_action(self, event):
        """Reboot the VM."""
        if self.unit.is_leader():
            proxy = self.get_ssh_proxy()
            stdout, stderr = proxy.run("sudo reboot")
            if len(stderr):
                event.fail(stderr)
        else:
            event.fail("Unit is not leader")
            return

    def on_upgrade_action(self, event):
        """Upgrade the VNF service on the VM."""
        pass


if __name__ == "__main__":
    main(SshproxyCharm)
