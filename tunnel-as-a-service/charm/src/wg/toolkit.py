from wg.base import WGBase
from wg.network_mgmt import NetworkMgmt
from wg.aux import WGAux
from wg.peers import WGPeers
import wgconfig
import os
from wg.command import Command
import json


import logging
# Logger
logging.basicConfig(
    format="%(module)-15s:%(levelname)-10s| %(message)s",
    level=logging.INFO
)

class WGToolkit:

    def __init__(self, tunnel_charm):
        self.tunnel_charm = tunnel_charm
        self.aux = WGAux(tunnel_charm)
        self.base = WGBase(tunnel_charm, self.aux)
        self.network_mgmt = NetworkMgmt(tunnel_charm, self.aux)
        self.peers = WGPeers(tunnel_charm, self.aux)
        
