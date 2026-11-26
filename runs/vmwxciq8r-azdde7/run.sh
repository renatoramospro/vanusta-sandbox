#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwxciq8r-azdde7====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwxciq8r-azdde7 exit=${code}====="
exit "$code"
