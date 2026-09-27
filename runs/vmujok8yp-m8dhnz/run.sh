#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmujok8yp-m8dhnz====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmujok8yp-m8dhnz exit=${code}====="
exit "$code"
