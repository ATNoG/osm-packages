import glob
import json
from charms.reactive import (
    hook,
    clear_flag,
    when,
    when_not,
    set_flag
)

import charms.sshproxy
from charmhelpers.core import hookenv, unitdata
from charmhelpers.core.hookenv import (
    application_version_set,
    config,
    log,
    status_set,
    action_fail,
    action_set,
    action_get
)

# sudo ethtool -s ens3 speed 100 duplex full autoneg off


#IP4
# ifconfig | echo $(awk "/^[a-z]/ { sub(\":\",\"\"); iface = \$1; getline; sub(\"addr:\", \"\"); print \"\\\"\"iface\"\\\":\",\"\\\"\"\$2\"\\\",\" }"| grep -v 127.0.0.1) | awk "{print \"{\"substr(\$0, 1, length(\$0)-1)\"}\"}"

#or

#ip addr | echo $(awk "/^[0-9]+: [a-z]/ { sub(\":\",\"\"); iface = \$2 ; getline ; getline ; sub(\"/[0-9]+\",\"\") ; print \"\\\"\"iface\"\\\":\",\"\\\"\"\$2\"\\\",\" }"| grep -v 127.0.0.1) | awk "{print \"{\"substr(\$0, 1, length(\$0)-1)\"}\"}"

#MACs
#ip addr | echo $(awk "/^[0-9]+: [a-z]/ { sub(\":\",\"\"); iface = \$2 ; getline ; print \"\\\"\"iface\"\\\":\",\"\\\"\"\$2\"\\\",\" }"| grep -v 00:00:00:00:00:00) | awk "{print \"{\"substr(\$0, 1, length(\$0)-1)\"}\"}"

config=config()
db=unitdata.kv()

@when('sshproxy.configured')
@when_not('interdomainvdu.installed')
def install_packages():
    status_set('maintenance', 'Installing wireguard')
    result=err = ''
    try:
        package="wireguard"
        cmd = ['sudo apt update']
        result, err = charms.sshproxy._run(cmd)

        log("updated packages")
        cmd = ['sudo apt install {} -y'.format(package)]
        result, err = charms.sshproxy._run(cmd)

        cmd = ['sudo apt install {} -y'.format("net-tools")]    
        result, err = charms.sshproxy._run(cmd)
        set_flag('interdomainvdu.apt.installed')
        status_set('maintenance', 'Package Wireguard Installed')
    except:
        log('command failed:' + err)
        set_flag('interdomainvdu.apt.not_installed')
        status_set('error', 'Unable to install packages')

@when('interdomainvdu.apt.installed')
@when_not('interdomainvdu.installed')
def wireguard_version_check():
    log('setting application version')
    
    result=err = ''
    
    try: 
        cmd = ['wg --version']
        result, err = charms.sshproxy._run(cmd)
    except:
        log('command failed:' + err)
        log('wireguard not installed')
    finally:
        status_set('maintenance', result)
        
        # files=glob.glob("files/*key")
        # count=0

        # if not config['wg_server']:
        #     set_flag('config.keygen')
        # else:
        #     for x in files:
        #         with open(x) as f:
        #             if f.read() is not None:
        #                 count+=1        
        #         f.close()
        #     if count==2:
        set_flag('config.keygen')
        # else:
        #     set_flag('config.loadkey')

@when('config.keygen')
@when_not('interdomainvdu.installed')
def configuration_keygen():
    status_set('maintenance', 'Wireguard Key generation')
        
    private_key_path="/etc/wireguard/privatekey"
    public_key_path="/etc/wireguard/publickey"
    key_location=[private_key_path,public_key_path]
 
    log('Key Generation start')
    result=err = ''
    
    try:
        
        cmd = ['wg genkey | sudo tee {} | wg pubkey | sudo tee {}'.format(key_location[0],key_location[1])]
        result, err = charms.sshproxy._run(cmd)
    except:
        log('command failed:' + err)
        set_flag('keygen.failed')
    finally:
        set_flag('keygen.done')
        status_set('maintenance', 'Keygen Done')
    
        status_set('maintenance',result)
    
    for x in key_location:
        result=err = ''
        try:
            cmd = ['sudo cat {}'.format(x)]
            result, err = charms.sshproxy._run(cmd)
            log(x+":"+result)
        except:
            log('command failed:' + err)
            log('cat '+x+' failed')
            set_flag('keygen.failed')
        
    set_flag('keygen.done')
    log("Key Generation done")
    # if config['wg_server']: 
    #     set_flag('interdomainvdu.server.config')
    # else:
    set_flag('interdomainvdu.tunnel.config')

