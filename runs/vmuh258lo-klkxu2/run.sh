#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuh258lo-klkxu2====="
(
  set -e
  python 'alocador.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuh258lo-klkxu2 exit=${code}====="
exit "$code"
