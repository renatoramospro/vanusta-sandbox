#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvd3wpz3-qginun====="
(
  set -e
  python 'ldap_auth_simulator.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvd3wpz3-qginun exit=${code}====="
exit "$code"
