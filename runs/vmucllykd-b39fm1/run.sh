#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmucllykd-b39fm1====="
(
  set -e
  python 'modelo_risco_definitivo.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmucllykd-b39fm1 exit=${code}====="
exit "$code"
