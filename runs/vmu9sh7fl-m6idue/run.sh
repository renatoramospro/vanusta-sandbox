#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmu9sh7fl-m6idue====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmu9sh7fl-m6idue exit=${code}====="
exit "$code"
