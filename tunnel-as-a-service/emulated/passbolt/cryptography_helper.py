import logging
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa,padding
from cryptography.hazmat.primitives.serialization import load_pem_private_key, load_pem_public_key, load_ssh_public_key
import base64

# Logger
logging.basicConfig(
    format="%(module)-15s:%(levelname)-10s| %(message)s",
    level=logging.INFO
)
class CryptographyHelper:
    def __init__(self) -> None:
        self.public_key = None
        self.private_key = None
        self.digest='SHA-256'

    def get_digest(self):
        if self.digest == 'SHA-256':
            return hashes.SHA256()

    
    def load_private_key(self,key_path):

        try:
            self.private_key = load_pem_private_key(
                open(key_path).read().encode('utf-8'),
                password=None
            )
        except Exception as e:
            logging.error(f"Could not load private key!: {e}")
            return False
        return isinstance(self.private_key,rsa.RSAPrivateKey)

    def load_public_key(self,key_path,is_file=True):

        try:
            if is_file:
                data = open(key_path).read()
            else:
                data = key_path
            if(type(data)==str):
                data= data.encode('utf-8')
            self.public_key = load_pem_public_key(
                data
            )

        except Exception as e:
            logging.error(f"Could not load public key!: {e}")
            return False

        return isinstance(self.private_key,rsa.RSAPublicKey)

    def encrypt_data(self,data):
        if self.public_key:
            ciphered_message = self.public_key.encrypt(
                        data.encode('utf-8'),
                        padding.OAEP(
                            mgf=padding.MGF1(algorithm=self.get_digest()),
                            algorithm=self.get_digest(),
                            label=None)
                        )
            logging.info("Sucessfully encrypted message")
            return base64.b64encode(ciphered_message)
        logging.error("A public and private key must be loaded firstly")
        return None

    def decrypt_data(self,data):
        data = base64.b64decode(data)
        if self.private_key:
            message = self.private_key.decrypt(
                        data,
                        padding.OAEP(
                            mgf=padding.MGF1(algorithm=self.get_digest()),
                            algorithm=self.get_digest(),
                            label=None)
                        ).decode()
            logging.info("Sucessfully decrypted message")
            return message
        logging.error("A private key must be loaded firstly")
        return None



