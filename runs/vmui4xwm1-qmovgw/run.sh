#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmui4xwm1-qmovgw====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmui4xwm1-qmovgw exit=${code}====="
exit "$code"
