#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmubnxcwh-kb6sx0====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmubnxcwh-kb6sx0 exit=${code}====="
exit "$code"
