#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmukcw094-cwrqyu====="
(
  set -e
  python 'chaos_framework_secure.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmukcw094-cwrqyu exit=${code}====="
exit "$code"
