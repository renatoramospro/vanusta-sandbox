#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuf5o6bt-tlxqie====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuf5o6bt-tlxqie exit=${code}====="
exit "$code"
