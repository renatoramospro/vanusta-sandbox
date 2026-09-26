#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuiog2f4-i9w60u====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest 'pytest' 'pytest-asyncio'
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuiog2f4-i9w60u exit=${code}====="
exit "$code"
