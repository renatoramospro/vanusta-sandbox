#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuinp1wt-sx8uvw====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest 'pytest' 'pytest-asyncio'
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuinp1wt-sx8uvw exit=${code}====="
exit "$code"
