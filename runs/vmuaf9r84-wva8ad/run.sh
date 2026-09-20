#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuaf9r84-wva8ad====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuaf9r84-wva8ad exit=${code}====="
exit "$code"
