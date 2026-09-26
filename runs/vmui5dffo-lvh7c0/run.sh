#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmui5dffo-lvh7c0====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmui5dffo-lvh7c0 exit=${code}====="
exit "$code"
