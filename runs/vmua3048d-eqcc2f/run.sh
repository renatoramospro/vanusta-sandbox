#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmua3048d-eqcc2f====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmua3048d-eqcc2f exit=${code}====="
exit "$code"
