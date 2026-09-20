#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmua5rjpz-puaa36====="
(
  set -e
  python 'health_check_system.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmua5rjpz-puaa36 exit=${code}====="
exit "$code"
