#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmu9htk6i-f11x05====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmu9htk6i-f11x05 exit=${code}====="
exit "$code"
