#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuerb0g4-25xcb9====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuerb0g4-25xcb9 exit=${code}====="
exit "$code"
