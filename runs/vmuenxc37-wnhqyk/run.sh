#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuenxc37-wnhqyk====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuenxc37-wnhqyk exit=${code}====="
exit "$code"
