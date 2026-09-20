#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmu9lahuh-06r5z2====="
(
  set -e
  python 'leak_simulator.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmu9lahuh-06r5z2 exit=${code}====="
exit "$code"
