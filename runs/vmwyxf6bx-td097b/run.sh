#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwyxf6bx-td097b====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwyxf6bx-td097b exit=${code}====="
exit "$code"
