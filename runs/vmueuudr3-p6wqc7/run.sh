#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmueuudr3-p6wqc7====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmueuudr3-p6wqc7 exit=${code}====="
exit "$code"
