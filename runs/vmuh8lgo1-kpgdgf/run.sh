#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuh8lgo1-kpgdgf====="
(
  set -e
  python 'vm.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuh8lgo1-kpgdgf exit=${code}====="
exit "$code"
