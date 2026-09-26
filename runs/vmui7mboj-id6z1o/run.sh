#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmui7mboj-id6z1o====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmui7mboj-id6z1o exit=${code}====="
exit "$code"
