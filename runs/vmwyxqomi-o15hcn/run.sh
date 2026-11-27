#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwyxqomi-o15hcn====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwyxqomi-o15hcn exit=${code}====="
exit "$code"
