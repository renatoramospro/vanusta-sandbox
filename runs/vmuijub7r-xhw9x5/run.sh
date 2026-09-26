#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuijub7r-xhw9x5====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuijub7r-xhw9x5 exit=${code}====="
exit "$code"