@when('config.loadkey')
@when_not('interdomainvdu.installed')
def configuration_loadkey():
    status_set('maintenance', 'Wireguard Load Keys')

    private_key_path="/etc/wireguard/privatekey"
    public_key_path="/etc/wireguard/publickey"
    key_location=[private_key_path,public_key_path]
    
    for x in key_location:
        key=""
        y="files/"+x.lstrip('/etc/wireguard/')
        
        with open(y,'r') as f:
            key=f.read()
        f.close()
        result=err = ''
        try:
            cmd = ['echo {} |sudo tee {}'.format(key,x)]
            result, err = charms.sshproxy._run(cmd)
        except:
            log('command failed:' + err)
            set_flag('interdomainvdu.load.keys.failed')
        finally:
            key=result
    status_set('maintenance', 'Load Keys')
    set_flag('interdomainvdu.tunnel.config')

@when('interdomainvdu.tunnel.config')
@when_not('interdomainvdu.installed')
def wireguard_server_configuration():
    status_set('maintenance', 'Server wireguard configuration started')
    result=err = ''
    try:
        filename="/etc/wireguard/privatekey"
        cmd = ['sudo cat {}'.format(filename)]
        result, err = charms.sshproxy._run(cmd)
    except:
        log('command failed:' + result+"|"+err)
        set_flag('interdomainvdu.load.keys.failed')
    finally:
        key=result
  
    conf="/etc/wireguard/"+config['forward_interface']+".conf"

    wg_conf="[Interface]\nAddress = "+config['tunnel_address']+"\nSaveConfig = "+str(config['save_config'])+"\nListenPort = "+str(config['listen_port'])+"\nPrivateKey = "+key+"\n\n"

    # \nPostUp = iptables -A FORWARD -i %i -j ACCEPT; iptables -t nat -A POSTROUTING -o "+config['forward_interface']+" -j MASQUERADE"+"\nPostDown = iptables -D FORWARD -i %i -j ACCEPT; iptables -t nat -D POSTROUTING -o "+config['forward_interface']+" -j MASQUERADE

    # """[Interface]
    # Address = server_tunnel_address
    # SaveConfig = save_config
    # ListenPort = listen_port
    # PrivateKey = key
    # PostUp = iptables -A FORWARD -i %i -j ACCEPT; iptables -t nat -A POSTROUTING -o forward_interface -j MASQUERADE
    # PostDown = iptables -D FORWARD -i %i -j ACCEPT; iptables -t nat -D POSTROUTING -o forward_interface -j MASQUERADE"""

    log(wg_conf)

    result = err = ''

    try:
        cmd = ['sudo sysctl -w net.ipv4.ip_forward=1']
        result, err = charms.sshproxy._run(cmd)

        log(result)
        set_flag('wireguard.ipforwarding.enabled')
    except:
        log('command failed:' + result+"|"+err)
        set_flag('wireguard.server.config.failed')

    result=err = ''
    try:
        cmd = ['echo "{}" |sudo tee {}'.format(wg_conf,conf)]
        result, err = charms.sshproxy._run(cmd)
        log(result)
        set_flag('wireguard.start')
    except:
        log('command failed:' + result+"|"+err)
        set_flag('wireguard.server.config.failed')
    

