#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvml0plh-je8v5i====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvml0plh-je8v5i exit=${code}====="
exit "$code"
