#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmublx7ys-o3h3vd====="
(
  set -e
  python 'registry_demo.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmublx7ys-o3h3vd exit=${code}====="
exit "$code"
