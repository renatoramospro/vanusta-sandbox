#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmufcf10p-z28rur====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest 'PyJWT==2.8.0' 'pytest==8.0.0'
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmufcf10p-z28rur exit=${code}====="
exit "$code"
