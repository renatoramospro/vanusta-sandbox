#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmujjqnjj-nzxo7b====="
(
  set -e
  python 'service_discovery_server.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmujjqnjj-nzxo7b exit=${code}====="
exit "$code"
