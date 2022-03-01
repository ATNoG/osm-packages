import sys

sys.path.append(".")
from osm_ssh_proxy import SSHProxy
import logging
from wg.toolkit import WGToolkit

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

    def del_param(self, key):
        del self.params[key]

    def set_results(self, results):
        print("Event results -> " + str(results))

        pass
##### END OF MOCKS #####

class TunnelCharm:
    def __init__(self, username, password, hostname):
        self.username = username
        self.password = password
        self.hostname = hostname
        self.ssh_proxy = SSHProxy(hostname, username, password)
        self.model = Model(Unit()) 
        self.wg_toolkit = WGToolkit(self)
        self.wg_aux = self.wg_toolkit.aux
        
    ##### MOCKS #####
    def get_ssh_proxy(self):
        return self.ssh_proxy
    ##### END OF MOCKS #####


    def install_wg_packages(self, event):
        return self.wg_toolkit.base.install_wg_packages(event)


    def wireguard_version_check(self, event):
        return self.wg_toolkit.base.wireguard_version_check(event)


    def configuration_keygen(self, event):
        return self.wg_toolkit.base.configuration_keygen(event)


    def wireguard_server_configuration(self, event):
        return self.wg_toolkit.base.wireguard_server_configuration(event)


    def start_wireguard(self, event):
        return self.wg_toolkit.base.start_wireguard(event)

    def get_wireguard_base_info(self, event):
        return self.wg_toolkit.base.get_wireguard_base_info(event)


    def add_peer(self, event):
        return self.wg_toolkit.peers.add_peer(event)


    def get_vnf_ip(self, event):
        return self.wg_toolkit.network_mgmt.get_vnf_ip(event)
    

    def modify_tunnel(self, event):
        self.wg_toolkit.network_mgmt.modify_tunnel(event)

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

<<<<<<< HEAD
    
=======
    def set_credentials(self,event):
        return self.wg_toolkit.openstack_mgmt.set_credentials(event)
    
    def get_server_details(self,event):
        return self.wg_toolkit.openstack_mgmt.get_server_details(event)

    def get_server_ports(self,event):
        return self.wg_toolkit.openstack_mgmt.get_server_ports(event)

    def add_address_pairs(self,event):
        return self.wg_toolkit.openstack_mgmt.add_address_pairs(event)

>>>>>>> 29323274d753feee89d444594b1c328e35e36e41

if __name__ == "__main__":
    tunnel_charm = TunnelCharm("ubuntu", "ubuntu", "10.0.12.107")
    # Install wireguard and start thee tunnel
    #tunnel_charm.install_wg_packages(None)
    #tunnel_charm.wireguard_version_check(None)
    #tunnel_charm.configuration_keygen(None)
    #tunnel_charm.wireguard_server_configuration(None)
    # Add Peer
    event = Event()
    event.add_param("peer_key", "U5H6wmmosBhVLLm1A1p/Hbx7M/hhtvpQ8D+20K0ORj0=")
    event.add_param("peer_endpoint", "155.44.99.111:51820")
    event.add_param("allowed_networks", "10.10.10.0/24,10.10.11.0/24")
    tunnel_charm.add_peer(event)
    # Get VNF IPs
    #event = Event()
    #tunnel_charm.get_vnf_ip(event)
    # Add route
    #event = Event()
    #event.add_param("action", "add")
    #event.add_param("network", "10.0.16.0/23")
    #event.add_param("gw_address", "10.0.12.1")
    #tunnel_charm.ip_route_management(event)
    #tunnel_charm.ip_route_management(event)
    #event.add_param("action", "delete")
    #tunnel_charm.ip_route_management(event)
    #tunnel_charm.ip_route_management(event)
    # Get Peers
    #event = Event()
    #tunnel_charm.get_peers(event)
    # Get specific peer - public key
    #event = Event()
    #event.add_param("peer_public_key","U5H6wmmosBhVLLm1A1p/Hbx7M/hhtvpQ8D+20K0ORj0=")
    #tunnel_charm.get_peers(event)
    # Get specific peer - endpoint ip
    #event = Event()
    #event.add_param("peer_endpoint_ip", "155.44.99.111")
    #tunnel_charm.get_peers(event)
    # Update peers endpoint
    #event = Event()
    #event.add_param("peer_public_key","U5H6wmmosBhVLLm1A1p/Hbx7M/hhtvpQ8D+20K0ORj0=")
    #event.add_param("new_endpoint", "155.44.99.111:51823")
    #tunnel_charm.update_peer_endpoint(event)
    #event = Event()
    #event.add_param("peer_endpoint_ip", "155.44.99.111")
    #event.add_param("new_endpoint", "155.44.99.111:51824")
    #tunnel_charm.update_peer_endpoint(event)
    # Update peers allowed ips
    #event = Event()
    #event.add_param("peer_public_key","U5H6wmmosBhVLLm1A1p/Hbx7M/hhtvpQ8D+20K0ORj0=")
    #event.add_param("action", "add")
    #event.add_param("network", "10.10.17.0/24")
    #tunnel_charm.update_peer_allowed_ips(event)
    #event.add_param("action", "delete")
    #event.add_param("network", "10.10.17.0/24")
    #tunnel_charm.update_peer_allowed_ips(event)
    # Add another peer
    #event = Event()
    #event.add_param("peer_key", "X5H6wmmosBhVLLm1A1p/Hbx7M/hhtvpQ8D+20K0ORj0=")
    #event.add_param("peer_endpoint", "155.44.99.111:51820")
    #event.add_param("allowed_networks", ["10.10.10.0/24"])
    #tunnel_charm.add_peer(event)
    # Delete peer
    #event = Event()
    #event.add_param("peer_key", "X5H6wmmosBhVLLm1A1p/Hbx7M/hhtvpQ8D+20K0ORj0=")
    #tunnel_charm.delete_peer(event)
    # Change ip routes
    #event = Event()
    #tunnel_charm.get_ip_routes(event)
    #event.add_param("action", "add")
    #event.add_param("network", "10.0.16.0/23")
    #event.add_param("gw_address", "10.0.12.1")
    #event.add_param("action", "add")
    #tunnel_charm.ip_route_management(event)
    #event.add_param("action", "delete")
    #tunnel_charm.ip_route_management(event)
    #event.add_param("action", "delete")
    #tunnel_charm.ip_route_management(event)
<<<<<<< HEAD
    # Get WG Base Info
    event = Event()
    tunnel_charm.get_wireguard_base_info(event)
=======
    
    #Set OpenStack Credentials
    # event = Event()
    # event.add_param("username",'')
    # event.add_param('password','')
    # event.add_param('user_domain_name','')    
    # event.add_param('domain_name','')
    # event.add_param('project_name','')
    # event.add_param('host','')
    # tunnel_charm.set_credentials(event)

    # Get Server Details
    # event = Event()
    # event.add_param('server_id','26f4aec2-2148-43b9-9d9f-56e0c1d1c2cd')
    # tunnel_charm.get_server_details(event)

    # Get Server Interfaces
    # event = Event()
    # event.add_param('server_id','26f4aec2-2148-43b9-9d9f-56e0c1d1c2cd')
    # tunnel_charm.get_server_ports(event)

    # Add Address Pairs
    # event = Event()
    # event.add_param('ports_id_list',['955989fe-9864-4216-9f3a-1ea8f4710ced'])
    # event.add_param('ip_address_list',['10.100.100.0/24','192.168.100.0/24'])
    # tunnel_charm.add_address_pairs(event)

>>>>>>> 29323274d753feee89d444594b1c328e35e36e41
