#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuijiepl-8ikqvs====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuijiepl-8ikqvs exit=${code}====="
exit "$code"
