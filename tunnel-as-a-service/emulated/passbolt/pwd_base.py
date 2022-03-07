from passbolt.cryptography_helper import CryptographyHelper
from wg.command import Command
import passbolt.constants as Constants
import json
import logging
import base64

# Logger
logging.basicConfig(
    format="%(module)-15s:%(levelname)-10s| %(message)s",
    level=logging.INFO
)
class PwdBase:

    def __init__(self,tunnel_charm, aux) -> None:
        self.tunnel_charm = tunnel_charm
        self.aux = aux
        self.cryptography = CryptographyHelper()
    

    def install_openstack_wrapper(self,event):
        if self.tunnel_charm.model.unit.is_leader():

            url = Constants.ARTIFACTORY_FILE
            commands = [
                Command(
                    None,
                    f"wget -q {url}",
                    "Getting OpenStack Wrapper...",
                    "Openstack Wrapper retrieved.",
                    "Could not get Openstack Wrapper"
                ),
                Command(
                    None,
                    "sudo apt install python3-pip",
                    "Installing pip",
                    "Pip installed",
                    "Could not install pip"
                ),
                Command(
                    None,
                    "tar -xzf openstackutils.tar.gz",
                    "Extracting files",
                    "Files Extracted",
                    "Could not extract files"
                ),
                Command(
                    None,
                    F"pip3 install -r {Constants.WRAPPER_DIR}/requirements.txt",
                    "Installing python requirements",
                    "Python requirements installed",
                    "Could not install python requirements"
                )
            ]
            self.aux.execute_commands_list(commands)
        else:
            event.fail("Unit is not leader")


    def configure_key_gen(self, event):
        if self.tunnel_charm.model.unit.is_leader():
            commands = [
                Command(None,
                "\"yes y | ssh-keygen  -f {} -q -m pem -N '' \"".format(
                    Constants.PRIVATE_KEY_FILEPATH
                ),
                "Creating key pair...",
                "Created key pair",
                "Could not create key pair"
                ),
                Command(None,
                f'sudo cat {Constants.PUBLIC_KEY_FILEPATH}',
                "Checking Public key...",
                "Public key okay",
                "Could not validate Public key!"
                ),
                Command(None,
                "\"ssh-keygen -e -f {} -m PKCS8  > {}.pkcs8 \"".format(
                    Constants.PUBLIC_KEY_FILEPATH, Constants.PUBLIC_KEY_FILEPATH
                ),
                "Converting Public key to PKCS8 format..",
                "Converted public key to PKCS8 format",
                "Could not convert key to PKCS8 format"
                )
                
            
            ]
            self.aux.execute_commands_list(commands)
        else:
            event.fail("Unit is not leader")
        
    def get_public_key(self,event):
        if self.tunnel_charm.model.unit.is_leader():
            command = Command(None,
            f'sudo cat {Constants.PUBLIC_KEY_FILEPATH}.pkcs8',
            "Getting Public key...",
            "Public key Retrieved",
            "Could not Get Public key!"
            )
            ret = self.aux.execute_command(command)
            public_key = ret['output']

            event.set_results({'output': public_key, 'errors':''})
            return True
        else:
            event.fail("Unit is not leader")
    
    def add_address_pair(self, event):
        server_id = event.params['server_id'].strip()
        addresses = ''.join(event.params['address_pairs'].split())
        if self.tunnel_charm.model.unit.is_leader():
            command = Command(
                None,
                "\"export OS_USERNAME={} \
                && export OS_PASSWORD={} \
                && export OS_USER_DOMAIN_NAME={} \
                && export OS_PROJECT_DOMAIN_NAME={} \
                && export OS_PROJECT_NAME={}  \
                && export OS_HOST={} \
                && cd {}  \
                && python3 openstackinterfaces.py -server_id {} -ips {} \"".format(
                    event.params['username'].decode(),
                    event.params['password'].decode(),
                    event.params['user_domain_name'].decode(),
                    event.params['domain_name'].decode(),
                    event.params['project_name'].decode(),
                    event.params['host'].decode(),
                    Constants.WRAPPER_DIR,
                    server_id,
                    addresses
                ),
                "Setting Environment Variables on VNF..",
                "Environment Variables Set",
                "Could not Set Environment Variables."
            )
            self.aux.execute_command(command)
            event.set_results({'output': 'Sucessfully sent encrypted credentials and added the address pairs',
             'errors':''})
        else:
            event.fail("Unit is not leader")