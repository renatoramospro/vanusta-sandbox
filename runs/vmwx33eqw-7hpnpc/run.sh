#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwx33eqw-7hpnpc====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwx33eqw-7hpnpc exit=${code}====="
exit "$code"
