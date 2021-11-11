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
    function_fail,
    function_set,
    function_get
)

config=config()
db=unitdata.kv()

#IP4
# ifconfig | echo $(awk "/^[a-z]/ { sub(\":\",\"\"); iface = \$1; getline; sub(\"addr:\", \"\"); print \"\\\"\"iface\"\\\":\",\"\\\"\"\$2\"\\\",\" }"| grep -v 127.0.0.1) | awk "{print \"{\"substr(\$0, 1, length(\$0)-1)\"}\"}"

#or

#ip addr | echo $(awk "/^[0-9]+: [a-z]/ { sub(\":\",\"\") ; sub(\":\",\"\") ; iface = \$2 ; getline ; getline ; sub(\"/[0-9]+\",\"\") ; print \"\\\"\"iface\"\\\":\",\"\\\"\"\$2\"\\\",\" }"| grep -v 127.0.0.1) | awk "{print \"{\"substr(\$0, 1, length(\$0)-1)\"}\"}"

#MACs
#ip addr | echo $(awk "/^[0-9]+: [a-z]/ { sub(\":\",\"\") ; sub(\":\",\"\") ; iface = \$2 ; getline ; print \"\\\"\"iface\"\\\":\",\"\\\"\"\$2\"\\\",\" }"| grep -v 00:00:00:00:00:00) | awk "{print \"{\"substr(\$0, 1, length(\$0)-1)\"}\"}"

#get gw ip
# route -n | grep ^0.0.0.0 | awk "{print \$2}"

#get gw mac address
# arp -n | grep "^$(route -n | grep ^0.0.0.0 | awk "{print \$2}") " | awk "{print \$3}"



#
##Actions
#

@when('actions.touch')
def touch():
    result=err = ''
    try:
        filename = function_get('filename')
        cmd = ['touch {}'.format(filename)]
        result, err = charms.sshproxy._run(cmd)
    except:
        function_fail('command failed:' + err)
    else:
        function_set({'output': result, "errors": err})
    finally:
        clear_flag('actions.touch')

#####

@when('actions.configurebridge')
def configurebridge():
    result=err = ''

    try:
        cmd = ['sudo ip addr show eth0 2>/dev/null | awk "/^[0-9]+: [a-z]/ {getline; print \$2}"']
        result, err = charms.sshproxy._run(cmd)
    except:
        function_fail('command failed:' + err)
    else:
        function_set({'output': result, "errors": err})
    finally:
        eth0MAC=result

    newEth0MAC=eth0MAC[:-1]+chr(ord(eth0MAC[-1])+1)

    try:
        cmd = ['sudo ifconfig eth0 hw ether {} 2>/dev/null'.format(newEth0MAC)]
        result, err = charms.sshproxy._run(cmd)
    except:
        function_fail('command failed:' + err)
    else:
        function_set({'output': result, "errors": err})
    
    try:
        cmd = ['sudo ovs-vsctl set bridge br-c1 other-config:hwaddr={} 2>/dev/null'.format(eth0MAC)]
        result, err = charms.sshproxy._run(cmd)
    except:
        function_fail('command failed:' + err)
    else:
        function_set({'output': result, "errors": err})

    try:
        cmd = ['sudo ifconfig eth0 up 2>/dev/null']
        result, err = charms.sshproxy._run(cmd)
    except:
        function_fail('command failed:' + err)
    else:
        function_set({'output': result, "errors": err})

    try:
        cmd = ['sudo ifdown br-c1 2>/dev/null']
        result, err = charms.sshproxy._run(cmd)
    except:
        function_fail('command failed:' + err)
    else:
        function_set({'output': result, "errors": err})

    try:
        cmd = ['sudo ifup br-c1 2>/dev/null']
        result, err = charms.sshproxy._run(cmd)
    except:
        function_fail('command failed:' + err)
    else:
        function_set({'output': result, "errors": err})
    

    clear_flag('actions.configurebridge')

######

