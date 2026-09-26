#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuhr85gn-1fkrsf====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuhr85gn-1fkrsf exit=${code}====="
exit "$code"
