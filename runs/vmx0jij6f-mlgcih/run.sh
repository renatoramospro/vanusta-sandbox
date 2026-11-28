#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmx0jij6f-mlgcih====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmx0jij6f-mlgcih exit=${code}====="
exit "$code"
