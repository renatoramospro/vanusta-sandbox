#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmui4q9qf-4aplhi====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmui4q9qf-4aplhi exit=${code}====="
exit "$code"
