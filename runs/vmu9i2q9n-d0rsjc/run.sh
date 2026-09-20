#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmu9i2q9n-d0rsjc====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest 'pytest==7.4.3' 'pytest-asyncio==0.21.1'
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmu9i2q9n-d0rsjc exit=${code}====="
exit "$code"
