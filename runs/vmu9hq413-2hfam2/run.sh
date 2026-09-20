#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmu9hq413-2hfam2====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest 'pytest' 'pytest-asyncio'
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmu9hq413-2hfam2 exit=${code}====="
exit "$code"
