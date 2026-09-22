#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuckysek-rvb55i====="
(
  set -e
  python 'modelo_risco.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuckysek-rvb55i exit=${code}====="
exit "$code"
