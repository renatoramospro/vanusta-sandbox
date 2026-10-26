#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvp6ks1w-6mrbgq====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvp6ks1w-6mrbgq exit=${code}====="
exit "$code"
