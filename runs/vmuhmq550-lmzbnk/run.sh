#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuhmq550-lmzbnk====="
(
  set -e
  python 'dns_iterative_server.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuhmq550-lmzbnk exit=${code}====="
exit "$code"
