#!/bin/sh
set -e

# Start zerotier-one in the background
zerotier-one &
ZT_PID=$!

# Wait for zerotier-one to initialize
sleep 5

# Join the network if the ID is set
if [ -n "$ZEROTIER_NETWORK_ID" ]; then
  zerotier-cli join "$ZEROTIER_NETWORK_ID"
else
  echo "ZEROTIER_NETWORK_ID not set!"
fi

# Wait for zerotier-one process (or tail logs to keep container running)
tail -f /dev/null 