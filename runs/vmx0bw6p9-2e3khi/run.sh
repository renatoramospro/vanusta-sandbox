#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmx0bw6p9-2e3khi====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmx0bw6p9-2e3khi exit=${code}====="
exit "$code"
