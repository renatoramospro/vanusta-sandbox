#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuj7b22m-6naevq====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuj7b22m-6naevq exit=${code}====="
exit "$code"
