#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmx07qb7q-24irtc====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmx07qb7q-24irtc exit=${code}====="
exit "$code"
