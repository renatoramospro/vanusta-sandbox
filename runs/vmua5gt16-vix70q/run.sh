#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmua5gt16-vix70q====="
(
  set -e
  python 'health_check_system.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmua5gt16-vix70q exit=${code}====="
exit "$code"
