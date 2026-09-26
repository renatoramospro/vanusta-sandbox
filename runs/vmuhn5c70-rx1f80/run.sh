#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuhn5c70-rx1f80====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuhn5c70-rx1f80 exit=${code}====="
exit "$code"
