#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuj59rli-tihsjo====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuj59rli-tihsjo exit=${code}====="
exit "$code"