@when('actions.getmtdinfo')
def getmtdinfo():
    result=err = ''

    try:
        vnfMgmtIp = config['ssh-hostname']
        mtdmode = config['mtd-mode']

        try:
            cmd = ['sudo ifconfig 2>/dev/null | echo $(awk "/^[a-z]/ { sub(\\":\\",\\"\\"); iface = \$1; getline; sub(\\"addr:\\", \\"\\"); print \\"\\\\\\"\\"iface\\"\\\\\\":\\",\\"\\\\\\"\\"\$2\\"\\\\\\",\\" }"| grep -v 127.0.0.1) | awk "{print \\"{\\"substr(\$0, 1, length(\$0)-1)\\"}\\"}"']
            result, err = charms.sshproxy._run(cmd)
        except:
            log('command failed:' + err)
        else:
            set_flag('mtdvdu.getinterfacesips.failed')
        finally:
            log("interfacesIps: "+result)
            interfacesAndIps=json.loads(result)

        try:
            cmd = ['sudo ip addr 2>/dev/null | echo $(awk "/^[0-9]+: [a-z]/ { sub(\\":\\",\\"\\") ; sub(\\":\\",\\"\\") ; iface = \$2 ; getline ; print \\"\\\\\\"\\"iface\\"\\\\\\":\\",\\"\\\\\\"\\"\$2\\"\\\\\\",\\" }"| grep -v 00:00:00:00:00:00) | awk "{print \\"{\\"substr(\$0, 1, length(\$0)-1)\\"}\\"}"']
            result, err = charms.sshproxy._run(cmd)
        except:
            log('command failed:' + err)
        else:
            set_flag('mtdvdu.getinterfacesmacs.failed')
        finally:
            log("interfacesMACs: "+result)
            interfacesAndMACs=json.loads(result)

        try:
            cmd = ['sudo route -n 2>/dev/null | grep ^0.0.0.0 | awk "{print \$2}" | head -n 1']
            result, err = charms.sshproxy._run(cmd)
        except:
            log('command failed:' + err)
        else:
            set_flag('mtdvdu.getgwip.failed')
        finally:
            log("gwIp: "+result)
            gwIp=result

        try:
            cmd = ['sudo arp -n 2>/dev/null | grep "^$(sudo route -n 2>/dev/null | grep ^0.0.0.0 | awk "{print \$2}" | head -n 1) " | awk "{print \$3}"']
            result, err = charms.sshproxy._run(cmd)
        except:
            log('command failed:' + err)
        else:
            set_flag('mtdvdu.getgwmac.failed')
        finally:
            log("gwMAC: "+result)
            gwMAC=result


        result=json.dumps({"mtdInternalIp":interfacesAndIps["br-c1"],"mtdPublicIp":interfacesAndIps["br-c1"],"mtdMAC":interfacesAndMACs["br-c1"],"gwIp":gwIp, "gwMAC":gwMAC, "mtdMode":mtdmode})

    except:
        function_fail('command failed:' + err)
    else:
        function_set({'output': result, "errors": err})
    finally:
        log(result)

    clear_flag('actions.getmtdinfo')

#####

@when('actions.activatemtd')
def activatemtd():
    result=err = ''

    try:
        try:
            cmd = ['sudo chmod 666 /opt/mtd-totp/authenticator/config.json 2>/dev/null']
            result, err = charms.sshproxy._run(cmd)
        except:
            function_fail('command failed:' + err)
        else:
            function_set({'output': result, "errors": err})

        try:
            ip_client=function_get('ip-client')
            mac_client=function_get('mac-client')
            ip_server=function_get('ip-server')
            mac_server=function_get('mac-server')
            mac_gw_client=function_get('mac-gw-client')
            mac_gw_server=function_get('mac-gw-server')
            ip_mtd_client_internal=function_get('ip-mtd-client-internal')
            ip_mtd_server_internal=function_get('ip-mtd-server-internal')
            ip_mtd_client_public=function_get('ip-mtd-client-public')
            ip_mtd_server_public=function_get('ip-mtd-server-public')
            mac_mtd_client=function_get('mac-mtd-client')
            mac_mtd_server=function_get('mac-mtd-server')

            real_port=config["mtd-real-port"]
            mode=config["mtd-mode"]
            interval=config["mtd-interval"]
            offset=config["mtd-offset"]
            secret=config["mtd-secret"]

            myConfig={
                "ip_client":ip_client,
                "mac_client":mac_client,
                "ip_server":ip_server,
                "mac_server":mac_server,
                "mac_gw_client":mac_gw_client,
                "mac_gw_server":mac_gw_server,
                "ip_mtd_client_internal":ip_mtd_client_internal,
                "ip_mtd_server_internal":ip_mtd_server_internal,
                "ip_mtd_client_public":ip_mtd_client_public,
                "ip_mtd_server_public":ip_mtd_server_public,
                "mac_mtd_client":mac_mtd_client,
                "mac_mtd_server":mac_mtd_server,
                "real_port":real_port,
                "mode":mode,
                "interval":interval,
                "offset":offset,
                "secret":secret
            }

            log("MTD config: "+json.dumps(myConfig))

            cmd = ["echo '{}' > /opt/mtd-totp/authenticator/config.json".format(json.dumps(myConfig))]
            result, err = charms.sshproxy._run(cmd)
        except Exception as e:
            log('command failed:' + str(e))
        else:
            set_flag('mtdvdu.activatemtd.writefile.failed')


        try:
            cmd = ['sudo systemctl start authenticator.service 2>/dev/null']
            result, err = charms.sshproxy._run(cmd)
        except Exception as e:
            log('command failed:' + str(e))
        else:
            set_flag('mtdvdu.activatemtd.authenticator.failed')
        
    except:
        function_fail('command failed:' + err)
    finally:
        log(result)
        clear_flag('actions.activatemtd')
