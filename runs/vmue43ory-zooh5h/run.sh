#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmue43ory-zooh5h====="
(
  set -e
  python 'generate_docs.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmue43ory-zooh5h exit=${code}====="
exit "$code"
