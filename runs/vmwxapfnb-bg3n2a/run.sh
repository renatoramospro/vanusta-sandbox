#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwxapfnb-bg3n2a====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwxapfnb-bg3n2a exit=${code}====="
exit "$code"
