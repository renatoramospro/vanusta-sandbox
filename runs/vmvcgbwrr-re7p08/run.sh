#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvcgbwrr-re7p08====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvcgbwrr-re7p08 exit=${code}====="
exit "$code"
