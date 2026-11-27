#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwyimqgz-500sme====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwyimqgz-500sme exit=${code}====="
exit "$code"
