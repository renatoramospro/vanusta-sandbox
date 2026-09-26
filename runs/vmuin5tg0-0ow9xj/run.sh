#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuin5tg0-0ow9xj====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest 'pytest' 'pytest-asyncio'
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuin5tg0-0ow9xj exit=${code}====="
exit "$code"
