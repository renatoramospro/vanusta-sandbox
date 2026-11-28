#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmx07fllx-8306ib====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmx07fllx-8306ib exit=${code}====="
exit "$code"