@when('wireguard.start')
@when_not('interdomainvdu.installed')
def start_wireguard():

    status_set('maintenance','Wireguard quick start')
    result=err = ''
    try:
        forward_interface=config['forward_interface']
        
        cmd = ['sudo wg-quick up {}'.format(forward_interface)]
        result, err = charms.sshproxy._run(cmd)
        log(result)
    except:
        log('command failed:' + err)
        set_flag('wireguard.server.start.failed')

    log("Wireguard interface up:\n"+result)
    
    result=err = ''
    try:
        cmd = ['sudo wg show {}'.format(config['forward_interface'])]
        result, err = charms.sshproxy._run(cmd)
        log(result)
    except:
        log('command failed:' + err)
        set_flag('wireguard.server.config.failed')

    # result=err = ''
    # try:
    #     cmd = ['sudo dhclient']
    #     result, err = charms.sshproxy._run(cmd)
    #     log(result)
    # except:
    #     log('command failed:' + err)
    #     set_flag('wireguard.server.config.failed')
    
    log("Wireguard config:\n"+result)
    status_set('active','Wireguard installed and configured')
    set_flag('interdomainvdu.installed')
    status_set('active', 'Ready!')

#
##Actions
#

@when('actions.touch')
@when('interdomainvdu.installed')
def touch():
    result=err = ''
    try:
        filename = action_get('filename')
        cmd = ['touch {}'.format(filename)]
        result, err = charms.sshproxy._run(cmd)
    except:
        action_fail('command failed:' + err)
    else:
        action_set({'output': result, "errors": err})
    finally:
        clear_flag('actions.touch')

##############

@when('actions.addpeer')
@when('interdomainvdu.installed')
def addpeer():
    result=err = ''

    try:           
        cmd = ['sudo wg-quick down {}'.format(config['forward_interface'])]
        result, err = charms.sshproxy._run(cmd)
    except:
        action_fail('command failed:' + err)
        log('command failed:' + err)
    else:
        action_set({'output': result, "errors": err})
    finally:
        log(result)

    result=err = ''

    try:
        peer_key= action_get('peer_key')
        peer_endpoint = action_get('peer_endpoint')
        peer_network= action_get('peer_network')
  
        conf="/etc/wireguard/"+config['forward_interface']+".conf"
        wgconf="\n\n[Peer]\nPublicKey= "+peer_key+"\nEndpoint = "+peer_endpoint+":"+str(config['listen_port'])+"\nAllowedIPs = "+peer_network+"\n\n"

        # """[Peer]
        # PublicKey= peer_key
        # Endpoint = peer_endpoint
        # AllowedIPs = peer_network"""


        cmd = ['echo "{}" | sudo tee -a {}'.format(wgconf,conf)]
        log(cmd)
        result, err = charms.sshproxy._run(cmd)
    except:
        action_fail('command failed:' + err)
    else:
        action_set({'output': result, "errors": err})
    finally:
        log(result)
    
    try:           
        cmd = ['sudo wg-quick up {}'.format(config['forward_interface'])]
        result, err = charms.sshproxy._run(cmd)
    except:
        action_fail('command failed:' + err)
        log('command failed:' + err)
    else:
        action_set({'output': result, "errors": err})
    finally:
        log(result)

    clear_flag('actions.addpeer')

####

@when('actions.sendvnfinfo')
@when('interdomainvdu.installed')
def sendVnfIp():
    result=err = ''

#     try:
#         use_data_interfaces = config['use_data_interfaces']
#         vnfMgmtIp = config['ssh-hostname']
#         tunnelAddress = config['tunnel_address']
#         tunnelId = config['tunnel_id']
#         vsiId = config['vsi_id']
#         vsEndpoint = action_get('vsEndpoint')

#         bandwidth = config['bandwidth']

#         log(config)

#         try:
#             cmd = ['ifconfig | echo $(awk "/^[a-z]/ { sub(\\":\\",\\"\\"); iface = \$1; getline; sub(\\"addr:\\", \\"\\"); print \\"\\\\\\"\\"iface\\"\\\\\\":\\",\\"\\\\\\"\\"\$2\\"\\\\\\",\\" }"| grep -v 127.0.0.1) | awk "{print \\"{\\"substr(\$0, 1, length(\$0)-1)\\"}\\"}"']
#             result, err = charms.sshproxy._run(cmd)
#         except:
#             log('command failed:' + err)
#         else:
#             set_flag('interdomainvdu.getinterfaces.failed')
#         finally:
#             log("interfaces: "+result)
#             interfacesAndIps=json.loads(result)

