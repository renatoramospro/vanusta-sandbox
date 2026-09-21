#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmubillbz-m93uol====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmubillbz-m93uol exit=${code}====="
exit "$code"
