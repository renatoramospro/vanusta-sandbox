#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvd3hb6m-21auoq====="
(
  set -e
  python 'ldap_auth_simulator.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvd3hb6m-21auoq exit=${code}====="
exit "$code"
