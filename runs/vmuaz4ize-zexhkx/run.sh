#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuaz4ize-zexhkx====="
(
  set -e
  python 'network_sync_sim.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuaz4ize-zexhkx exit=${code}====="
exit "$code"
