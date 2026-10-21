#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvia9qvb-nvkio2====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvia9qvb-nvkio2 exit=${code}====="
exit "$code"
