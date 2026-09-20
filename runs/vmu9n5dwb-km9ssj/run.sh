#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmu9n5dwb-km9ssj====="
(
  set -e
  python -m pip install -q --disable-pip-version-check 'cryptography'
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmu9n5dwb-km9ssj exit=${code}====="
exit "$code"
