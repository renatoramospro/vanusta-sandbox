#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuimy1wl-w6uhpv====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest 'pytest' 'pytest-asyncio'
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuimy1wl-w6uhpv exit=${code}====="
exit "$code"
