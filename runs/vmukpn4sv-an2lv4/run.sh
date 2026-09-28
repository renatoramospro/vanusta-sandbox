#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmukpn4sv-an2lv4====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmukpn4sv-an2lv4 exit=${code}====="
exit "$code"
