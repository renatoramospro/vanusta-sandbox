#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvle9crg-sshpri====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvle9crg-sshpri exit=${code}====="
exit "$code"
