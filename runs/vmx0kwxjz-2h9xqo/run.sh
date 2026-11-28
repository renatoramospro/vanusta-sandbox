#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmx0kwxjz-2h9xqo====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmx0kwxjz-2h9xqo exit=${code}====="
exit "$code"
