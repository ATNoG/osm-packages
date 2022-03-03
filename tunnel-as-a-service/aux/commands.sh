#!/bin/bash
SCRIPT=$(readlink -f $0)
SCRIPTPATH=`dirname $SCRIPT`
ACTION_PARAMETERS=$SCRIPTPATH/actions_parameters/

CHARM_UNIT_ID=1

actions=(
    "get-wireguard-base-info"
    "get-vnf-ip"
    "add-peer"
    "get-ip-route - 1"
    "ip-route-management - 1"
    "ip-route-management - 2"
    "get-ip-route - 2"
    "ip-route-management - 3"
    "get-ip-route - 3"
    "get-peers (all)"
    "get-peers (given publik_key)"
    "get-peers (given endpoint_ip)"
    "update-peer-endpoint (given publik_key)"
    "update-peer-endpoint (given endpoint_ip)"
    "update-peer-allowed-ips (add network)"
    "update-peer-allowed-ips (delete network)"
    "delete-peer"
    )
commands=(
    "juju run-action tunnel-as-a-service/$CHARM_UNIT_ID get-wireguard-base-info --wait" 
    "juju run-action tunnel-as-a-service/$CHARM_UNIT_ID get-vnf-ip --wait"
    "juju run-action tunnel-as-a-service/$CHARM_UNIT_ID add-peer --params $ACTION_PARAMETERS/add_peer_1.yaml --wait"
    "juju run-action tunnel-as-a-service/$CHARM_UNIT_ID get-ip-routes --wait"
    "juju run-action tunnel-as-a-service/$CHARM_UNIT_ID ip-route-management --params $ACTION_PARAMETERS/ip_route_management_1.yaml --wait"
    "juju run-action tunnel-as-a-service/$CHARM_UNIT_ID ip-route-management --params $ACTION_PARAMETERS/ip_route_management_2.yaml --wait"
    "juju run-action tunnel-as-a-service/$CHARM_UNIT_ID get-ip-routes --wait"
    "juju run-action tunnel-as-a-service/$CHARM_UNIT_ID ip-route-management --params $ACTION_PARAMETERS/ip_route_management_3.yaml --wait"
    "juju run-action tunnel-as-a-service/$CHARM_UNIT_ID get-ip-routes --wait"
    "juju run-action tunnel-as-a-service/$CHARM_UNIT_ID get-peers --wait"
    "juju run-action tunnel-as-a-service/$CHARM_UNIT_ID get-peers --params $ACTION_PARAMETERS/get_peers_1.yaml --wait"
    "juju run-action tunnel-as-a-service/$CHARM_UNIT_ID get-peers --params $ACTION_PARAMETERS/get_peers_2.yaml --wait"
    "juju run-action tunnel-as-a-service/$CHARM_UNIT_ID update-peer-endpoint --params $ACTION_PARAMETERS/update_peer_endpoint_1.yaml --wait"
    "juju run-action tunnel-as-a-service/$CHARM_UNIT_ID update-peer-endpoint --params $ACTION_PARAMETERS/update_peer_endpoint_2.yaml --wait"
    "juju run-action tunnel-as-a-service/$CHARM_UNIT_ID update-peer-allowed-ips --params $ACTION_PARAMETERS/update_peer_allowed_ips_1.yaml --wait"
    "juju run-action tunnel-as-a-service/$CHARM_UNIT_ID update-peer-allowed-ips --params $ACTION_PARAMETERS/update_peer_allowed_ips_2.yaml --wait"
    "juju run-action tunnel-as-a-service/$CHARM_UNIT_ID delete-peer --params $ACTION_PARAMETERS/delete_peer.yaml --wait"
    )

for i in ${!actions[@]};
do
    if [ $i -ge 16 ]; then
        action=${actions[$i]}
        echo -e "\n\n\n*-----Action $action----*"
        echo $command
        $command
        echo -e "*-----End of Action $action----*\n"
    fi
done