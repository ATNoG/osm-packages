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
class NetworkMgmt:
    def __init__(self, tunnel_charm, wg_aux):
        self.tunnel_charm = tunnel_charm
        self.wg_aux = wg_aux

    def get_vnf_ip(self, event):
        if self.tunnel_charm.model.unit.is_leader():
            forward_interface = self.tunnel_charm.model.config["forward_interface"]
            vnf_mgmt_ip = self.tunnel_charm.model.config['ssh-hostname']
            tunnel_peer_address = self.tunnel_charm.model.config['tunnel_peer_address']
            vsi_id = self.tunnel_charm.model.config['vsi_id']

            command = Command(
                event,
                "ls /sys/class/net/",
                "Getting VNF network interfaces...",
                "Got VNF network interfaces",
                "Could not get VNF network interfaces!",
            )
            ret = self.wg_aux.execute_command(command)
            network_interfaces = ret["output"].split("\n")
            logging.info("VNF network interfaces: {}".format(
                network_interfaces))

            network_interfaces_info = {}
            for net_int in network_interfaces:
                net_int_ip = None
                net_int_mac = None
                command = Command(
                    event,
                    "ip addr show {} | grep inet | head -n1 | xargs ".format(
                        net_int),
                    "Getting {} Network interface Information (IP)".format(
                        net_int),
                    "Got {} Network interface Information (IP)".format(
                        net_int),
                    "Could not get {} Network interface Information! (IP)".format(
                        net_int),
                )
                ret = self.wg_aux.execute_command(command)
                if len(ret["output"]) != 0:
                    net_int_ip = ret["output"].split(" ")[1].split("/")[0]
                    #logging.info("VNF IP: {}".format(vnfIp))

                command = Command(
                    event,
                    "ip addr show {} | grep ether | xargs".format(net_int),
                    "Getting {} Network interface Information (MAC)".format(
                        net_int),
                    "Got {} Network interface Information (MAC)".format(
                        net_int),
                    "Could not get {} Network interface Information! (MAC)".format(
                        net_int),
                )
                ret = self.wg_aux.execute_command(command)
                if len(ret["output"]) != 0:
                    net_int_mac = ret["output"].split(" ")[1]

                command = Command(
                    event,
                    "ip addr show {} | grep ether | xargs".format(net_int),
                    "Getting {} Network interface Information (Gateway)".format(
                        net_int),
                    "Got {} Network interface Information (Gateway)".format(
                        net_int),
                    "Could not get {} Network interface Information! (Gateway)".format(
                        net_int),
                )
                ret = self.wg_aux.execute_command(command)
                if len(ret["output"]) != 0:
                    net_int_mac = ret["output"].split(" ")[1]

                network_interfaces_info[net_int] = {
                    "ip": net_int_ip,
                    "mac": net_int_mac
                }

            print(network_interfaces_info)

            command = Command(
                event,
                "sudo cat {}".format(Constants.PUBLIC_KEY_FILEPATH),
                "Checking wireguard public key...",
                "Checked wireguard public key",
                "Could not validate wireguard public key!",
            )

            ret = self.wg_aux.execute_command(command)
            public_key = ret["output"]

            result = json.dumps({
                "vsiId": vsi_id,
                "publicKey": public_key,
                "publicEndpoint": vnf_mgmt_ip,
                "internalEndpoint": vnf_mgmt_ip,
                "tunnelId": tunnel_peer_address,
                "network_interfaces_info": network_interfaces_info

            })

            logging.info("VNF Network Info: {}".format(result))
            event.set_results({'output': result, "errors": "-"})
            return True
            #self.unit.status = ActiveStatus("<-replace->")
        else:
            event.fail("Unit is not leader")


    def ip_route_management(self, event):
        network = event.params["network"]
        action = event.params["action"]
        gw_address = event.params["gw_address"]

        if self.tunnel_charm.model.unit.is_leader():

            if action == 'add':
                command = Command(
                    event,
                    "sudo ip r add {} via {} >> /dev/null 2>&1 || sudo ip r chg {} via {}".format( network, gw_address, network, gw_address),
                    "Adding route ({} via {})...".format(action, network, gw_address),
                    "Added route ({} via {})".format(action, network, gw_address),
                    "could not add route ({} via {})".format(network, gw_address),
                )
                self.wg_aux.execute_command(command)

            elif action == 'delete':
                command = Command(
                    event,
                    "sudo ip r delete {} via {} >> /dev/null 2>&1 || true".format( network, gw_address),
                    "Deleting route ({} via {})...".format(action, network, gw_address),
                    "Deleted route ({} via {})".format( action, network, gw_address),
                    "Could not delete route ({} via {})".format(network, gw_address),
                )
                self.wg_aux.execute_command(command)
            else:
                event.set_results({'output': "", "errors": "Action not supported! Allowed actions = [add, delete]"})
                logging.error("Action not supported! Allowed actions = [add, delete]")
                #self.unit.status = BlockedStatus(command.error_status)
                raise Exception( "Action not supported! Allowed actions = [add, delete]")
                
            event.set_results({'output': "Routes update with success", "errors": ""})  
            return True
        else:
            event.fail("Unit is not leader")

    def modify_tunnel(self, event):
        if self.tunnel_charm.model.unit.is_leader():
            pass
            #self.unit.status = ActiveStatus("<-replace->")
            return True
        else:
            event.fail("Unit is not leader")

    def get_ip_routes(self, event):
        if self.tunnel_charm.model.unit.is_leader():

            command = Command(
                event,
                "ip r",
                "Getting IP routes...",
                "Got Ip routes",
                "Couldn't get IP routes"
            )
            ret = self.wg_aux.execute_command(command)
            event.set_results({'output': ret["output"], "errors": ""})
            return True
        else:
            event.fail("Unit is not leader")

    def modify_tunnel(self, event):
        if self.tunnel_charm.model.unit.is_leader():
            pass
            #self.unit.status = ActiveStatus("<-replace->")
            return True
        else:
            event.fail("Unit is not leader")
