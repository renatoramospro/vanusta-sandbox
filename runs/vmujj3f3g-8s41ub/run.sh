#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmujj3f3g-8s41ub====="
(
  set -e
  python 'service_discovery.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmujj3f3g-8s41ub exit=${code}====="
exit "$code"
