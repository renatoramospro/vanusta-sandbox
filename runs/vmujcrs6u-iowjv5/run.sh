#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmujcrs6u-iowjv5====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmujcrs6u-iowjv5 exit=${code}====="
exit "$code"
