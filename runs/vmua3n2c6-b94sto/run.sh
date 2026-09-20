#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmua3n2c6-b94sto====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmua3n2c6-b94sto exit=${code}====="
exit "$code"
