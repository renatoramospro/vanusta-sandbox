#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmucflx9m-m6zw88====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmucflx9m-m6zw88 exit=${code}====="
exit "$code"
