#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmubbyhqn-pilsu7====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmubbyhqn-pilsu7 exit=${code}====="
exit "$code"
