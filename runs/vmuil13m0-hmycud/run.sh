#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuil13m0-hmycud====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuil13m0-hmycud exit=${code}====="
exit "$code"
