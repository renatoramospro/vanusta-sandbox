#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvca42sk-vuhd55====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvca42sk-vuhd55 exit=${code}====="
exit "$code"