#         try:
#             filename="/etc/wireguard/publickey"
#             cmd = ['sudo cat {}'.format(filename)]
#             result, err = charms.sshproxy._run(cmd)
#         except:
#             log('command failed:' + err)
#         else:
#             set_flag('interdomainvdu.load.keys.failed')
#         finally:
#             publicKey=result


#         if use_data_interfaces:
#             if len(interfacesAndIps)==3:

#                 vnfMgmtIp=vnfMgmtIp.split("/")[0]
#                 tunnelAddress=tunnelAddress.split("/")[0]

#                 for key, value in interfacesAndIps.items():
#                     if str(value) != str(vnfMgmtIp) and str(value) != str(tunnelAddress):
#                         log("found data interface: "+key+", ip: "+value)
#                         vnfIp=str(value)
#                         config["data_address"]=vnfIp
#                         config["data_interface"]=str(key)
#                         db.set("data_interface", str(key))
#                         db.flush()
#                         break

#                 try:
#                     log("using interface: "+key)
#                     cmd = ['sudo tc qdisc add dev {} root cake bandwidth {}mbit'.format(key, bandwidth)]
#                     result, err = charms.sshproxy._run(cmd)
#                     log("enabled tc-cake to interface")
#                 except:
#                     log('command failed:' + result)
#                     log('command failed:' + err)
#                     set_flag('interdomainvdu.tccakeaddinterface.failed')

#                 data={"vsiId":vsiId,"publicKey": publicKey,"vnfIp":vnfIp, "tunnelId":tunnelId}
    
#                 cmd = ['curl -X POST -H "Content-Type: application/json"  -d {} {}'.format(json.dumps(json.dumps(data)),vsEndpoint)]
#                 log(cmd)
#                 result, err = charms.sshproxy._run(cmd)
#             else:
#                 log('Expecting 3 network interfaces')
#                 action_fail('Expecting 3 network interfaces')

#         else:
#             vnfMgmtIp=vnfMgmtIp.split("/")[0]

#             data={"vsiId":vsiId,"publicKey": publicKey,"vnfIp":vnfMgmtIp, "tunnelId":tunnelId}

#             cmd = ['curl -X POST -H "Content-Type: application/json"  -d {} {}'.format(json.dumps(json.dumps(data)),vsEndpoint)]
#             log(cmd)
#             result, err = charms.sshproxy._run(cmd)

#     except:
#         action_fail('command failed:' + err)
#     else:
#         action_set({'output': result, "errors": err})
#     finally:
#         log(result)

#     clear_flag('actions.sendvnfinfo')


