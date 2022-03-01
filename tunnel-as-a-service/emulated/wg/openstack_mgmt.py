import requests
import datetime
import dateutil.parser
import logging
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Logger
logging.basicConfig(
    format="%(module)-15s:%(levelname)-10s| %(message)s",
    level=logging.INFO
)


class OpenStackMgmt:
    def __init__(self,tunnel_charm,wg_aux) -> None:
        self.tunnel_charm = tunnel_charm
        self.wg_aux = wg_aux
        self.user_domain_name =None
        self.username =None
        self.password =None
        self.domain_name =None
        self.projectname =None
        self.auth_endpoint='/identity/v3/auth/tokens?nocatalog'
        self.nova_endpoint='/compute/v2.1'
        self.token = None
        self.expire_time = None

    def set_credentials(self,event):
        if self.tunnel_charm.model.unit.is_leader():
            self.username=event.params['username']
            self.password=event.params['password']
            self.user_domain_name=event.params['user_domain_name']
            self.domain_name = event.params['domain_name']
            self.projectname = event.params['project_name']
            self.host = self.parse_ip(event.params['host'])
            logging.info('Set OpenStack Credentials for later use')
           
            return True
        else:
            event.fail("Unit is not leader")
    def parse_ip(self,host):
        if 'https://' in host:
            return host
        else:
            host = f'https://{host}'
            return host 
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
        self.token = r.headers['X-Subject-Token']
        self.expire_time = dateutil.parser.parse(str(r.json()['token']['expires_at']))

    @require_auth
    def get_server_details(self,event):
        server_id = event.params['server_id']
        if self.tunnel_charm.model.unit.is_leader():

            servers = requests.get(url=f'{self.host}{self.nova_endpoint}/servers',
            headers={'X-Auth-Token': f'{self.token}'},verify=False)

            if servers.status_code != 200:
                event.set_results({'output':'', 'errors': f'Could not obtain server {server_id} details with success'})
                logging.error(f'Could not obtain server {server_id} details with success')
                raise Exception(f'Could not obtain server {server_id} details with success')
            servers_list = servers.json()['servers']
            choosen_server = None

            for server in servers_list:
                if server['id'] == server_id:
                    choosen_server = server
            logging.info(f"Retrieved Server details for instance with id {server_id}")
            event.set_results({'output': choosen_server, 'errors': ''})
            return True
        else:
            event.fail("Unit is not leader")
    @require_auth
    def get_server_ports(self,event):
        if self.tunnel_charm.model.unit.is_leader():

            server_id = event.params['server_id'] 
            try:
                servers = requests.get(url=f'{self.host}{self.nova_endpoint}/servers/{server_id}/os-interface',
                headers={'X-Auth-Token': f'{self.token}'},verify=False)

                if servers.status_code != 200:
                    logging.error(f"Could not get interfaces for server with id {server_id}")
                    event.set_results({'output':'', 'errors': f'Could not get interfaces for server with id {server_id}'})
                    raise Exception(f'Could not get interfaces for server with id {server_id}')

                logging.info(f"Retrieved all interfaces for server with id {server_id}")
                ports_id_list = [x['port_id'] for x in servers.json()['interfaceAttachments']]
                event.set_results({'output':ports_id_list, 'errors': ''})

            except Exception as e:
                logging.error(f"Could not obtain server Interfaces. Reason: {e}")
                return None
            return True
        else:
            event.fail('Unit is not leader')

    @require_auth
    def add_address_pairs(self,event):
        if self.tunnel_charm.model.unit.is_leader():
            ports_id_list = list(event.params['ports_id_list'])
            ip_address_list = list(event.params['ip_address_list'])
            ip_address_objs = [ {'ip_address': ip } for ip in ip_address_list]
            obj={'port': {'allowed_address_pairs': ip_address_objs }}

            for port_id in ports_id_list:
                try:
                    _ = requests.put(url=f'{self.host}:9696/v2.0/ports/{port_id}',
                    headers={'X-Auth-Token': f'{self.token}'}, json=obj,verify=False)
                    
                except Exception as e:
                    logging.error(f"Could not add address pair. Reason: {e}")
                    event.set_results({'output':'', 'errors': f'Could not add address pair. Reason: {e}'})
                    raise Exception( f'Could not add address pair. Reason: {e}')
            event.set_results({'output':'Success', 'errors': ''})
            logging.info(f"Added address pairs for interface with id {port_id}")
            return True
        else:
            event.fail('Unit is not leader')


