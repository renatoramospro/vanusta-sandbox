#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmu9i2pwo-2j7dd3====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest 'pytest' 'pytest-asyncio'
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmu9i2pwo-2j7dd3 exit=${code}====="
exit "$code"
