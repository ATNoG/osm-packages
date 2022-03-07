import sys
import os
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
        "ssh-hostname": "10.0.12.212",
        "username": "ubuntu",
        "password": "password",
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


    # Passwd Actions
    def install_openstack_wrapper(self,event):
        return self.wg_toolkit.pwdBase.install_openstack_wrapper(event)

    def configure_key_gen(self,event):
        return self.wg_toolkit.pwdBase.configure_key_gen(event)

    def get_public_key(self,event):
        return self.wg_toolkit.pwdBase.get_public_key(event)
    
    def add_address_pair(self,event):
        return self.wg_toolkit.pwdBase.add_address_pair(event)



if __name__ == "__main__":
    tunnel_charm = TunnelCharm("ubuntu", "password", "10.0.12.212")
    # Install wireguard and start thee tunnel
    #tunnel_charm.install_wg_packages(None)
    #tunnel_charm.wireguard_version_check(None)
    #tunnel_charm.configuration_keygen(None)
    #tunnel_charm.wireguard_server_configuration(None)
    # Add Peer
    # event = Event()
    # event.add_param("peer_key", "U5H6wmmosBhVLLm1A1p/Hbx7M/hhtvpQ8D+20K0ORj0=")
    # event.add_param("peer_endpoint", "155.44.99.111:51820")
    # event.add_param("allowed_networks", "10.10.10.0/24,10.10.11.0/24")
    # tunnel_charm.add_peer(event)
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
    # --- 
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
    #-----
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


    # Get WG Base Info
    #event = Event()
    #tunnel_charm.get_wireguard_base_info(event)
    
    
    # Configure key pair
    event = Event()
    tunnel_charm.install_openstack_wrapper(event)
    #tunnel_charm.configure_key_gen(event)
    event = Event()
    tunnel_charm.get_public_key(event)
    username = b'HOctTcgSVrXXyrr9W7GAQ945E1JJWsJcI16D+S7ZAkvRVfkCLHIiAR7PR/HyHrxmZstIyABVnLNcprJRkabszmCN4aOo0I/GtjZeKACKL4dR49lRi5rtYA0/QiQnizkl/AnNHBkLOJGn3PWmjbYNhVAKsDOy8kDHK3bR68dLlyHCxeMdycEfaGvFOcR5zmASTgDPyUlN4WpjxIxHZS0zQWBhdax9xmC82FAU6Th8GtxcCvJZrz0i1oDgxljxNljNaL8WG/+G3N5wKcZPAgmSzWcKDdTKqO6zeAltQ7C/BCmbldGqGFtBm8VdyhVwpCbrsh/458V+LwzqNmal1x7VIbmc7wfLd83kWFCxRHlny+bHKQIombdC3Skmyq6jieqyuhUTnISykFOG9M0+x1uKYfrJImBYcwfIEWwdbFWlXIx1EwgjMbhtyKIDF3HHtIu+RC72PY4m5RyNhYi/PTLhCPzT632X5PaFAi89aSKsAf8qRNd7yShtEVSnePd8YDf7'
    password = b'FpsqDIxkbegUeW+RbTAxh/4UNGzcVCRTLiyK6J+ynK3YznfeNtLjPTq3czXTiDjFhVEzL+mCApm0sT1XdLL/+zXAodGblx7vSsw4YibgW/+WfZBC7wLozJH8ddcNG3V//Ssq3ttWSUAaB4Mr3WU9di0syOW9TUH2GJ/6g1M75GukDejI+vT+5/Q9M78NqE+ApvZkFn9gxO93x8cp9u7vUvybeW67jcXLWkFRltC0SP1PGWnTQBAbaxTfKzLRLMjmWakZGLMCR8RYgwdMH3zDVs8GnDz4HNMzWCh7PnFRAMlFhvCh9+EI97UKjaxa9PXAjLTQkFUbnDgTZ/+UNCFsFAIpteYUMu2NNnSDoU6jMlkgkLmX5Wn5UX+tfC5wPj+v5l9qG3OB/aXFSRt6bNyrr2tSd3jL1zxVy9i3GSRN0Ivq5FYU+XXAvo/5YLRTUeeWQ9MlGnPUguwPkdlfQzomejx8sv6NorHiCx71sKXnHSVnk1jZkny1pZACvUD9WWKm'
    user_domain_name = b"kOOiE8FcYCAubxhSo7G3eToHV/qwfx0RtPUdCzmfS3OOy1sXfWUBw0z7wxZPnJJYnxBjvb17/MhXCdIb4xniMiydxNgk62KxaWms3k9Nn6B9tlMvzPewMdzosHXc582tUQHt+SEiyWti/dZQLoaOn3kmtyf8qYrTtC4xFqK4HL2VV2ZdREFctJ7gacsw4gl2DRylOwM11KG8v1uRtypF/B/FrpQ5Kgb22q7hXXYwJJEhc2JigcLY21Am0Now5N1GfvnPCNPmIedDMlpCkcuZ8N7iNPuuKrZ20C6hXp+FM59mrxz9kNDn4OYKOaPF2AC6Cjj+vwMIn840D+abpq0dZMqSXgxWtLrygL3WOrzDHwnLQ4bhaVsdHNJDOHMoOTfc57/duKzB5AJOIJEGdL95EuNEIHPRXjFq9QTfRD7/l633cu3D2+R2DYghoI8BxlgnKRrhE7qpk3kuBb+7lVwsHEm1aJjgJRCeRGqsWJdckfIrl7kPxRfTMkQ+UCadmY6s"
    domain_name = b'FGk688AWTuC4hnXjPtrZM5b5uxICNistpbPG6stZrt01YJI6SeHIOXhBpJFW/Q+9TTsxV0Ie3JMQjsYuHBip8tTaj8F+j0PsgCvE8wXIiMYmm39MGWe/WAhGxmI1bzp3SbAoaz7i+lYzE2qK+Ae9Fp6Hx7t3Dd78m+M1EBNUceQnoTjPbX8ASDCnfWZN/4Y2Trs/if3ZgfADAcgyv0F/zhhtuSWXaRTLlXTOfnU4Qkg04/D9+aGGvjxG9eD6kkObO6g7w9RNmI8ybTzlFen9snxExnlD/wdVBUBCgypmN7gTGJSfKXCb8MTQOEsO1Bh6T4DvSXYdJtDjxQxLEan7tRGE0yKKTW6T+K0HmbYs4WaUu/KAD/0EE8BJakprAhycaSrc3jVUlXKHHY20+PlP2CBpjbc5TDHEXWOvYg2ibn//ffwrJ5JBIgFZx7+YgIszJmtQSvbQVZDEmYID8TkhU3DkBFmnmNSLkuMdFRIWcO3jof/YUqGoYd6DJvDWwqOt'
    project_name = b'PeazqqLQMcUp1VBo05AwYoHXUG3T1YflW1LZNBh/wdV+kVZFBcP7mtiFVX6Sz46lDvM7adToKvYs6qAx+0AHrQLp8/K7AyGOKOF0ca7dhwfwih9Nb1UyG3a6RfdSr4/CpAmK/Q7+P61TkIoBWZ9x3gaVqHei+6aeq/2U/004yRhV/ojU7ULvcFvpxYmv/ogelH7+fmZHV/aHrLQqtX30ymZ5tzdb3ONv0DRra+GP+TSsdTLHvfdObFyOQX9DxFj+IXoO+aluOTeOrNYpffjZepj8C/UyMKx4jpsKAuPFN1pphoSGrSY2WhXnfckBaeokhJcts+0xOFEaADiHm/AUm+4Sc/pfOAKxuBOsAB9PELpx7UicCc/dPvgdEtMIwQ9ZJcsNzoGpg4a3FZY3A6KTU9gE/TqxjPYYpPxB1Qbm6qj8cJXsTGj/xeQkTTwV6L/wqunxCKqhp4zd6ZYjSJhXWe5s034wJM4ow0HFZ4Qez+Six9hOOvwVenyUlubE/sVi'
    host = b'EvT3We35STk6arUIsaTN79siNVFP3o0Tju03Zd0QiuKJj/NYa0E0xZMSL9KUPjWrIGmKUc4b1mxpYjzI/EBTfLMYqMCfu9rd7N27Ee6Hb0GmoqPCLNRlO1FXmklw2sPFJdd6Cl7L3nDxIjfWpK0uk4aEMWdrxgwG3L/WOMPcSWkBPK8FC2WQlXXyNdPPr3vHnN9g0KWu6IWgucmbQCkNyV3PFJLJLbz96frrFA8q6QJAGO5AJPkdf3CMCcR+IedPZ6GOUXgItwLib7kLhzm5GNtE1G2kdaTDvg/Sq8addKppCmYoaGQyGO2iN8CJFHluoUoEdQSwCL7RyxUxROSjWE6+Ya0ZeARTs8IcJqq71cioMYcgqUbfmv1lB5g2xruvgWjd5PEaTSgdFWC2Uo6QSs1i2biFvnoI6TVdZZpnJdn2cPZpLd5pO6vc3iAp5YOIChuDL18FW7pidTFkQIdUaKxZqAxbMcl9xhPyLtF/WlWAirhxbx3NrktrlfumEFqp'
    event = Event()
    event.add_param("username",username)
    event.add_param('password', password)
    event.add_param('user_domain_name',user_domain_name)  
    event.add_param('domain_name',domain_name)
    event.add_param('project_name',project_name)
    event.add_param('host',host)
    event.add_param('server_id','8b3ca827-f6bf-4065-add5-0341f78a2928')
    event.add_param('address_pairs',"10.100.100.0/24, 192.168.100.0/24")
    tunnel_charm.add_address_pair(event)


