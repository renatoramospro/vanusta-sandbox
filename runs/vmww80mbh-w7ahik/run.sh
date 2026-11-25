#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmww80mbh-w7ahik====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmww80mbh-w7ahik exit=${code}====="
exit "$code"
