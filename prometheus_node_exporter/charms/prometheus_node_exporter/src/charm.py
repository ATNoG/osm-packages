#!/usr/bin/env python3
import sys

sys.path.append("lib")

from charms.osm.sshproxy import SSHProxyCharm
from ops.main import main
from ops.model import (
    ActiveStatus,
    MaintenanceStatus,
    BlockedStatus,
    WaitingStatus,
    ModelError,
)

class SampleProxyCharm(SSHProxyCharm):
    def __init__(self, framework, key):
        super().__init__(framework, key)

        # Listen to charm events
        self.framework.observe(self.on.config_changed, self.on_config_changed)
        self.framework.observe(self.on.install, self.on_install)
        self.framework.observe(self.on.start, self.on_start)
        # self.framework.observe(self.on.upgrade_charm, self.on_upgrade_charm)

        # Listen to the touch action event
        self.framework.observe(self.on.configure_remote_action, self.configure_remote)
        self.framework.observe(self.on.start_service_action, self.start_service)

        # Custom actions 
        self.framework.observe(self.on.start_prometheus_exporter_action, self.on_start_prometheus_exporter)


    def on_config_changed(self, event):
        """Handle changes in configuration"""
        super().on_config_changed(event)

    def on_install(self, event):
        """Called when the charm is being installed"""
        super().on_install(event)

    def on_start(self, event):
        """Called when the charm is being started"""
        super().on_start(event)

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
                event.set_results({"output": stdout})
            except Exception as e:
                event.fail("Action failed {}. Stderr: {}".format(e, stderr))
        else:
            event.fail("Unit is not leader")

    def start_service(self, event):
        """Start service action."""

        if self.model.unit.is_leader():
            stderr = None
            try:
                cmd = "sudo service vnfoper start"
                proxy = self.get_ssh_proxy()
                stdout, stderr = proxy.run(cmd)
                event.set_results({"output": stdout})
            except Exception as e:
                event.fail("Action failed {}. Stderr: {}".format(e, stderr))
        else:
            event.fail("Unit is not leader")


    ##########################
    #    Custom Functions    #
    ##########################

    def on_start_prometheus_exporter(self, event):
        self._get_prometheus_exporter(event)


    def _get_prometheus_exporter(self, event):
        may_proceed = True

        self.unit.status = MaintenanceStatus("Getting Prometheus Exporter Bin...")
        try:
            cmd = "wget https://github.com/prometheus/node_exporter/releases/download/v1.3.1/node_exporter-1.3.1.linux-amd64.tar.gz"
            proxy = self.get_ssh_proxy()
            result, error = proxy.run(cmd)
            event.set_results({"output": result})
            self.unit.status = MaintenanceStatus("Obtained Prometheus Exporter Tar")
        except Exception as e:
            may_proceed = False
            event.fail("Action failed {}. Stderr: {}".format(e, error))
            self.unit.status = BlockedStatus("Couldn't Obtain Prometheus Exporter Tar")

        if may_proceed:
            self.unit.status = MaintenanceStatus("Decompressing Prometheus Exporter Tar...")
            try:
                cmd = "tar xvfz node_exporter-1.3.1.linux-amd64.tar.gz"
                proxy = self.get_ssh_proxy()
                result, error = proxy.run(cmd)
                event.set_results({"output": result})
                self.unit.status = MaintenanceStatus("Decompressed Prometheus Exporter Tar")
            except Exception as e:
                may_proceed = False
                event.fail("Action failed {}. Stderr: {}".format(e, error))
                self.unit.status = BlockedStatus("Couldn't Decompress Prometheus Exporter Tar")
        
        if may_proceed:
            self.unit.status = MaintenanceStatus("Moving Prometheus Exporter Bin to the Right Location...")
            try:
                cmd = "sudo cp node_exporter-1.3.1.linux-amd64/node_exporter /usr/local/bin/"
                proxy = self.get_ssh_proxy()
                result, error = proxy.run(cmd)
                event.set_results({"output": result})
                self.unit.status = MaintenanceStatus("Moved Prometheus Exporter Bin to /usr/local/bin/")
            except Exception as e:
                may_proceed = False
                event.fail("Action failed {}. Stderr: {}".format(e, error))
                self.unit.status = BlockedStatus("Couldn't Move the Prometheus Exporter Bin to /usr/local/bin/")

        if not may_proceed:
            event.fail("Unable to Get the Prometheus Exporter Binary")
            self.unit.status = BlockedStatus("Unable to Get the Prometheus Exporter Binary")
        else:
            self.unit.status = ActiveStatus("Prometheus Exporter Binary Obatined With Success")


    def _create_prometheus_exporter_service(self, event):
        pass

    def _run_prometheus_exporter(self, event):
        pass

    def _is_prometheus_exporter_on_machine(self, event):
        pass

    def _is_prometheus_exporter_service_configured(self, event):
        pass
    
    def _is_prometheus_exporter_service_runnning(self, event):
        pass

if __name__ == "__main__":
    main(SampleProxyCharm)
