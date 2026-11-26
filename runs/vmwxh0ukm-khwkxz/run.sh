#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwxh0ukm-khwkxz====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwxh0ukm-khwkxz exit=${code}====="
exit "$code"
