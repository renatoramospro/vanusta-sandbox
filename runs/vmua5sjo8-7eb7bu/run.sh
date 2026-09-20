#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmua5sjo8-7eb7bu====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmua5sjo8-7eb7bu exit=${code}====="
exit "$code"
