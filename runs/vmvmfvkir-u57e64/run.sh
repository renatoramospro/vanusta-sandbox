#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvmfvkir-u57e64====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvmfvkir-u57e64 exit=${code}====="
exit "$code"
