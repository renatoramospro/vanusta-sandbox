#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuchjcl1-ioqhvi====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuchjcl1-ioqhvi exit=${code}====="
exit "$code"
