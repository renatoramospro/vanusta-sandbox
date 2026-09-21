#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmubbefzy-244i6x====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmubbefzy-244i6x exit=${code}====="
exit "$code"
