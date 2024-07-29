#!/bin/sh

if [ "$VPN_ENABLED" = "true" ]; then
    echo "VPN is enabled, starting with VPN..."
    /app/python-version/scripts/start_vpn.sh
    sleep 15
    # Check VPN status or connectivity
    # Start the main service with VPN
else
    echo "VPN is not enabled, starting normally..."
    # Start the main service without VPN
fi

python /app/python-version/utils/run_all_commands_linux.py

# Keep the container running
tail -f /dev/null