@when('actions.getvnfinfo')
@when('interdomainvdu.installed')
def getVnfIp():
    result=err = ''

    try:
        # use_data_interfaces = config['use_data_interfaces']
        vnfMgmtIp = config['ssh-hostname']
        tunnelId = config['tunnel_id']
        vsiId = config['vsi_id']

        # bandwidth = config['bandwidth']

        use_data_interfaces = config['use_data_interfaces']
        if use_data_interfaces:
            interface="ens4"
        else:
            interface="ens3"

        # ifconfig | echo $(awk "/^[a-z]/ { sub(\\":\\",\\"\\"); iface = \$1; getline; sub(\\"addr:\\", \\"\\"); print \\"\\\\\\"\\"iface\\"\\\\\\":\\",\\"\\\\\\"\\"\$2\\"\\\\\\",\\" }"| grep -v 127.0.0.1) | awk "{print \\"{\\"substr(\$0, 1, length(\$0)-1)\\"}\\"}"
        try:
            cmd = ["sudo ip a show {} | grep inet | head -n1 | awk '{{print substr($2, 1, length($2)-3)}}'".format(interface)]
            result, err = charms.sshproxy._run(cmd)
        except:
            log('command failed:' + err)
        else:
            set_flag('interdomainvdu.getvnfip.failed')
        finally:
            log("vnfIp: "+result)
            vnfIp=result

        # sudo ip addr 2>/dev/null | echo $(awk "/^[0-9]+: [a-z]/ { sub(\\":\\",\\"\\") ; sub(\\":\\",\\"\\") ; iface = \$2 ; getline ; print \\"\\\\\\"\\"iface\\"\\\\\\":\\",\\"\\\\\\"\\"\$2\\"\\\\\\",\\" }"| grep -v 00:00:00:00:00:00) | awk "{print \\"{\\"substr(\$0, 1, length(\$0)-1)\\"}\\"}"
        try:
            cmd = ["sudo ip a show {} | grep link/ether | head -n1 | awk '{{print $2}}'".format(interface)]
            result, err = charms.sshproxy._run(cmd)
        except:
            log('command failed:' + err)
        else:
            set_flag('interdomainvdu.getvnfmac.failed')
        finally:
            log("vnfMac: "+result)
            vnfMac=result

        # sudo arp -n 2>/dev/null | grep "^$(sudo route -n 2>/dev/null | grep ^0.0.0.0 | awk "{print \$2}" | head -n 1) " | awk "{print \$3}"
        try:
            cmd = ["IP=\"$(sudo ip r | grep {} | grep via | head -n1 | awk '{{print $3}}')\";XX=$(ping -c1 $IP >> /dev/null);echo $(sudo ip n | grep $IP) | awk '{{print $5}}'".format(interface)]
            result, err = charms.sshproxy._run(cmd)
        except:
            log('command failed:' + err)
        else:
            set_flag('interdomainvdu.getgwmac.failed')
        finally:
            log("gwMAC: "+result)
            gwMAC=result

        try:
            filename="/etc/wireguard/publickey" 
            cmd = ['sudo cat {}'.format(filename)]
            result, err = charms.sshproxy._run(cmd)
        except:
            log('command failed:' + err)
        else:
            set_flag('interdomainvdu.load.keys.failed')
        finally:
            publicKey=result

        if not use_data_interfaces:
            vnfIp=vnfMgmtIp

        config["data_address"]=vnfIp
        config["data_interface"]=interface
        db.set("data_interface", interface)
        db.flush()
        result=json.dumps({"vsiId":vsiId,"publicKey": publicKey,"publicEndpoint":vnfIp, "internalEndpoint":vnfIp, "tunnelId":tunnelId,"vnfMAC":vnfMac, "gwMAC":gwMAC})
        # try:
        #     cmd = ['sudo tc qdisc add dev {} root cake bandwidth {}mbit'.format(interface, bandwidth)]
        #     result, err = charms.sshproxy._run(cmd)
        #     log("enabled tc-cake to interface")
        # except:
        #     log('command failed:' + result)
        #     log('command failed:' + err)
        #     set_flag('interdomainvdu.tccakeaddinterface.failed')
    except:
        action_fail('command failed:' + err)
    else:
        action_set({'output': result, "errors": err})
    finally:
        log(result)

    clear_flag('actions.getvnfinfo')

@when('actions.modifytunnel')
@when('interdomainvdu.installed')
def modifyTunnel():
    result=err = ''

    # try:
    #     try:
    #         bandwidth = action_get('bandwidth')
    #         # data_interface = config['data_interface']
    #         data_interface=db.get("data_interface")

    #         log("Interface to modify: "+data_interface)

    #         if data_interface == "error":
    #             action_fail('the data interface was not updated')

    #         cmd = ['sudo tc qdisc change dev {} root cake bandwidth {}mbit'.format(data_interface, bandwidth)]
    #         result, err = charms.sshproxy._run(cmd)
    #     except Exception as e:
    #         log('command failed:' + str(e))
    #     else:
    #         set_flag('interdomainvdu.modifytunnel.failed')


    # except:
    #     action_fail('command failed:' + err)
    # finally:
    #     log(result)

@when('actions.routemgmt')
@when('interdomainvdu.installed')
def ipRouteMgmt():
    result = err = ''
    try:
        try:
            allowed_ips=action_get('allowed-ips')
            action=action_get('action')
            gwaddress = action_get('gw-address')

            if action not in ["add","del"]:
                action_fail('Action not supported')

            cmd = ['sudo ip r {} {} via {}'.format(action, allowed_ips, gwaddress)]
            result, err = charms.sshproxy._run(cmd)
        except Exception as e:
            log('command failed:' + str(e))
        else:
            set_flag('interdomainvdu.routemgmt.failed')
    except:
        action_fail('command failed:' + err)
    finally:
        log(result)
    clear_flag('actions.routemgmt')