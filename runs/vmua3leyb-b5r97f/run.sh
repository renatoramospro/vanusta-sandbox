#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmua3leyb-b5r97f====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmua3leyb-b5r97f exit=${code}====="
exit "$code"
