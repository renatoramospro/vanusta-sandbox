#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuh33z1n-ahwkw1====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuh33z1n-ahwkw1 exit=${code}====="
exit "$code"
