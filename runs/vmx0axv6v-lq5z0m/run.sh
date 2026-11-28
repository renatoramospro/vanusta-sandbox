#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmx0axv6v-lq5z0m====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmx0axv6v-lq5z0m exit=${code}====="
exit "$code"
