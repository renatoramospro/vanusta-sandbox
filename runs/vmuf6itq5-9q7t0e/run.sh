#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuf6itq5-9q7t0e====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuf6itq5-9q7t0e exit=${code}====="
exit "$code"
