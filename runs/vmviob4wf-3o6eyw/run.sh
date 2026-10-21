#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmviob4wf-3o6eyw====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmviob4wf-3o6eyw exit=${code}====="
exit "$code"
