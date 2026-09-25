#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuhmamz0-piou0n====="
(
  set -e
  python 'dns_iterative_server.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuhmamz0-piou0n exit=${code}====="
exit "$code"
