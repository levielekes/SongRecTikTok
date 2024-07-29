#!/bin/bash
echo 'Stoping openvpn ...'
sudo killall openvpn
ovpn_file=$(ls /etc/openvpn/surfshark-config/*udp.ovpn |sort -R |tail -1)
printf "$ovpn_file\n"
echo "$ovpn_file" > /var/log/vpn.log
sudo chmod 777 /var/log/vpn.log
source /app/.env
echo 'Starting openvpn ...'
/app/scripts/start_vpn.exp $ovpn_file $VPN_USERNAME $VPN_PASSWORD
