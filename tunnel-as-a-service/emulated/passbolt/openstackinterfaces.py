import requests
import os
import datetime
import dateutil.parser
import logging
import constants as Constants
from cryptography_helper import CryptographyHelper
import sys
import argparse
# Logger
logging.basicConfig(
    format="%(module)-15s:%(levelname)-10s| %(message)s",
    level=logging.INFO
)

class OpenStackInterfaceManager:
    def __init__(self) -> None:
        self.user_domain_name = None
        self.username =  None
        self.password = None
        self.domain_name = None
        self.projectname = None
        self.host = None
        self.auth_endpoint='/identity/v3/auth/tokens?nocatalog'
        self.nova_endpoint='/compute/v2.1'
        self.token = None
        self.expire_time = None
        self.cryptography = CryptographyHelper()
        self.decrypt_and_set_variables()
    

    def decrypt_and_set_variables(self):
        logging.info("started decription")
        self.cryptography.load_private_key(f'{Constants.PYTHON_PRIVATE_KEY_FILE_PATH}')
        self.user_domain_name = self.cryptography.decrypt_data(os.getenv('OS_USER_DOMAIN_NAME'))
        self.username = self.cryptography.decrypt_data(os.getenv('OS_USERNAME'))
        self.password = self.cryptography.decrypt_data(os.getenv('OS_PASSWORD'))
        self.domain_name = self.cryptography.decrypt_data(os.getenv('OS_PROJECT_DOMAIN_NAME'))
        self.projectname = self.cryptography.decrypt_data(os.getenv('OS_PROJECT_NAME'))
        self.host = self.cryptography.decrypt_data(os.getenv('OS_HOST'))
        
    def require_auth(func, *args, **kwargs):
        def wrapper(self, *args, **kwargs):
            if self.has_expired():
                logging.info("Token has expired. Authenticating again...")
                self.authenticate()
            return func(self, *args, **kwargs)
        return wrapper

    def has_expired(self):
        if self.token and self.expire_time:
            return self.expire_time<datetime.datetime.now(self.expire_time.tzinfo)
        return True

    def authenticate(self):
        obj = { "auth": { "identity": { "methods": ["password"],
        "password": {"user": {"domain": {"name": f"{self.user_domain_name}"},"name": f"{self.username}",
        "password": f"{self.password}"} } }, "scope": { "project": { "domain": { "name": f"{self.domain_name}" },
        "name":  f"{self.projectname}" } } }}
        r = requests.post(url=f'{self.host}{self.auth_endpoint}',json=obj,verify=False)
        logging.info("Authentication Sucessful")
        print(r.text)
        self.token = r.headers['X-Subject-Token']
        self.expire_time = dateutil.parser.parse(str(r.json()['token']['expires_at']))

    @require_auth
    def get_server_details(self,server_id='1594869a-21f8-42c9-8473-4766340cb57f'):
        print(self.token)
        servers = requests.get(url=f'{self.host}{self.nova_endpoint}/servers',headers={'X-Auth-Token': f'{self.token}'},verify=False)
        servers_list = servers.json()['servers']
        choosen_server = None
        for server in servers_list:
            if server['id'] == server_id:
                choosen_server = server
        logging.info(f"Retrieved Server details for instance with id {server_id}")
        return choosen_server

    @require_auth
    def get_server_ports(self,_id='1594869a-21f8-42c9-8473-4766340cb57f'):
        try:
            servers = requests.get(url=f'{self.host}{self.nova_endpoint}/servers/{_id}/os-interface',headers={'X-Auth-Token': f'{self.token}'},verify=False)
            if servers.status_code != 200:
                logging.error(f"Could not find any server with id {_id}")
            ports_id_list = [x['port_id'] for x in servers.json()['interfaceAttachments']]
            logging.info(f"Retrieved all interfaces for server with id {_id}")
        except Exception as e:
            logging.error(f"Could not obtain server Interfaces. Reason: {e}")
            return None
        return ports_id_list

    @require_auth
    def add_address_pair(self,ports_id_list, ip_addresses):
        lst_addresses = [ {'ip_address': x } for x in ip_addresses.split(',')]
        obj={'port': {'allowed_address_pairs': lst_addresses  }}
        if self.host[-1] == '/':
            self.host= self.host[:-1]

        for port_id in ports_id_list:
            try:
                _ = requests.put(url=f'{self.host}:9696/v2.0/ports/{port_id}',headers={'X-Auth-Token': f'{self.token}'}, json=obj,verify=False)
                logging.info(f"Added address pair for interface with id {port_id}")
            except Exception as e:
                logging.error(f"Could not add address pair. Reason: {e}")


    
def usage():
    print("Usage: python3 main.py\
        \n\t-server_id <UUID of the server to add the address pairs:str>\
        \n\t-ips <IP addresses pairs to be allowed:str>")

arg_parser = argparse.ArgumentParser(
        prog="OpenStackInterfaceManager",
        usage=usage
    )
arg_parser.add_argument('-server_id',type=str, nargs=1,required=True)
arg_parser.add_argument('-ips', nargs=1, default=['10.100.100.0/24, 192.168.100.0/24'])

def check_arguments():
    try:
        args = arg_parser.parse_args()
    except:
        usage()
        sys.exit(0)
    return args


if __name__ == '__main__':

    args= check_arguments()
    manager = OpenStackInterfaceManager()
    ports_list = manager.get_server_ports(args.server_id[0])
    manager.add_address_pair(ports_list, args.ips[0])
