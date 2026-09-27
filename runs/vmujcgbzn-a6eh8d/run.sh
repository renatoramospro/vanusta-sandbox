#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmujcgbzn-a6eh8d====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmujcgbzn-a6eh8d exit=${code}====="
exit "$code"
